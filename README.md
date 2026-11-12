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

---

## 📋 รายงานสรุปงานวิจัยทางคลินิกล่าสุด (Latest Weekly Digest)

<!-- SENTINEL_REPORT_START -->

# 🩺 สรุปรายงานวิจัยทางคลินิก 7 หมวดสำคัญ (Clinical Pharmacy Research Update)
**ประจำวันที่:** 2026-11-12 | **เวอร์ชันเครื่องยนต์:** `v2.2.0-HQ (5-Allied HQs Synchronized)`  
*ทีมสารสนเทศสมุนไพรและเภสัชบำบัด (IM Team) โรงพยาบาลเสิงสาง*

---

### 1. 🫁 เภสัชบำบัดโรคหอบหืดและปอดอุดกั้นเรื้อรัง (Asthma & COPD Pharmacotherapy)

#### 1. Effectiveness of a Multicomponent Digital Therapeutic Program on Inhaled Medication Adherence in Chronic Obstructive Pulmonary Disease: Pilot Randomized Controlled Trial.
- **วารสาร & PMID:** JMIR mHealth and uHealth • [PMID: 42993869](https://pubmed.ncbi.nlm.nih.gov/42993869/) • 👥 `N=158` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13742779/)
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** โปรแกรมดิจิทัลบำบัดร่วมกับการติดตามกระบอกพ่นยาช่วยเพิ่มความร่วมมือในการใช้ยาพ่นสูดในผู้ป่วย COPD ได้อย่างมีนัยสำคัญตลอด 24 สัปดาห์
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [ความร่วมมือในการใช้ยาพ่นวัดผ่านระบบอิเล็กทรอนิกส์ (EIM): กลุ่มดิจิทัล 59.5% vs กลุ่มดูแลปกติ 33.1% (p = 0.009)]
  • [สัดส่วนผู้ป่วยที่เกิดการเปลี่ยนแปลง CAT score ในระดับที่มีความสำคัญทางคลินิก (MCID): OR 2.21 (95% CI 1.11-4.41, p = 0.02)]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** พัฒนาระบบติดตามและแจ้งเตือนการใช้ยาพ่นผ่าน LINE OA เพื่อส่งเสริมความร่วมมือในการใช้ยาของผู้ป่วย COPD ในคลินิกโรคเรื้อรัง
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ทบทวนเทคนิคการพ่นยา (Inhaler Technique) ทุกครั้งก่อนปรับ Step ยา • ยากลุ่ม Biologics ต้องคัดกรอง Eosinophils/FeNO ตามเกณฑ์
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ยากลุ่ม Biologics มีราคาสูง ควรจำกัดเฉพาะเคส Severe Refractory ที่ลดการส่งตัวผ่าตัดซ้ำหรือลดการแอดมิด ICU ได้ชัดเจน
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42993869/)

#### 2. Asthma in Older Adults: A Systematic Review of Real-World Burden and Outcomes.
- **วารสาร & PMID:** Current allergy and asthma reports • [PMID: 42980725](https://pubmed.ncbi.nlm.nih.gov/42980725/) • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13736361/)
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** หอบหืดในผู้สูงอายุพบสูงขึ้นแต่ยังได้รับการวินิจฉัยและการรักษาต่ำกว่าที่ควรเนื่องจากความซับซ้อนของโรคและข้อจำกัดด้านเทคนิคการพ่นยา
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Systematic Review พบปัญหา Underdiagnosis และ Undertreatment สูงมากในผู้สูงอายุที่มีโรคร่วมหลายโรค]
  • [ปัจจัยขัดขวางสำคัญ: ความรอบรู้ด้านสุขภาพต่ำ (Low health literacy), เทคนิคการพ่นยาไม่ถูกต้อง และอาการทับซ้อนกับภาวะหัวใจ/COPD]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** จัดทำแนวทางการประเมินเทคนิคการพ่นยา (Inhaler Device Check) และพิจารณาใช้ Spacer ในผู้สูงอายุทุกรายที่คลินิกระบบทางเดินหายใจ
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ทบทวนเทคนิคการพ่นยา (Inhaler Technique) ทุกครั้งก่อนปรับ Step ยา • ยากลุ่ม Biologics ต้องคัดกรอง Eosinophils/FeNO ตามเกณฑ์
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ยากลุ่ม Biologics มีราคาสูง ควรจำกัดเฉพาะเคส Severe Refractory ที่ลดการส่งตัวผ่าตัดซ้ำหรือลดการแอดมิด ICU ได้ชัดเจน
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42980725/)

#### 3. Inhaled Corticosteroids and Sickle Cell Disease Severity in Adults Without Asthma: A Randomized Clinical Trial.
- **วารสาร & PMID:** JAMA network open • [PMID: 43007675](https://pubmed.ncbi.nlm.nih.gov/43007675/) • 👥 `N=77`
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** ไม่ควรใช้ยาพ่นสเตียรอยด์ (Mometasone) ระยะยาวในผู้ใหญ่ที่เป็น Sickle Cell Disease ที่มีอาการไอ/หวีดโดยไม่ได้เป็นหอบหืด เพราะทำให้ค่าการอักเสบแย่ลง
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [ระดับ sVCAM-1 เพิ่มขึ้น 42% ในกลุ่ม Mometasone เทียบกับ Placebo (95% CI -11% ถึง 96%, p = 0.02)]
  • [ผลลัพธ์ทางคลินิกในกลุ่มที่ได้ยาพ่นสเตียรอยด์โดยไม่มีภาวะ Asthma มีแนวโน้มแย่กว่ากลุ่ม Placebo]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ทบทวนการสั่งใช้ ICS ในผู้ป่วยที่มีอาการทางระบบหายใจเรื้อรัง โดยต้องยืนยันการวินิจฉัยโรคหอบหืดที่ชัดเจนก่อนเริ่มยาพ่นสเตียรอยด์ระยะยาว
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ทบทวนเทคนิคการพ่นยา (Inhaler Technique) ทุกครั้งก่อนปรับ Step ยา • ยากลุ่ม Biologics ต้องคัดกรอง Eosinophils/FeNO ตามเกณฑ์
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ยากลุ่ม Biologics มีราคาสูง ควรจำกัดเฉพาะเคส Severe Refractory ที่ลดการส่งตัวผ่าตัดซ้ำหรือลดการแอดมิด ICU ได้ชัดเจน
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/43007675/)

---

### 2. 🚭 เภสัชบำบัดช่วยเลิกบุหรี่ (Smoking Cessation Pharmacotherapy)

#### 1. Combination bupropion-zonisamide facilitates rapid reduction in smoke exposure and prevents weight gain during switching to electronic nicotine delivery systems: A randomized clinical trial.
- **วารสาร & PMID:** Drug and alcohol dependence • [PMID: 42849341](https://pubmed.ncbi.nlm.nih.gov/42849341/) • 👥 `N=60`
- **สถานะบัญชียา รพ.เสิงสาง:** `🔴 ยานอกบัญชี รพ. / ผู้ท้าชิงเข้า PTC`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** สูตรผสม Bupropion+Zonisamide ช่วยลดปริมาณควันบุหรี่ได้อย่างรวดเร็วและป้องกันน้ำหนักตัวพุ่งหลังหยุดสูบบุหรี่ได้ดีกว่าสูตรเดี่ยว
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [อัตราการเลิกสูบบุหรี่ (mITT): BUP/ZON 26.7% และ BUP 25.0% vs Placebo 10.0%]
  • [กลุ่ม BUP/ZON มีระดับก๊าซคาร์บอนมอนอกไซด์ (eCO) ลดลงชัดเจนและป้องกันปัญหาน้ำหนักตัวเด้งหลังเลิกบุหรี่ได้สำเร็จ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ในคลินิกฟ้าใส รพ.เสิงสาง ใช้ Bupropion ร่วมกับการให้คำปรึกษาควบคุมน้ำหนักและหญ้าดอกขาวในผู้ป่วยที่กังวลเรื่องอ้วนหลังเลิกบุหรี่
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** คัดกรองประวัติโรคลมชัก (Seizure risk) ก่อนจ่าย Bupropion ในคลินิกฟ้าใส • ติดตามอาการนอนไม่หลับและน้ำหนักตัว
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** การช่วยให้ผู้ป่วยเลิกบุหรี่สำเร็จในคลินิกฟ้าใส ให้ผลตอบแทนทางเศรษฐศาสตร์สาธารณสุขสูงสุดในการลดโรคหลอดเลือดหัวใจและ COPD กำเริบ
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42849341/)

#### 2. The influence of pharmacogenetics on the treatment-related outcomes of antidepressants and antipsychotics in Brazil: a systematic review.
- **วารสาร & PMID:** Pharmacogenomics • [PMID: 42740717](https://pubmed.ncbi.nlm.nih.gov/42740717/) • 👥 `N=2,590` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13671432/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟢 มีในคลังยา รพ.เสิงสาง`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** ความหลากหลายของยีนตับ CYP2B6 สัมพันธ์กับอัตราความสำเร็จในการใช้ยา Bupropion ช่วยเลิกบุหรี่
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Systematic Review 19 การศึกษา (N=2,590) พบยีน CYP2B6 rs2279343 AA สัมพันธ์กับการเลิกบุหรี่ด้วย Bupropion ที่สำเร็จสูงกว่า]
  • [การตอบสนองต่อยาจิตเวชและยาช่วยเลิกบุหรี่ขึ้นกับเอนไซม์ CYP2B6 และ CYP2C19 อย่างมีนัยสำคัญ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ติดตามการตอบสนองทางคลินิกต่อ Bupropion ในคลินิกฟ้าใสอย่างใกล้ชิด หากไม่ตอบสนองภายใน 4–6 สัปดาห์ให้พิจารณาปรับแผนการรักษา
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** คัดกรองประวัติโรคลมชัก (Seizure risk) ก่อนจ่าย Bupropion ในคลินิกฟ้าใส • ติดตามอาการนอนไม่หลับและน้ำหนักตัว
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** การช่วยให้ผู้ป่วยเลิกบุหรี่สำเร็จในคลินิกฟ้าใส ให้ผลตอบแทนทางเศรษฐศาสตร์สาธารณสุขสูงสุดในการลดโรคหลอดเลือดหัวใจและ COPD กำเริบ
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42740717/)

---

### 3. 🌿 สมุนไพรไทยทางคลินิกในระบบทางเดินหายใจ (Thai Herbal Medicine in Respiratory Care)

#### 1. Triple-pathway synergistic senolysis via AKAP1 silencing and calcium overload: An aptamer-functionalized DNAzyme nanoplatform for anti-pulmonary fibrosis research.
- **วารสาร & PMID:** Colloids and surfaces. B, Biointerfaces • [PMID: 42667699](https://pubmed.ncbi.nlm.nih.gov/42667699/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟢 มีในคลังยา รพ.เสิงสาง`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** การใช้เคอร์คูมิน (Curcumin จากขมิ้นชัน) ในรูปแบบนาโนแพลตฟอร์มส่งยาเข้าสู่เซลล์ถุงลมปอดโดยตรง ช่วยทำลายเซลล์เสื่อมสภาพและชะลอภาวะพังผืดในปอด
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [นวัตกรรม CCMD@Lipo-Apt ปลดปล่อย Curcumin + Ca2+ กระตุ้น Calcium overload ในเซลล์ปอดที่เสื่อมสภาพอย่างจำเพาะเจาะจง]
  • [ลดการแสดงออกของยีนพังผืดและยับยั้ง SAEC II senescent cells ช่วยฟื้นฟูเนื้อเยื่อถุงลมปอดในภาวะ Pulmonary Fibrosis]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** สารสกัดขมิ้นชันมีศักยภาพสูงในการต่อยอดสู่นวัตกรรมบำบัดโรคปอดเรื้อรัง ควบคู่กับการเฝ้าระวังอันตรกิริยาต่อตับและยาละลายลิ่มเลือด
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** CYP450 Herb-Drug Alert: ฟ้าทะลายโจรและขมิ้นชันยับยั้ง CYP2C9/CYP3A4 ห้ามจ่ายร่วมกับ Warfarin หรือยากดภูมิคุ้มกัน (เสี่ยงเลือดออกง่าย)
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ส่งเสริมการใช้ยาสมุนไพรในบัญชียาหลักแห่งชาติ ทดแทนยานำเข้าและสร้างความมั่นคงทางยาของ รพ.ชุมชน
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42667699/)

#### 2. Integrated analytical characterization and multiscale modeling of supramolecular interactions in lumefantrine-curcumin coamorphous systems with enhanced biopharmaceutical and anticancer performance.
- **วารสาร & PMID:** Talanta • [PMID: 42398138](https://pubmed.ncbi.nlm.nih.gov/42398138/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟢 มีในคลังยา รพ.เสิงสาง`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** นวัตกรรมพัฒนายาร่วม Lumefantrine และเคอร์คูมิน (ขมิ้นชัน) รูปแบบ Coamorphous ช่วยแก้ปัญหาการละลาย เพิ่มการดูดซึม และคงตัวได้นาน 6 เดือน
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [เพิ่มการละลายน้ำ (Apparent solubility) สูงขึ้น 2-4 เท่า และปลดปล่อยตัวยา >85-90% ภายใน 6 ชั่วโมง]
  • [คงสภาพโครงสร้าง amorphous นาน 6 เดือน ในสภาวะเร่ง และเพิ่มฤทธิ์เร่งการตาย (Apoptosis) ของเซลล์มะเร็งปอด A549]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ใช้เป็นข้อมูลสนับสนุนการพัฒนานวัตกรรมนำส่งยาจากสารสกัดสมุนไพรไทย (ขมิ้นชัน) ร่วมกับยาแผนปัจจุบันเพื่อเพิ่มประสิทธิผลการรักษา
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** CYP450 Herb-Drug Alert: ฟ้าทะลายโจรและขมิ้นชันยับยั้ง CYP2C9/CYP3A4 ห้ามจ่ายร่วมกับ Warfarin หรือยากดภูมิคุ้มกัน (เสี่ยงเลือดออกง่าย)
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ส่งเสริมการใช้ยาสมุนไพรในบัญชียาหลักแห่งชาติ ทดแทนยานำเข้าและสร้างความมั่นคงทางยาของ รพ.ชุมชน
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42398138/)

---

### 4. 🫀 ชะลอไตเสื่อม & เมตาบอลิกหัวใจ (Cardio-Renal CRM: SGLT2i, GLP-1RA, Finerenone)

#### 1. Network and pairwise meta-analysis of the effects of novel hypoglycemic agents on cardiorenal outcomes in patients with type 2 diabetes and heart failure.
- **วารสาร & PMID:** Frontiers in endocrinology • [PMID: 42952754](https://pubmed.ncbi.nlm.nih.gov/42952754/) • 👥 `N=13,886` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13713430/)
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** Network Meta-Analysis ยืนยัน SGLT2i และ GLP-1RA ให้ประโยชน์สูงสุดในการลดอัตรานอน รพ. จาก Heart Failure และชะลอโรคไตในผู้ป่วยเบาหวานที่มีภาวะหัวใจล้มเหลว
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [วิเคราะห์เปรียบเทียบ RCTs (N=13,886) ระหว่างยากลุ่ม SGLT2i, GLP-1RA, DPP-4i และ GIP/GLP-1RA]
  • [SGLT2i นำโด่งด้านการลด Heart Failure Hospitalization และชะลอการเสื่อมของไต (Cardiorenal composite outcome)]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ผู้ป่วยเบาหวานชนิดที่ 2 ร่วมกับภาวะหัวใจล้มเหลวหรือโรคไตเรื้อรังใน รพ.เสิงสาง ควรได้รับ Dapagliflozin (SGLT2i) เป็นลำดับแรกตามเกณฑ์
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ตรวจ eGFR ก่อนเริ่มยา (Dapagliflozin ห้ามเริ่มหาก eGFR < 25 mL/min) • เฝ้าระวัง Euglycemic DKA และการติดเชื้อทางเดินปัสสาวะ
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** คุ้มค่าสูง (High ROI): ลดค่าใช้จ่ายการนอน รพ.ซ้ำจากภาวะหัวใจล้มเหลว (HF Readmission) และชะลอการฟอกไตในระยะยาว
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42952754/)

#### 2. Influence of diabetes mellitus on dapagliflozin response after transcatheter aortic valve replacement (TAVR): insights from the DAPA-TAVI trial.
- **วารสาร & PMID:** Cardiovascular diabetology • [PMID: 43004293](https://pubmed.ncbi.nlm.nih.gov/43004293/) • 👥 `N=1,222` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13746418/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟢 มีในคลังยา รพ.เสิงสาง`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** Dapagliflozin ช่วยลดการเสียชีวิตและภาวะหัวใจล้มเหลวกำเริบหลังเปลี่ยนลิ้นหัวใจ TAVR ได้ดีเท่าเทียมกันทั้งในผู้ที่เป็นและไม่เป็นเบาหวาน
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [DAPA-TAVI RCT (N=1,222 ราย ใน 39 ศูนย์ ติดตามผล 1 ปี) เปรียบเทียบ Dapagliflozin 10 mg กับ Standard care]
  • [ลดผลลัพธ์หลัก (All-cause death หรือ Worsening HF) ได้สอดคล้องกันทั้งกลุ่มเป็นเบาหวานและไม่เป็นเบาหวาน (P-interaction > 0.05)]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** มั่นใจในการสั่งจ่าย Dapagliflozin เพื่อป้องกัน Heart Failure กำเริบในผู้ป่วยโรคหัวใจแม้ไม่มีโรคเบาหวานร่วมด้วย
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ตรวจ eGFR ก่อนเริ่มยา (Dapagliflozin ห้ามเริ่มหาก eGFR < 25 mL/min) • เฝ้าระวัง Euglycemic DKA และการติดเชื้อทางเดินปัสสาวะ
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** คุ้มค่าสูง (High ROI): ลดค่าใช้จ่ายการนอน รพ.ซ้ำจากภาวะหัวใจล้มเหลว (HF Readmission) และชะลอการฟอกไตในระยะยาว
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/43004293/)

---

### 5. 🩸 ยาต้านการแข็งตัวของเลือด & HAD (Warfarin vs DOACs)

#### 1. Prevention of Venous Thromboembolism after Total Hip or Knee Replacement.
- **วารสาร & PMID:** The New England journal of medicine • [PMID: 43013818](https://pubmed.ncbi.nlm.nih.gov/43013818/) • 👥 `N=18,883`
- **สถานะบัญชียา รพ.เสิงสาง:** `🟡 ยาบัญชี จ(2) / เงื่อนไขเฉพาะ รพ.`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** เปรียบเทียบ 3 ยาหลักป้องกันลิ่มเลือดอุดตัน (VTE) หลังผ่าตัดเปลี่ยนข้อสะโพก/ข้อเข่า (PEPPER Trial, N=18,883): Warfarin/Rivaroxaban ลด VTE ได้ดีกว่าเล็กน้อย แต่ Aspirin มีความปลอดภัยด้านเลือดออกเหนือกว่าระดับมีนัยสำคัญ
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [PEPPER RCT (N=18,883 ราย ใน NEJM) เปรียบเทียบ Aspirin 81 mg BID vs Warfarin (INR 2.0) vs Rivaroxaban 10 mg QD นาน 30 วัน]
  • [กลุ่ม Warfarin และ Rivaroxaban มีความเสี่ยงเลือดออกและการต้องผ่าตัดซ้ำสูงกว่ากลุ่ม Aspirin อย่างมีนัยสำคัญ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** ในผู้ป่วยหลังผ่าตัดเปลี่ยนข้อที่มีความเสี่ยง VTE ต่ำหรือเสี่ยงเลือดออกสูง Aspirin เป็นทางเลือกที่ปลอดภัยและช่วยลดภาระการเจาะวัด INR ของคลินิกวาร์ฟาริน
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ประเมินค่าไต CrCl ก่อนจ่าย DOACs • กรณีใช้ Warfarin ให้คุม Target INR 2.0–3.0 และระวังอันตรกิริยากับยาฆ่าเชื้อ/สมุนไพร
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ลดต้นทุนแฝง รพ.: การใช้ Aspirin ในกลุ่มเสี่ยงต่ำหลังผ่าตัดข้อ หรือเลือก DOAC ในกลุ่มเสี่ยงเลือดออกทางเดินอาหาร ช่วยลดภาระการเจาะ Lab INR และค่านอน รพ.จาก GI Bleed
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/43013818/)

#### 2. Efficacy and safety of apixaban versus rivaroxaban in acute venous thromboembolism: a systematic review and meta-analysis.
- **วารสาร & PMID:** European journal of clinical pharmacology • [PMID: 43004015](https://pubmed.ncbi.nlm.nih.gov/43004015/) • 👥 `N=233,569` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7556153/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟡 ยาบัญชี จ(2) / เงื่อนไขเฉพาะ รพ.`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** Apixaban มีประสิทธิผลป้องกันการกลับเป็นซ้ำของลิ่มเลือดอุดตัน (Acute VTE) เทียบเท่า Rivaroxaban แต่มีอัตราการเกิดเลือดออกทางเดินอาหารและ Major Bleeding ต่ำกว่า
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Systematic Review & Meta-analysis รวม 13 การศึกษา (ผู้ป่วย N=233,569 ราย) เปรียบเทียบ Apixaban กับ Rivaroxaban]
  • [Apixaban ลดความเสี่ยง Major Bleeding และ Gastrointestinal Bleeding ได้ดีกว่า Rivaroxaban อย่างมีนัยสำคัญ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** หากต้องเลือกใช้ยากลุ่ม DOACs ในผู้ป่วย Acute VTE ที่มีประวัติโรคกระเพาะหรือเสี่ยงเลือดออกทางเดินอาหาร ควรพิจารณา Apixaban เป็นลำดับแรก
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** ประเมินค่าไต CrCl ก่อนจ่าย DOACs • กรณีใช้ Warfarin ให้คุม Target INR 2.0–3.0 และระวังอันตรกิริยากับยาฆ่าเชื้อ/สมุนไพร
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ลดต้นทุนแฝง รพ.: การใช้ Aspirin ในกลุ่มเสี่ยงต่ำหลังผ่าตัดข้อ หรือเลือก DOAC ในกลุ่มเสี่ยงเลือดออกทางเดินอาหาร ช่วยลดภาระการเจาะ Lab INR และค่านอน รพ.จาก GI Bleed
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/43004015/)

---

### 6. 🦠 การจัดการยาปฏิชีวนะ & สูตรยาสั้น (AMS & Short-Course RDU)

#### 1. Short- versus long-course antibiotic therapy in non-severe CAP in children: a systematic review and meta-analysis.
- **วารสาร & PMID:** European journal of pediatrics • [PMID: 42844453](https://pubmed.ncbi.nlm.nih.gov/42844453/) • 👥 `N=8,970`
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** ยาปฏิชีวนะสูตรสั้น (3–5 วัน) รักษาโรคปอดอักเสบชุมชนชนิดไม่รุนแรงในเด็ก (Pediatric Non-severe CAP) ได้ผลไม่ต่างจากสูตรยาว (7–10 วัน) พร้อมเพิ่มความร่วมมือในการกินยา
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Meta-analysis (N=8,970 ราย) ยืนยันอัตราการรักษาล้มเหลวหรือการกลับเป็นซ้ำไม่แตกต่างกันระหว่างยาสูตรสั้นและสูตรยาว]
  • [กลุ่มยาสูตรสั้นมีอัตราการกินยาไม่ครบ (Non-adherence) ต่ำกว่าอย่างชัดเจนและลดผลข้างเคียงจากยาปฏิชีวนะ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** สนับสนุนการจ่าย Amoxicillin สูตรสั้น 3–5 วัน ในเด็กปอดบวมชนิดไม่รุนแรงที่ รพ.เสิงสาง เพื่อลดเชื้อดื้อยาและช่วยให้ผู้ปกครองป้อนยาครบคอร์สได้ง่ายขึ้น
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** เกณฑ์ Short-Course RDU ใช้เฉพาะผู้ป่วย Non-severe ที่ภูมิคุ้มกันปกติ • ประเมินอาการไข้ลดลงครบ 48 ชม. ก่อนหยุดยา
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ประหยัดงบค่ายาโดยตรง 40–50% ต่อคอร์ส ลดโอกาสเกิดเชื้อดื้อยาที่ต้องใช้ยาฉีดราคาแพง (Carbapenems/Vancomycin)
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42844453/)

#### 2. Effectiveness and safety of the available preventive tuberculosis treatment regimens for children and adolescents: systematic review and network meta-analysis.
- **วารสาร & PMID:** BMJ paediatrics open • [PMID: 42816130](https://pubmed.ncbi.nlm.nih.gov/42816130/) • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13629875/)
- **สถานะบัญชียา รพ.เสิงสาง:** `🟢 มีในคลังยา รพ.เสิงสาง`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** ยาป้องกันวัณโรคสูตรสั้นที่มี Rifamycin (เช่น 3HP, 3HR, 4R) ในเด็กและวัยรุ่น มีอัตราการกินยาครบคอร์สสูงกว่าและเกิดพิษต่อตับต่ำกว่าสูตร Isoniazid ยาว 6–9 เดือน
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Network Meta-Analysis ในเด็กและวัยรุ่นที่สัมผัสผู้ป่วยวัณโรค เปรียบเทียบสูตรสั้น (3HP, 3HR, 4R) กับสูตรดั้งเดิม (6H/9H)]
  • [สูตรสั้นที่มี Rifampicin/Rifapentine ช่วยลดอุบัติการณ์เกิดวัณโรคระยะลุกลามและมี Completion rate สูงกว่าอย่างมีนัยสำคัญ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** คลินิกวัณโรค รพ.เสิงสาง ควรใช้สูตรยาสั้น (3HP หรือ 3HR/4R) ในการทำ TB Preventive Treatment (TPT) ในเด็กและผู้สัมผัสใกล้ชิดเพื่อลดพิษต่อตับ
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** เกณฑ์ Short-Course RDU ใช้เฉพาะผู้ป่วย Non-severe ที่ภูมิคุ้มกันปกติ • ประเมินอาการไข้ลดลงครบ 48 ชม. ก่อนหยุดยา
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ประหยัดงบค่ายาโดยตรง 40–50% ต่อคอร์ส ลดโอกาสเกิดเชื้อดื้อยาที่ต้องใช้ยาฉีดราคาแพง (Carbapenems/Vancomycin)
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42816130/)

---

### 7. 👴 การทบทวนและหยุดยาที่ไม่เหมาะสมในผู้สูงอายุ (Deprescribing & Polypharmacy)

#### 1. Barriers and enablers to deprescribing from the perspectives of older adults with polypharmacy and their stakeholders: A systematic review of qualitative studies.
- **วารสาร & PMID:** International journal of nursing studies • [PMID: 42815285](https://pubmed.ncbi.nlm.nih.gov/42815285/)
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** ความสำเร็จของการตัดยาล้นเกิน (Deprescribing) ในผู้สูงอายุขึ้นอยู่กับความไว้วางใจในทีมสุขภาพและการสื่อสารแบบตัดสินใจร่วมกัน (Shared Decision-Making) เพื่อลดความกลัวโรคกำเริบ
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Systematic Review วิเคราะห์ปัจจัยส่งเสริมและอุปสรรคของการหยุดยาในผู้สูงอายุที่ใช้ยาตั้งแต่ 5 รายการขึ้นไป (Polypharmacy)]
  • [การวางแผนลดยาเป็นลำดับขั้น (Stepwise Tapering) ร่วมกับการให้ข้อมูลที่ชัดเจนช่วยเพิ่มการยอมรับของผู้ป่วยและญาติ]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** เภสัชกรประจำคลินิกผู้สูงอายุและ NCDs รพ.เสิงสาง ควรใช้แนวทางค่อยๆ ปรับลดขนาดยาควบคู่กับการสร้างความมั่นใจแก่ผู้ป่วยและผู้ดูแล
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** การหยุดยาในผู้สูงอายุ (Deprescribing) โดยเฉพาะกลุ่ม BZD, Beta-blocker และ PPI ต้องทำ Tapering ค่อยๆ ลดขนาดยาเพื่อป้องกันอาการถอนยา
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ลดมูลค่าค่ายาส่วนเกิน (Polypharmacy Waste) ในคลินิกผู้สูงอายุและป้องกันค่าใช้จ่ายจากการรักษาอาการไม่พึงประสงค์จากการใช้ยา (ADE)
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42815285/)

#### 2. Cancer co-medication quality in older patients with polypharmacy: A large randomized trial testing a medication review versus usual care.
- **วารสาร & PMID:** Journal of internal medicine • [PMID: 42773858](https://pubmed.ncbi.nlm.nih.gov/42773858/) • 👥 `N=234` • 📖 [อ่านฟรี PMC Full-Text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13741811/)
- **สถานะบัญชียา รพ.เสิงสาง:** `📋 แนวทางบริบาลเภสัชกรรมคลินิก`
- 🎯 **ใจความสำคัญ 1 บรรทัด:** การทบทวนรายการยาโดยใช้เครื่องมือ FORTA (Fit fOR The Aged) ช่วยลดการใช้ยาที่ไม่เหมาะสม (PIMs) และการใช้ยาเกินความจำเป็นในผู้สูงอายุได้อย่างมีนัยสำคัญ
- 📊 **ตัวเลขผลลัพธ์สำคัญ:**
  • [Multicentre RCT (N=443 ราย; กลุ่มทดลอง N=234 vs กลุ่มควบคุม N=209) ประเมินการทบทวนยาตามเกณฑ์ FORTA เทียบกับการดูแลปกติ]
  • [ลดสัดส่วนผู้ป่วยที่ได้รับยาไม่เหมาะสม (PIMs) ลงถึง 41.3% และลดการใช้ยาเกินจำเป็น (Overuse) ลง 30.7% (p < 0.001)]
- 💡 **สิ่งที่ต้องรู้ใน รพ.เสิงสาง:** นำเกณฑ์ FORTA / Beers Criteria มาประยุกต์ใช้ในระบบ Medication Reconciliation หอผู้ป่วยในและคลินิกผู้สูงอายุ รพ.เสิงสาง
- ⚠️ **คำเตือนเภสัชกร (Rx-Sentinel HQ):** การหยุดยาในผู้สูงอายุ (Deprescribing) โดยเฉพาะกลุ่ม BZD, Beta-blocker และ PPI ต้องทำ Tapering ค่อยๆ ลดขนาดยาเพื่อป้องกันอาการถอนยา
- 💰 **มุมมองความคุ้มค่า & งบประมาณ (BI-HQ):** ลดมูลค่าค่ายาส่วนเกิน (Polypharmacy Waste) ในคลินิกผู้สูงอายุและป้องกันค่าใช้จ่ายจากการรักษาอาการไม่พึงประสงค์จากการใช้ยา (ADE)
- 🔗 **ลิงก์ศึกษาต่อ:** [คลิกเปิดอ่านบทคัดย่อตัวเต็มบน PubMed →](https://pubmed.ncbi.nlm.nih.gov/42773858/)

---

**จัดทำโดย:** ภก.รัฐนนท์ แสงไทยทวีพร, เภสัชกรชำนาญการ  
*ประธานทีม Information Management (IM) โรงพยาบาลเสิงสาง*

<!-- SENTINEL_REPORT_END -->
