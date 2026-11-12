#!/usr/bin/env python3
"""
PubMed Clinical Sentinel
Master Automated Surveillance Pipeline for:
- Asthma & COPD Pharmacotherapy
- Smoking Cessation Pharmacotherapy
- Thai Herbal Medicine in Respiratory Care

Author: ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ
Hospital: โรงพยาบาลเสิงสาง
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
SEEN_FILE = os.path.join(DATA_DIR, "seen_pmids.json")

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
USER_AGENT = "PubMedClinicalSentinel/1.0 (nutcodelaw@gmail.com; Soeng Sang Hospital IM Team)"

TRACK_CONFIGS = [
    {
        "id": "asthma_copd",
        "name": "Asthma & COPD Pharmacotherapy",
        "name_th": "เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD)",
        "days": 14,
        "max_results": 4,
        "query": (
            '("Asthma"[Mesh] OR "Pulmonary Disease, Chronic Obstructive"[Mesh] OR Asthma[tiab] OR COPD[tiab]) '
            'AND ("Drug Therapy"[Mesh] OR "pharmacotherapy"[tiab] OR "triple therapy"[tiab] OR "biologic"[tiab] '
            'OR "inhaler"[tiab] OR "ensifentrine"[tiab] OR "dupilumab"[tiab] OR "mepolizumab"[tiab] '
            'OR "benralizumab"[tiab] OR "tezepelumab"[tiab] OR "itepekimab"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
        )
    },
    {
        "id": "smoking_cessation",
        "name": "Smoking Cessation Pharmacotherapy",
        "name_th": "เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation)",
        "days": 60,
        "max_results": 3,
        "query": (
            '("Smoking Cessation"[Mesh] OR "smoking cessation"[tiab] OR "tobacco cessation"[tiab]) '
            'AND ("Varenicline"[Mesh] OR "Bupropion"[Mesh] OR "Cytisine"[Mesh] OR "varenicline"[tiab] '
            'OR "cytisine"[tiab] OR "bupropion"[tiab] OR "nicotine replacement"[tiab] OR "NRT"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
        )
    },
    {
        "id": "thai_herbs",
        "name": "Thai Herbal Medicine in Respiratory Care",
        "name_th": "สมุนไพรไทยและการแพทย์ผสมผสานด้านระบบทางเดินหายใจ",
        "days": 180,
        "max_results": 3,
        "query": (
            '("Vernonia cinerea"[tiab] OR "little ironweed"[tiab] OR "Andrographis paniculata"[tiab] '
            'OR "andrographolide"[tiab] OR "Curcuma longa"[tiab] OR "curcumin"[tiab] OR "Phyllanthus emblica"[tiab]) '
            'AND ("respiratory"[tiab] OR "cough"[tiab] OR "asthma"[tiab] OR "copd"[tiab] OR "pulmonary"[tiab] '
            'OR "smoking"[tiab] OR "bronchitis"[tiab] OR "airway"[tiab] OR "anti-inflammatory"[tiab] OR "antioxidant"[tiab]) '
            'AND ("Humans"[Mesh] OR "Clinical Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt])'
        )
    }
]

def load_seen_pmids():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_updated": None, "processed_pmids": []}

def save_seen_pmids(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def search_pubmed_pmids(term, reldate=14, retmax=10):
    params = {
        "db": "pubmed",
        "term": term,
        "reldate": reldate,
        "datetype": "edat",
        "retmax": retmax,
        "retmode": "json",
        "sort": "pub_date"
    }
    url = f"{NCBI_ESEARCH}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[WARN] PubMed search failed for query: {e}")
        return []

def fetch_pubmed_articles(pmids):
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    url = f"{NCBI_EFETCH}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"[ERROR] Failed to fetch PubMed XML: {e}")
        return []

    articles = []
    try:
        root = ET.fromstring(xml_data)
        for article_tag in root.findall(".//PubmedArticle"):
            pmid_tag = article_tag.find(".//MedlineCitation/PMID")
            pmid = pmid_tag.text if pmid_tag is not None else ""

            title_tag = article_tag.find(".//ArticleTitle")
            title = "".join(title_tag.itertext()).strip() if title_tag is not None else "No Title"

            journal_tag = article_tag.find(".//Journal/Title")
            if journal_tag is None:
                journal_tag = article_tag.find(".//Journal/ISOAbbreviation")
            journal = journal_tag.text if journal_tag is not None else "Unknown Journal"

            # PubDate
            year = article_tag.find(".//JournalIssue/PubDate/Year")
            month = article_tag.find(".//JournalIssue/PubDate/Month")
            day = article_tag.find(".//JournalIssue/PubDate/Day")
            pub_date = f"{year.text if year is not None else ''} {month.text if month is not None else ''}".strip()

            # Abstract
            abstract_parts = []
            for ab_text in article_tag.findall(".//Abstract/AbstractText"):
                label = ab_text.get("Label", "")
                text = "".join(ab_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = "\n\n".join(abstract_parts) if abstract_parts else "Abstract not available."

            # DOI
            doi = ""
            for id_tag in article_tag.findall(".//ArticleIdList/ArticleId"):
                if id_tag.get("IdType") == "doi":
                    doi = id_tag.text or ""
                    break

            articles.append({
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "pub_date": pub_date,
                "doi": doi,
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
    except Exception as e:
        print(f"[ERROR] XML parsing error: {e}")

    return articles

def analyze_with_gemini(articles_by_track, report_date):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[WARN] GEMINI_API_KEY is not set. Using structured fallback formatter.")
        return generate_fallback_report(articles_by_track, report_date)

    # Prepare compact payload to avoid token limits / 503 timeouts
    compact_tracks = {}
    for tid, articles in articles_by_track.items():
        compact_tracks[tid] = []
        for a in articles:
            compact_tracks[tid].append({
                "pmid": a["pmid"],
                "title": a["title"],
                "journal": a["journal"],
                "pub_date": a["pub_date"],
                "abstract": a["abstract"][:800] + ("..." if len(a["abstract"]) > 800 else "")
            })

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านเภสัชบำบัดทางคลินิก ร่วมกับท่านประธาน ภก.รัฐนนท์ แสงไทยทวีพร (เภสัชกรชำนาญการ ประธานทีม IM โรงพยาบาลเสิงสาง)

หน้าที่: จัดทำสรุปรายงานงานวิจัยทางคลินิกใหม่ด้าน Asthma, COPD, ยาช่วยเลิกบุหรี่ และสมุนไพรไทย ประจำวันที่ {report_date}

ข้อมูลงานวิจัยจาก PubMed:
{json.dumps(compact_tracks, ensure_ascii=False, indent=2)}

กฎเหล็กรูปแบบการนำเสนอ (สำคัญที่สุด):
- **ห้ามเขียนเป็น Text บรรยายยาวๆ เป็นพารากราฟเด็ดขาด** 
- ให้สรุปแบบ **"Quick-Scan Card"** เน้นความกระชับ ตรงเป้า สกัดเฉพาะเนื้อหาใจความสำคัญ ให้อ่านจบใน 10 วินาทีต่อเรื่อง

สำหรับแต่ละบทความ ให้ใช้โครงสร้างสั้น กระชับ ดังนี้:
### [ลำดับ]. [ชื่อเรื่องภาษาอังกฤษสั้นๆ]
- **วารสาร & PMID:** [ชื่อย่อวารสาร] ([ปี/เดือน]) • [PMID: <PMID>](https://pubmed.ncbi.nlm.nih.gov/<PMID>/)
- 🎯 **ใจความสำคัญ 1 บรรทัด:** [สรุปประเด็นหลักสั้นที่สุด ไม่เกิน 1-2 บรรทัด]
- 📊 **ตัวเลขผลลัพธ์สำคัญ:** 
  • [สถิติ/ผลลัพธ์ 1: เช่น N=..., ลดกำเริบ...%, FEV1...]
  • [สถิติ/ผลลัพธ์ 2: ความปลอดภัย/ผลข้างเคียง]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** [นัยสำคัญทางคลินิกต่อ รพ.ชุมชน 1 ข้อสั้นๆ คมๆ]
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/<PMID>/)

แบ่งเนื้อหาเป็น 3 หมวดชัดเจน:
1. 🫁 เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD)
2. 🚭 เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation)
3. 🌿 สมุนไพรไทยทางคลินิกในระบบทางเดินหายใจ (Thai Herbal Medicine)
(หากหมวดใดไม่มีเปเปอร์ใหม่ ให้สรุป Landmark Study หรือ Clinical Review สั้นๆ 1 เรื่องแทน)

ท้ายรายงานให้ลงท้ายว่า:
---
**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  
*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*
"""

    models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]

    # Try official google.genai SDK first
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for model_name in models_to_try:
            try:
                print(f"[AI] Calling Gemini SDK with model: {model_name}...")
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if resp and resp.text:
                    return resp.text
            except Exception as me:
                print(f"[WARN] Model {model_name} failed: {me}. Trying next...")
    except ImportError:
        print("[INFO] google.genai not installed, using REST API fallback.")

    # REST API fallback
    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"[WARN] REST API call for {model_name} failed: {e}")

    print("[ERROR] All Gemini models failed. Using structured fallback.")
    return generate_fallback_report(articles_by_track, report_date)

def generate_fallback_report(articles_by_track, report_date):
    lines = [
        f"# 🩺 สรุปรายงานวิจัยทางคลินิกด้านระบบทางเดินหายใจ & ยาช่วยเลิกบุหรี่ & สมุนไพรไทย",
        f"**ประจำวันที่:** {report_date} | **สถานะ:** PubMed E-Utilities Direct Feed\n",
        "> [!NOTE]\n> รายงานนี้ดึงข้อมูลตรงจาก PubMed NCBI อัตโนมัติ\n"
    ]

    for track in TRACK_CONFIGS:
        tid = track["id"]
        tname = track["name_th"]
        articles = articles_by_track.get(tid, [])
        lines.append(f"## 📌 {tname}")
        if not articles:
            lines.append("*(ไม่พบงานวิจัยใหม่ที่มีนัยสำคัญในรอบการค้นหานี้)*\n")
            continue

        for i, a in enumerate(articles, 1):
            doi_str = f" | DOI: {a['doi']}" if a.get('doi') else ""
            lines.append(f"### {i}. {a['title']}")
            lines.append(f"- **วารสาร & วันที่:** {a['journal']} ({a['pub_date']})")
            lines.append(f"- **แหล่งอ้างอิง:** [PMID: {a['pmid']}]({a['url']}){doi_str}")
            lines.append(f"- **บทคัดย่อ (Abstract สรุป):**\n  > {a['abstract'][:400]}...\n")

    lines.append("---\n**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  \n*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*")
    return "\n".join(lines)

def generate_html_dashboard(markdown_content, report_date, articles_by_track):
    total_articles = sum(len(v) for v in articles_by_track.values())
    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>PubMed Clinical Sentinel | ภก.รัฐนนท์ แสงไทยทวีพร</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&family=Sarabun:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: rgba(22, 30, 49, 0.75);
      --card-border: rgba(56, 189, 248, 0.15);
      --primary: #06b6d4;
      --primary-glow: rgba(6, 182, 212, 0.25);
      --emerald: #10b981;
      --amber: #f59e0b;
      --purple: #a855f7;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
    body {{
      font-family: 'Prompt', 'Sarabun', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding-bottom: 5rem;
    }}
    .app-header {{
      background: linear-gradient(180deg, rgba(6, 182, 212, 0.12) 0%, transparent 100%);
      padding: 1.5rem 1rem 1rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .header-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(6, 182, 212, 0.15);
      border: 1px solid rgba(6, 182, 212, 0.3);
      color: #38bdf8;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 0.6rem;
    }}
    .app-title {{
      font-size: 1.4rem;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .app-subtitle {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}
    .canva-banner-bar {{
      margin-top: 0.8rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(124, 58, 237, 0.15);
      border: 1px solid rgba(168, 85, 247, 0.3);
      padding: 0.5rem 0.85rem;
      border-radius: 0.75rem;
      font-size: 0.8rem;
    }}
    .canva-link {{
      color: #c084fc;
      text-decoration: none;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }}
    .sticky-controls {{
      position: sticky;
      top: 0;
      z-index: 40;
      background: rgba(9, 13, 22, 0.92);
      backdrop-filter: blur(12px);
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    .search-box {{
      width: 100%;
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.75rem;
      padding: 0.6rem 1rem;
      color: #ffffff;
      font-size: 0.88rem;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box:focus {{
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }}
    .filter-scroll {{
      display: flex;
      gap: 0.5rem;
      overflow-x: auto;
      margin-top: 0.65rem;
      padding-bottom: 0.2rem;
      scrollbar-width: none;
    }}
    .filter-scroll::-webkit-scrollbar {{ display: none; }}
    .pill-btn {{
      white-space: nowrap;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 500;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(30, 41, 59, 0.6);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s;
    }}
    .pill-btn.active {{
      background: var(--primary);
      color: #042f2e;
      font-weight: 600;
      border-color: var(--primary);
      box-shadow: 0 2px 10px var(--primary-glow);
    }}
    .container {{
      max-width: 760px;
      margin: 0 auto;
      padding: 1rem;
    }}
    .stat-cards {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.6rem;
      margin-bottom: 1.2rem;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 0.75rem;
      padding: 0.75rem;
      text-align: center;
    }}
    .stat-val {{
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--primary);
    }}
    .stat-lbl {{
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 0.1rem;
    }}
    .content-area {{
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}
    .content-area h1, .content-area h2 {{
      color: #38bdf8;
      font-size: 1.2rem;
      margin: 1.2rem 0 0.5rem 0;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .content-area h3 {{
      font-size: 1rem;
      color: #34d399;
      margin: 0.8rem 0 0.4rem 0;
    }}
    .content-area p, .content-area li {{
      color: #cbd5e1;
      font-size: 0.9rem;
      line-height: 1.6;
    }}
    .content-area ul {{
      margin-left: 1.2rem;
      margin-bottom: 0.8rem;
    }}
    .content-area a {{
      color: #38bdf8;
      text-decoration: none;
      font-weight: 500;
    }}
    .content-area blockquote {{
      border-left: 3px solid var(--primary);
      background: rgba(6, 182, 212, 0.08);
      padding: 0.6rem 0.85rem;
      border-radius: 0 0.5rem 0.5rem 0;
      margin: 0.75rem 0;
      color: #94a3b8;
      font-size: 0.85rem;
    }}
    .app-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.25rem;
      backdrop-filter: blur(8px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    .app-footer {{
      margin-top: 2.5rem;
      text-align: center;
      color: var(--text-muted);
      font-size: 0.75rem;
      padding-top: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="header-badge">🏥 โรงพยาบาลเสิงสาง • ทีม IM</div>
    <div class="app-title">🧬 PubMed Clinical Sentinel</div>
    <div class="app-subtitle">ระบบเฝ้าระวังและสังเคราะห์หลักฐานเชิงประจักษ์ทางคลินิก (Asthma • COPD • Smoking • Herbs)</div>
    
    <div class="canva-banner-bar">
      <span>🎨 ออกแบบร่วมกับ Canva Pro</span>
      <a class="canva-link" href="https://canva.link/v9g5tfxdg349vbg" target="_blank" rel="noopener">เปิดดู Template ใน Canva →</a>
    </div>
  </header>

  <div class="sticky-controls">
    <input type="text" id="searchInput" class="search-box" placeholder="🔍 ค้นหาชื่อยา, โรค, หรือคีย์เวิร์ด..." onkeyup="filterArticles()">
    <div class="filter-scroll">
      <button class="pill-btn active" onclick="setCategory('all', this)">🌟 ทั้งหมด</button>
      <button class="pill-btn" onclick="setCategory('asthma', this)">🫁 Asthma & COPD</button>
      <button class="pill-btn" onclick="setCategory('smoking', this)">🚭 เลิกบุหรี่</button>
      <button class="pill-btn" onclick="setCategory('herbs', this)">🌿 สมุนไพรไทย</button>
    </div>
  </div>

  <div class="container">
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-val">{report_date}</div>
        <div class="stat-lbl">รอบรายงาน</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{total_articles}</div>
        <div class="stat-lbl">เปเปอร์วิจัยใหม่</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">Tier-1</div>
        <div class="stat-lbl">มาตรฐานหลักฐาน</div>
      </div>
    </div>

    <main class="app-card content-area" id="markdown-container">
      <!-- Dynamic Markdown rendered here -->
    </main>

    <footer class="app-footer">
      <p><strong>ผู้รับผิดชอบระบบ:</strong> ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ</p>
      <p>ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง</p>
      <p style="margin-top: 0.4rem; color: #64748b;">Automated by GitHub Actions • Cloud 24/7</p>
    </footer>
  </div>

  <script>
    const rawMarkdown = {json.dumps(markdown_content)};
    const container = document.getElementById('markdown-container');
    container.innerHTML = marked.parse(rawMarkdown);

    function filterArticles() {{
      const query = document.getElementById('searchInput').value.toLowerCase();
      const headings = container.querySelectorAll('h3');
      headings.forEach(h3 => {{
        let content = h3.textContent.toLowerCase();
        let sibling = h3.nextElementSibling;
        let block = [h3];
        while (sibling && sibling.tagName !== 'H3' && sibling.tagName !== 'H2' && sibling.tagName !== 'H1') {{
          content += ' ' + sibling.textContent.toLowerCase();
          block.push(sibling);
          sibling = sibling.nextElementSibling;
        }}
        const match = content.includes(query);
        block.forEach(el => el.style.display = match ? '' : 'none');
      }});
    }}

    function setCategory(cat, btn) {{
      document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const text = btn.textContent.replace(/[^\u0E00-\u0E7Fa-zA-Z]/g, '').trim();
      document.getElementById('searchInput').value = cat === 'all' ? '' : text;
      filterArticles();
    }}
  </script>
</body>
</html>"""
    return html

def main():
    report_date = datetime.date.today().strftime("%Y-%m-%d")
    print(f"=== Starting PubMed Clinical Sentinel: {report_date} ===")

    seen_data = load_seen_pmids()
    seen_set = set(seen_data.get("processed_pmids", []))
    print(f"[INFO] Loaded {len(seen_set)} previously processed PMIDs.")

    articles_by_track = {}
    newly_discovered_pmids = []

    for track in TRACK_CONFIGS:
        tid = track["id"]
        tname = track["name"]
        print(f"\n[SCAN] Searching track: {tname} (Past {track['days']} days)...")

        pmids = search_pubmed_pmids(track["query"], reldate=track["days"], retmax=track["max_results"] * 2)
        print(f"  Found {len(pmids)} PMIDs in PubMed search.")

        # Deduplicate
        unseen_pmids = [p for p in pmids if p not in seen_set][:track["max_results"]]
        print(f"  Unseen target PMIDs to fetch: {unseen_pmids}")

        if unseen_pmids:
            articles = fetch_pubmed_articles(unseen_pmids)
            articles_by_track[tid] = articles
            newly_discovered_pmids.extend(unseen_pmids)
            print(f"  Successfully fetched {len(articles)} article details.")
        else:
            articles_by_track[tid] = []
            print(f"  No new unseen articles for track: {tname}")

    total_new = len(newly_discovered_pmids)
    print(f"\n[INFO] Total new unique articles across all tracks: {total_new}")

    # Generate Report using Gemini API
    print("[AI] Synthesizing clinical intelligence with Gemini API...")
    markdown_report = analyze_with_gemini(articles_by_track, report_date)

    # 1. Save README.md (Repository Front Page)
    readme_path = os.path.join(BASE_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"[SAVE] Updated {readme_path}")

    # 2. Save Historical Weekly Report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_file = os.path.join(REPORTS_DIR, f"{report_date}_respiratory_sentinel.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"[SAVE] Archived report to {report_file}")

    # 3. Save GitHub Pages Mobile Dashboard
    os.makedirs(DOCS_DIR, exist_ok=True)
    html_dashboard = generate_html_dashboard(markdown_report, report_date, articles_by_track)
    html_path = os.path.join(DOCS_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_dashboard)
    print(f"[SAVE] Generated mobile HTML dashboard at {html_path}")

    # 4. Update seen_pmids.json
    if newly_discovered_pmids:
        seen_data["processed_pmids"].extend(newly_discovered_pmids)
        seen_data["last_updated"] = report_date
        save_seen_pmids(seen_data)
        print(f"[DATA] Updated seen_pmids.json with {len(newly_discovered_pmids)} new PMIDs.")

    print("\n=== PubMed Clinical Sentinel completed successfully! ===")

if __name__ == "__main__":
    main()
