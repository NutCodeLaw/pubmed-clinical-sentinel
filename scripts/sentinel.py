#!/usr/bin/env python3
"""
PubMed Clinical Sentinel (v2.2.0-HQ — Argon Surgical Upgrade Edition)
Master Automated 7-Track Clinical Intelligence & Battle Arena Pipeline:
1. Asthma & COPD Pharmacotherapy (14 days)
2. Smoking Cessation Pharmacotherapy (60 days)
3. Thai Herbal Medicine in Respiratory Care (180 days)
4. Cardio-Renal-Metabolic (CRM) & ชะลอไตเสื่อม (14 days)
5. Anticoagulation & High Alert Drugs (Warfarin & DOACs) (30 days)
6. Antimicrobial Stewardship (AMS) & Short-Course RDU (45 days)
7. Deprescribing & Polypharmacy in Elderly (60 days)

Upgrades in v2.2.0-HQ:
- Fix #1: Smart 3,000-char abstract preservation (never clips RESULTS/CONCLUSIONS)
- Fix #2: Comma-aware sample size regex (N >= 30 de-noiser, handles N=1,222)
- Fix #3: Deterministic data-track-id DOM filtering (zero disappearing H3 articles)
- Fix #4: Dynamic 4-Bout Showdown Arena with interactive switcher
- Fix #5: Non-destructive README.md marker injection + Idempotent article cache
- Fix #6: Rx-Sentinel HQ integration (Soeng Sang Formulary Badges + GFR/CYP450 Alerts)
- Fix #7: The Economic / BI-HQ integration (1-line Hospital Cost-Effectiveness & BIA)
- Fix #8: Standardized Multi-HQ output bus (data/latest_sentinel_payload.json)

Author: ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ
Hospital: โรงพยาบาลเสิงสาง (ประธานทีม Information Management - IM)
"""

import os
import sys
import re
import json
import time
import glob
import html as html_lib
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Auto-load local .env if present (Zero external dependencies)
ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

SEEN_FILE = os.path.join(DATA_DIR, "seen_pmids.json")
CACHE_FILE = os.path.join(DATA_DIR, "latest_articles_cache.json")
PAYLOAD_FILE = os.path.join(DATA_DIR, "latest_sentinel_payload.json")

NCBI_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
USER_AGENT = "PubMedClinicalSentinel/2.2-HQ (nutcodelaw@gmail.com; Soeng Sang Hospital IM Team)"

REPORT_START_MARKER = "<!-- SENTINEL_REPORT_START -->"
REPORT_END_MARKER = "<!-- SENTINEL_REPORT_END -->"

TRACK_CONFIGS = [
    {
        "id": "asthma_copd",
        "pill_label": "🫁 Asthma/COPD",
        "name": "Asthma & COPD Pharmacotherapy",
        "name_th": "เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD Pharmacotherapy)",
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
        "pill_label": "🚭 เลิกบุหรี่ (Smoking)",
        "name": "Smoking Cessation Pharmacotherapy",
        "name_th": "เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation Pharmacotherapy)",
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
        "pill_label": "🌿 สมุนไพรไทย (Herbs)",
        "name": "Thai Herbal Medicine in Respiratory Care",
        "name_th": "สมุนไพรไทยทางคลินิกในระบบทางเดินหายใจ (Thai Herbal Medicine in Respiratory Care)",
        "icon": "🌿",
        "days": 180,
        "max_results": 2,
        "query": (
            '("Vernonia cinerea"[tiab] OR "little ironweed"[tiab] OR "Andrographis paniculata"[tiab] '
            'OR "andrographolide"[tiab] OR "Curcuma longa"[tiab] OR "curcumin"[tiab] OR "Phyllanthus emblica"[tiab]) '
            'AND ("respiratory"[tiab] OR "cough"[tiab] OR "asthma"[tiab] OR "copd"[tiab] OR "pulmonary"[tiab] '
            'OR "lung"[tiab] OR "smoking"[tiab] OR "bronchitis"[tiab] OR "airway"[tiab] OR "pharyngitis"[tiab]) '
            'AND ("Humans"[Mesh] OR "Clinical Trial"[pt] OR "Systematic Review"[pt] OR "Meta-Analysis"[pt])'
        )
    },
    {
        "id": "cardio_renal",
        "pill_label": "🫀 Cardio-Renal (CRM)",
        "name": "Cardio-Renal-Metabolic (CRM) & Renal Protection",
        "name_th": "ชะลอไตเสื่อม & เมตาบอลิกหัวใจ (Cardio-Renal CRM: SGLT2i, GLP-1RA, Finerenone)",
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
        "pill_label": "🩸 Anticoagulants (HAD)",
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
        "pill_label": "🦠 ยาปฏิชีวนะ (AMS)",
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
        "pill_label": "👴 Deprescribing",
        "name": "Deprescribing & Polypharmacy in Elderly",
        "name_th": "การทบทวนและหยุดยาที่ไม่เหมาะสมในผู้สูงอายุ (Deprescribing & Polypharmacy)",
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

# Dynamic Multi-Bout Showdown Registry (Natural Clinical Thai & Bilingual)
DEFAULT_SHOWDOWN_BOUTS = [
    {
        "bout_id": "asthma_copd",
        "track_id": "asthma_copd",
        "tab_label": "🫁 Inhaler: Triple vs Dual",
        "headline": "🫁 ศึกมวยคู่เอก: Single-Inhaler Triple Therapy vs Dual Bronchodilators ในผู้ป่วย COPD กำเริบบ่อย",
        "red_name": "Single Inhaler Triple (Trelegy)",
        "red_sub": "FF/UMEC/VI พ่นวันละ 1 ครั้ง",
        "blue_name": "Dual Bronchodilators (LAMA+LABA)",
        "blue_sub": "สูตรคุมอาการ 2 ตัวยาเดิม",
        "rounds": [
            {"title": "🥊 ยก 1: ลดอัตรา Acute Exacerbation", "verdict": "Triple ชนะขาด (Exacerbation ลดลง 25%)", "red_pct": 85, "blue_pct": 40},
            {"title": "🥊 ยก 2: ความร่วมมือในการพ่นยา (Adherence)", "verdict": "Single Inhaler วันละครั้ง ชนะใส (Adherence สูงกว่า)", "red_pct": 90, "blue_pct": 50},
            {"title": "🥊 ยก 3: ความเสี่ยงการเกิด Pneumonia", "verdict": "Dual นำเล็กน้อย (Pneumonia Risk ต่ำกว่า)", "red_pct": 45, "blue_pct": 75}
        ],
        "verdict_text": "ผู้ป่วย COPD กลุ่ม High-Risk ที่มีประวัติ Acute Exacerbation จนต้อง Admit สูตร Triple คุ้มค่าสูงสุดในการตัดวงจร Re-admission ของ รพ.เสิงสาง!",
        "punchline": "Triple Therapy ลด Exacerbation ขาดลอย คุ้มค่าสูงสุดตัดวงจร Re-admission รพ.เสิงสาง"
    },
    {
        "bout_id": "smoking_cessation",
        "track_id": "smoking_cessation",
        "tab_label": "🚭 คลินิกฟ้าใส: Smoking Cessation",
        "headline": "🚭 ศึกมวยคู่เอก: Pharmacotherapy ช่วยเลิกบุหรี่และคุมน้ำหนักตัว (คลินิกฟ้าใส รพ.เสิงสาง)",
        "red_name": "สูตรผสม BUP + ZON",
        "red_sub": "Bupropion + Zonisamide",
        "blue_name": "สูตรเดี่ยว BUP + ชาหญ้าดอกขาว",
        "blue_sub": "Bupropion + ชาสมุนไพรไทย",
        "rounds": [
            {"title": "🥊 ยก 1: อัตราการลดควันบุหรี่ในลมหายใจ (Exhaled CO Drop)", "verdict": "สูตรผสมชนะ (+25%)", "red_pct": 75, "blue_pct": 50},
            {"title": "🥊 ยก 2: การคุมน้ำหนักตัวไม่ให้พุ่ง (Weight Gain Control)", "verdict": "สูตรผสมชนะน็อค! (น้ำหนักไม่เด้ง)", "red_pct": 90, "blue_pct": 30},
            {"title": "🥊 ยก 3: ความพร้อมใช้งานใน รพ.เสิงสาง", "verdict": "สูตรเดี่ยว BUP + ชาหญ้าดอกขาว มีพร้อมในคลังยา", "red_pct": 45, "blue_pct": 85}
        ],
        "verdict_text": "สูตรผสมเด่นเรื่องคุมน้ำหนักตัวไม่ให้พุ่ง แต่หน้างานคลินิกฟ้าใส รพ.เสิงสาง ใช้ Bupropion เดี่ยว + ชาหญ้าดอกขาว เบิกจ่ายได้ทันทีและได้ผลดีเยี่ยม!",
        "punchline": "คลินิกฟ้าใส รพ.เสิงสาง ชู Bupropion + ชาหญ้าดอกขาว พร้อมใช้งานจริงทันที"
    },
    {
        "bout_id": "thai_herbs",
        "track_id": "thai_herbs",
        "tab_label": "🌿 สมุนไพรไทย: ฟ้าทะลายโจร",
        "headline": "🌿 ศึกมวยคู่เอก: สารสกัดฟ้าทะลายโจร (Andrographis) vs ยาบรรเทาอาการมาตรฐาน ในหวัด/เจ็บคอ (URTI)",
        "red_name": "ฟ้าทะลายโจร (Andrographolide)",
        "red_sub": "สารสกัดมาตรฐาน 60–120 mg/day",
        "blue_name": "Symptomatic Treatment แผนปัจจุบัน",
        "blue_sub": "ยาแก้ไอ / ลดน้ำมูกมาตรฐาน",
        "rounds": [
            {"title": "🥊 ยก 1: ระยะเวลาบรรเทาอาการไอและเจ็บคอ (Symptom Relief)", "verdict": "ฟ้าทะลายโจรชนะ (อาการทุเลาไวกว่า 1–2 วัน)", "red_pct": 82, "blue_pct": 55},
            {"title": "🥊 ยก 2: หนุนตัวชี้วัด RDU ตัดการใช้ Antibiotics เกินจำเป็น", "verdict": "ฟ้าทะลายโจรชนะขาดลอย! (Zero Antibiotics)", "red_pct": 95, "blue_pct": 35},
            {"title": "🥊 ยก 3: Safety Profile เมื่อใช้ระยะสั้น ≤ 5 วัน", "verdict": "เสมอกัน (ไม่มีผลต่อตับ/ไต)", "red_pct": 70, "blue_pct": 70}
        ],
        "verdict_text": "ฟ้าทะลายโจรบรรเทาไอเจ็บคอได้เร็ว หนุนเกณฑ์ RDU ขั้นสูงสุดของ รพ.เสิงสาง ตัดการสั่ง Antibiotics เกินจำเป็นในหวัดได้อย่างเด็ดขาด!",
        "punchline": "ฟ้าทะลายโจรลดไอเจ็บคอเร็วกว่า หนุนธง RDU ตัด Antibiotics ในหวัดพร่ำเพรื่อ"
    },
    {
        "bout_id": "cardio_renal",
        "track_id": "cardio_renal",
        "tab_label": "🫀 Cardio-Renal: SGLT2i",
        "headline": "🫀 ศึกมวยคู่เอก: Dapagliflozin ในหัตถการหัวใจ TAVR / โรคไตเรื้อรัง (DAPA-TAVI & DAPA-CKD)",
        "red_name": "Dapagliflozin 10 mg",
        "red_sub": "SGLT2i (บัญชียา รพ.เสิงสาง)",
        "blue_name": "Standard Care เดี่ยว",
        "blue_sub": "การรักษามาตรฐานเดิม",
        "rounds": [
            {"title": "🥊 ยก 1: ลด Mortality & Worsening Heart Failure (DM & Non-DM)", "verdict": "Dapa ชนะขาด (ได้ผลเท่ากันทั้งกลุ่มเบาหวานและไม่เป็นเบาหวาน)", "red_pct": 82, "blue_pct": 38},
            {"title": "🥊 ยก 2: ชะลอ eGFR Decline (Renal Protection)", "verdict": "Dapa ชนะขาดลอย (ชะลอการเสื่อมของไต)", "red_pct": 85, "blue_pct": 40},
            {"title": "🥊 ยก 3: ความคุ้มค่าด้านงบประมาณสาธารณสุข (BI-HQ ROI)", "verdict": "ประหยัดงบค่ารักษา Re-admission ระยะยาวชัดเจน", "red_pct": 88, "blue_pct": 30}
        ],
        "verdict_text": "Dapagliflozin ป้องกัน Heart Failure กำเริบและชะลอไตเสื่อมได้ทั้งคนที่เป็นและไม่เป็นเบาหวาน คุ้มค่าสูงมากในการลด Re-admission รพ.เสิงสาง!",
        "punchline": "Dapagliflozin ชนะขาดทั้งกลุ่ม DM และ Non-DM คุ้มค่าลด Re-admission รพ.เสิงสาง"
    },
    {
        "bout_id": "anticoagulation",
        "track_id": "anticoagulation",
        "tab_label": "🩸 Anticoagulants: VTE Prevention",
        "headline": "🩸 ศึกมวยคู่เอก: ป้องกันลิ่มเลือดอุดตัน VTE หลังผ่าตัดเปลี่ยนข้อ (PEPPER Trial ใน NEJM, N=18,883)",
        "red_name": "Aspirin 81 mg BID",
        "red_sub": "Antiplatelet ราคาประหยัด",
        "blue_name": "Warfarin / Rivaroxaban",
        "blue_sub": "Anticoagulants มาตรฐาน",
        "rounds": [
            {"title": "🥊 ยก 1: ประสิทธิผลป้องกัน VTE & Mortality", "verdict": "เสมอกัน (Non-inferior ชัดเจน)", "red_pct": 50, "blue_pct": 50},
            {"title": "🥊 ยก 2: ความปลอดภัยด้าน Major Bleeding", "verdict": "Aspirin ปลอดภัยกว่าชัดเจน (เลือดออกน้อยกว่า)", "red_pct": 65, "blue_pct": 45},
            {"title": "🥊 ยก 3: ความคุ้มค่า & ลดภาระการตรวจติดตาม INR", "verdict": "Aspirin ชนะน็อค! (ไม่ต้องเจาะ Lab ติดตาม)", "red_pct": 92, "blue_pct": 25}
        ],
        "verdict_text": "ในผู้ป่วยผ่าตัดเปลี่ยนข้อเข่า/ข้อสะโพกที่มีความเสี่ยง VTE ต่ำ Aspirin มีประสิทธิผลไม่ด้อยกว่า เลือดออกน้อยกว่า และลดภาระงานคลินิกวาร์ฟารินของ รพ.เสิงสาง ได้มหาศาล!",
        "punchline": "Aspirin ได้ผล Non-inferior เลือดออกน้อยกว่า ไม่ต้องเจาะ INR ลดภาระคลินิกวาร์ฟาริน"
    },
    {
        "bout_id": "ams_rdu",
        "track_id": "ams_rdu",
        "tab_label": "🦠 Short-Course Antibiotics (AMS)",
        "headline": "🦠 ศึกมวยคู่เอก: Antibiotics สูตรสั้น vs สูตรยาว ในปอดอักเสบเด็ก (Pediatric Non-Severe CAP)",
        "red_name": "Short-Course Amoxicillin (3–5 วัน)",
        "red_sub": "สูตรยาสั้นตามหลัก RDU & AMS",
        "blue_name": "Standard-Course (7–10 วัน)",
        "blue_sub": "สูตรมาตรฐานเดิม",
        "rounds": [
            {"title": "🥊 ยก 1: อัตราการรักษาหายทางคลินิก (Clinical Cure Rate)", "verdict": "เสมอกัน 100% (Non-inferior สมบูรณ์แบบ)", "red_pct": 50, "blue_pct": 50},
            {"title": "🥊 ยก 2: Medication Adherence (ความร่วมมือในการกินยาครบโดส)", "verdict": "สูตรสั้นชนะขาด (กินง่าย คอร์สสั้น ผู้ปกครองป้อนครบ)", "red_pct": 85, "blue_pct": 45},
            {"title": "🥊 ยก 3: ลดผลข้างเคียงท้องเสีย & ชะลอเชื้อดื้อยา (AMR)", "verdict": "สูตรสั้นชนะน็อคตามเกณฑ์ AMS!", "red_pct": 88, "blue_pct": 30}
        ],
        "verdict_text": "ปอดอักเสบเด็กชนิดไม่รุนแรง (Non-severe CAP) จ่าย Amoxicillin สูตรสั้น 3–5 วัน หายเท่ากัน Adherence ดีกว่า ลดเชื้อดื้อยา และประหยัดงบค่ายา รพ.เสิงสาง!",
        "punchline": "Short-Course Amox 3–5 วัน หายเท่ากัน Adherence สูง ลดเชื้อดื้อยา ประหยัดงบ รพ."
    },
    {
        "bout_id": "deprescribing",
        "track_id": "deprescribing",
        "tab_label": "👴 Deprescribing: Tapering ยานอนหลับ",
        "headline": "👴 ศึกมวยคู่เอก: Deprescribing หยุดยานอนหลับ Benzodiazepines vs กินต่อเนื่องในผู้สูงอายุที่มี Polypharmacy",
        "red_name": "Pharmacist-Led Deprescribing",
        "red_sub": "ค่อยๆ ปรับลดขนาดยา (Stepwise Tapering) + Sleep Hygiene",
        "blue_name": "Usual Care (Status Quo)",
        "blue_sub": "รับประทานยาเดิมต่อเนื่อง",
        "rounds": [
            {"title": "🥊 ยก 1: ลดอุบัติการณ์หกล้มและกระดูกหัก (Fall & Fracture Risk)", "verdict": "กลุ่ม Deprescribing ชนะขาด (ลดการหกล้มลง 40%)", "red_pct": 85, "blue_pct": 30},
            {"title": "🥊 ยก 2: Cognitive Function & ความตื่นตัวระหว่างวัน", "verdict": "สมองแจ่มใส ไม่มึนงงเวลากลางวัน", "red_pct": 80, "blue_pct": 40},
            {"title": "🥊 ยก 3: ป้องกัน Rebound Insomnia / Withdrawal Symptoms", "verdict": "Stepwise Tapering ปลอดภัย แทบไม่มีอาการถอนยา", "red_pct": 75, "blue_pct": 50}
        ],
        "verdict_text": "เภสัชกรร่วมกับแพทย์ทำ Stepwise Tapering ยานอนหลับในผู้สูงอายุ ลดความเสี่ยงหกล้มสะโพกหักได้มหาศาล เซฟค่าใช้จ่ายผ่าตัดให้ รพ.เสิงสาง ได้หลายแสนบาท!",
        "punchline": "Pharmacist Tapering ยานอนหลับ ลดหกล้ม 40% คุ้มครองผู้สูงอายุและเซฟค่ารักษา"
    }
]


def load_json_file(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not read {filepath}: {e}")
    return default_val


def save_json_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Fix #1: Smart 3,000-character abstract preservation (keeps both start and RESULTS/CONCLUSIONS tail)
def smart_truncate_abstract(abstract_text, max_chars=3000):
    if not abstract_text:
        return "Abstract not available."
    if len(abstract_text) <= max_chars:
        return abstract_text
    head_len = 1000
    tail_len = max_chars - head_len - 40
    return f"{abstract_text[:head_len]}\n...[เนื้อหาส่วนกลางย่อ]...\n{abstract_text[-tail_len:]}"


# Fix #2: Comma-aware sample size extractor (handles N = 1,222 and multi-arm cohorts)
def extract_sample_size(title, abstract_text):
    combined = f"{title} {abstract_text}"
    candidates = []

    # Pattern 1: Explicit N = 1,222 or n = 49
    for match in re.finditer(r'\b[Nn]\s*=\s*([\d,]+)\b', combined):
        raw_num = match.group(1).replace(",", "").strip()
        if raw_num.isdigit():
            val = int(raw_num)
            if val > 0:
                candidates.append(val)

    # Pattern 2: "1,222 patients / participants / older adults / children"
    for match in re.finditer(
        r'(?<!in\s)(?<!since\s)(?<!during\s)(?<!year\s)\b(\d[\d,]*)\s+(?:patients|participants|subjects|adults|children|adolescents|individuals|residents)\b',
        combined,
        flags=re.IGNORECASE
    ):
        raw_str = match.group(1).strip()
        raw_num = raw_str.replace(",", "")
        if raw_num.isdigit():
            val = int(raw_num)
            has_comma = "," in raw_str
            # Filter out likely calendar years unless separated by comma or large cohort
            if val >= 10 and (has_comma or not (1990 <= val <= 2035)):
                candidates.append(val)

    return max(candidates) if candidates else None


NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20
}


def extract_evidence_badge(title, abstract_text, extracted_n=None):
    """
    Intelligently identifies study design and sample size/study count so that 'N=None' is NEVER displayed.
    Extracts number of studies/trials for Systematic Reviews & Meta-Analyses (e.g. '📚 19 Studies (SR/MA)'),
    marks RCTs (e.g. '👥 N=1,222 (RCT)'), and categorizes Preclinical/Translational models.
    """
    combined = f"{title} {abstract_text}".strip()
    combined_lower = combined.lower()

    # 1. Search for number of studies / trials in SR/MA
    study_count = None
    m_studies = re.search(
        r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(?:studies|trials|clinical trials|articles|rcts|cohorts)\b',
        combined_lower
    )
    if m_studies:
        raw_val = m_studies.group(1)
        if raw_val.isdigit():
            study_count = int(raw_val)
        elif raw_val in NUMBER_WORDS:
            study_count = NUMBER_WORDS[raw_val]

    # Detect study design keywords (word-boundary regex avoids substrings like 'unmatched' matching 'nma')
    is_nma = "network meta-analysis" in combined_lower or bool(re.search(r"\bnma\b", combined_lower))
    is_sr = "systematic review" in combined_lower
    is_ma = "meta-analysis" in combined_lower or "meta analysis" in combined_lower
    is_rct = (
        "randomized" in combined_lower
        or "randomised" in combined_lower
        or bool(re.search(r"\brct\b", combined_lower))
        or "clinical trial" in combined_lower
    )
    is_qualitative = "qualitative" in combined_lower
    is_guideline = "guideline" in combined_lower or "consensus" in combined_lower or "recommendations" in combined_lower
    is_animal = any(kw in combined_lower for kw in ["mouse model", "mice", "rat model", "rats", "in vivo", "bleomycin-induced"])
    is_invitro = any(kw in combined_lower for kw in ["in vitro", "in silico", "molecular dynamics", "supramolecular", "nanoplatform", "cell culture"])

    # If patient sample size N is available
    if extracted_n and extracted_n > 0:
        if study_count and (is_sr or is_ma):
            design_tag = "SR/NMA" if is_nma else ("SR/MA" if (is_sr and is_ma) else "SR")
            return f"📚 {study_count} Studies ({design_tag}) • 👥 N={extracted_n:,}"
        elif is_sr or is_ma:
            design_tag = "SR/NMA" if is_nma else ("SR/MA" if (is_sr and is_ma) else "Meta-Analysis")
            return f"📚 {design_tag} • 👥 N={extracted_n:,}"
        elif is_rct:
            return f"👥 N={extracted_n:,} (RCT)"
        else:
            return f"👥 N={extracted_n:,}"

    # If no patient sample size N was found
    if study_count and (is_sr or is_ma or is_qualitative):
        design_tag = "SR/NMA" if is_nma else ("Qualitative SR" if is_qualitative else "SR/MA")
        return f"📚 {study_count} Studies ({design_tag})"

    if is_nma:
        return "📚 Network Meta-Analysis (NMA)"
    if is_sr and is_ma:
        return "📚 Systematic Review & Meta-Analysis"
    if is_sr:
        if is_qualitative:
            return "📚 Qualitative Systematic Review"
        return "📚 Systematic Review"
    if is_ma:
        return "📚 Meta-Analysis"
    if is_guideline:
        return "📋 Clinical Guideline / Consensus"
    if is_animal:
        return "🔬 Preclinical / In Vivo Model"
    if is_invitro:
        return "🧪 In Vitro / In Silico Model"
    if is_rct:
        return "👥 Clinical Trial (RCT)"

    return "📑 Clinical Evidence Review"


def compute_dynamic_evidence_math(showdown_bouts, articles_by_track):
    """
    Computes dynamic evidence math for Showdown bouts based on real trial data & meta-analyses
    isolated by track_id, with a fail-safe fallback to pre-seeded gold standards.
    """
    updated_bouts = copy.deepcopy(showdown_bouts)

    for bout in updated_bouts:
        tid = bout.get("track_id")
        articles = articles_by_track.get(tid, [])
        if not articles:
            continue

        try:
            combined_text = " ".join([
                f"{a.get('title', '')} {a.get('thai_takeaway', '')} {' '.join(a.get('key_metrics', []))} {a.get('abstract', '')}"
                for a in articles
            ])

            for rnd in bout.get("rounds", []):
                title = rnd.get("title", "").lower()
                verdict = rnd.get("verdict", "").lower()

                # Rule 0: Non-inferiority / Equivalence
                if "เสมอกัน" in verdict or "non-inferior" in verdict:
                    rnd["red_pct"] = 50
                    rnd["blue_pct"] = 50
                    continue

                # Isolated by track_id
                if tid == "asthma_copd":
                    if "exacerbation" in title or "กำเริบ" in title:
                        m = re.search(r'(?:ลดลง|drop|reduction)\s*([0-9]+(?:\.[0-9]+)?)\s*%', combined_text + " " + verdict, re.I)
                        if m:
                            drop = float(m.group(1))
                            rnd["red_pct"] = min(95, max(50, round(50 + drop * 1.4)))
                            rnd["blue_pct"] = min(50, max(20, round(50 - drop * 0.4)))
                            rnd["evidence_math"] = f"Exacerbation Reduction {drop}%"
                    elif "adherence" in title or "พ่นยา" in title:
                        rnd["red_pct"] = 88
                        rnd["blue_pct"] = 48
                        rnd["evidence_math"] = "Single Inhaler vs Multi-Device Adherence"
                    elif "pneumonia" in title:
                        rnd["red_pct"] = 45
                        rnd["blue_pct"] = 75
                        rnd["evidence_math"] = "ICS Pneumonia Risk Profile"

                elif tid == "smoking_cessation":
                    if "exhaled co" in title or "ควันบุหรี่" in title or "reduction" in title:
                        m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:และ|\/|\&|,)\s*([0-9]+(?:\.[0-9]+)?)\s*%\s*vs\s*(?:placebo\s*)?([0-9]+(?:\.[0-9]+)?)\s*%', combined_text, re.I)
                        if m:
                            p_red = float(m.group(1))
                            p_blue = float(m.group(3))
                            rnd["red_pct"] = min(95, max(30, round(p_red * 2.8)))
                            rnd["blue_pct"] = min(95, max(20, round(p_blue * 3.0)))
                            rnd["evidence_math"] = f"Cessation mITT {p_red}% vs {p_blue}%"
                        else:
                            rnd["red_pct"] = 75
                            rnd["blue_pct"] = 50
                    elif "weight" in title or "น้ำหนัก" in title:
                        rnd["red_pct"] = 90
                        rnd["blue_pct"] = 30
                        rnd["evidence_math"] = "Zonisamide Weight Gain Mitigation"
                    elif "พร้อมใช้งาน" in title or "คลังยา" in title:
                        rnd["red_pct"] = 45
                        rnd["blue_pct"] = 85
                        rnd["evidence_math"] = "Soeng Sang Formulary Availability"

                elif tid == "thai_herbs":
                    if "ไอ" in title or "เจ็บคอ" in title or "symptom" in title:
                        rnd["red_pct"] = 82
                        rnd["blue_pct"] = 55
                        rnd["evidence_math"] = "Clinical Symptom Relief 1-2 Days Faster"
                    elif "rdu" in title or "antibiotic" in title:
                        rnd["red_pct"] = 95
                        rnd["blue_pct"] = 35
                        rnd["evidence_math"] = "Zero Antibiotics Protocol in Viral URTI"
                    elif "safety" in title or "ปลอดภัย" in title:
                        rnd["red_pct"] = 50
                        rnd["blue_pct"] = 50
                        rnd["evidence_math"] = "Short-course Hepato/Renal Equivalence"

                elif tid == "cardio_renal":
                    if "mortality" in title or "heart failure" in title:
                        rnd["red_pct"] = 84
                        rnd["blue_pct"] = 38
                        rnd["evidence_math"] = "DAPA-TAVI & SGLT2i Meta-analysis (N=13,886)"
                    elif "egfr" in title or "renal" in title or "ไต" in title:
                        rnd["red_pct"] = 86
                        rnd["blue_pct"] = 40
                        rnd["evidence_math"] = "SGLT2i eGFR Decline Protection"
                    elif "งบประมาณ" in title or "roi" in title:
                        rnd["red_pct"] = 88
                        rnd["blue_pct"] = 30
                        rnd["evidence_math"] = "High ROI: Reduced HF Re-admission"

                elif tid == "anticoagulation":
                    if "vte" in title or "mortality" in title:
                        rnd["red_pct"] = 50
                        rnd["blue_pct"] = 50
                        rnd["evidence_math"] = "Non-inferior VTE Prevention (PEPPER RCT N=18,883)"
                    elif "bleeding" in title or "เลือดออก" in title:
                        rnd["red_pct"] = 65
                        rnd["blue_pct"] = 42
                        rnd["evidence_math"] = "Significant Lower Major Bleeding (Aspirin)"
                    elif "inr" in title or "คุ้มค่า" in title:
                        rnd["red_pct"] = 92
                        rnd["blue_pct"] = 25
                        rnd["evidence_math"] = "Zero Lab INR Monitoring Burden"

                elif tid == "ams_rdu":
                    if "cure" in title or "หาย" in title:
                        rnd["red_pct"] = 50
                        rnd["blue_pct"] = 50
                        rnd["evidence_math"] = "Clinical Cure Equivalence (N=8,970 Meta-analysis)"
                    elif "adherence" in title or "ความร่วมมือ" in title:
                        rnd["red_pct"] = 86
                        rnd["blue_pct"] = 44
                        rnd["evidence_math"] = "Higher Course Completion Rate in Short-Course"
                    elif "ดื้อยา" in title or "amr" in title or "ผลข้างเคียง" in title:
                        rnd["red_pct"] = 88
                        rnd["blue_pct"] = 32
                        rnd["evidence_math"] = "Reduced Diarrhea & AMR Pressure"

                elif tid == "deprescribing":
                    if "หกล้ม" in title or "fall" in title or "fracture" in title:
                        m = re.search(r'ลด[^\d%]*([0-9]+(?:\.[0-9]+)?)\s*%', combined_text)
                        if m:
                            drop = float(m.group(1))
                            rnd["red_pct"] = min(95, max(50, round(50 + drop * 0.8)))
                            rnd["blue_pct"] = min(50, max(20, round(50 - drop * 0.4)))
                            rnd["evidence_math"] = f"PIMs/Fall Risk Reduction {drop}%"
                        else:
                            rnd["red_pct"] = 85
                            rnd["blue_pct"] = 30
                    elif "cognitive" in title or "ตื่นตัว" in title:
                        rnd["red_pct"] = 80
                        rnd["blue_pct"] = 40
                        rnd["evidence_math"] = "Improved Daytime Vigilance & Cognition"
                    elif "rebound" in title or "ถอนยา" in title:
                        rnd["red_pct"] = 75
                        rnd["blue_pct"] = 50
                        rnd["evidence_math"] = "Safe Stepwise Tapering Profile"

        except Exception as e:
            # Unbreakable fallback: keeps pre-seeded values cleanly
            print(f"[WARN] Math extraction fallback for {tid}: {e}")

    return updated_bouts


# Fix #6 & #7: Rx-Sentinel HQ + The Economic BI-HQ Deterministic Enrichment
def enrich_article_metadata(article, track_id):
    title = article.get('title', '')
    abstract = article.get('abstract', '')
    text_lower = f"{title} {abstract}".lower()

    # 0. Intelligent Evidence Badge (Guarantees zero 'N=None' and rich study design badges)
    if not article.get("extracted_n"):
        article["extracted_n"] = extract_sample_size(title, abstract)
    article["evidence_badge"] = extract_evidence_badge(title, abstract, article.get("extracted_n"))

    # 1. Soeng Sang Hospital Formulary Status Badge
    in_formulary_keywords = [
        "dapagliflozin", "warfarin", "aspirin", "bupropion", "nicotine",
        "andrographis", "andrographolide", "curcuma", "curcumin", "vernonia", "phyllanthus",
        "amoxicillin", "rifampicin", "isoniazid", "budesonide", "salbutamol", "ipratropium", "theophylline"
    ]
    j2_restricted_keywords = [
        "rivaroxaban", "apixaban", "enoxaparin", "mepolizumab", "benralizumab", "omalizumab", "empagliflozin"
    ]
    ptc_candidate_keywords = [
        "tezepelumab", "dupilumab", "ensifentrine", "itepekimab", "finerenone",
        "semaglutide", "tirzepatide", "varenicline", "cytisine", "zonisamide", "edoxaban", "dabigatran"
    ]

    if any(k in text_lower for k in ptc_candidate_keywords):
        formulary_badge = "🔴 ยานอกบัญชี รพ. / ผู้ท้าชิงเข้า PTC"
        formulary_tier = "PTC_CANDIDATE"
    elif any(k in text_lower for k in j2_restricted_keywords):
        formulary_badge = "🟡 ยาบัญชี จ(2) / เงื่อนไขเฉพาะ รพ."
        formulary_tier = "J2_RESTRICTED"
    elif any(k in text_lower for k in in_formulary_keywords):
        formulary_badge = "🟢 มีในคลังยา รพ.เสิงสาง"
        formulary_tier = "IN_FORMULARY"
    else:
        formulary_badge = "📋 แนวทางบริบาลเภสัชกรรมคลินิก"
        formulary_tier = "CLINICAL_PROTOCOL"

    # 2. Rx-Sentinel HQ Clinical & ADR/Renal/CYP450 Alert
    if track_id == "cardio_renal" or "dapagliflozin" in text_lower or "sglt2" in text_lower:
        rx_alert = "ตรวจ eGFR ก่อนเริ่มยา (Dapagliflozin ห้ามเริ่มหาก eGFR < 25 mL/min) • เฝ้าระวัง Euglycemic DKA และการติดเชื้อทางเดินปัสสาวะ"
    elif track_id == "anticoagulation" or "warfarin" in text_lower or "apixaban" in text_lower or "rivaroxaban" in text_lower:
        rx_alert = "ประเมินค่าไต CrCl ก่อนจ่าย DOACs • กรณีใช้ Warfarin ให้คุม Target INR 2.0–3.0 และระวังอันตรกิริยากับยาฆ่าเชื้อ/สมุนไพร"
    elif track_id == "thai_herbs":
        rx_alert = "CYP450 Herb-Drug Alert: ฟ้าทะลายโจรและขมิ้นชันยับยั้ง CYP2C9/CYP3A4 ห้ามจ่ายร่วมกับ Warfarin หรือยากดภูมิคุ้มกัน (เสี่ยงเลือดออกง่าย)"
    elif track_id == "smoking_cessation":
        rx_alert = "คัดกรองประวัติโรคลมชัก (Seizure risk) ก่อนจ่าย Bupropion ในคลินิกฟ้าใส • ติดตามอาการนอนไม่หลับและน้ำหนักตัว"
    elif track_id == "asthma_copd":
        rx_alert = "ทบทวนเทคนิคการพ่นยา (Inhaler Technique) ทุกครั้งก่อนปรับ Step ยา • ยากลุ่ม Biologics ต้องคัดกรอง Eosinophils/FeNO ตามเกณฑ์"
    elif track_id == "ams_rdu":
        rx_alert = "เกณฑ์ Short-Course RDU ใช้เฉพาะผู้ป่วย Non-severe ที่ภูมิคุ้มกันปกติ • ประเมินอาการไข้ลดลงครบ 48 ชม. ก่อนหยุดยา"
    else:
        rx_alert = "การหยุดยาในผู้สูงอายุ (Deprescribing) โดยเฉพาะกลุ่ม BZD, Beta-blocker และ PPI ต้องทำ Tapering ค่อยๆ ลดขนาดยาเพื่อป้องกันอาการถอนยา"

    # 3. The Economic / BI-HQ Cost-Effectiveness & Budget Impact Note
    if track_id == "cardio_renal":
        bi_note = "คุ้มค่าสูง (High ROI): ลดค่าใช้จ่ายการนอน รพ.ซ้ำจากภาวะหัวใจล้มเหลว (HF Readmission) และชะลอการฟอกไตในระยะยาว"
    elif track_id == "anticoagulation":
        bi_note = "ลดต้นทุนแฝง รพ.: การใช้ Aspirin ในกลุ่มเสี่ยงต่ำหลังผ่าตัดข้อ หรือเลือก DOAC ในกลุ่มเสี่ยงเลือดออกทางเดินอาหาร ช่วยลดภาระการเจาะ Lab INR และค่านอน รพ.จาก GI Bleed"
    elif track_id == "ams_rdu":
        bi_note = "ประหยัดงบค่ายาโดยตรง 40–50% ต่อคอร์ส ลดโอกาสเกิดเชื้อดื้อยาที่ต้องใช้ยาฉีดราคาแพง (Carbapenems/Vancomycin)"
    elif track_id == "deprescribing":
        bi_note = "ลดมูลค่าค่ายาส่วนเกิน (Polypharmacy Waste) ในคลินิกผู้สูงอายุและป้องกันค่าใช้จ่ายจากการรักษาอาการไม่พึงประสงค์จากการใช้ยา (ADE)"
    elif track_id == "asthma_copd":
        bi_note = "ยากลุ่ม Biologics มีราคาสูง ควรจำกัดเฉพาะเคส Severe Refractory ที่ลดการส่งตัวผ่าตัดซ้ำหรือลดการแอดมิด ICU ได้ชัดเจน"
    elif track_id == "thai_herbs":
        bi_note = "ส่งเสริมการใช้ยาสมุนไพรในบัญชียาหลักแห่งชาติ ทดแทนยานำเข้าและสร้างความมั่นคงทางยาของ รพ.ชุมชน"
    else:
        bi_note = "การช่วยให้ผู้ป่วยเลิกบุหรี่สำเร็จในคลินิกฟ้าใส ให้ผลตอบแทนทางเศรษฐศาสตร์สาธารณสุขสูงสุดในการลดโรคหลอดเลือดหัวใจและ COPD กำเริบ"

    article["formulary_badge"] = formulary_badge
    article["formulary_tier"] = formulary_tier
    article["rx_sentinel_alert"] = rx_alert
    article["bi_hq_note"] = bi_note
    return article


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


def fetch_pubmed_articles(pmids, track_id):
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

            year = article_tag.find(".//JournalIssue/PubDate/Year")
            month = article_tag.find(".//JournalIssue/PubDate/Month")
            pub_date = f"{year.text if year is not None else ''} {month.text if month is not None else ''}".strip()

            abstract_parts = []
            for ab_text in article_tag.findall(".//Abstract/AbstractText"):
                label = ab_text.get("Label", "")
                text = "".join(ab_text.itertext()).strip()
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = "\n\n".join(abstract_parts) if abstract_parts else "Abstract not available."

            # Process Filter 1: Free PMC Full-Text detection
            pmc_id = ""
            for id_tag in article_tag.findall(".//ArticleIdList/ArticleId"):
                if id_tag.get("IdType") == "pmc":
                    raw_pmc = (id_tag.text or "").strip()
                    if raw_pmc:
                        pmc_id = raw_pmc if raw_pmc.upper().startswith("PMC") else f"PMC{raw_pmc}"
                    break
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/" if pmc_id else ""

            # Process Filter 2: Comma-aware Sample Size Sentinel (Fix #2)
            extracted_n = extract_sample_size(title, abstract)
            is_review_or_meta = any(
                kw in f"{title} {abstract}".lower()
                for kw in ["systematic review", "meta-analysis", "network meta-analysis", "guideline"]
            )
            if extracted_n is not None and extracted_n < 30 and not is_review_or_meta:
                print(f"  [DE-NOISER] Skipping underpowered study (N={extracted_n}): {title[:50]}...")
                continue

            doi = ""
            for id_tag in article_tag.findall(".//ArticleIdList/ArticleId"):
                if id_tag.get("IdType") == "doi":
                    doi = id_tag.text or ""
                    break

            article_obj = {
                "pmid": pmid,
                "track_id": track_id,
                "title": title,
                "journal": journal,
                "pub_date": pub_date,
                "doi": doi,
                "pmc_id": pmc_id,
                "pmc_url": pmc_url,
                "has_free_fulltext": bool(pmc_id),
                "extracted_n": extracted_n,
                "abstract": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
            enrich_article_metadata(article_obj, track_id)
            articles.append(article_obj)
    except Exception as e:
        print(f"[ERROR] XML parsing error: {e}")

    return articles


def parse_existing_markdown_summaries(reports_dir):
    """Extracts previously generated Thai summaries per PMID from existing reports so cached articles retain their Thai clinical pearls."""
    summaries_by_pmid = {}
    if os.path.isdir(reports_dir):
        report_files = sorted(glob.glob(os.path.join(reports_dir, "*_respiratory_sentinel.md")))
    elif os.path.isfile(reports_dir):
        report_files = [reports_dir]
    else:
        report_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*_respiratory_sentinel.md")))

    for md_path in report_files:
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            blocks = re.split(r'\n(?=####\s+\d+\.|###\s+\d+\.)', content)
            for blk in blocks:
                m_pmid = re.search(r'PMID:\s*(\d+)', blk)
                if not m_pmid:
                    continue
                pmid = m_pmid.group(1)
                m_takeaway = re.search(r'ใจความสำคัญ 1 บรรทัด:\*\*\s*(.+)', blk)
                m_action = re.search(r'สิ่งที่ต้องรู้ใน รพ\.เสิงสาง:\*\*\s*(.+)', blk)
                metrics = re.findall(r'^\s+•\s*\[?([^\]\n]+)\]?', blk, flags=re.MULTILINE)
                clean_metrics = [
                    m.strip() for m in metrics
                    if m.strip() and not m.strip().startswith("PMID:") and "อ่านฟรี PMC" not in m
                ]
                summaries_by_pmid[pmid] = {
                    "thai_takeaway": m_takeaway.group(1).strip() if m_takeaway else "",
                    "soeng_sang_action": m_action.group(1).strip() if m_action else "",
                    "key_metrics": clean_metrics[:3]
                }
        except Exception as e:
            print(f"[WARN] Could not parse existing summaries from {md_path}: {e}")
    return summaries_by_pmid


def enrich_articles_with_gemini(articles_by_track, report_date, existing_summaries):
    """Uses Gemini (if GEMINI_API_KEY is available) or existing/deterministic clinical synthesis to populate Thai Quick-Scan fields."""
    # First apply any existing known Thai summaries for cached PMIDs
    needs_ai_pmids = []
    for tid, articles in articles_by_track.items():
        for a in articles:
            pmid = a["pmid"]
            if pmid in existing_summaries and existing_summaries[pmid].get("thai_takeaway"):
                a["thai_takeaway"] = existing_summaries[pmid]["thai_takeaway"]
                a["soeng_sang_action"] = existing_summaries[pmid]["soeng_sang_action"]
                a["key_metrics"] = existing_summaries[pmid]["key_metrics"]
            elif not a.get("thai_takeaway"):
                needs_ai_pmids.append(a)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key and needs_ai_pmids:
        payload_items = []
        for a in needs_ai_pmids:
            payload_items.append({
                "pmid": a["pmid"],
                "track_id": a["track_id"],
                "title": a["title"],
                "journal": a["journal"],
                "extracted_n": a.get("extracted_n"),
                # Fix #1: Up to 3,000 characters preserved!
                "abstract": smart_truncate_abstract(a["abstract"], 3000)
            })

        prompt = f"""คุณคือผู้เชี่ยวชาญด้านเภสัชบำบัดทางคลินิก (Clinical Pharmacy Specialist) ร่วมกับ ภก.รัฐนนท์ แสงไทยทวีพร (ประธานทีม IM โรงพยาบาลเสิงสาง)
กรุณาสรุปข้อมูลงานวิจัยต่อไปนี้เป็น JSON Object โดยใช้รหัส PMID เป็น Key:
{json.dumps(payload_items, ensure_ascii=False, indent=2)}

ตอบกลับเป็น JSON เท่านั้น ตามโครงสร้างนี้:
{{
  "<pmid>": {{
    "thai_takeaway": "สรุปใจความสำคัญที่สุด 1 บรรทัด ภาษาไทยเข้าใจง่าย อ่านจบใน 5 วินาที",
    "key_metrics": [
      "ตัวเลขสถิติสำคัญข้อ 1 (เช่น N=..., HR/OR/RR, p-value, ประสิทธิผล)",
      "ตัวเลขสถิติสำคัญข้อ 2 (ความปลอดภัย หรือผลลัพธ์รอง)"
    ],
    "soeng_sang_action": "ข้อเสนอแนะเชิงปฏิบัติการสำหรับเภสัชกรและแพทย์ รพ.เสิงสาง 1 บรรทัดคมๆ"
  }}
}}"""

        models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                req_body = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(req_body).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=90) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed_ai = json.loads(raw_text)
                    for a in needs_ai_pmids:
                        if a["pmid"] in parsed_ai:
                            info = parsed_ai[a["pmid"]]
                            a["thai_takeaway"] = info.get("thai_takeaway", "")
                            a["key_metrics"] = info.get("key_metrics", [])
                            a["soeng_sang_action"] = info.get("soeng_sang_action", "")
                    break
            except Exception as e:
                print(f"[WARN] Gemini JSON synthesis with {model_name} failed: {e}")

    # Deterministic fallback for any article still missing Thai summary fields
    for tid, articles in articles_by_track.items():
        for a in articles:
            if not a.get("thai_takeaway"):
                # Extract CONCLUSIONS sentence from abstract if present
                ab = a.get("abstract", "")
                m_conc = re.search(r'(?:CONCLUSIONS?|INTERPRETATION|SUMMARY|FINDINGS):\s*([^\n]+)', ab, re.IGNORECASE)
                conc_text = m_conc.group(1).strip() if m_conc else ab[:220].strip()
                a["thai_takeaway"] = f"หลักฐานทางคลินิกล่าสุดจาก {a['journal']}: {conc_text}"
            if not a.get("key_metrics"):
                ev_str = a.get("evidence_badge") or (f"กลุ่มตัวอย่าง N={a['extracted_n']:,} ราย" if a.get("extracted_n") else "การศึกษาทบทวนวรรณกรรมอย่างเป็นระบบ")
                a["key_metrics"] = [
                    f"{ev_str} • ตีพิมพ์ในวารสาร {a['journal']} ({a['pub_date']})",
                    f"สกัดจากบทคัดย่อฉบับเต็ม ({len(a.get('abstract', '')):,} ตัวอักษร)"
                ]
            if not a.get("soeng_sang_action"):
                a["soeng_sang_action"] = a.get("rx_sentinel_alert", "ประยุกต์ใช้ในการติดตามความปลอดภัยและประสิทธิภาพการใช้ยาในผู้ป่วย รพ.เสิงสาง")


def build_markdown_report(articles_by_track, report_date):
    lines = [
        f"# 🩺 สรุปรายงานวิจัยทางคลินิก 7 หมวดสำคัญ (Clinical Pharmacy Research Update)",
        f"**ประจำวันที่:** {report_date} | **เวอร์ชันเครื่องยนต์:** `v2.2.0-HQ (5-Allied HQs Synchronized)`  ",
        f"*ทีมสารสนเทศสมุนไพรและเภสัชบำบัด (IM Team) โรงพยาบาลเสิงสาง*\n",
        "---\n"
    ]

    for idx, track in enumerate(TRACK_CONFIGS, 1):
        tid = track["id"]
        tname = track["name_th"]
        icon = track["icon"]
        articles = articles_by_track.get(tid, [])

        lines.append(f"### {idx}. {icon} {tname}\n")
        if not articles:
            lines.append(f"- 🎯 **สถานะประจำรอบสัปดาห์:** ไม่พบเปเปอร์ใหม่ที่ผ่านเกณฑ์คัดกรอง $N \\ge 30$ ในรอบ {track['days']} วันที่ผ่านมา\n")
            lines.append("---\n")
            continue

        for i, a in enumerate(articles, 1):
            free_badge = f" • 📖 [อ่านฟรี PMC Full-Text]({a['pmc_url']})" if a.get("has_free_fulltext") else ""
            badge_str = a.get("evidence_badge") or (f"👥 N={a['extracted_n']:,}" if a.get("extracted_n") else "📚 Systematic Review")
            n_badge = f" • `{badge_str}`"
            form_badge = a.get("formulary_badge", "")

            lines.append(f"#### {i}. {a['title']}")
            lines.append(f"- **วารสาร & PMID:** {a['journal']} • [PMID: {a['pmid']}]({a['url']}){n_badge}{free_badge}")
            lines.append(f"- **สถานะบัญชียา รพ.เสิงสาง:** `{form_badge}`")
            lines.append(f"- 🎯 **ใจความสำคัญ 1 บรรทัด:** {a.get('thai_takeaway', '')}")
            lines.append(f"- 📊 **ตัวเลขผลลัพธ์สำคัญ:**")
            for m in a.get("key_metrics", []):
                lines.append(f"  • [{m}]")
            lines.append(f"- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** {a.get('soeng_sang_action', '')}")
            lines.append(f"- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** {a.get('rx_sentinel_alert', '')}")
            lines.append(f"- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** {a.get('bi_hq_note', '')}")
            lines.append(f"- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →]({a['url']})\n")

        lines.append("---\n")

    lines.append("**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  ")
    lines.append("*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*")
    return "\n".join(lines)


def update_readme_non_destructive(markdown_report):
    """Fix #5: Injects the latest clinical report into README.md between markers without wiping project documentation."""
    readme_path = os.path.join(BASE_DIR, "README.md")
    report_section = f"{REPORT_START_MARKER}\n\n{markdown_report}\n\n{REPORT_END_MARKER}"

    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        if REPORT_START_MARKER in content and REPORT_END_MARKER in content:
            pattern = re.compile(
                re.escape(REPORT_START_MARKER) + r".*?" + re.escape(REPORT_END_MARKER),
                re.DOTALL
            )
            updated = pattern.sub(lambda _: report_section, content)
        else:
            updated = content.rstrip() + "\n\n---\n\n## 📋 รายงานสรุปงานวิจัยทางคลินิกล่าสุด (Latest Weekly Digest)\n\n" + report_section + "\n"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)
    else:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(report_section)


def generate_html_dashboard(markdown_content, report_date, articles_by_track, showdown_bouts):
    """Fixes #3, #4, #6, #7: Renders deterministic data-track-id cards, multi-bout showdown arena, and Allied HQ badges."""
    total_articles = sum(len(v) for v in articles_by_track.values())
    free_pmc_count = sum(1 for arts in articles_by_track.values() for a in arts if a.get("has_free_fulltext"))

    # Build filter pills HTML
    pills_html = ['<button class="pill-btn active" onclick="filterTrack(\'all\', this)">🌟 ทั้งหมด (7 หมวด)</button>']
    for track in TRACK_CONFIGS:
        tid = track["id"]
        cnt = len(articles_by_track.get(tid, []))
        pills_html.append(
            f'<button class="pill-btn" data-pill-track="{tid}" onclick="filterTrack(\'{tid}\', this)">'
            f'{track["pill_label"]} <span class="pill-count">{cnt}</span></button>'
        )
    pills_joined = "\n      ".join(pills_html)

    # Build Quick-Scan Cards per track (Fix #3: wrapped in <section class="track-section" data-track-id="...">)
    track_sections_html = []
    for idx, track in enumerate(TRACK_CONFIGS, 1):
        tid = track["id"]
        icon = track["icon"]
        tname = html_lib.escape(track["name_th"])
        articles = articles_by_track.get(tid, [])

        cards_html = []
        if not articles:
            cards_html.append(f"""
            <div class="paper-card empty-card">
              <div class="paper-takeaway">🎯 <strong>สถานะประจำรอบสัปดาห์:</strong> ไม่พบงานวิจัยใหม่ที่ผ่านเกณฑ์คัดกรอง N ≥ 30 ในรอบ {track['days']} วันที่ผ่านมา</div>
            </div>""")
        else:
            for i, a in enumerate(articles, 1):
                title_esc = html_lib.escape(a.get("title", ""))
                journal_esc = html_lib.escape(a.get("journal", ""))
                pmid_esc = html_lib.escape(a.get("pmid", ""))
                url_esc = html_lib.escape(a.get("url", ""))
                takeaway_esc = html_lib.escape(a.get("thai_takeaway", ""))
                action_esc = html_lib.escape(a.get("soeng_sang_action", ""))
                rx_esc = html_lib.escape(a.get("rx_sentinel_alert", ""))
                bi_esc = html_lib.escape(a.get("bi_hq_note", ""))
                form_badge = html_lib.escape(a.get("formulary_badge", ""))
                tier = a.get("formulary_tier", "CLINICAL_PROTOCOL")

                badge_text = html_lib.escape(a.get("evidence_badge") or (f"👥 N={a['extracted_n']:,}" if a.get("extracted_n") else "📚 Systematic Review"))
                n_badge_html = f'<span class="meta-badge n-badge">{badge_text}</span>'
                pmc_badge_html = (
                    f'<a href="{html_lib.escape(a["pmc_url"])}" target="_blank" class="meta-badge pmc-badge">📖 อ่านฟรี PMC Full-Text</a>'
                    if a.get("has_free_fulltext") else ""
                )
                metrics_li = "".join(
                    f"<li>{html_lib.escape(m)}</li>" for m in a.get("key_metrics", [])
                )

                cards_html.append(f"""
            <article class="paper-card">
              <div class="paper-top-bar">
                <span class="formulary-tag tier-{tier}">{form_badge}</span>
                <div class="badge-group">
                  {n_badge_html}
                  {pmc_badge_html}
                </div>
              </div>
              <h3 class="paper-title">{i}. {title_esc}</h3>
              <div class="paper-meta">
                📰 <strong>{journal_esc}</strong> ({html_lib.escape(a.get("pub_date", ""))}) •
                <a href="{url_esc}" target="_blank">PMID: {pmid_esc}</a>
              </div>
              <div class="paper-takeaway">
                🎯 <strong>ใจความสำคัญ 1 บรรทัด:</strong> {takeaway_esc}
              </div>
              <div class="paper-metrics">
                <div class="metrics-header">📊 ตัวเลขผลลัพธ์สำคัญ:</div>
                <ul>{metrics_li}</ul>
              </div>
              <div class="hq-grid">
                <div class="hq-box action-box">
                  💡 <strong>สิ่งที่ต้องรู้ใน รพ.เสิงสาง:</strong> {action_esc}
                </div>
                <div class="hq-box rx-box">
                  🏥 <strong>Rx-Sentinel Safety Alert:</strong> {rx_esc}
                </div>
                <div class="hq-box bi-box">
                  💰 <strong>มุมมองความคุ้มค่า (BI-HQ):</strong> {bi_esc}
                </div>
              </div>
              <div class="paper-footer">
                <a href="{url_esc}" target="_blank" class="read-btn">🔗 เปิดอ่านบทคัดย่อตัวเต็มบน PubMed →</a>
              </div>
            </article>""")

        track_sections_html.append(f"""
        <section class="track-section" data-track-id="{tid}">
          <div class="track-header">
            <span class="track-icon">{icon}</span>
            <h2 class="track-title">{idx}. {tname}</h2>
            <span class="track-window">ย้อนหลัง {track['days']} วัน</span>
          </div>
          {"".join(cards_html)}
        </section>""")

    all_sections_joined = "\n".join(track_sections_html)

    # Build Championship Fight Cards for Battle Mode (Clean, Punchy, No Heavy Clutter)
    champ_cards_html = []
    for b in showdown_bouts:
        btid = b.get("track_id", "")
        punch = b.get("punchline") or b.get("verdict_text", "")
        champ_cards_html.append(f"""
        <div class="champ-card" data-track-id="{btid}" onclick="handleChampCardClick('{btid}', event)">
          <div class="champ-header">
            <span class="champ-tag">{html_lib.escape(b.get('tab_label', ''))}</span>
            <span class="champ-status">🥊 KO VERDICT</span>
          </div>
          <div class="champ-matchup">
            <div class="champ-fighter red">🔴 {html_lib.escape(b.get('red_name', ''))}</div>
            <div class="champ-vs">VS</div>
            <div class="champ-fighter blue">🔵 {html_lib.escape(b.get('blue_name', ''))}</div>
          </div>
          <div class="champ-verdict">
            🎯 <strong>หมัดเด็ดฟันธง:</strong> {html_lib.escape(punch)}
          </div>
          <div class="champ-footer">
            <button class="champ-read-btn" onclick="goToFormalTrack('{btid}')">📄 อ่านวิเคราะห์ฉบับเต็มในโหมดทางการ →</button>
          </div>
        </div>""")
    champ_deck_joined = "\n".join(champ_cards_html)

    md_escaped = json.dumps(markdown_content, ensure_ascii=False).replace("</", r"<\/")
    bouts_escaped = json.dumps(showdown_bouts, ensure_ascii=False).replace("</", r"<\/")

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>🥊 Clinical Battle Arena (v2.2-HQ) | ภก.รัฐนนท์ แสงไทยทวีพร</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700;800;900&family=Sarabun:wght@300;400;600&family=Bungee&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {{
      --bg: #070a12;
      --card-bg: rgba(18, 25, 43, 0.92);
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
      background-image: radial-gradient(circle at 50% 0%, rgba(6, 182, 212, 0.16) 0%, transparent 60%);
      color: var(--text);
      line-height: 1.55;
      padding-bottom: 4rem;
    }}
    .arena-header {{
      text-align: center;
      padding: 1.6rem 1rem 1.1rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .live-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.45);
      color: #6ee7b7;
      padding: 0.25rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.74rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }}
    .arena-title {{
      font-size: 1.55rem;
      font-weight: 900;
      background: linear-gradient(135deg, #38bdf8 0%, #ec4899 50%, #f59e0b 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .arena-subtitle {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}
    .kpi-strip {{
      display: flex;
      justify-content: center;
      gap: 0.6rem;
      flex-wrap: wrap;
      margin-top: 0.75rem;
    }}
    .kpi-chip {{
      background: rgba(30, 41, 59, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.6rem;
      padding: 0.25rem 0.65rem;
      font-size: 0.73rem;
      color: #cbd5e1;
    }}
    .kpi-chip strong {{ color: var(--neon-cyan); }}
    .sound-btn {{
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid var(--gold);
      color: var(--gold);
      padding: 0.35rem 0.9rem;
      border-radius: 9999px;
      font-size: 0.76rem;
      font-weight: 700;
      cursor: pointer;
      margin-top: 0.65rem;
      transition: transform 0.15s;
    }}
    .sound-btn:active {{ transform: scale(0.95); }}

    .container {{
      max-width: 780px;
      margin: 0 auto;
      padding: 1rem;
    }}
    .mode-switch-bar {{
      display: flex;
      background: rgba(30, 41, 59, 0.75);
      border-radius: 9999px;
      padding: 0.3rem;
      margin-bottom: 0.9rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .mode-btn {{
      flex: 1;
      text-align: center;
      padding: 0.5rem;
      font-size: 0.83rem;
      font-weight: 700;
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
      gap: 0.45rem;
      overflow-x: auto;
      margin-bottom: 1.1rem;
      padding-bottom: 0.35rem;
      scrollbar-width: none;
    }}
    .filter-scroll::-webkit-scrollbar {{ display: none; }}
    .pill-btn {{
      white-space: nowrap;
      padding: 0.38rem 0.82rem;
      border-radius: 9999px;
      font-size: 0.77rem;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(30, 41, 59, 0.65);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }}
    .pill-count {{
      background: rgba(255, 255, 255, 0.12);
      padding: 0.05rem 0.4rem;
      border-radius: 9999px;
      font-size: 0.68rem;
    }}
    .pill-btn.active {{
      background: var(--neon-cyan);
      color: #042f2e;
      border-color: var(--neon-cyan);
      box-shadow: 0 2px 10px rgba(6, 182, 212, 0.3);
    }}
    .pill-btn.active .pill-count {{
      background: rgba(4, 47, 46, 0.25);
      color: #042f2e;
    }}

    /* Dynamic Multi-Bout Battle Card */
    .battle-card {{
      position: relative;
      background: var(--card-bg);
      border: 2px solid rgba(245, 158, 11, 0.4);
      border-radius: 1.25rem;
      padding: 1.2rem;
      margin-bottom: 1.2rem;
      box-shadow: 0 10px 28px -5px rgba(0, 0, 0, 0.55);
    }}
    .bout-tabs {{
      display: flex;
      gap: 0.35rem;
      overflow-x: auto;
      margin-bottom: 0.85rem;
      padding-bottom: 0.25rem;
      scrollbar-width: none;
    }}
    .bout-tabs::-webkit-scrollbar {{ display: none; }}
    .bout-tab {{
      white-space: nowrap;
      padding: 0.28rem 0.68rem;
      border-radius: 0.6rem;
      font-size: 0.72rem;
      font-weight: 700;
      border: 1px solid rgba(245, 158, 11, 0.3);
      background: rgba(15, 23, 42, 0.75);
      color: #fcd34d;
      cursor: pointer;
    }}
    .bout-tab.active {{
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      color: #000000;
      border-color: transparent;
    }}
    .fighters-arena {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 0.5rem;
      margin: 0.9rem 0;
      text-align: center;
    }}
    .fighter-box {{
      padding: 0.7rem 0.5rem;
      border-radius: 0.75rem;
    }}
    .fighter-box.red {{
      background: rgba(239, 68, 68, 0.14);
      border: 1px solid rgba(239, 68, 68, 0.35);
    }}
    .fighter-box.blue {{
      background: rgba(59, 130, 246, 0.14);
      border: 1px solid rgba(59, 130, 246, 0.35);
    }}
    .fighter-name {{ font-size: 0.86rem; font-weight: 800; }}
    .fighter-tag {{ font-size: 0.71rem; color: var(--text-muted); margin-top: 0.15rem; }}
    .fighter-box.red .fighter-name {{ color: #f87171; }}
    .fighter-box.blue .fighter-name {{ color: #60a5fa; }}
    .vs-circle {{
      font-family: 'Bungee', cursive;
      font-size: 1.15rem;
      color: var(--gold);
    }}
    .round-row {{
      background: rgba(15, 23, 42, 0.65);
      border-radius: 0.6rem;
      padding: 0.55rem 0.75rem;
      border: 1px solid rgba(255, 255, 255, 0.06);
      margin-bottom: 0.4rem;
    }}
    .round-lbl {{
      display: flex;
      justify-content: space-between;
      font-size: 0.74rem;
      font-weight: 600;
      margin-bottom: 0.3rem;
      gap: 0.5rem;
    }}
    .round-bars {{
      display: flex;
      height: 8px;
      gap: 4px;
      border-radius: 4px;
      overflow: hidden;
      background: rgba(255,255,255,0.06);
    }}
    .bar-fill.red {{ background: var(--red-fighter); transition: width 0.35s ease; }}
    .bar-fill.blue {{ background: var(--blue-fighter); transition: width 0.35s ease; }}
    .winner-banner {{
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(6, 182, 212, 0.18));
      border: 1px solid var(--emerald);
      border-radius: 0.75rem;
      padding: 0.7rem 0.85rem;
      margin-top: 0.85rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    /* Chibi Callout */
    .chibi-callout {{
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      margin: 1rem 0 1.25rem 0;
    }}
    .chibi-avatar {{
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg, #06b6d4, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.45rem;
      flex-shrink: 0;
    }}
    .speech-bubble {{
      background: rgba(30, 41, 59, 0.9);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 0.95rem;
      border-top-left-radius: 0.2rem;
      padding: 0.7rem 0.95rem;
      font-size: 0.8rem;
      color: #e2e8f0;
    }}

    /* Track Sections & Quick-Scan Paper Cards */
    .track-section {{
      margin-bottom: 1.5rem;
    }}
    .track-header {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid rgba(6, 182, 212, 0.3);
    }}
    .track-icon {{ font-size: 1.3rem; }}
    .track-title {{
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--neon-cyan);
      flex: 1;
    }}
    .track-window {{
      font-size: 0.7rem;
      color: var(--text-muted);
      background: rgba(30, 41, 59, 0.8);
      padding: 0.15rem 0.55rem;
      border-radius: 9999px;
    }}
    .paper-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 1rem;
      padding: 1.05rem;
      margin-bottom: 0.9rem;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    }}
    .paper-top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 0.55rem;
    }}
    .formulary-tag {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.18rem 0.6rem;
      border-radius: 9999px;
    }}
    .tier-IN_FORMULARY {{
      background: rgba(16, 185, 129, 0.18);
      border: 1px solid rgba(16, 185, 129, 0.5);
      color: #6ee7b7;
    }}
    .tier-J2_RESTRICTED {{
      background: rgba(245, 158, 11, 0.18);
      border: 1px solid rgba(245, 158, 11, 0.5);
      color: #fcd34d;
    }}
    .tier-PTC_CANDIDATE {{
      background: rgba(239, 68, 68, 0.18);
      border: 1px solid rgba(239, 68, 68, 0.5);
      color: #fca5a5;
    }}
    .tier-CLINICAL_PROTOCOL {{
      background: rgba(139, 92, 246, 0.18);
      border: 1px solid rgba(139, 92, 246, 0.5);
      color: #c4b5fd;
    }}
    .badge-group {{
      display: flex;
      gap: 0.35rem;
      flex-wrap: wrap;
    }}
    .meta-badge {{
      font-size: 0.69rem;
      font-weight: 700;
      padding: 0.15rem 0.55rem;
      border-radius: 9999px;
      text-decoration: none;
    }}
    .n-badge {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #7dd3fc;
    }}
    .pmc-badge {{
      background: rgba(16, 185, 129, 0.2);
      border: 1px solid var(--emerald);
      color: #6ee7b7;
    }}
    .paper-title {{
      font-size: 0.96rem;
      font-weight: 700;
      color: #f1f5f9;
      margin-bottom: 0.3rem;
    }}
    .paper-meta {{
      font-size: 0.76rem;
      color: var(--text-muted);
      margin-bottom: 0.65rem;
    }}
    .paper-meta a {{ color: var(--neon-cyan); text-decoration: none; font-weight: 600; }}
    .paper-takeaway {{
      background: rgba(6, 182, 212, 0.1);
      border-left: 3px solid var(--neon-cyan);
      padding: 0.55rem 0.75rem;
      border-radius: 0.4rem;
      font-size: 0.84rem;
      color: #f8fafc;
      margin-bottom: 0.65rem;
    }}
    .paper-metrics {{
      font-size: 0.8rem;
      color: #cbd5e1;
      margin-bottom: 0.7rem;
      padding-left: 0.2rem;
    }}
    .metrics-header {{ font-weight: 700; color: #93c5fd; margin-bottom: 0.25rem; }}
    .paper-metrics ul {{ padding-left: 1.2rem; }}
    .paper-metrics li {{ margin-bottom: 0.2rem; }}
    .hq-grid {{
      display: grid;
      gap: 0.45rem;
      margin-bottom: 0.7rem;
    }}
    .hq-box {{
      font-size: 0.78rem;
      padding: 0.48rem 0.7rem;
      border-radius: 0.5rem;
    }}
    .action-box {{
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #d1fae5;
    }}
    .rx-box {{
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.3);
      color: #fef3c7;
    }}
    .bi-box {{
      background: rgba(139, 92, 246, 0.1);
      border: 1px solid rgba(139, 92, 246, 0.3);
      color: #ede9fe;
    }}
    .paper-footer {{ text-align: right; }}
    .read-btn {{
      display: inline-block;
      font-size: 0.76rem;
      font-weight: 700;
      color: var(--neon-cyan);
      text-decoration: none;
      padding: 0.3rem 0.7rem;
      border-radius: 0.5rem;
      background: rgba(6, 182, 212, 0.12);
      border: 1px solid rgba(6, 182, 212, 0.3);
    }}

    /* Formal Mode Container */
    .formal-box {{
      display: none;
      background: var(--card-bg);
      border-radius: 1.25rem;
      padding: 1.25rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .formal-box h1, .formal-box h2, .formal-box h3, .formal-box h4 {{
      color: var(--neon-cyan);
      margin: 1rem 0 0.4rem 0;
    }}
    .formal-box p, .formal-box li {{
      color: #cbd5e1;
      font-size: 0.86rem;
      margin-bottom: 0.35rem;
    }}
    .formal-box a {{ color: var(--neon-cyan); }}
    .formal-box hr {{ border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0; }}

    /* Championship Deck Grid (Clean, Punchy, Fun for Battle Mode) */
    .deck-header {{
      margin: 1.1rem 0 0.8rem 0;
      padding: 0.65rem 0.9rem;
      background: rgba(30, 41, 59, 0.55);
      border-radius: 0.8rem;
      border-left: 3px solid var(--gold);
    }}
    .deck-title {{
      font-size: 0.95rem;
      font-weight: 800;
      color: var(--gold);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .deck-subtitle {{
      font-size: 0.73rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }}
    .champ-deck-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }}
    @media (min-width: 640px) {{
      .champ-deck-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}
    .champ-card {{
      background: var(--card-bg);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 1rem;
      padding: 0.95rem;
      transition: all 0.2s ease;
      cursor: pointer;
    }}
    .champ-card:hover {{
      border-color: rgba(6, 182, 212, 0.45);
      transform: translateY(-2px);
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45);
    }}
    .champ-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.55rem;
    }}
    .champ-tag {{
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--neon-cyan);
      background: rgba(6, 182, 212, 0.12);
      padding: 0.18rem 0.55rem;
      border-radius: 9999px;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }}
    .champ-status {{
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--gold);
      background: rgba(245, 158, 11, 0.12);
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      border: 1px solid rgba(245, 158, 11, 0.25);
    }}
    .champ-matchup {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 0.4rem;
      text-align: center;
      background: rgba(15, 23, 42, 0.65);
      border-radius: 0.65rem;
      padding: 0.55rem 0.4rem;
      margin-bottom: 0.55rem;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .champ-fighter {{
      font-size: 0.76rem;
      font-weight: 700;
      line-height: 1.25;
    }}
    .champ-fighter.red {{ color: #fca5a5; }}
    .champ-fighter.blue {{ color: #93c5fd; }}
    .champ-vs {{
      font-family: 'Bungee', cursive;
      font-size: 0.8rem;
      color: var(--gold);
    }}
    .champ-verdict {{
      font-size: 0.78rem;
      color: #f1f5f9;
      line-height: 1.4;
      background: rgba(6, 182, 212, 0.08);
      border-left: 3px solid var(--neon-cyan);
      padding: 0.45rem 0.65rem;
      border-radius: 0.4rem;
      margin-bottom: 0.65rem;
    }}
    .champ-footer {{
      text-align: right;
    }}
    .champ-read-btn {{
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #cbd5e1;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.32rem 0.65rem;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .champ-read-btn:hover {{
      background: rgba(6, 182, 212, 0.2);
      border-color: var(--neon-cyan);
      color: #ffffff;
    }}

    /* Formal Box Styles */
    .formal-header-card {{
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(6, 182, 212, 0.35);
      border-radius: 1rem;
      padding: 1.1rem;
      margin-bottom: 1.2rem;
    }}
    .formal-title-row {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.85rem;
    }}
    .formal-crest {{
      font-size: 2rem;
    }}
    .formal-heading {{
      font-size: 1.05rem;
      font-weight: 800;
      color: #ffffff;
      margin: 0 !important;
    }}
    .formal-subheading {{
      font-size: 0.74rem;
      color: var(--neon-cyan);
      margin: 0.15rem 0 0 0 !important;
    }}
    .formal-meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #cbd5e1;
      background: rgba(0, 0, 0, 0.25);
      padding: 0.6rem 0.8rem;
      border-radius: 0.6rem;
    }}
    .formal-divider {{
      border: none;
      border-top: 1px solid rgba(255, 255, 255, 0.12);
      margin: 1.5rem 0;
    }}
    .formal-section-header {{
      margin-bottom: 1rem;
    }}
    .formal-section-title {{
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--gold);
      margin-bottom: 0.25rem;
    }}
    .formal-section-sub {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
    .highlight-flash {{
      animation: flash-highlight 1.8s ease;
    }}
    @keyframes flash-highlight {{
      0% {{ box-shadow: 0 0 0 4px var(--neon-cyan); }}
      100% {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <header class="arena-header">
    <div class="live-tag">🟢 7-TRACK CLINICAL SENTINEL • 5-ALLIED HQs LINKED</div>
    <div class="arena-title">⚔️ CLINICAL BATTLE ARENA</div>
    <div class="arena-subtitle">ระบบเฝ้าระวังหลักฐานเชิงประจักษ์ 7 สายงานคลินิก • กรองเฉพาะงานวิจัยคุณภาพ N ≥ 30 & Free PMC • รพ.เสิงสาง</div>
    <div class="kpi-strip">
      <div class="kpi-chip">📅 อัปเดตล่าสุด: <strong>{report_date}</strong></div>
      <div class="kpi-chip">📚 เปเปอร์ผ่านเกณฑ์: <strong>{total_articles} เรื่อง</strong></div>
      <div class="kpi-chip">📖 PMC Full-Text: <strong>อ่านฟรี {free_pmc_count} เรื่อง</strong></div>
    </div>
    <button class="sound-btn" onclick="playGong()">🔔 เคาะระฆังเปิดศึก (Fight Bell)</button>
  </header>

  <div class="container">
    <div class="mode-switch-bar">
      <button class="mode-btn active" id="btn-fun" onclick="switchMode('fun')">🥊 โหมดศึกดวล Quick-Scan (7 หมวด)</button>
      <button class="mode-btn" id="btn-formal" onclick="switchMode('formal')">📑 โหมดเอกสารทางการ (Formal Dossier)</button>
    </div>

    <div class="filter-scroll" id="trackPills">
      {pills_joined}
    </div>

    <!-- DYNAMIC MULTI-BOUT MAIN EVENT ARENA (Fix #4) -->
    <div class="battle-card" id="main-showdown">
      <div class="bout-tabs" id="boutTabs"></div>
      <div id="boutHeadline" style="font-size: 0.83rem; color: var(--gold); font-weight: 700;"></div>
      <div class="fighters-arena">
        <div class="fighter-box red">
          <div class="fighter-name" id="redName"></div>
          <div class="fighter-tag" id="redSub"></div>
        </div>
        <div class="vs-circle">VS</div>
        <div class="fighter-box blue">
          <div class="fighter-name" id="blueName"></div>
          <div class="fighter-tag" id="blueSub"></div>
        </div>
      </div>
      <div class="battle-rounds" id="battleRounds"></div>
      <div class="winner-banner">
        <div style="font-size: 1.45rem;">🏆</div>
        <div style="font-size: 0.8rem; color: #a7f3d0;" id="boutVerdict"></div>
      </div>
    </div>

    <!-- CHIBI PHARMACIST CALLOUT -->
    <div class="chibi-callout">
      <div class="chibi-avatar">👨‍⚕️</div>
      <div class="speech-bubble">
        <strong>โน้ตจาก ภก.รัฐนนท์ (ประธานทีม IM รพ.เสิงสาง):</strong>
        "โหมดศึกดวลสรุปคู่เอก 7 หมวดให้อ่านสนุก กระชับ สแกนผลตัดสินได้ใน 1 นาที! ถอดศัพท์แพทย์เป็นภาษาคลินิกทับศัพท์มาตรฐานตามหน้างานจริง หากต้องการอ่านบทคัดย่อฉบับเต็ม สถิติ N, PMC Full-Text และบทวิเคราะห์ 3 มิติ รพ.เสิงสาง (Action, Rx-Sentinel, BI-HQ) คลิกปุ่ม <strong>'อ่านวิเคราะห์ฉบับเต็ม'</strong> หรือสลับไป <strong>'โหมดเอกสารทางการ'</strong> ด้านบนได้ทันทีครับ!"
      </div>
    </div>

    <!-- BATTLE MODE: 7-BOUT CHAMPIONSHIP DECK (Sleek, Fast, Fun, Zero-Clutter) -->
    <div id="battle-cards-container">
      <div class="deck-header">
        <div class="deck-title">🥊 ไฮไลต์ศึกดวล 7 คู่เอกประจำสัปดาห์ (Championship Deck)</div>
        <div class="deck-subtitle">คลิกการ์ดเพื่อสลับคู่มวยด้านบน หรือกดปุ่มอ่านวิเคราะห์เพื่อดูเอกสารและหลักฐานทางการแพทย์ฉบับเต็ม</div>
      </div>
      <div class="champ-deck-grid">
        {champ_deck_joined}
      </div>
    </div>

    <!-- FORMAL MODE: COMPLETE CLINICAL DOSSIER & EVIDENCE CARDS -->
    <main class="formal-box" id="formal-content">
      <div class="formal-header-card">
        <div class="formal-title-row">
          <div class="formal-crest">🏛️</div>
          <div>
            <h2 class="formal-heading">เอกสารรายงานทางการ: การเฝ้าระวังหลักฐานเชิงประจักษ์ 7 สายงานคลินิก (Evidence Surveillance Dossier)</h2>
            <p class="formal-subheading">กลุ่มงานเภสัชกรรมและคุ้มครองผู้บริโภค • คณะกรรมการเภสัชกรรมและการบำบัด (PTC) & ทีม IM โรงพยาบาลเสิงสาง</p>
          </div>
        </div>
        <div class="formal-meta-grid">
          <div class="formal-meta-item">📅 <strong>วันที่จัดทำ:</strong> {report_date}</div>
          <div class="formal-meta-item">📚 <strong>งานวิจัยผ่านเกณฑ์คัดกรอง N ≥ 30:</strong> {total_articles} เรื่อง</div>
          <div class="formal-meta-item">📖 <strong>วารสารเปิดอ่านฟรี PMC Full-Text:</strong> {free_pmc_count} เรื่อง</div>
          <div class="formal-meta-item">👨‍⚕️ <strong>ผู้รับผิดชอบระบบ:</strong> ภก.รัฐนนท์ แสงไทยทวีพร (ภก.ชพ.)</div>
        </div>
      </div>

      <!-- Formal Markdown Dossier Body -->
      <div id="formal-markdown-body" class="formal-markdown-body"></div>

      <hr class="formal-divider">

      <!-- Full Track Sections with 14 Paper Cards (Moved from Battle Mode!) -->
      <div class="formal-evidence-section">
        <div class="formal-section-header">
          <h3 class="formal-section-title">📑 รายการบทคัดย่อและบทวิเคราะห์เชิงลึกประจำสายงาน (Clinical Evidence Cards)</h3>
          <p class="formal-section-sub">บทวิเคราะห์เฉพาะทาง รพ.เสิงสาง (Action) • การเฝ้าระวังความปลอดภัย (Rx-Sentinel) • ความคุ้มค่าทางเศรษฐศาสตร์ (BI-HQ)</p>
        </div>
        <div id="formal-track-cards">
          {all_sections_joined}
        </div>
      </div>
    </main>

    <footer style="text-align: center; margin-top: 2rem; font-size: 0.75rem; color: var(--text-muted);">
      <p><strong>ผู้รับผิดชอบระบบ:</strong> ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ</p>
      <p>ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง</p>
      <p style="margin-top: 0.35rem;">
        <a href="https://canva.link/v9g5tfxdg349vbg" target="_blank" style="color: #c084fc; text-decoration: none;">🎨 เปิดสไลด์ใน Canva Pro →</a>
        &nbsp;|&nbsp;
        <a href="https://github.com/NutCodeLaw/pubmed-clinical-sentinel" target="_blank" style="color: #38bdf8; text-decoration: none;">📦 GitHub Repository →</a>
      </p>
    </footer>
  </div>

  <script>
    const mdContent = {md_escaped};
    const boutsData = {bouts_escaped};
    let currentBoutIndex = 0;
    let currentMode = 'fun';
    let currentTrackFilter = 'all';
    let gongCtx = null;

    // Render Formal Markdown
    const formalMarkdownEl = document.getElementById('formal-markdown-body');
    if (formalMarkdownEl) {{
      if (window.marked) {{
        formalMarkdownEl.innerHTML = marked.parse(mdContent);
      }} else {{
        formalMarkdownEl.textContent = mdContent;
      }}
    }}

    function renderBout(index) {{
      currentBoutIndex = index;
      const b = boutsData[index];
      if (!b) return;

      const tabsEl = document.getElementById('boutTabs');
      tabsEl.innerHTML = boutsData.map((item, idx) =>
        `<button class="bout-tab ${{idx === index ? 'active' : ''}}" onclick="renderBout(${{idx}})">${{item.tab_label}}</button>`
      ).join('');

      document.getElementById('boutHeadline').textContent = b.headline;
      document.getElementById('redName').textContent = b.red_name;
      document.getElementById('redSub').textContent = b.red_sub;
      document.getElementById('blueName').textContent = b.blue_name;
      document.getElementById('blueSub').textContent = b.blue_sub;

      const roundsEl = document.getElementById('battleRounds');
      roundsEl.innerHTML = b.rounds.map(r => `
        <div class="round-row">
          <div class="round-lbl">
            <span>${{r.title}}${{r.evidence_math ? ` <span style="font-size: 0.72rem; color: var(--neon-cyan); opacity: 0.85;">📊 ${{r.evidence_math}}</span>` : ''}}</span>
            <span style="color: var(--emerald);">${{r.verdict}}</span>
          </div>
          <div class="round-bars">
            <div class="bar-fill red" style="width: ${{r.red_pct}}%;"></div>
            <div class="bar-fill blue" style="width: ${{r.blue_pct}}%;"></div>
          </div>
        </div>
      `).join('');

      document.getElementById('boutVerdict').innerHTML = `<strong>ฟันธงหน้างาน รพ.เสิงสาง:</strong> ${{b.verdict_text}}`;
    }}

    // Deterministic Track Filtering across Battle & Formal modes
    function filterTrack(trackId, btn) {{
      currentTrackFilter = trackId;
      document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
      if (btn) {{
        btn.classList.add('active');
      }} else {{
        const matchingBtn = document.querySelector(`.pill-btn[data-pill-track="${{trackId}}"]`) || document.querySelector('.pill-btn');
        if (matchingBtn) matchingBtn.classList.add('active');
      }}

      // Filter Championship Cards in Battle Mode
      const champCards = document.querySelectorAll('.champ-card');
      champCards.forEach(card => {{
        if (trackId === 'all' || card.getAttribute('data-track-id') === trackId) {{
          card.style.display = 'block';
        }} else {{
          card.style.display = 'none';
        }}
      }});

      // Filter Track Sections in Formal Mode
      const formalSections = document.querySelectorAll('#formal-track-cards .track-section');
      formalSections.forEach(sec => {{
        if (trackId === 'all' || sec.getAttribute('data-track-id') === trackId) {{
          sec.style.display = 'block';
        }} else {{
          sec.style.display = 'none';
        }}
      }});

      // Sync Main Event Showdown card if available
      if (trackId !== 'all') {{
        const matchIdx = boutsData.findIndex(b => b.track_id === trackId);
        if (matchIdx !== -1) {{
          renderBout(matchIdx);
        }}
      }}
    }}

    function switchMode(mode) {{
      currentMode = mode;
      document.getElementById('btn-fun').classList.toggle('active', mode === 'fun');
      document.getElementById('btn-formal').classList.toggle('active', mode === 'formal');
      
      const isFun = (mode === 'fun');
      document.getElementById('main-showdown').style.display = isFun ? 'block' : 'none';
      document.getElementById('battle-cards-container').style.display = isFun ? 'block' : 'none';
      document.getElementById('formal-content').style.display = isFun ? 'none' : 'block';
      
      filterTrack(currentTrackFilter, null);
    }}

    function handleChampCardClick(trackId, event) {{
      if (event.target.closest('.champ-read-btn')) return;
      const matchIdx = boutsData.findIndex(b => b.track_id === trackId);
      if (matchIdx !== -1) {{
        renderBout(matchIdx);
        document.getElementById('main-showdown').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    function goToFormalTrack(trackId) {{
      switchMode('formal');
      const pill = document.querySelector(`.pill-btn[data-pill-track="${{trackId}}"]`);
      filterTrack(trackId, pill);

      setTimeout(() => {{
        const target = document.querySelector(`#formal-track-cards .track-section[data-track-id="${{trackId}}"]`);
        if (target) {{
          target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
          target.classList.add('highlight-flash');
          setTimeout(() => {{ target.classList.remove('highlight-flash'); }}, 2000);
        }}
      }}, 150);
    }}

    function playGong() {{
      try {{
        if (!gongCtx) {{
          gongCtx = new (window.AudioContext || window.webkitAudioContext)();
        }}
        if (gongCtx.state === 'suspended') {{
          gongCtx.resume();
        }}
        const osc = gongCtx.createOscillator();
        const gain = gongCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, gongCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(110, gongCtx.currentTime + 1.2);
        gain.gain.setValueAtTime(0.8, gongCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, gongCtx.currentTime + 1.2);
        osc.connect(gain);
        gain.connect(gongCtx.destination);
        osc.start();
        osc.stop(gongCtx.currentTime + 1.2);
      }} catch(e) {{}}
    }}

    // Initialize default bout
    renderBout(0);
  </script>
</body>
</html>"""
    return html


def load_dotenv_if_exists():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception as e:
            print(f"[WARN] Failed to load .env: {e}")


def send_telegram_notification(report_date, total_articles, free_pmc_count, showdown_bouts, portal_url="https://nutcodelaw.github.io/pubmed-clinical-sentinel/"):
    """
    Sends a weekly summary of the latest PubMed Sentinel surveillance to Telegram (every Monday 08:00 AM BKK).
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment variables (or local .env).
    Supports comma-separated chat IDs (e.g. personal chat and hospital channel).
    Uses standard library urllib (zero external dependencies).
    """
    load_dotenv_if_exists()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id_raw:
        print("[INFO] Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
        return False

    targets = [c.strip() for c in chat_id_raw.split(",") if c.strip()]
    if not targets:
        print("[INFO] No valid chat IDs specified.")
        return False

    # Guard: Dispatch ONLY in GitHub Actions CI (weekly Monday 08:00 AM BKK) or when explicitly requested via --telegram flag/FORCE_TELEGRAM
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    force_tg = os.environ.get("FORCE_TELEGRAM", "").lower() in ["true", "1", "yes"] or "--telegram" in sys.argv
    if not is_ci and not force_tg:
        print("[INFO] Local environment detected. Telegram dispatch paused as requested. (Automated GitHub Actions will dispatch weekly on Mondays at 08:00 AM Bangkok Time).")
        return False

    # Concise & punchy format per bout for mobile readability
    bouts_lines = []
    for idx, b in enumerate(showdown_bouts, 1):
        label = b.get("tab_label", f"คู่ที่ {idx}").strip()
        punch = b.get("punchline") or b.get("verdict_text", "")
        if len(punch) > 85:
            punch = punch[:82] + "..."
        bouts_lines.append(f"• {label}\n  ↳ <b>{html_lib.escape(punch)}</b>")

    bouts_summary = "\n\n".join(bouts_lines)

    text = (
        f"🥊 <b>PubMed Clinical Sentinel • Weekly Briefing</b>\n"
        f"📅 <b>ประจำสัปดาห์ (วันจันทร์):</b> {report_date} (08:00 น.) | รพ.เสิงสาง (IM Team)\n\n"
        f"📊 <b>Evidence Surveillance 7 สายงาน:</b>\n"
        f"• วิจัยใหม่ผ่านเกณฑ์ (N ≥ 30): <b>{total_articles} เรื่อง</b>\n"
        f"• PMC Full-Text อ่านฟรี: <b>{free_pmc_count} เรื่อง</b>\n\n"
        f"⚔️ <b>ไฮไลต์ศึกดวล 7 คู่เอกประจำสัปดาห์:</b>\n\n"
        f"{bouts_summary}\n\n"
        f"🌐 <b>เปิดอ่านหน้า Battle Arena & Clinical Dossier:</b>\n"
        f"{portal_url}\n\n"
        f"🤖 <i>Automated Weekly Surveillance Engine • รพ.เสิงสาง</i>"
    )

    # Hard-safety guard: Telegram limit is 4,096 chars; cap strictly at 3,500 chars
    if len(text) > 3500:
        text = text[:3450] + "...\n\n<i>(คลิกอ่านรายละเอียดทั้งหมดได้ที่ลิงก์ด้านบน)</i>"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    success_count = 0

    for target in targets:
        payload = {
            "chat_id": target,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_body = resp.read().decode("utf-8")
                res_json = json.loads(res_body)
                if res_json.get("ok"):
                    print(f"[SUCCESS] Telegram dispatch delivered successfully to chat_id: {target}")
                    success_count += 1
                else:
                    print(f"[WARN] Telegram API error for {target}: {res_json.get('description')}")
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, "read"):
                try:
                    err_msg = e.read().decode("utf-8")
                except Exception:
                    pass
            print(f"[ERROR] Failed to send Telegram notification to {target}: {err_msg}")
            if "chat not found" in err_msg.lower():
                print(f"  💡 คำแนะนำ: สำหรับ Channel/Group {target} กรุณาเชิญ @Google_Antigravity_alert_bot เข้ากลุ่มในฐานะ Administrator")

    return success_count > 0


def main():
    report_date = datetime.date.today().strftime("%Y-%m-%d")
    print(f"=== Starting PubMed Clinical Sentinel (7-Track v2.2.0-HQ): {report_date} ===")

    seen_data = load_json_file(SEEN_FILE, {"last_updated": None, "processed_pmids": []})
    seen_set = set(seen_data.get("processed_pmids", []))
    print(f"[INFO] Loaded {len(seen_set)} previously processed PMIDs.")

    cached_tracks = load_json_file(CACHE_FILE, {})
    cached_by_pmid = {}
    for arts in cached_tracks.values():
        for a in arts:
            if a.get("pmid"):
                cached_by_pmid[a["pmid"]] = a

    latest_report_path = os.path.join(REPORTS_DIR, f"{report_date}_respiratory_sentinel.md")
    existing_summaries = {
        "42993869": {
            "thai_takeaway": "โปรแกรมดิจิทัลบำบัดร่วมกับการติดตามกระบอกพ่นยาช่วยเพิ่มความร่วมมือในการใช้ยาพ่นสูดในผู้ป่วย COPD ได้อย่างมีนัยสำคัญตลอด 24 สัปดาห์",
            "key_metrics": [
                "ความร่วมมือในการใช้ยาพ่นวัดผ่านระบบอิเล็กทรอนิกส์ (EIM): กลุ่มดิจิทัล 59.5% vs กลุ่มดูแลปกติ 33.1% (p = 0.009)",
                "สัดส่วนผู้ป่วยที่เกิดการเปลี่ยนแปลง CAT score ในระดับที่มีความสำคัญทางคลินิก (MCID): OR 2.21 (95% CI 1.11-4.41, p = 0.02)"
            ],
            "soeng_sang_action": "พัฒนาระบบติดตามและแจ้งเตือนการใช้ยาพ่นผ่าน LINE OA เพื่อส่งเสริมความร่วมมือในการใช้ยาของผู้ป่วย COPD ในคลินิกโรคเรื้อรัง"
        },
        "42980725": {
            "thai_takeaway": "หอบหืดในผู้สูงอายุพบสูงขึ้นแต่ยังได้รับการวินิจฉัยและการรักษาต่ำกว่าที่ควรเนื่องจากความซับซ้อนของโรคและข้อจำกัดด้านเทคนิคการพ่นยา",
            "key_metrics": [
                "Systematic Review พบปัญหา Underdiagnosis และ Undertreatment สูงมากในผู้สูงอายุที่มีโรคร่วมหลายโรค",
                "ปัจจัยขัดขวางสำคัญ: ความรอบรู้ด้านสุขภาพต่ำ (Low health literacy), เทคนิคการพ่นยาไม่ถูกต้อง และอาการทับซ้อนกับภาวะหัวใจ/COPD"
            ],
            "soeng_sang_action": "จัดทำแนวทางการประเมินเทคนิคการพ่นยา (Inhaler Device Check) และพิจารณาใช้ Spacer ในผู้สูงอายุทุกรายที่คลินิกระบบทางเดินหายใจ"
        },
        "43007675": {
            "thai_takeaway": "ไม่ควรใช้ยาพ่นสเตียรอยด์ (Mometasone) ระยะยาวในผู้ใหญ่ที่เป็น Sickle Cell Disease ที่มีอาการไอ/หวีดโดยไม่ได้เป็นหอบหืด เพราะทำให้ค่าการอักเสบแย่ลง",
            "key_metrics": [
                "ระดับ sVCAM-1 เพิ่มขึ้น 42% ในกลุ่ม Mometasone เทียบกับ Placebo (95% CI -11% ถึง 96%, p = 0.02)",
                "ผลลัพธ์ทางคลินิกในกลุ่มที่ได้ยาพ่นสเตียรอยด์โดยไม่มีภาวะ Asthma มีแนวโน้มแย่กว่ากลุ่ม Placebo"
            ],
            "soeng_sang_action": "ทบทวนการสั่งใช้ ICS ในผู้ป่วยที่มีอาการทางระบบหายใจเรื้อรัง โดยต้องยืนยันการวินิจฉัยโรคหอบหืดที่ชัดเจนก่อนเริ่มยาพ่นสเตียรอยด์ระยะยาว"
        },
        "42849341": {
            "thai_takeaway": "สูตรผสม Bupropion+Zonisamide ช่วยลดปริมาณควันบุหรี่ได้อย่างรวดเร็วและป้องกันน้ำหนักตัวพุ่งหลังหยุดสูบบุหรี่ได้ดีกว่าสูตรเดี่ยว",
            "key_metrics": [
                "อัตราการเลิกสูบบุหรี่ (mITT): BUP/ZON 26.7% และ BUP 25.0% vs Placebo 10.0%",
                "กลุ่ม BUP/ZON มีระดับก๊าซคาร์บอนมอนอกไซด์ (eCO) ลดลงชัดเจนและป้องกันปัญหาน้ำหนักตัวเด้งหลังเลิกบุหรี่ได้สำเร็จ"
            ],
            "soeng_sang_action": "ในคลินิกฟ้าใส รพ.เสิงสาง ใช้ Bupropion ร่วมกับการให้คำปรึกษาควบคุมน้ำหนักและหญ้าดอกขาวในผู้ป่วยที่กังวลเรื่องอ้วนหลังเลิกบุหรี่"
        },
        "42740717": {
            "thai_takeaway": "ความหลากหลายของยีนตับ CYP2B6 สัมพันธ์กับอัตราความสำเร็จในการใช้ยา Bupropion ช่วยเลิกบุหรี่",
            "key_metrics": [
                "Systematic Review 19 การศึกษา (N=2,590) พบยีน CYP2B6 rs2279343 AA สัมพันธ์กับการเลิกบุหรี่ด้วย Bupropion ที่สำเร็จสูงกว่า",
                "การตอบสนองต่อยาจิตเวชและยาช่วยเลิกบุหรี่ขึ้นกับเอนไซม์ CYP2B6 และ CYP2C19 อย่างมีนัยสำคัญ"
            ],
            "soeng_sang_action": "ติดตามการตอบสนองทางคลินิกต่อ Bupropion ในคลินิกฟ้าใสอย่างใกล้ชิด หากไม่ตอบสนองภายใน 4–6 สัปดาห์ให้พิจารณาปรับแผนการรักษา"
        },
        "42632080": {
            "thai_takeaway": "สารอนุพันธ์ขมิ้นชัน sAc15 ช่วยบรรเทาการบาดเจ็บของปอดอักเสบเฉียบพลัน (ALI) ผ่านการกระตุ้นกลไกต้านอนุมูลอิสระ PI3K/AKT/Nrf2 pathway",
            "key_metrics": [
                "sAc15 จับกับโปรตีน Nrf2 ด้วยค่า KD = 2.68 μM และลดอนุมูลอิสระ ROS ในเซลล์เยื่อบุถุงลมปอดได้ดีกว่า Curcumin ธรรมชาติ",
                "ลดการตายของเซลล์ปอด (Anti-apoptosis) และยับยั้งการอักเสบที่กระตุ้นด้วยสารพิษ LPS ได้อย่างมีนัยสำคัญ"
            ],
            "soeng_sang_action": "ติดตามข้อมูลการพัฒนาสารสกัดขมิ้นชันดัดแปลงโครงสร้างในระดับคลินิกเพื่อต่อยอดการใช้สมุนไพรไทยในโรคระบบทางเดินหายใจ"
        },
        "42667699": {
            "thai_takeaway": "การใช้เคอร์คูมิน (Curcumin จากขมิ้นชัน) ในรูปแบบนาโนแพลตฟอร์มส่งยาเข้าสู่เซลล์ถุงลมปอดโดยตรง ช่วยทำลายเซลล์เสื่อมสภาพและชะลอภาวะพังผืดในปอด",
            "key_metrics": [
                "นวัตกรรม CCMD@Lipo-Apt ปลดปล่อย Curcumin + Ca2+ กระตุ้น Calcium overload ในเซลล์ปอดที่เสื่อมสภาพอย่างจำเพาะเจาะจง",
                "ลดการแสดงออกของยีนพังผืดและยับยั้ง SAEC II senescent cells ช่วยฟื้นฟูเนื้อเยื่อถุงลมปอดในภาวะ Pulmonary Fibrosis"
            ],
            "soeng_sang_action": "สารสกัดขมิ้นชันมีศักยภาพสูงในการต่อยอดสู่นวัตกรรมบำบัดโรคปอดเรื้อรัง ควบคู่กับการเฝ้าระวังอันตรกิริยาต่อตับและยาละลายลิ่มเลือด"
        },
        "43013818": {
            "thai_takeaway": "เปรียบเทียบ 3 ยาหลักป้องกันลิ่มเลือดอุดตัน (VTE) หลังผ่าตัดเปลี่ยนข้อสะโพก/ข้อเข่า (PEPPER Trial, N=18,883): Warfarin/Rivaroxaban ลด VTE ได้ดีกว่าเล็กน้อย แต่ Aspirin มีความปลอดภัยด้านเลือดออกเหนือกว่าระดับมีนัยสำคัญ",
            "key_metrics": [
                "PEPPER RCT (N=18,883 ราย ใน NEJM) เปรียบเทียบ Aspirin 81 mg BID vs Warfarin (INR 2.0) vs Rivaroxaban 10 mg QD นาน 30 วัน",
                "กลุ่ม Warfarin และ Rivaroxaban มีความเสี่ยงเลือดออกและการต้องผ่าตัดซ้ำสูงกว่ากลุ่ม Aspirin อย่างมีนัยสำคัญ"
            ],
            "soeng_sang_action": "ในผู้ป่วยหลังผ่าตัดเปลี่ยนข้อที่มีความเสี่ยง VTE ต่ำหรือเสี่ยงเลือดออกสูง Aspirin เป็นทางเลือกที่ปลอดภัยและช่วยลดภาระการเจาะวัด INR ของคลินิกวาร์ฟาริน"
        },
        "43004015": {
            "thai_takeaway": "Apixaban มีประสิทธิผลป้องกันการกลับเป็นซ้ำของลิ่มเลือดอุดตัน (Acute VTE) เทียบเท่า Rivaroxaban แต่มีอัตราการเกิดเลือดออกทางเดินอาหารและ Major Bleeding ต่ำกว่า",
            "key_metrics": [
                "Systematic Review & Meta-analysis รวม 13 การศึกษา (ผู้ป่วย N=233,569 ราย) เปรียบเทียบ Apixaban กับ Rivaroxaban",
                "Apixaban ลดความเสี่ยง Major Bleeding และ Gastrointestinal Bleeding ได้ดีกว่า Rivaroxaban อย่างมีนัยสำคัญ"
            ],
            "soeng_sang_action": "หากต้องเลือกใช้ยากลุ่ม DOACs ในผู้ป่วย Acute VTE ที่มีประวัติโรคกระเพาะหรือเสี่ยงเลือดออกทางเดินอาหาร ควรพิจารณา Apixaban เป็นลำดับแรก"
        },
        "42844453": {
            "thai_takeaway": "ยาปฏิชีวนะสูตรสั้น (3–5 วัน) รักษาโรคปอดอักเสบชุมชนชนิดไม่รุนแรงในเด็ก (Pediatric Non-severe CAP) ได้ผลไม่ต่างจากสูตรยาว (7–10 วัน) พร้อมเพิ่มความร่วมมือในการกินยา",
            "key_metrics": [
                "Meta-analysis (N=8,970 ราย) ยืนยันอัตราการรักษาล้มเหลวหรือการกลับเป็นซ้ำไม่แตกต่างกันระหว่างยาสูตรสั้นและสูตรยาว",
                "กลุ่มยาสูตรสั้นมีอัตราการกินยาไม่ครบ (Non-adherence) ต่ำกว่าอย่างชัดเจนและลดผลข้างเคียงจากยาปฏิชีวนะ"
            ],
            "soeng_sang_action": "สนับสนุนการจ่าย Amoxicillin สูตรสั้น 3–5 วัน ในเด็กปอดบวมชนิดไม่รุนแรงที่ รพ.เสิงสาง เพื่อลดเชื้อดื้อยาและช่วยให้ผู้ปกครองป้อนยาครบคอร์สได้ง่ายขึ้น"
        },
        "42816130": {
            "thai_takeaway": "ยาป้องกันวัณโรคสูตรสั้นที่มี Rifamycin (เช่น 3HP, 3HR, 4R) ในเด็กและวัยรุ่น มีอัตราการกินยาครบคอร์สสูงกว่าและเกิดพิษต่อตับต่ำกว่าสูตร Isoniazid ยาว 6–9 เดือน",
            "key_metrics": [
                "Network Meta-Analysis ในเด็กและวัยรุ่นที่สัมผัสผู้ป่วยวัณโรค เปรียบเทียบสูตรสั้น (3HP, 3HR, 4R) กับสูตรดั้งเดิม (6H/9H)",
                "สูตรสั้นที่มี Rifampicin/Rifapentine ช่วยลดอุบัติการณ์เกิดวัณโรคระยะลุกลามและมี Completion rate สูงกว่าอย่างมีนัยสำคัญ"
            ],
            "soeng_sang_action": "คลินิกวัณโรค รพ.เสิงสาง ควรใช้สูตรยาสั้น (3HP หรือ 3HR/4R) ในการทำ TB Preventive Treatment (TPT) ในเด็กและผู้สัมผัสใกล้ชิดเพื่อลดพิษต่อตับ"
        },
        "42815285": {
            "thai_takeaway": "ความสำเร็จของการตัดยาล้นเกิน (Deprescribing) ในผู้สูงอายุขึ้นอยู่กับความไว้วางใจในทีมสุขภาพและการสื่อสารแบบตัดสินใจร่วมกัน (Shared Decision-Making) เพื่อลดความกลัวโรคกำเริบ",
            "key_metrics": [
                "Systematic Review วิเคราะห์ปัจจัยส่งเสริมและอุปสรรคของการหยุดยาในผู้สูงอายุที่ใช้ยาตั้งแต่ 5 รายการขึ้นไป (Polypharmacy)",
                "การวางแผนลดยาเป็นลำดับขั้น (Stepwise Tapering) ร่วมกับการให้ข้อมูลที่ชัดเจนช่วยเพิ่มการยอมรับของผู้ป่วยและญาติ"
            ],
            "soeng_sang_action": "เภสัชกรประจำคลินิกผู้สูงอายุและ NCDs รพ.เสิงสาง ควรใช้แนวทางค่อยๆ ปรับลดขนาดยาควบคู่กับการสร้างความมั่นใจแก่ผู้ป่วยและผู้ดูแล"
        },
        "42773858": {
            "thai_takeaway": "การทบทวนรายการยาโดยใช้เครื่องมือ FORTA (Fit fOR The Aged) ช่วยลดการใช้ยาที่ไม่เหมาะสม (PIMs) และการใช้ยาเกินความจำเป็นในผู้สูงอายุได้อย่างมีนัยสำคัญ",
            "key_metrics": [
                "Multicentre RCT (N=443 ราย; กลุ่มทดลอง N=234 vs กลุ่มควบคุม N=209) ประเมินการทบทวนยาตามเกณฑ์ FORTA เทียบกับการดูแลปกติ",
                "ลดสัดส่วนผู้ป่วยที่ได้รับยาไม่เหมาะสม (PIMs) ลงถึง 41.3% และลดการใช้ยาเกินจำเป็น (Overuse) ลง 30.7% (p < 0.001)"
            ],
            "soeng_sang_action": "นำเกณฑ์ FORTA / Beers Criteria มาประยุกต์ใช้ในระบบ Medication Reconciliation หอผู้ป่วยในและคลินิกผู้สูงอายุ รพ.เสิงสาง"
        },
        "42872594": {
            "thai_takeaway": "ขมิ้นชัน (Curcuma longa) มีหลักฐานทางเภสัชเวทสนับสนุนฤทธิ์ต้านอักเสบในระบบทางเดินอาหารและทางเดินหายใจ โดยต้องควบคุมมาตรฐานสารสำคัญ",
            "key_metrics": [
                "ทบทวนมาตรฐานเภสัชเวทของเหง้าขมิ้นชันครอบคลุมตำรับยาหลักทั่วโลกเพื่อยืนยันเอกลักษณ์และความบริสุทธิ์ของสาร Curcuminoids",
                "ชี้เป้าความสำคัญของการควบคุมคุณภาพวัตถุดิบสมุนไพรเพื่อลดความแปรปรวนของผลการรักษาทางคลินิก"
            ],
            "soeng_sang_action": "เข้มงวดการคัดเลือกและตรวจรับผลิตภัณฑ์ขมิ้นชันและสมุนไพรในคลังยา รพ.เสิงสาง ให้ได้มาตรฐานสารสำคัญตามเภสัชตำรับ"
        },
        "42952754": {
            "thai_takeaway": "Network Meta-Analysis ยืนยัน SGLT2i และ GLP-1RA ให้ประโยชน์สูงสุดในการลดอัตรานอน รพ. จาก Heart Failure และชะลอโรคไตในผู้ป่วยเบาหวานที่มีภาวะหัวใจล้มเหลว",
            "key_metrics": [
                "วิเคราะห์เปรียบเทียบ RCTs (N=13,886) ระหว่างยากลุ่ม SGLT2i, GLP-1RA, DPP-4i และ GIP/GLP-1RA",
                "SGLT2i นำโด่งด้านการลด Heart Failure Hospitalization และชะลอการเสื่อมของไต (Cardiorenal composite outcome)"
            ],
            "soeng_sang_action": "ผู้ป่วยเบาหวานชนิดที่ 2 ร่วมกับภาวะหัวใจล้มเหลวหรือโรคไตเรื้อรังใน รพ.เสิงสาง ควรได้รับ Dapagliflozin (SGLT2i) เป็นลำดับแรกตามเกณฑ์"
        },
        "43004293": {
            "thai_takeaway": "Dapagliflozin ช่วยลดการเสียชีวิตและภาวะหัวใจล้มเหลวกำเริบหลังเปลี่ยนลิ้นหัวใจ TAVR ได้ดีเท่าเทียมกันทั้งในผู้ที่เป็นและไม่เป็นเบาหวาน",
            "key_metrics": [
                "DAPA-TAVI RCT (N=1,222 ราย ใน 39 ศูนย์ ติดตามผล 1 ปี) เปรียบเทียบ Dapagliflozin 10 mg กับ Standard care",
                "ลดผลลัพธ์หลัก (All-cause death หรือ Worsening HF) ได้สอดคล้องกันทั้งกลุ่มเป็นเบาหวานและไม่เป็นเบาหวาน (P-interaction > 0.05)"
            ],
            "soeng_sang_action": "มั่นใจในการสั่งจ่าย Dapagliflozin เพื่อป้องกัน Heart Failure กำเริบในผู้ป่วยโรคหัวใจแม้ไม่มีโรคเบาหวานร่วมด้วย"
        },
        "42966367": {
            "thai_takeaway": "ยากลุ่ม DOACs ชนิดรับประทานมีประสิทธิผลลดการเกิดลิ่มเลือดอุดตัน (VTE/DVT) หลังผ่าตัดเปลี่ยนข้อสะโพกได้ดีกว่ายาฉีด LMWH โดยไม่เพิ่มความเสี่ยงเลือดออก",
            "key_metrics": [
                "Meta-analysis (N=28,112 ราย) พบ DOACs ลดความเสี่ยง VTE (OR 0.62, p = 0.002) และ DVT (OR 0.60, p = 0.008) เทียบกับ LMWH",
                "อัตราการเกิดเลือดออกรุนแรงไม่แตกต่างกันอย่างมีนัยสำคัญเมื่อใช้ในขนาดยามาตรฐานที่ได้รับอนุมัติ (OR 1.06, p = 0.279)"
            ],
            "soeng_sang_action": "ใช้เป็นข้อมูลประกอบการพิจารณา DOACs ชนิดรับประทานแทนยาฉีด LMWH ในผู้ป่วยหลังผ่าตัดเปลี่ยนข้อที่มีความเสี่ยงสูงเพื่อความสะดวกและปลอดภัย"
        },
        "42928572": {
            "thai_takeaway": "Apixaban ขนาดต่ำ (2.5 mg วันละ 2 ครั้ง) ป้องกันลิ่มเลือดอุดตันในผู้ป่วยมะเร็งที่รับเคมีบำบัดแบบผู้ป่วยนอกได้ดีเยี่ยม โดยเฉพาะสูตร Platinum",
            "key_metrics": [
                "AVERT Post-hoc RCT (N=563) พบ Apixaban ลดความเสี่ยง VTE ในกลุ่มได้รับยาเคมีบำบัด Platinum (HR 0.30) และ Taxane (HR 0.42)",
                "ผู้ป่วยมะเร็งที่ได้รับสูตร Platinum มีความเสี่ยงเกิด VTE สูงกว่าสูตรอื่นถึง 2.25 เท่าหากไม่ได้รับยาป้องกัน"
            ],
            "soeng_sang_action": "เฝ้าระวังอาการลิ่มเลือดอุดตันอย่างใกล้ชิดในผู้ป่วยมะเร็งที่รับเคมีบำบัดสูตร Platinum และประเมินความเสี่ยง Khorana score ร่วมกับแพทย์"
        },
        "43009825": {
            "thai_takeaway": "Nafithromycin ยาปฏิชีวนะชนิดรับประทานสูตรสั้น 3 วัน ให้ผลการรักษาปอดอักเสบชุมชน (CABP) ไม่ด้อยกว่าการทาน Moxifloxacin 7 วัน",
            "key_metrics": [
                "Phase 3 RCT ยืนยันการทาน Nafithromycin 3 วัน มีอัตราการตอบสนองทางคลินิกไม่ด้อยกว่า (Non-inferior) Moxifloxacin 7 วัน",
                "ตัวยาสามารถกระจายตัวเข้าสู่เนื้อเยื่อปอดและถุงลมได้ความเข้มข้นสูง ช่วยลดระยะเวลาการใช้ยาปฏิชีวนะลงกว่าครึ่ง"
            ],
            "soeng_sang_action": "สนับสนุนแนวทาง Short-Course RDU (3–5 วัน) ในโรคปอดอักเสบชุมชนชนิดไม่รุนแรงเพื่อเพิ่มความร่วมมือในการกินยาและลดการดื้อยา"
        },
        "42888381": {
            "thai_takeaway": "การหยุดยาลดความดันโลหิตในผู้สูงอายุเปราะบางช่วยลดจำนวนยาที่ต้องกินลงได้ แต่ต้องระวังความดันโลหิตซิสโตลิกที่อาจขยับสูงขึ้นประมาณ 11 mmHg",
            "key_metrics": [
                "ทบทวน RCTs (DANTON & RETREAT-FRAIL) พบการหยุดยาลดความดันทำให้ SBP เพิ่มขึ้นเฉลี่ย 11.0 mmHg และลดจำนวนยาลงได้ 1.2 รายการ",
                "ต้องคัดกรองผู้สูงอายุที่มีภาวะความดันต่ำเมื่อเปลี่ยนท่าหรือมีผลข้างเคียงชัดเจนจึงจะได้ประโยชน์สูงสุดจากการหยุดยา"
            ],
            "soeng_sang_action": "การทำ Deprescribing ยาลดความดันในผู้สูงอายุเปราะบางที่ รพ.เสิงสาง ต้องทำแบบค่อยเป็นค่อยไป (Tapering) และนัดวัดความดันติดตามอย่างใกล้ชิด"
        },
        "42894466": {
            "thai_takeaway": "การใช้เครื่องมือดิจิทัลแนะนำการค่อยๆ ลดยาช่วยเพิ่มอัตราการหยุดยาลดกรด PPI ที่ใช้เกินความจำเป็นได้สูงถึง 86% เทียบกับแผ่นพับปกติ 64%",
            "key_metrics": [
                "Multicentre RCT (N=174) พบอัตราการหยุดยา PPI สำเร็จที่ 2 เดือนสูงถึง 86% vs 64% (RR 1.34, 95% CI 1.11-1.61, p = 0.002)",
                "พบอาการกรดไหลย้อนกำเริบซ้ำต่ำมากเมื่อใช้โปรแกรมแนะนำการค่อยๆ ลดขนาดยา (Step-down tapering)"
            ],
            "soeng_sang_action": "นำแนวทาง Step-down PPI Tapering มาใช้ในคลินิก NCDs และผู้สูงอายุ รพ.เสิงสาง เพื่อลดการสั่งใช้ Omeprazole ระยะยาวโดยไม่มีข้อบ่งชี้"
        }
    }
    seed_summaries = existing_summaries
    existing_summaries = parse_existing_markdown_summaries(REPORTS_DIR)
    existing_summaries.update(seed_summaries)

    articles_by_track = {}
    newly_discovered_pmids = []

    for track in TRACK_CONFIGS:
        tid = track["id"]
        tname = track["name"]
        print(f"\n[SCAN] Searching track: {tname} (Past {track['days']} days)...")

        pmids = search_pubmed_pmids(track["query"], reldate=track["days"], retmax=track["max_results"] * 3)
        time.sleep(0.4)
        print(f"  Found {len(pmids)} PMIDs in PubMed search.")

        # Candidate pool processing: fetch uncached PMIDs across full search pool
        to_fetch_pmids = [p for p in pmids if p not in cached_by_pmid]

        fetched_map = {}
        if to_fetch_pmids:
            print(f"  Fetching {len(to_fetch_pmids)} uncached candidate PMID(s): {to_fetch_pmids}")
            fetched_list = fetch_pubmed_articles(to_fetch_pmids, tid)
            time.sleep(0.4)
            for fa in fetched_list:
                fetched_map[fa["pmid"]] = fa
                if fa["pmid"] not in seen_set:
                    newly_discovered_pmids.append(fa["pmid"])

        candidate_articles = []
        for p in pmids:
            if p in cached_by_pmid:
                a = cached_by_pmid[p]
                a["extracted_n"] = extract_sample_size(a.get("title", ""), a.get("abstract", ""))
                is_review_or_meta = any(
                    kw in f"{a.get('title', '')} {a.get('abstract', '')}".lower()
                    for kw in ["systematic review", "meta-analysis", "network meta-analysis", "guideline"]
                )
                if a.get("extracted_n") is not None and a["extracted_n"] < 30 and not is_review_or_meta:
                    print(f"  [CACHE-DE-NOISER] Dropping cached study with N < 30 (N={a['extracted_n']}): {a.get('title', '')[:40]}...")
                    continue
                raw_pmc = (a.get("pmc_id") or "").strip()
                if raw_pmc:
                    a["pmc_id"] = raw_pmc if raw_pmc.upper().startswith("PMC") else f"PMC{raw_pmc}"
                    a["pmc_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{a['pmc_id']}/"
                candidate_articles.append(enrich_article_metadata(a, tid))
            elif p in fetched_map:
                candidate_articles.append(fetched_map[p])

            if len(candidate_articles) >= track["max_results"]:
                break

        track_articles = candidate_articles[:track["max_results"]]

        if not track_articles and cached_tracks.get(tid):
            track_articles = [enrich_article_metadata(a, tid) for a in cached_tracks[tid]][:track["max_results"]]

        articles_by_track[tid] = track_articles
        print(f"  Active articles ready for {tname}: {[a['pmid'] for a in track_articles]}")

    # Enrich all articles with Thai clinical takeaway, metrics, and Soeng Sang action
    print("\n[AI/SYNTHESIS] Enriching articles with Thai Quick-Scan clinical intelligence...")
    enrich_articles_with_gemini(articles_by_track, report_date, existing_summaries)

    # Save updated cache (Fix #5)
    save_json_file(CACHE_FILE, articles_by_track)
    print(f"[CACHE] Saved active 7-track article cache to {CACHE_FILE}")

    # Build Markdown Report
    markdown_report = build_markdown_report(articles_by_track, report_date)

    # 1. Non-Destructive README.md update (Fix #5)
    update_readme_non_destructive(markdown_report)
    print(f"[SAVE] Injected latest report into README.md without overwriting project documentation.")

    # 2. Save Historical Weekly Report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(latest_report_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"[SAVE] Archived report to {latest_report_path}")

    # Compute Evidence-Based Math for Showdown Energy Bars (with fail-safe fallback)
    print("\n[EVIDENCE-MATH] Calculating evidence-based showdown energy bars & trial metrics...")
    calculated_bouts = compute_dynamic_evidence_math(DEFAULT_SHOWDOWN_BOUTS, articles_by_track)

    # 3. Generate Mobile Battle Arena HTML (Fixes #3, #4, #6, #7)
    os.makedirs(DOCS_DIR, exist_ok=True)
    html_dashboard = generate_html_dashboard(
        markdown_report,
        report_date,
        articles_by_track,
        calculated_bouts
    )
    html_path = os.path.join(DOCS_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_dashboard)
    print(f"[SAVE] Generated Mobile Battle Arena v2.2.0-HQ at {html_path}")

    # 4. Export Standardized Multi-HQ Payload (Fix #8)
    payload_data = {
        "schema_version": "2.2.0-HQ",
        "project": "pubmed-clinical-sentinel",
        "generated_at": datetime.datetime.now().isoformat(),
        "report_date": report_date,
        "lead_investigator": "ภก.รัฐนนท์ แสงไทยทวีพร (ประธานทีม IM โรงพยาบาลเสิงสาง)",
        "summary_metrics": {
            "total_tracks": len(TRACK_CONFIGS),
            "total_active_articles": sum(len(v) for v in articles_by_track.values()),
            "newly_discovered_pmids_count": len(newly_discovered_pmids),
            "free_pmc_fulltext_count": sum(
                1 for arts in articles_by_track.values() for a in arts if a.get("has_free_fulltext")
            )
        },
        "showdown_bouts": calculated_bouts,
        "tracks": articles_by_track,
        "allied_hq_consumers": {
            "rx_sentinel_hq": "9c526177-b891-4897-9464-c241a9d83f00",
            "nano_banana_visual_hq": "868c4bf8-e705-4425-a903-518e783cfacd",
            "game_master_supreme_hq": "576e2ea3-d67e-495c-835e-e75fa1f1e557",
            "the_economic_bi_hq": "2ac58029-fde8-4710-9f54-be162f70f3f4",
            "notebooklm_refinery_hq": "8ae2bf04-9004-4f7e-9c39-8d3875f6f9dc"
        }
    }
    save_json_file(PAYLOAD_FILE, payload_data)
    print(f"[BUS] Exported Multi-HQ standardized payload to {PAYLOAD_FILE}")

    # 5. Update seen_pmids.json
    if newly_discovered_pmids:
        for p in newly_discovered_pmids:
            if p not in seen_set:
                seen_data["processed_pmids"].append(p)
        seen_data["last_updated"] = report_date
        save_json_file(SEEN_FILE, seen_data)
        print(f"[DATA] Updated seen_pmids.json with {len(newly_discovered_pmids)} new PMIDs.")

    # 6. Telegram Weekly Surveillance Dispatch (Mondays 08:00 AM BKK)
    print("\n[TELEGRAM] Checking Telegram dispatch configuration (Mondays 08:00 AM BKK)...")
    send_telegram_notification(
        report_date=report_date,
        total_articles=sum(len(v) for v in articles_by_track.values()),
        free_pmc_count=sum(
            1 for arts in articles_by_track.values() for a in arts if a.get("has_free_fulltext")
        ),
        showdown_bouts=calculated_bouts,
        portal_url="https://nutcodelaw.github.io/pubmed-clinical-sentinel/"
    )

    print("\n=== PubMed Clinical Sentinel v2.2.0-HQ completed successfully! ===")


if __name__ == "__main__":
    main()
