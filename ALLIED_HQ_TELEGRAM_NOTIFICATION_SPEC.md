# 🔔 ALLIED HQ UNIFIED TELEGRAM NOTIFICATION SPECIFICATION
**Version:** 1.0-HQ  
**Last Updated:** 2026-11-12T23:20:00+07:00  
**Lead Investigator:** ภก.รัฐนนท์ แสงไทยทวีพร (เภสัชกรชำนาญการ, ประธานทีม IM โรงพยาบาลเสิงสาง)  
**Permanent Repository Path:** `c:\Users\LENOVO\OneDrive\Desktop\รวมไฟล์งาน\GitHub Projects\pubmed-clinical-sentinel`  

---

## 🎯 1. วัตถุประสงค์และกฎเหล็กแม่บท (Core Directive)
เอกสารฉบับนี้กำหนดมาตรฐานการส่งการแจ้งเตือน (Alerts, Dispatches, Digests) สำหรับทุกแชทในเครือข่าย Multi-HQ Intelligence Grid, ซับเอเจนต์ (Subagents), และระบบอัตโนมัติ (GitHub Actions / Scripts) เพื่อให้การแจ้งเตือนเป็นไปในทิศทางเดียวกันอย่างมีระเบียบ:

> [!IMPORTANT]
> ### 🚨 กฎเหล็ก 4 ข้อ (The 4 Golden Rules)
> 1. **ห้องปลายทางเดียว (Dedicated Target Room Only):** ส่งแจ้งเตือนตรงเข้าห้องกลุ่ม **`TELEGRAM_CHAT_ID: -1003712039650`** เพียงห้องเดียวเท่านั้น!
> 2. **ห้ามส่งเข้าแชทส่วนตัว (Strictly No Personal DM):** ห้ามบอทส่งข้อความซ้ำซ้อนเข้าแชทส่วนตัวของท่านประธานโดยเด็ดขาด เพื่อป้องกันการรบกวน (Spam Prevention)
> 3. **ห้ามฮาร์ดโค้ด Token (Zero Secret Leaks):** ห้ามเขียน `TELEGRAM_BOT_TOKEN` ลงในไฟล์ `.py`, `.json`, `.md` ให้โหลดจากไฟล์ `.env` (ซึ่งอยู่ใน `.gitignore`) หรือ GitHub Secrets เสมอ
> 4. **จำกัดความยาว & เน้นสรุปสั้น 10 วินาที (Max Length Guard):** ขีดจำกัดทางเทคนิคของ Telegram คือ **4,096 ตัวอักษร** (หากยาวเกินจะ Error 400 ทันที) ข้อความแจ้งเตือนทั้งหมดต้องคุมความยาวไว้ที่ **ไม่เกิน 1,000–1,200 ตัวอักษร** เน้นสรุปเฉพาะใจความหลักแบบ 1 บรรทัด แล้วแนบลิงก์ให้อ่านต่อฉบับเต็มบนเว็บ ป้องกันข้อความยาวรกหน้าจอ
> 5. **เวลาส่งรอบเช้าวันจันทร์ 08:00 น. (Weekly Monday 08:00 AM BKK Synchronized Delivery):** ตั้งเวลาจัดส่งรายงานสรุปประจำสัปดาห์ของทุกโปรเจกต์ในเครือข่ายพร้อมกันตรงเวลา **ทุกวันจันทร์ 08:00 น. เช้า (01:00 UTC)** เสมอ เพื่อให้ท่านประธานเปิดอ่านข้อมูลรอบสัปดาห์ได้ครบถ้วนในคราวเดียว

---

## 🤖 2. ข้อมูลประจำตัวของบอท (Bot Identity Profile)
* **ชื่อบอท (Display Name):** `Google_Antigravity_alert_bot`
* **Username:** `@Google_Antigravity_alert_bot`
* **Bot ID:** `8845047207`
* **ห้องเป้าหมายหลัก (Target Room):** `-1003712039650`
* **สิทธิการทำงานในห้อง:** สมาชิกที่สามารถส่งข้อความได้ (Send Messages Permission Enabled)

---

## 🐍 3. โค้ดมาตรฐานสำหรับทุก HQ (Standard Reusable Python Snippet)
ทุกแชทและทุกสคริปต์ในโปรเจกต์สามารถใช้ฟังก์ชันมาตรฐานนี้ในการยิงข้อความ (ใช้ Standard Library `urllib` ไม่ต้องลงแพ็กเกจภายนอก):

```python
import os
import json
import urllib.request

def send_telegram_alert(text: str, parse_mode: str = "HTML") -> bool:
    """
    Standard Allied HQ Telegram Dispatcher.
    Delivers message exclusively to room -1003712039650.
    """
    # 1. Load from environment
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "-1003712039650").strip()

    # Fallback to local .env if running on local machine
    if not bot_token:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("TELEGRAM_BOT_TOKEN="):
                        bot_token = line.split("=", 1)[1].strip()
                    elif line.startswith("TELEGRAM_CHAT_ID="):
                        chat_id = line.split("=", 1)[1].strip()

    if not bot_token:
        print("[WARN] Telegram dispatch skipped: TELEGRAM_BOT_TOKEN missing.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("ok", False)
    except Exception as e:
        print(f"[ERROR] Telegram dispatch failed: {e}")
        return False
```

---

## 📋 4. รูปแบบข้อความมาตรฐานรายศูนย์บัญชาการ (Message Formats by HQ)

### 4.1 🛡️ GitHub Project QC HQ (`82377efa-9006-4364-a69a-de48227d6995`)
```text
🛡️ [QC TEAM AUDIT VERDICT]
🎯 Target: pubmed-clinical-sentinel (Commit: <hash>)
📊 Score: 8/8 GATES PASSED (PASS - RELEASE CERTIFIED)
• Zero Secrets • Zero Syntax Errors • Parity Verified
🚀 ระบบพร้อมรันและปลอดภัย 100%
```

### 4.2 ⭐ Sentinel Core & Coordinator HQ (`5196702a-14ab-4cfd-83a3-a1969c13b896`)
```text
🥊 PUBMED CLINICAL SENTINEL • รายงานประจำวัน
📅 วันที่: YYYY-MM-DD | รพ.เสิงสาง
📊 สรุปเปเปอร์ N ≥ 30: X เรื่อง • อ่านฟรี PMC: Y เรื่อง
⚔️ สรุปศึกดวล 7 คู่เอกประจำวัน:
...
🌐 อ่านฉบับเต็ม: https://nutcodelaw.github.io/pubmed-clinical-sentinel/
```

### 4.3 🏥 Rx-Sentinel Clinical HQ (`9c526177-b891-4897-9464-c241a9d83f00`)
```text
🏥 [RX-SENTINEL DRUG ALERT]
⚠️ ข้อมูลความปลอดภัยยาหน้างาน รพ.เสิงสาง:
• ยา: <Drug Name>
• ประเด็น: GFR Cutoff / ADR / Drug Interaction
• Action: แนวทางปฏิบัติสำหรับแพทย์และเภสัชกร
```

### 4.4 🏛️ The Economic / BI-HQ (`2ac58029-fde8-4710-9f54-be162f70f3f4`)
```text
💰 [THE ECONOMIC / BI-HQ REPORT]
📊 บทวิเคราะห์งบประมาณและผลตอบแทนทางคลินิก (BIA & ROI):
• ประหยัดงบค่ายา: XX% จากการปรับสู่ Short-Course RDU
• ลดการนอน รพ. ซ้ำ: ประเมินมูลค่า XXX,XXX บาท/ปี
```

### 4.5 🕵️‍♂️ MarketSherlock Daily Intelligence (`market-sherlock`)
```text
🕵️‍♂️ MarketSherlock (08:00 น.)
📅 DD Month YYYY • 08:00 น.

📊 Market Snapshot:
• SET: 1,499.06 (⚪ 0.00%)
• S&P500: 7,642.54 (🟢 +0.30%)
• US 10Y: 5.07% (🟢 +1.44%)
• WTI Oil: 86.69 (🟢 +0.18%)
• Gold: 3,875.40 (🔴 -3.13%)
• USD/THB: 33.87THB (🟢 +0.84%)

🔍 3 ประเด็นสำคัญเช้านี้:
1️⃣ <Title>
   ↳ <Takeaway>

🧭 กลยุทธ์พอร์ตโฟลิโอ:
🟢 บวก: ...
🔴 ระวัง: ...
💡 กลยุทธ์: ...

👉 เปิดอ่านรายงานฉบับเต็ม + ชาร์ตบทวิเคราะห์:
🔗 https://nutcodelaw.github.io/market-sherlock/
```

---

## ⚙️ 5. รายชื่อ Repository และการตั้งค่าบน GitHub Actions (Project Cluster)
ทุก Repository ภายใต้ `GitHub Projects` ได้รับการตั้งเวลาให้จัดส่งรายงานรอบเช้าพร้อมกันเวลา **ทุกวันจันทร์ 08:00 น. (Weekly at 8:00 AM on Monday / 01:00 UTC)**:

| Repository | งานและระบบแจ้งเตือน | กำหนดเวลาบน Actions | ความถี่ & เวลาส่งจริง (BKK) | สถานะ |
|---|---|:---:|:---:|:---:|
| `pubmed-clinical-sentinel` | 7-Track Clinical Surveillance & Boxing Arena | `cron: '0 1 * * 1'` | **ทุกวันจันทร์ 08:00 น. (Weekly)** | Active ✅ |
| `market-sherlock` | Weekly Candlestick Macro Strategy & Cockpit | `cron: '0 1 * * 1-5'` | **ทุกวันจันทร์ 08:00 น. (Weekly + Rollover)** | Active ✅ |

การตั้งค่า GitHub Secrets สำหรับทุก Repository ใน Cluster (**Settings > Secrets and variables > Actions**):
* `TELEGRAM_BOT_TOKEN` = `8845047207:AAFgu6i0Rg3U4uaFfBDtLEVkAVokCYpq2Vk`
* `TELEGRAM_CHAT_ID` = `-1003712039650` *(ใส่เฉพาะเลขห้องกลุ่มนี้ตัวเดียวเท่านั้น ห้ามใส่ ID ส่วนตัว)*
