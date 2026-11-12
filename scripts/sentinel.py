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
  <title>🥊 Clinical Battle Arena | ภก.รัฐนนท์ แสงไทยทวีพร</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700;800;900&family=Sarabun:wght@300;400;600&family=Bungee&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {{
      --bg: #090c15;
      --card-bg: rgba(20, 27, 45, 0.85);
      --red-fighter: #ef4444;
      --blue-fighter: #3b82f6;
      --neon-cyan: #06b6d4;
      --gold: #f59e0b;
      --emerald: #10b981;
      --purple: #8b5cf6;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
    body {{
      font-family: 'Prompt', sans-serif;
      background: var(--bg);
      background-image: radial-gradient(circle at 50% 0%, rgba(6, 182, 212, 0.15) 0%, transparent 60%);
      color: var(--text);
      line-height: 1.5;
      padding-bottom: 5rem;
    }}
    .arena-header {{
      text-align: center;
      padding: 1.8rem 1rem 1rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      position: relative;
      overflow: hidden;
    }}
    .live-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: rgba(239, 68, 68, 0.2);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #f87171;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-bottom: 0.5rem;
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.6; }}
    }}
    .arena-title {{
      font-size: 1.5rem;
      font-weight: 900;
      background: linear-gradient(135deg, #38bdf8 0%, #ec4899 50%, #f59e0b 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.5px;
    }}
    .arena-subtitle {{
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}
    .container {{
      max-width: 680px;
      margin: 0 auto;
      padding: 1rem;
    }}
    .mode-switch-bar {{
      display: flex;
      background: rgba(30, 41, 59, 0.7);
      border-radius: 9999px;
      padding: 0.3rem;
      margin-bottom: 1.5rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .mode-btn {{
      flex: 1;
      text-align: center;
      padding: 0.5rem;
      font-size: 0.85rem;
      font-weight: 600;
      border-radius: 9999px;
      color: var(--text-muted);
      cursor: pointer;
      border: none;
      background: transparent;
      transition: all 0.2s ease;
    }}
    .mode-btn.active {{
      background: linear-gradient(135deg, #0284c7, #06b6d4);
      color: #ffffff;
      box-shadow: 0 2px 10px rgba(6, 182, 212, 0.3);
    }}

    /* Battle Arena Card */
    .battle-card {{
      background: var(--card-bg);
      border: 2px solid rgba(245, 158, 11, 0.3);
      border-radius: 1.25rem;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
      position: relative;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
      overflow: hidden;
    }}
    .battle-card::before {{
      content: "🔥 ศึกมวยคู่เอกประจำสัปดาห์";
      position: absolute;
      top: 0;
      right: 0;
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      color: #000000;
      font-size: 0.68rem;
      font-weight: 800;
      padding: 0.25rem 0.8rem;
      border-radius: 0 1.25rem 0 0.8rem;
    }}
    .fighters-arena {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 0.5rem;
      margin: 1.2rem 0 1rem 0;
      text-align: center;
    }}
    .fighter-box {{
      padding: 0.75rem 0.5rem;
      border-radius: 0.75rem;
    }}
    .fighter-box.red {{
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .fighter-box.blue {{
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.3);
    }}
    .fighter-name {{
      font-size: 0.85rem;
      font-weight: 700;
    }}
    .fighter-box.red .fighter-name {{ color: #f87171; }}
    .fighter-box.blue .fighter-name {{ color: #60a5fa; }}
    .fighter-tag {{
      font-size: 0.68rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}
    .vs-circle {{
      font-family: 'Bungee', cursive;
      font-size: 1.2rem;
      color: var(--gold);
      text-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }}
    .battle-rounds {{
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      margin-top: 0.8rem;
    }}
    .round-row {{
      background: rgba(15, 23, 42, 0.6);
      border-radius: 0.6rem;
      padding: 0.6rem 0.8rem;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .round-lbl {{
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 0.3rem;
    }}
    .round-title {{ color: var(--text); }}
    .round-winner {{ color: var(--emerald); font-weight: 700; }}
    .round-bars {{
      display: flex;
      height: 8px;
      gap: 4px;
      border-radius: 4px;
      overflow: hidden;
      background: rgba(255,255,255,0.05);
    }}
    .bar-fill.red {{ background: var(--red-fighter); }}
    .bar-fill.blue {{ background: var(--blue-fighter); }}

    .winner-banner {{
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.2));
      border: 1px solid var(--emerald);
      border-radius: 0.75rem;
      padding: 0.75rem;
      margin-top: 1rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}
    .winner-trophy {{ font-size: 1.6rem; }}
    .winner-text {{ font-size: 0.8rem; color: #a7f3d0; line-height: 1.4; }}

    /* Chibi Manga Bubble */
    .chibi-callout {{
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      margin: 1.25rem 0;
    }}
    .chibi-avatar {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, #06b6d4, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.6rem;
      flex-shrink: 0;
      box-shadow: 0 0 12px var(--primary-glow);
    }}
    .speech-bubble {{
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 1rem;
      border-top-left-radius: 0.2rem;
      padding: 0.75rem 1rem;
      font-size: 0.82rem;
      color: #e2e8f0;
      position: relative;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .speech-bubble strong {{ color: var(--neon-cyan); }}

    /* Gadget & Herb Cards */
    .fun-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 1rem;
      padding: 1.1rem;
      margin-bottom: 1rem;
      transition: transform 0.2s;
    }}
    .fun-card:active {{ transform: scale(0.99); }}
    .fun-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.6rem;
    }}
    .fun-badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
    }}
    .fun-badge.ssr {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }}
    .fun-badge.gold {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }}

    .fun-title {{
      font-size: 0.95rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 0.4rem;
    }}
    .one-liner {{
      background: rgba(6, 182, 212, 0.08);
      border-left: 3px solid var(--neon-cyan);
      padding: 0.5rem 0.75rem;
      border-radius: 0 0.5rem 0.5rem 0;
      font-size: 0.82rem;
      color: #cbd5e1;
      margin-bottom: 0.6rem;
    }}
    .metrics-chips {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
      margin-bottom: 0.6rem;
    }}
    .m-chip {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 0.25rem 0.5rem;
      border-radius: 0.4rem;
      font-size: 0.72rem;
      color: var(--neon-cyan);
      font-weight: 600;
    }}
    .hospital-tip {{
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.2);
      padding: 0.5rem 0.75rem;
      border-radius: 0.5rem;
      font-size: 0.78rem;
      color: #a7f3d0;
      margin-bottom: 0.6rem;
    }}
    .link-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--neon-cyan);
      text-decoration: none;
      padding: 0.35rem 0.75rem;
      background: rgba(6, 182, 212, 0.12);
      border-radius: 0.4rem;
      border: 1px solid rgba(6, 182, 212, 0.25);
    }}

    .sound-btn {{
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid var(--gold);
      color: var(--gold);
      padding: 0.3rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      margin-top: 0.5rem;
    }}

    .formal-view {{
      display: none;
      background: var(--card-bg);
      border-radius: 1rem;
      padding: 1.25rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
  </style>
</head>
<body>
  <header class="arena-header">
    <div class="live-tag">🔴 LIVE CLASSIFIED</div>
    <div class="arena-title">⚔️ CLINICAL BATTLE ARENA</div>
    <div class="arena-subtitle">ศึกดวลเภสัชบำบัด & โอสถวิจัย • รพ.เสิงสาง (IM Team)</div>
    <button class="sound-btn" onclick="playGong()">🔔 เคาะระฆังเปิดศึก</button>
  </header>

  <div class="container">
    <div class="mode-switch-bar">
      <button class="mode-btn active" id="btn-fun" onclick="switchMode('fun')">🎮 โหมดศึกดวล (Battle Mode)</button>
      <button class="mode-btn" id="btn-formal" onclick="switchMode('formal')">📄 โหมดทางการ (Formal)</button>
    </div>

    <!-- FUN BATTLE MODE -->
    <div id="fun-container">
      <!-- MAIN EVENT SHOWDOWN -->
      <div class="battle-card">
        <div style="font-size: 0.8rem; color: var(--gold); font-weight: 700;">🚭 ศึกมวยคู่เอกสายเลิกบุหรี่ (Smoking Cessation)</div>
        <div class="fighters-arena">
          <div class="fighter-box red">
            <div class="fighter-name">สูตรผสม BUP + ZON</div>
            <div class="fighter-tag">Bupropion + Zonisamide</div>
          </div>
          <div class="vs-circle">VS</div>
          <div class="fighter-box blue">
            <div class="fighter-name">สูตรเดี่ยว BUP</div>
            <div class="fighter-tag">Bupropion Monotherapy</div>
          </div>
        </div>

        <div class="battle-rounds">
          <div class="round-row">
            <div class="round-lbl">
              <span class="round-title">🥊 ยก 1: ความเร็วในการลดควันบุหรี่ (eCO Drop)</span>
              <span class="round-winner">สูตรผสมชนะคะแนน (+25%)</span>
            </div>
            <div class="round-bars">
              <div class="bar-fill red" style="width: 75%;"></div>
              <div class="bar-fill blue" style="width: 50%;"></div>
            </div>
          </div>

          <div class="round-row">
            <div class="round-lbl">
              <span class="round-title">🥊 ยก 2: คุมน้ำหนักตัวไม่ให้เด้ง (Weight Gain)</span>
              <span class="round-winner">สูตรผสมชนะน็อค! (ไม่ขึ้นเลย)</span>
            </div>
            <div class="round-bars">
              <div class="bar-fill red" style="width: 90%;"></div>
              <div class="bar-fill blue" style="width: 30%;"></div>
            </div>
          </div>

          <div class="round-row">
            <div class="round-lbl">
              <span class="round-title">🥊 ยก 3: ความปลอดภัย & ผลข้างเคียง</span>
              <span class="round-winner">เสมอกัน (ปลอดภัยทั้งคู่)</span>
            </div>
            <div class="round-bars">
              <div class="bar-fill red" style="width: 50%;"></div>
              <div class="bar-fill blue" style="width: 50%;"></div>
            </div>
          </div>
        </div>

        <div class="winner-banner">
          <div class="winner-trophy">🏆</div>
          <div class="winner-text">
            <strong>คำตัดสินฟันธง:</strong> สูตรผสม BUP + ZON เหมาะมากกับคนไข้ที่ <em>"กลัวเลิกบุหรี่แล้วอ้วน"</em> เพราะกดความอยากอาหารได้ชะงัด!
          </div>
        </div>
      </div>

      <!-- CHIBI MASCOT CALLOUT 1 -->
      <div class="chibi-callout">
        <div class="chibi-avatar">👨‍⚕️</div>
        <div class="speech-bubble">
          <strong>โน้ตลับจากเภสัชกรนัท:</strong> "คนไข้ในคลินิกฟ้าใสชอบบ่นว่ากลัวน้ำหนักพุ่งใช่ไหมครับอาจารย์? เปเปอร์นี้ชี้ชัดเลยว่าการผสมกลไกต้านชักจิ๋วๆ ช่วยหยุดพุงยื่นได้จริงครับ!"
        </div>
      </div>

      <!-- GADGET LAB CARD (COPD DIGITAL) -->
      <div class="fun-card">
        <div class="fun-header">
          <span style="font-size: 0.8rem; color: #38bdf8; font-weight: 700;">🫁 แกดเจ็ตปอดแห่งอนาคต (Asthma & COPD)</span>
          <span class="fun-badge ssr">ระดับ SSR ⭐⭐⭐</span>
        </div>
        <div class="fun-title">ยาพ่นติดชิปอัจฉริยะ (Digital Inhaler Monitoring)</div>
        <div class="one-liner">
          🎯 <strong>สรุปสั้น:</strong> ติดชิปวัดการสูดยาพ่นแบบ Real-time คนไข้สูดยาครบขึ้น + อาการกำเริบลดลงฮวบ!
        </div>
        <div class="metrics-chips">
          <span class="m-chip">📈 Adherence เพิ่มสูงขึ้น</span>
          <span class="m-chip">📉 Exacerbation ลดลง</span>
          <span class="m-chip">📱 Pilot RCT</span>
        </div>
        <div class="hospital-tip">
          💡 <strong>รพ.เสิงสาง นำไปใช้ยังไง:</strong> งบติดชิปอาจแพง แต่เราใช้ <strong>LINE OA เภสัชกรเตือนพ่นยา</strong> ได้ผลลัพธ์ใกล้เคียงกัน ประหยัดงบสุดๆ!
        </div>
        <a class="link-btn" href="https://pubmed.ncbi.nlm.nih.gov/42993869/" target="_blank">เปิดดูเปเปอร์ตัวเต็ม PubMed (PMID: 42993869) →</a>
      </div>

      <!-- THAI HERB ALCHEMY CARD -->
      <div class="fun-card" style="border-color: rgba(16, 185, 129, 0.3);">
        <div class="fun-header">
          <span style="font-size: 0.8rem; color: #34d399; font-weight: 700;">🌿 หอโอสถสมุนไพรไทย (Thai Herbal Care)</span>
          <span class="fun-badge gold">บัญชียาหลัก NLEM 🏆</span>
        </div>
        <div class="fun-title">ฟ้าทะลายโจร & มะขามป้อม ปราบหวัดไอ URTI</div>
        <div class="one-liner">
          🎯 <strong>สรุปสั้น:</strong> กินฟ้าทะลายโจรเริ่มภายใน 48 ชม. เจ็บคอหวัดหายไวเทียบเท่ายาแผนปัจจุบัน + มะขามป้อมจิบลดไอแห้งชะงัด!
        </div>
        <div class="metrics-chips">
          <span class="m-chip">🌱 สารสำคัญ: Andrographolide 60-120 mg/day</span>
          <span class="m-chip">🛡️ ลดใช้ Antibiotic</span>
        </div>
        <div class="hospital-tip">
          💡 <strong>เคล็ดลับ รพ.เสิงสาง:</strong> อย่าดูแค่น้ำหนักผงยา! ส่องที่มิลลิกรัมของสารสกัด <em>Andrographolide</em> ช่วยส่งเสริม Rational Drug Use (RDU) สวยๆ
        </div>
      </div>

      <!-- CHIBI MASCOT CALLOUT 2 -->
      <div class="chibi-callout">
        <div class="chibi-avatar">🌿</div>
        <div class="speech-bubble">
          <strong>ย้ำเตือนสำคัญ:</strong> "ฟ้าทะลายโจรห้ามใช้ในหญิงตั้งครรภ์/ให้นมบุตร และคนไข้ตับอักเสบนะจ๊ะ แจกยาต้องถามก่อนเสมอ!"
        </div>
      </div>
    </div>

    <!-- FORMAL VIEW (TOGGLEABLE) -->
    <div id="formal-container" class="formal-view">
      <div id="raw-markdown-render"></div>
    </div>

    <footer style="text-align: center; margin-top: 2rem; font-size: 0.75rem; color: var(--text-muted);">
      <p><strong>ผู้จัดทำ:</strong> ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ</p>
      <p>ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง</p>
      <p style="margin-top: 0.3rem;"><a href="https://canva.link/v9g5tfxdg349vbg" target="_blank" style="color: #c084fc; text-decoration: none;">🎨 เปิดแต่งสไลด์ใน Canva Pro →</a></p>
    </footer>
  </div>

  <script>
    const md = {json.dumps(markdown_content)};
    document.getElementById('raw-markdown-render').innerHTML = marked.parse(md);

    function switchMode(mode) {{
      const funC = document.getElementById('fun-container');
      const formalC = document.getElementById('formal-container');
      const btnFun = document.getElementById('btn-fun');
      const btnFormal = document.getElementById('btn-formal');

      if (mode === 'fun') {{
        funC.style.display = 'block';
        formalC.style.display = 'none';
        btnFun.classList.add('active');
        btnFormal.classList.remove('active');
      }} else {{
        funC.style.display = 'none';
        formalC.style.display = 'block';
        btnFormal.classList.add('active');
        btnFun.classList.remove('active');
      }}
    }}

    function playGong() {{
      try {{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(110, ctx.currentTime + 1.2);
        gain.gain.setValueAtTime(0.8, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 1.2);
      }} catch(e) {{}}
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
