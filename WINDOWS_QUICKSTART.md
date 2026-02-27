# 🚀 LibLogin - Windows Server Quick Start Guide

คู่มือเริ่มต้นอย่างรวดเร็วสำหรับติดตั้งบน Windows Server

---

## 📋 ขั้นตอนย่อ (Quick Steps)

### 1. ติดตั้ง Prerequisites
- ✅ Python 3.8+ ([ดาวน์โหลด](https://www.python.org/downloads/))
- ✅ Git for Windows ([ดาวน์โหลด](https://git-scm.com/download/win))
- ✅ NSSM ([ดาวน์โหลด](https://nssm.cc/download))

### 2. Clone และติดตั้ง

```powershell
# Clone repository
cd C:\inetpub
git clone https://github.com/azimuthotg/LibLogin.git
cd LibLogin

# สร้าง Virtual Environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Setup Database
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 3. แก้ไข Settings

แก้ไข `backend\settings.py`:

```python
# เปลี่ยนค่าเหล่านี้
DEBUG = False
SECRET_KEY = 'your-new-secret-key'  # สร้างใหม่!
ALLOWED_HOSTS = ['192.168.1.100', 'localhost']  # ใส่ IP จริง
CORS_ALLOWED_ORIGINS = ["http://192.168.1.1"]  # MikroTik IP
```

### 4. ทดสอบ

```powershell
# ทดสอบรัน
python run_server.py

# เปิดเบราว์เซอร์ทดสอบ
http://localhost:8000/login/
```

### 5. ติดตั้ง Windows Service

```powershell
# เปิด PowerShell แบบ Administrator
nssm install LibLogin

# ใน GUI ที่เปิดขึ้น:
# Path: C:\inetpub\LibLogin\venv\Scripts\python.exe
# Startup directory: C:\inetpub\LibLogin
# Arguments: run_server.py

# เริ่มต้น Service
nssm start LibLogin
```

### 6. ตั้งค่า Firewall

```powershell
# เปิด port 8000
New-NetFirewallRule -DisplayName "LibLogin" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### 7. อัปเดต MikroTik

แก้ไข `mikrotik_login.html`:
```javascript
const API_BASE_URL = 'http://192.168.1.100:8000';  // ใส่ IP จริง
```

อัปโหลดไปยัง MikroTik ผ่าน WinBox (Files → Upload → เปลี่ยนชื่อเป็น `login.html`)

---

## ✅ เสร็จสิ้น!

ทดสอบ:
- 🌐 Web Interface: `http://192.168.1.100:8000/login/`
- 🔌 API: `http://192.168.1.100:8000/api/login-background/`
- 📱 MikroTik: เชื่อมต่อ WiFi เพื่อดูหน้า Login

---

## 📖 เอกสารเพิ่มเติม

- **รายละเอียดทั้งหมด**: [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md)
- **คู่มือผู้ใช้**: [USER_GUIDE.md](USER_GUIDE.md)
- **README**: [README.md](README.md)

---

## 🆘 ช่วยเหลือด่วน

### ปัญหา: Service ไม่ start
```powershell
# ดู error log
type C:\inetpub\LibLogin\logs\error.log
```

### ปัญหา: เข้าไม่ได้จากเครื่องอื่น
```powershell
# ตรวจสอบ Firewall
Get-NetFirewallRule -DisplayName "LibLogin"
```

### ปัญหา: API ไม่ตอบกลับ
```powershell
# ตรวจสอบ Service
nssm status LibLogin
```

---

**🎉 พร้อมใช้งาน!**
