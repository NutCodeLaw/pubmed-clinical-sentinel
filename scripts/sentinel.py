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

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านเภสัชบำบัดทางคลินิก (Clinical Pharmacy Specialist) ร่วมกับท่านประธาน ภก.รัฐนนท์ แสงไทยทวีพร (เภสัชกรชำนาญการ ประธานทีม IM โรงพยาบาลเสิงสาง)

หน้าที่: จัดทำสรุปรายงานงานวิจัยทางคลินิกใหม่ด้าน Asthma, COPD, ยาช่วยเลิกบุหรี่ และสมุนไพรไทย ประจำวันที่ {report_date}

ข้อมูลงานวิจัยจาก PubMed:
{json.dumps(compact_tracks, ensure_ascii=False, indent=2)}

ข้อกำหนดการจัดทำรายงาน:
1. วิเคราะห์และสรุปบทความวิจัยที่น่าสนใจและมีนัยสำคัญทางคลินิก แบ่งตาม 3 หมวด:
   - หมวดที่ 1: เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD)
   - หมวดที่ 2: เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation)
   - หมวดที่ 3: สมุนไพรไทยทางคลินิกในระบบทางเดินหายใจ (Thai Herbal Medicine)

2. สำหรับแต่ละบทความ ให้สรุปในโครงสร้าง 5 มิติ:
   - **[ชื่อบทความและแหล่งอ้างอิง]**: ชื่อเรื่องภาษาอังกฤษ, วารสาร, PMID พร้อมลิงก์ https://pubmed.ncbi.nlm.nih.gov/<PMID>/
   - **[Study Design & Population]**: รูปแบบการศึกษา, ขนาดตัวอย่าง (N), ลักษณะประชากร/Biomarkers
   - **[Intervention & Regimen]**: ตัวยา/สูตรตำรับ, ขนาดยา, กลุ่มเปรียบเทียบ
   - **[Key Clinical Findings]**: ผลลัพธ์หลักทางคลินิก (Exacerbation, FEV1, Cessation rate, Safety)
   - **[Clinical Takeaway / Pharmacist's Insight]**: นัยสำคัญต่อแนวทางเวชปฏิบัติ (GINA, GOLD, แนวทางเลิกบุหรี่ หรือบัญชียาหลักแห่งชาติด้านสมุนไพร) และบริบท รพ.เสิงสาง/รพ.ชุมชน

3. หากหมวดใดไม่มีงานวิจัยใหม่ ให้ระบุสั้นๆ และสรุป Clinical Review / Landmark Study ที่น่าสนใจ 1 เรื่องแทน
4. ท้ายรายงานให้ลงท้ายว่า:
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PubMed Clinical Sentinel - ภก.รัฐนนท์ แสงไทยทวีพร</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {{
      --primary: #0284c7;
      --primary-dark: #0369a1;
      --accent: #10b981;
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Sarabun', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      padding: 1.5rem;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
    }}
    header {{
      background: linear-gradient(135deg, #0369a1 0%, #0f766e 100%);
      padding: 2rem;
      border-radius: 1rem;
      margin-bottom: 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }}
    header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    header p {{ color: #e2e8f0; font-size: 1rem; }}
    .stats-bar {{
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }}
    .stat-pill {{
      background: rgba(255,255,255,0.15);
      padding: 0.4rem 1rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      backdrop-filter: blur(4px);
    }}
    .content-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 1rem;
      padding: 2rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }}
    .content-card h1, .content-card h2, .content-card h3 {{
      color: #38bdf8;
      margin: 1.5rem 0 0.75rem 0;
    }}
    .content-card h2 {{
      border-bottom: 2px solid var(--border);
      padding-bottom: 0.5rem;
      font-size: 1.35rem;
    }}
    .content-card h3 {{
      font-size: 1.15rem;
      color: #34d399;
    }}
    .content-card p, .content-card li {{
      margin-bottom: 0.75rem;
      color: #cbd5e1;
    }}
    .content-card a {{
      color: #38bdf8;
      text-decoration: none;
      border-bottom: 1px dashed #38bdf8;
    }}
    .content-card a:hover {{ color: #7dd3fc; }}
    .content-card blockquote {{
      border-left: 4px solid var(--primary);
      padding-left: 1rem;
      margin: 1rem 0;
      color: var(--text-muted);
      background: rgba(2, 132, 199, 0.08);
      border-radius: 0 0.5rem 0.5rem 0;
      padding: 0.75rem 1rem;
    }}
    .content-card strong {{ color: #f8fafc; }}
    footer {{
      text-align: center;
      margin-top: 3rem;
      color: var(--text-muted);
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🧬 PubMed Clinical Sentinel</h1>
      <p>ระบบตรวจจับและสังเคราะห์หลักฐานเชิงประจักษ์ทางคลินิก (Asthma • COPD • Smoking Cessation • Thai Herbs)</p>
      <div class="stats-bar">
        <span class="stat-pill">📅 อัปเดต: {report_date}</span>
        <span class="stat-pill">📚 พบงานวิจัยใหม่: {total_articles} เรื่อง</span>
        <span class="stat-pill">🏥 รพ.เสิงสาง (IM Team)</span>
      </div>
    </header>

    <main class="content-card" id="report-body">
      <!-- Markdown rendered here -->
    </main>

    <footer>
      <p>PubMed Clinical Sentinel Automation Engine • Developed for ภก.รัฐนนท์ แสงไทยทวีพร</p>
      <p>Powered by GitHub Actions & Gemini API</p>
    </footer>
  </div>

  <script>
    const markdown = {json.dumps(markdown_content)};
    document.getElementById('report-body').innerHTML = marked.parse(markdown);
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
