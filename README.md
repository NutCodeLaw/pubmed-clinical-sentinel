# 🛡️ PubMed Clinical Sentinel & Battle Arena Engine (v2.1.0-HQ)
### ระบบเฝ้าระวังงานวิจัยทางคลินิกอัจฉริยะ 7 สายงาน และสังเวียนดวลยาบนมือถือ (Mobile Battle Arena)
**สำหรับงานบริการบริบาลเภสัชกรรมคลินิก โรงพยาบาลเสิงสาง**

[![GitHub Pages](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen?style=for-the-badge&logo=github)](https://nutcodelaw.github.io/pubmed-clinical-sentinel/)
[![Canva Template](https://img.shields.io/badge/Canva-Pro%20Template-00C4CC?style=for-the-badge&logo=canva)](https://canva.link/v9g5tfxdg349vbg)
[![Surveillance Tracks](https://img.shields.io/badge/Active%20Tracks-7%20Clinical%20Tracks-blue?style=for-the-badge)](https://github.com/NutCodeLaw/pubmed-clinical-sentinel)
[![Automation](https://img.shields.io/badge/Automation-GitHub%20Actions%2024%2F7-purple?style=for-the-badge&logo=githubactions)](https://github.com/NutCodeLaw/pubmed-clinical-sentinel/actions)

---

## 🌟 จุดเด่นและความสามารถหลัก (Core Capabilities)

1. **7-Track Clinical Surveillance Engine:**
   * สแกน PubMed / NCBI Entrez อัตโนมัติ ครอบคลุม 7 สายคลินิกสำคัญของโรงพยาบาลเสิงสาง
   * ตัวกรองตัด Noise อัจฉริยะ: กรองเฉพาะงานวิจัยคุณภาพสูง, ตรวจจับกลุ่มตัวอย่าง ($N \ge 30$), และไฮไลต์เปเปอร์อ่านฟรี (Free PMC Full-Text Badge)
2. **⚔️ Clinical Battle Arena UI (สังเวียนดวลยาบนมือถือ):**
   * เปลี่ยนบทความวิชาการทื่อๆ เป็น **"ศึกมวยคู่เอก (3-Round Showdown)"** เปรียบเทียบยาคู่แข่งขันชัดเจนใน 10 วินาที
   * **Interactive Web Audio Gong:** เคาะระฆังเปิดศึกเวทีมวยด้วยพลัง Web Audio API ไม่ต้องโหลดไฟล์ MP3 ภายนอก
   * **Chibi Pharmacist Mascot:** มาสคอตเภสัชกรจิ๋วสรุปประเด็นฟันธงหน้างานสไตล์มังงะ
   * **1-Click Mode Toggle:** สลับระหว่าง `[🎮 โหมดศึกดวล (Battle Mode)]` และ `[📄 โหมดทางการ (Formal)]` ได้อย่างอิสระ
3. **🤝 เครือข่าย 5 ศูนย์บัญชาการพันธมิตร (5-Allied HQ Grid):**
   * เชื่อมต่อท่อส่งต่อความรู้ (Knowledge Pipes) กับ 5 ศูนย์แม่บท: `Rx-Sentinel HQ`, `Nano Banana Visual HQ`, `Game Master Supreme HQ`, `The Economic / BI-HQ`, และ `NotebookLM Refinery HQ`
4. **⏰ 24/7 Cloud Automation:**
   * รันสแกนอัตโนมัติบน GitHub Actions ทุกเช้าวันจันทร์ เวลา 07:00 น. (00:00 UTC)
   * ระบบจดจำ PMID (`seen_pmids.json`) ป้องกันการดึงและสรุปงานวิจัยซ้ำซ้อน 100%

---

## 🎯 7 สายคลินิกเฝ้าระวัง (The 7 Surveillance Tracks)

| สายงาน | ไอคอน | ชื่อสายคลินิก | กรอบเวลาสแกน | จุดเน้นเชิงเภสัชกรรม รพ.เสิงสาง |
| :---: | :---: | :--- | :---: | :--- |
| **Track 1** | 🫁 | **Asthma & COPD Pharmacotherapy** | 14 วัน | Triple Therapy, Biologics (TSLP/IL-5), Inhaler Devices |
| **Track 2** | 🚭 | **Smoking Cessation** | 60 วัน | Varenicline, Bupropion, Cytisine, คลินิกฟ้าใส รพ.เสิงสาง |
| **Track 3** | 🌿 | **Thai Herbal Medicine in Respiratory** | 180 วัน | ฟ้าทะลายโจร (Andrographolide mg), มะขามป้อม, ขมิ้นชัน, หญ้าดอกขาว |
| **Track 4** | 🫀 | **Cardio-Renal-Metabolic (CRM)** | 14 วัน | SGLT2i, GLP-1 RA, Finerenone, ชะลอไตเสื่อมใน DM/CKD/HF |
| **Track 5** | 🩸 | **Anticoagulation & High Alert Drugs** | 30 วัน | Warfarin vs DOACs, INR Stability, Bleeding vs Thrombosis |
| **Track 6** | 🦠 | **Antimicrobial Stewardship (AMS)** | 45 วัน | Short-course Antibiotics, RDU, IV-to-Oral Switch |
| **Track 7** | 👴 | **Deprescribing & Polypharmacy** | 60 วัน | การตัดยาล้นเกินในผู้สูงอายุ, Beers / STOPP Criteria |

---

## 📁 โครงสร้างโปรเจกต์ (Repository Architecture)

```
pubmed-clinical-sentinel/
├── .github/
│   └── workflows/
│       └── weekly_sentinel.yml       # GitHub Actions 24/7 Automated Cron
├── data/
│   └── seen_pmids.json              # ฐานข้อมูลจดจำ PMID ป้องกันการสแกนซ้ำ
├── docs/
│   └── index.html                   # หน้าเว็บ Mobile Battle Arena (GitHub Pages)
├── reports/
│   └── 2026-11-12_respiratory_sentinel.md  # รายงานสรุปคลินิกรอบสัปดาห์
├── scripts/
│   └── sentinel.py                  # เครื่องยนต์หลักดึง PubMed, ประมวลผล & สร้างเว็บ
├── ALLIED_HQ_HANDSHAKE_REGISTRY.md   # ทะเบียนและสเปกท่อส่งต่อความรู้ 5 ศูนย์แม่บท
├── ALLIED_HQ_HANDSHAKE_REGISTRY.json # สเปกเชื่อมต่อระดับ Machine-Readable
├── KNOWLEDGE_BASE_MASTER.md          # ฐานข้อมูลองค์ความรู้แม่บทจากการพัฒนา
├── project_manifest.json             # Manifest ประจำโปรเจกต์ (v2.1.0-HQ)
├── requirements.txt                  # Python Dependencies
└── README.md                         # คู่มือภาพรวมโครงการ
```

---

## 🚀 วิธีการติดตั้งและรันงาน (Quickstart Guide)

### 1. รันบนเครื่องคอมพิวเตอร์ (Local Execution)
```bash
# Clone โปรเจกต์
git clone https://github.com/NutCodeLaw/pubmed-clinical-sentinel.git
cd pubmed-clinical-sentinel

# ติดตั้ง Dependencies
pip install -r requirements.txt

# สั่งรันเครื่องยนต์สแกน 7 สายคลินิกทันที
python scripts/sentinel.py
```
*เมื่อสคริปต์รันเสร็จ จะอัปเดตไฟล์ `data/seen_pmids.json`, บันทึกรายงานใน `reports/`, และอัปเดตหน้าเว็บ `docs/index.html` โดยอัตโนมัติ*

### 2. ดูผลลัพธ์ผ่านหน้าเว็บมือถือทันที
เปิดไฟล์ `docs/index.html` บน Browser ใดๆ หรือเข้าชมผ่าน [Live GitHub Pages](https://nutcodelaw.github.io/pubmed-clinical-sentinel/)

---

## 🌐 ลิงก์เชื่อมโยงสำคัญ (Ecosystem Links)
* 📱 **Mobile Battle Arena Portal:** [https://nutcodelaw.github.io/pubmed-clinical-sentinel/](https://nutcodelaw.github.io/pubmed-clinical-sentinel/)
* 🎨 **Canva Pro Editable Presentation:** [https://canva.link/v9g5tfxdg349vbg](https://canva.link/v9g5tfxdg349vbg) (Design ID: `DAHarQlAFX8`)
* 📦 **GitHub Repository:** [https://github.com/NutCodeLaw/pubmed-clinical-sentinel](https://github.com/NutCodeLaw/pubmed-clinical-sentinel)

---

**จัดทำและดูแลโดย:**  
**ภก.รัฐนนท์ แสงไทยทวีพร**  
*เภสัชกรชำนาญการ (ประธานทีม Information Management โรงพยาบาลเสิงสาง)*
