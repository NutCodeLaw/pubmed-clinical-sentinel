#!/usr/bin/env python3
"""
PubMed Clinical Sentinel (v2.0 - 7-Track Surveillance Engine)
Master Automated Clinical Intelligence Pipeline:
1. Asthma & COPD Pharmacotherapy (14 days)
2. Smoking Cessation Pharmacotherapy (60 days)
3. Thai Herbal Medicine in Respiratory Care (180 days)
4. Cardio-Renal-Metabolic (CRM) & ชะลอไตเสื่อม (14 days)
5. Anticoagulation & High Alert Drugs (Warfarin & DOACs) (30 days)
6. Antimicrobial Stewardship (AMS) & Short-Course (45 days)
7. Deprescribing & Polypharmacy in Elderly (60 days)

Author: ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ
Hospital: โรงพยาบาลเสิงสาง (IM Team)
"""

import os
import sys
import re
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
USER_AGENT = "PubMedClinicalSentinel/2.0 (nutcodelaw@gmail.com; Soeng Sang Hospital IM Team)"

TRACK_CONFIGS = [
    {
        "id": "asthma_copd",
        "name": "Asthma & COPD Pharmacotherapy",
        "name_th": "เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD)",
        "icon": "🫁",
        "days": 14,
        "max_results": 3,
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
        "icon": "🚭",
        "days": 60,
        "max_results": 2,
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
        "icon": "🌿",
        "days": 180,
        "max_results": 2,
        "query": (
            '("Vernonia cinerea"[tiab] OR "little ironweed"[tiab] OR "Andrographis paniculata"[tiab] '
            'OR "andrographolide"[tiab] OR "Curcuma longa"[tiab] OR "curcumin"[tiab] OR "Phyllanthus emblica"[tiab]) '
            'AND ("respiratory"[tiab] OR "cough"[tiab] OR "asthma"[tiab] OR "copd"[tiab] OR "pulmonary"[tiab] '
            'OR "smoking"[tiab] OR "bronchitis"[tiab] OR "airway"[tiab] OR "anti-inflammatory"[tiab] OR "antioxidant"[tiab]) '
            'AND ("Humans"[Mesh] OR "Clinical Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt])'
        )
    },
    {
        "id": "cardio_renal",
        "name": "Cardio-Renal-Metabolic (CRM) & Renal Protection",
        "name_th": "ชะลอไตเสื่อม & เมตาบอลิกหัวใจ (SGLT2i, GLP-1, Finerenone)",
        "icon": "🫀",
        "days": 14,
        "max_results": 3,
        "query": (
            '("Chronic Kidney Disease"[Mesh] OR "Heart Failure"[Mesh] OR "Diabetic Nephropathies"[Mesh] OR "Cardio-renal"[tiab] OR "renal protection"[tiab]) '
            'AND ("Sodium-Glucose Transporter 2 Inhibitors"[Mesh] OR "SGLT2"[tiab] OR "dapagliflozin"[tiab] OR "empagliflozin"[tiab] OR "finerenone"[tiab] OR "semaglutide"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
        )
    },
    {
        "id": "anticoagulation",
        "name": "Anticoagulation & High Alert Drugs (Warfarin & DOACs)",
        "name_th": "ยาต้านการแข็งตัวของเลือด & HAD (Warfarin vs DOACs)",
        "icon": "🩸",
        "days": 30,
        "max_results": 2,
        "query": (
            '("Warfarin"[Mesh] OR "Anticoagulants"[Mesh] OR "apixaban"[tiab] OR "rivaroxaban"[tiab] OR "edoxaban"[tiab] OR "dabigatran"[tiab] OR "INR"[tiab]) '
            'AND ("bleeding"[tiab] OR "drug interaction"[tiab] OR "reversal"[tiab] OR "TTR"[tiab] OR "stroke prevention"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
        )
    },
    {
        "id": "ams_rdu",
        "name": "Antimicrobial Stewardship & Short-Course Therapy",
        "name_th": "การจัดการยาปฏิชีวนะ & สูตรยาสั้น (AMS & Short-Course RDU)",
        "icon": "🦠",
        "days": 45,
        "max_results": 2,
        "query": (
            '("Antimicrobial Stewardship"[Mesh] OR "Anti-Bacterial Agents"[Mesh] OR "antibiotic stewardship"[tiab]) '
            'AND ("short course"[tiab] OR "duration of therapy"[tiab] OR "oral switch"[tiab] OR "rational drug use"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
        )
    },
    {
        "id": "deprescribing",
        "name": "Deprescribing & Polypharmacy in Elderly",
        "name_th": "การตัดยาล้นเกินในผู้สูงอายุ (Deprescribing & Polypharmacy)",
        "icon": "👴",
        "days": 60,
        "max_results": 2,
        "query": (
            '("Inappropriate Prescribing"[Mesh] OR "Polypharmacy"[Mesh] OR "deprescribing"[tiab] OR "Beers criteria"[tiab] OR "STOPP"[tiab]) '
            'AND ("aged"[Mesh] OR "elderly"[tiab] OR "older adults"[tiab]) '
            'AND ("Clinical Trial"[pt] OR "Randomized Controlled Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt]) '
            'AND "Humans"[Mesh]'
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

            # Process Filter 1: Check for Free PMC Full-Text
            pmc_id = ""
            for id_tag in article_tag.findall(".//ArticleIdList/ArticleId"):
                if id_tag.get("IdType") == "pmc":
                    pmc_id = id_tag.text or ""
                    break
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else ""

            # Process Filter 2: Sample Size Sentinel (De-noiser for underpowered studies)
            # If explicit N is found and N < 30 in non-review studies, flag or skip
            n_match = re.search(r'\b[Nn]\s*=\s*(\d+)\b', abstract)
            if n_match:
                n_val = int(n_match.group(1))
                if n_val < 30 and "review" not in title.lower() and "meta-analysis" not in title.lower() and "case" in title.lower():
                    print(f"  [DE-NOISER] Skipping small sample study (N={n_val}): {title[:40]}...")
                    continue

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
                "pmc_id": pmc_id,
                "pmc_url": pmc_url,
                "has_free_fulltext": bool(pmc_id),
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

    compact_tracks = {}
    for tid, articles in articles_by_track.items():
        compact_tracks[tid] = []
        for a in articles:
            compact_tracks[tid].append({
                "pmid": a["pmid"],
                "title": a["title"],
                "journal": a["journal"],
                "has_free_fulltext": a["has_free_fulltext"],
                "pmc_url": a["pmc_url"],
                "abstract": a["abstract"][:650] + ("..." if len(a["abstract"]) > 650 else "")
            })

    prompt = f"""คุณคือผู้เชี่ยวชาญด้านเภสัชบำบัดทางคลินิก (Clinical Pharmacy Specialist) ร่วมกับท่านประธาน ภก.รัฐนนท์ แสงไทยทวีพร (เภสัชกรชำนาญการ ประธานทีม IM โรงพยาบาลเสิงสาง)

หน้าที่: จัดทำสรุปรายงานงานวิจัยทางคลินิก 7 หมวดสำคัญ (Asthma/COPD, ยาช่วยเลิกบุหรี่, สมุนไพรไทย, ชะลอไตเสื่อม/SGLT2i, Warfarin/DOACs, AMS ยาสั้น, และ Deprescribing ผู้สูงอายุ) ประจำวันที่ {report_date}

ข้อมูลงานวิจัยจาก PubMed (คัดกรองผ่าน Process Filter: Free Full-Text & Sample Size แล้ว):
{json.dumps(compact_tracks, ensure_ascii=False, indent=2)}

กฎเหล็กรูปแบบการนำเสนอ (สำคัญที่สุด):
- **ห้ามเขียนเป็น Text บรรยายยาวๆ เป็นพารากราฟเด็ดขาด** 
- สรุปแบบ **"Quick-Scan Card"** สั้น กระชับ กวนๆ ได้สาระ อ่านจบใน 10 วินาทีต่อเรื่อง

โครงสร้างของแต่ละเรื่อง:
### [ลำดับ]. [ชื่อเรื่องภาษาอังกฤษสั้นๆ]
- **วารสาร & PMID:** [ชื่อย่อวารสาร] • [PMID: <PMID>](https://pubmed.ncbi.nlm.nih.gov/<PMID>/) [ระบุว่า '📖 [อ่านฟรี PMC Full-Text](<pmc_url>)' หากมี]
- 🎯 **ใจความสำคัญ 1 บรรทัด:** [สรุปประเด็นหลักสั้นที่สุด 1 บรรทัดจบ]
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [ตัวเลขสถิติ 1: เช่น N=..., ลดกำเริบ...%, eGFR decline..., HR=...]
  • [ตัวเลขสถิติ 2: ผลข้างเคียง/ความปลอดภัย]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** [นัยสำคัญทางคลินิกต่อ รพ.ชุมชน 1 ข้อสั้นๆ คมๆ]
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/<PMID>/)

แบ่งตาม 7 หมวดชัดเจน:
1. 🫁 เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD)
2. 🚭 เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation)
3. 🌿 สมุนไพรไทยทางคลินิกในระบบทางเดินหายใจ (Thai Herbal Medicine)
4. 🫀 ชะลอไตเสื่อม & เมตาบอลิกหัวใจ (CRM: SGLT2i, GLP-1, Finerenone)
5. 🩸 ยาต้านการแข็งตัวของเลือด & HAD (Warfarin vs DOACs)
6. 🦠 การจัดการยาปฏิชีวนะ & สูตรยาสั้น (AMS & Short-Course RDU)
7. 👴 การตัดยาล้นเกินในผู้สูงอายุ (Deprescribing & Polypharmacy)
(หากหมวดใดไม่มีเปเปอร์ใหม่ในรอบค้นหา ให้สรุปประเด็นสำคัญสั้นๆ 1 ข้อ)

ท้ายรายงานให้ลงท้ายว่า:
---
**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  
*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*
"""

    models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]

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
        pass

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

    return generate_fallback_report(articles_by_track, report_date)

def generate_fallback_report(articles_by_track, report_date):
    lines = [
        f"# 🩺 สรุปรายงานวิจัยทางคลินิก 7 หมวดสำคัญ (Clinical Sentinel 7-Track)",
        f"**ประจำวันที่:** {report_date} | **สถานะ:** PubMed E-Utilities Direct Feed\n"
    ]
    for track in TRACK_CONFIGS:
        tid = track["id"]
        tname = track["name_th"]
        icon = track["icon"]
        articles = articles_by_track.get(tid, [])
        lines.append(f"## {icon} {tname}")
        if not articles:
            lines.append("*(ไม่พบงานวิจัยใหม่ที่มีนัยสำคัญในรอบการค้นหานี้)*\n")
            continue
        for i, a in enumerate(articles, 1):
            free_tag = f" • [📖 อ่านบทความวิจัยฉบับเต็มฟรี]({a['pmc_url']})" if a.get("has_free_fulltext") else ""
            lines.append(f"### {i}. {a['title']}")
            lines.append(f"- **วารสาร & แหล่งอ้างอิง:** {a['journal']} ({a['pub_date']}) • [PMID: {a['pmid']}]({a['url']}){free_tag}")
            lines.append(f"- **บทคัดย่อ (Abstract สรุป):**\n  > {a['abstract'][:300]}...\n")
    lines.append("---\n**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  \n*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*")
    return "\n".join(lines)

def generate_html_dashboard(markdown_content, report_date, articles_by_track):
    total_articles = sum(len(v) for v in articles_by_track.values())
    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>🥊 Clinical Battle Arena (7-Track) | ภก.รัฐนนท์ แสงไทยทวีพร</title>
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
    }}
    .arena-subtitle {{
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}
    .container {{
      max-width: 720px;
      margin: 0 auto;
      padding: 1rem;
    }}
    .mode-switch-bar {{
      display: flex;
      background: rgba(30, 41, 59, 0.7);
      border-radius: 9999px;
      padding: 0.3rem;
      margin-bottom: 1rem;
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
    .filter-scroll {{
      display: flex;
      gap: 0.4rem;
      overflow-x: auto;
      margin-bottom: 1.2rem;
      padding-bottom: 0.3rem;
      scrollbar-width: none;
    }}
    .filter-scroll::-webkit-scrollbar {{ display: none; }}
    .pill-btn {{
      white-space: nowrap;
      padding: 0.35rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(30, 41, 59, 0.6);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s;
    }}
    .pill-btn.active {{
      background: var(--neon-cyan);
      color: #042f2e;
      border-color: var(--neon-cyan);
      box-shadow: 0 2px 10px rgba(6, 182, 212, 0.3);
    }}

    /* Card System */
    .battle-card {{
      background: var(--card-bg);
      border: 2px solid rgba(245, 158, 11, 0.3);
      border-radius: 1.25rem;
      padding: 1.25rem;
      margin-bottom: 1.2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .battle-card::before {{
      content: "🔥 ศึกมวยคู่เอกเลิกบุหรี่";
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
    .vs-circle {{
      font-family: 'Bungee', cursive;
      font-size: 1.2rem;
      color: var(--gold);
    }}

    .round-row {{
      background: rgba(15, 23, 42, 0.6);
      border-radius: 0.6rem;
      padding: 0.6rem 0.8rem;
      border: 1px solid rgba(255, 255, 255, 0.05);
      margin-bottom: 0.4rem;
    }}
    .round-lbl {{
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      font-weight: 600;
      margin-bottom: 0.3rem;
    }}
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

    .chibi-callout {{
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      margin: 1.25rem 0;
    }}
    .chibi-avatar {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg, #06b6d4, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      flex-shrink: 0;
    }}
    .speech-bubble {{
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 1rem;
      border-top-left-radius: 0.2rem;
      padding: 0.75rem 1rem;
      font-size: 0.82rem;
      color: #e2e8f0;
    }}

    .content-box {{
      background: var(--card-bg);
      border-radius: 1.25rem;
      padding: 1.25rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .content-box h2 {{
      color: var(--neon-cyan);
      font-size: 1.15rem;
      margin: 1.2rem 0 0.6rem 0;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      padding-bottom: 0.3rem;
    }}
    .content-box h3 {{
      color: #34d399;
      font-size: 0.95rem;
      margin: 0.8rem 0 0.3rem 0;
    }}
    .content-box p, .content-box li {{
      color: #cbd5e1;
      font-size: 0.88rem;
      margin-bottom: 0.4rem;
    }}
    .content-box a {{
      color: var(--neon-cyan);
      text-decoration: none;
      font-weight: 500;
    }}
    .free-badge {{
      display: inline-block;
      background: rgba(16, 185, 129, 0.2);
      border: 1px solid var(--emerald);
      color: #6ee7b7;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      margin-left: 0.4rem;
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
      margin-top: 0.5rem;
    }}
  </style>
</head>
<body>
  <header class="arena-header">
    <div class="live-tag">🔴 7-TRACK ACTIVE INTELLIGENCE</div>
    <div class="arena-title">⚔️ CLINICAL BATTLE ARENA</div>
    <div class="arena-subtitle">ระบบเฝ้าระวัง 7 หมวดสำคัญ • คัดกรอง Free PMC & Sample Size • รพ.เสิงสาง</div>
    <button class="sound-btn" onclick="playGong()">🔔 เคาะระฆังเปิดศึก</button>
  </header>

  <div class="container">
    <div class="mode-switch-bar">
      <button class="mode-btn active" id="btn-fun" onclick="switchMode('fun')">🎮 ศึกดวล Quick-Scan (7 หมวด)</button>
      <button class="mode-btn" id="btn-formal" onclick="switchMode('formal')">📄 เอกสารฉบับเต็ม</button>
    </div>

    <div class="filter-scroll" id="trackPills">
      <button class="pill-btn active" onclick="filterTrack('all', this)">🌟 ทั้งหมด</button>
      <button class="pill-btn" onclick="filterTrack('Asthma', this)">🫁 Asthma/COPD</button>
      <button class="pill-btn" onclick="filterTrack('เลิกบุหรี่', this)">🚭 เลิกบุหรี่</button>
      <button class="pill-btn" onclick="filterTrack('สมุนไพร', this)">🌿 สมุนไพรไทย</button>
      <button class="pill-btn" onclick="filterTrack('ชะลอไต', this)">🫀 ชะลอไต (CRM)</button>
      <button class="pill-btn" onclick="filterTrack('Warfarin', this)">🩸 Warfarin/DOACs</button>
      <button class="pill-btn" onclick="filterTrack('ปฏิชีวนะ', this)">🦠 ยาฆ่าเชื้อ (AMS)</button>
      <button class="pill-btn" onclick="filterTrack('ผู้สูงอายุ', this)">👴 ตัดยาคนแก่</button>
    </div>

    <!-- MAIN EVENT BATTLE CARD (Smoking) -->
    <div class="battle-card" id="main-showdown">
      <div style="font-size: 0.8rem; color: var(--gold); font-weight: 700;">🚭 ศึกมวยคู่เอก: เภสัชบำบัดช่วยเลิกบุหรี่</div>
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
            <span>🥊 ยก 1: ความเร็วลดควันบุหรี่ (eCO Drop)</span>
            <span style="color: var(--emerald);">สูตรผสมชนะ (+25%)</span>
          </div>
          <div class="round-bars">
            <div class="bar-fill red" style="width: 75%;"></div>
            <div class="bar-fill blue" style="width: 50%;"></div>
          </div>
        </div>
        <div class="round-row">
          <div class="round-lbl">
            <span>🥊 ยก 2: คุมน้ำหนักตัวไม่ให้เด้ง (Weight Gain)</span>
            <span style="color: var(--emerald);">สูตรผสมชนะน็อค! (ไม่ขึ้นเลย)</span>
          </div>
          <div class="round-bars">
            <div class="bar-fill red" style="width: 90%;"></div>
            <div class="bar-fill blue" style="width: 30%;"></div>
          </div>
        </div>
      </div>
      <div class="winner-banner">
        <div style="font-size: 1.5rem;">🏆</div>
        <div style="font-size: 0.8rem; color: #a7f3d0;">
          <strong>ฟันธง:</strong> เหมาะกับผู้ป่วยที่ <em>"กลัวเลิกบุหรี่แล้วอ้วน"</em> เพราะระงับ Cravings ได้ชะงัด!
        </div>
      </div>
    </div>

    <!-- CHIBI MASCOT CALLOUT -->
    <div class="chibi-callout">
      <div class="chibi-avatar">👨‍⚕️</div>
      <div class="speech-bubble">
        <strong>โน้ตลับจากเภสัชกรนัท (IM Team):</strong> "ระบบอัปเกรดเป็น 7-Track แล้วครับอาจารย์! ตรวจจับทั้งเรื่องชะลอไต SGLT2i, วาร์ฟาริน, ยาฆ่าเชื้อสูตรสั้น และการตัดยาในคนแก่ พร้อมป้ายเตือนเปเปอร์โหลดฟรี PMC ให้เรียบร้อยครับ!"
      </div>
    </div>

    <!-- DYNAMIC REPORT CONTENT -->
    <main class="content-box" id="report-content">
      <!-- Rendered Markdown -->
    </main>

    <footer style="text-align: center; margin-top: 2rem; font-size: 0.75rem; color: var(--text-muted);">
      <p><strong>ผู้รับผิดชอบระบบ:</strong> ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ</p>
      <p>ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง</p>
      <p style="margin-top: 0.3rem;"><a href="https://canva.link/v9g5tfxdg349vbg" target="_blank" style="color: #c084fc; text-decoration: none;">🎨 เปิดสไลด์ใน Canva Pro →</a></p>
    </footer>
  </div>

  <script>
    const md = {json.dumps(markdown_content)};
    const contentBox = document.getElementById('report-content');
    contentBox.innerHTML = marked.parse(md);

    function filterTrack(keyword, btn) {{
      document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const showdown = document.getElementById('main-showdown');
      if (keyword === 'all' || keyword === 'เลิกบุหรี่') {{
        showdown.style.display = 'block';
      }} else {{
        showdown.style.display = 'none';
      }}

      const headers = contentBox.querySelectorAll('h2, h3');
      if (keyword === 'all') {{
        headers.forEach(h => {{
          let el = h;
          while (el && el !== contentBox) {{
            el.style.display = '';
            el = el.nextElementSibling;
            if (el && (el.tagName === 'H2' || el.tagName === 'H3')) break;
          }}
        }});
        return;
      }}

      headers.forEach(h => {{
        const isMatch = h.textContent.includes(keyword);
        let el = h.nextElementSibling;
        h.style.display = isMatch ? '' : 'none';
        while (el && el.tagName !== 'H2' && el.tagName !== 'H3') {{
          el.style.display = isMatch ? '' : 'none';
          el = el.nextElementSibling;
        }}
      }});
    }}

    function switchMode(mode) {{
      document.getElementById('btn-fun').classList.toggle('active', mode === 'fun');
      document.getElementById('btn-formal').classList.toggle('active', mode === 'formal');
      document.getElementById('main-showdown').style.display = mode === 'fun' ? 'block' : 'none';
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
    print(f"=== Starting PubMed Clinical Sentinel (7-Track v2.0): {report_date} ===")

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

        unseen_pmids = [p for p in pmids if p not in seen_set][:track["max_results"]]
        print(f"  Unseen target PMIDs to fetch: {unseen_pmids}")

        if unseen_pmids:
            articles = fetch_pubmed_articles(unseen_pmids)
            articles_by_track[tid] = articles
            newly_discovered_pmids.extend([a["pmid"] for a in articles])
            print(f"  Successfully fetched {len(articles)} article details (after filters).")
        else:
            articles_by_track[tid] = []
            print(f"  No new unseen articles for track: {tname}")

    total_new = len(newly_discovered_pmids)
    print(f"\n[INFO] Total new unique articles across all 7 tracks: {total_new}")

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
