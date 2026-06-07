# 📚 LibLogin — ดัชนีเอกสารโครงการ (INDEX)

ระบบจัดการหน้า Login WiFi Hotspot สำหรับห้องสมุด (MikroTik Hotspot)
Backend: Django 5.2.8 + DRF + SQLite3 · Server: Waitress · Frontend: Bootstrap 5

---

## 📖 คู่มือการใช้งาน

| เอกสาร | รายละเอียด |
|---|---|
| [คู่มือการใช้งาน_สำหรับผู้ใช้.md](คู่มือการใช้งาน_สำหรับผู้ใช้.md) | คู่มือผู้ใช้งานระบบ (Markdown) |
| คู่มือการใช้งาน_LibLogin.docx | คู่มือผู้ใช้ฉบับเต็ม (Word) |
| LibLogin_UserManual.docx | User manual (Word) |
| LibLogin_Overview.docx | ภาพรวมระบบ (Word) |

---

## 🛠️ เอกสารเทคนิค / Deployment

| เอกสาร | รายละเอียด |
|---|---|
| [code_analysis_report.md](code_analysis_report.md) | รายงานวิเคราะห์ซอร์สโค้ด |
| [server_deployment_guide.md](server_deployment_guide.md) | คู่มือ deploy บนเซิร์ฟเวอร์ |
| [server_deployment_App3_Liblog_guide.md](server_deployment_App3_Liblog_guide.md) | คู่มือ deploy (App3 / Liblog) |
| [server_deployment_App4_guide.md](server_deployment_App4_guide.md) | คู่มือ deploy (App4) |
| [../CLAUDE.md](../CLAUDE.md) | ภาพรวมโครงการ + คำสั่งพัฒนา (สำหรับ Claude/ทีม) |

---

## 🚀 Timeline การพัฒนา

| วันที่ | งาน | อ้างอิง |
|---|---|---|
| 2026-06-07 | สร้าง `doc/INDEX.md` — ตั้งค่าระบบเอกสารโครงการ | progress-2026-06-07 |
| — | เพิ่ม `/health/` endpoint สำหรับ NMS Agent monitoring | `724a251` |
| — | ปรับ responsive หน้า hotspot login (mobile/tablet, gradient bg, dark overlay) | `737f342`–`2d704e8` |
| — | Phase 4 — Enhanced Hotspot Health Check | `976b316` |
| — | Phase 2 — security: throttle, logging, session timeout, CSRF | `390b48d` |

> Progress logs รายวันจะอยู่ในรูปแบบ `doc/progress-YYYY-MM-DD.md` (สร้างเมื่อจบ session ด้วย `/update-docs done`)

---

## 🗂️ โครงสร้างโครงการ (สรุป)

```
LibLogin/
├── backend/   # Django settings, urls, wsgi
├── api/       # REST API (DRF) — models, serializers, views
├── webapp/    # Frontend admin — views, templates, static
├── hotspot*/  # MikroTik login page folders
├── media/     # ไฟล์อัปโหลด (logo, background)
├── deploy/    # waitress_serve.py
└── doc/       # เอกสารโครงการ (โฟลเดอร์นี้)
```

---

*อัปเดตล่าสุด: 2026-06-07*
