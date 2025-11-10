# LibLogin Deployment Guide for Windows Server

คู่มือการติดตั้งระบบ LibLogin บน Windows Server ด้วย Waitress + NSSM

---

## ข้อกำหนดของ Server

### System Requirements
- **OS**: Windows Server 2016 หรือใหม่กว่า (หรือ Windows 10/11)
- **Python**: 3.8 ขึ้นไป
- **RAM**: 2GB ขึ้นไป
- **Storage**: 10GB ขึ้นไป

### Software Required
- **Python 3.8+** - [ดาวน์โหลด](https://www.python.org/downloads/)
- **Git for Windows** - [ดาวน์โหลด](https://git-scm.com/download/win)
- **NSSM** - [ดาวน์โหลด](https://nssm.cc/download)
- **MySQL** (Optional) - [ดาวน์โหลด](https://dev.mysql.com/downloads/installer/)

---

## ขั้นตอนการติดตั้ง

### 1. เตรียม Server

#### 1.1 ติดตั้ง Python
```powershell
# ตรวจสอบ Python version
python --version
# ต้องได้ Python 3.8 ขึ้นไป

# ติดตั้ง pip (ถ้ายังไม่มี)
python -m pip install --upgrade pip
```

#### 1.2 ติดตั้ง Git
```powershell
# ตรวจสอบ Git
git --version
```

#### 1.3 ดาวน์โหลด NSSM
1. ดาวน์โหลดจาก https://nssm.cc/download
2. แตกไฟล์และคัดลอก `nssm.exe` ไปยัง `C:\Windows\System32\`
3. ทดสอบ:
```powershell
nssm --version
```

---

### 2. Clone Repository

```powershell
# เข้าไปยังโฟลเดอร์ที่ต้องการติดตั้ง
cd C:\inetpub\

# Clone repository
git clone https://github.com/azimuthotg/LibLogin.git
cd LibLogin
```

---

### 3. Setup Virtual Environment

```powershell
# สร้าง Virtual Environment
python -m venv venv

# เปิดใช้งาน venv
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# ติดตั้ง dependencies
pip install -r requirements.txt

# ติดตั้ง Waitress (WSGI Server สำหรับ Windows)
pip install waitress
```

---

### 4. Configure Settings

แก้ไขไฟล์ `backend\settings.py`:

```python
# ===================================
# Production Settings
# ===================================

# Security
DEBUG = False

# สร้าง SECRET_KEY ใหม่
# ใช้คำสั่งนี้ใน Python shell เพื่อสร้าง key ใหม่:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = 'your-new-secret-key-here'

# ใส่ IP ของ Server
ALLOWED_HOSTS = [
    '192.168.1.100',        # IP ของ Server
    'localhost',
    '127.0.0.1',
    'library.local',        # Domain name (ถ้ามี)
]

# CORS (Production) - ใส่ IP ของ MikroTik
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://192.168.1.1",      # MikroTik IP
    "http://192.168.1.100",    # Server IP (สำหรับทดสอบ)
]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'http://192.168.1.100',
    'http://192.168.1.100:8000',
]

# Database (ใช้ SQLite หรือเปลี่ยนเป็น MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ถ้าใช้ MySQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'liblogin_db',
#         'USER': 'liblogin_user',
#         'PASSWORD': 'your-password',
#         'HOST': 'localhost',
#         'PORT': '3306',
#     }
# }

# Static files (ต้องรัน collectstatic)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

### 5. Database Setup

```powershell
# ตรวจสอบว่า venv ยังเปิดอยู่
# ถ้าปิดไปแล้ว ใช้: .\venv\Scripts\activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: admin@library.local
# Password: ********

# Collect static files
python manage.py collectstatic --noinput
```

---

### 6. สร้างไฟล์ run_server.py

สร้างไฟล์ `run_server.py` ในโฟลเดอร์หลักของโปรเจกต์:

```python
# run_server.py
from waitress import serve
from backend.wsgi import application
import os

if __name__ == '__main__':
    # ตั้งค่า environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    # รัน Waitress
    print("Starting LibLogin on http://0.0.0.0:8000")
    print("Press Ctrl+C to quit")

    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=4,  # จำนวน threads
        url_scheme='http'
    )
```

บันทึกไฟล์

---

### 7. ทดสอบรันด้วย Waitress

```powershell
# เปิด venv
.\venv\Scripts\activate

# รันเซิร์ฟเวอร์
python run_server.py
```

ควรเห็น:
```
Starting LibLogin on http://0.0.0.0:8000
Press Ctrl+C to quit
```

**ทดสอบ:**
1. เปิดเบราว์เซอร์: `http://localhost:8000/login/`
2. เปิดจากเครื่องอื่น: `http://192.168.1.100:8000/login/` (เปลี่ยนเป็น IP จริง)

ถ้าทำงานได้ กด `Ctrl+C` เพื่อปิด แล้วไปขั้นตอนต่อไป

---

### 8. ติดตั้ง Windows Service ด้วย NSSM

#### 8.1 สร้าง Batch File

สร้างไฟล์ `start_liblogin.bat` ในโฟลเดอร์หลัก:

```batch
@echo off
cd /d C:\inetpub\LibLogin
call venv\Scripts\activate.bat
python run_server.py
```

บันทึกไฟล์

#### 8.2 ติดตั้ง Service ด้วย NSSM

เปิด **Command Prompt หรือ PowerShell แบบ Administrator**:

```powershell
# ติดตั้ง Service
nssm install LibLogin

# หน้าต่าง NSSM GUI จะเปิดขึ้น กรอกข้อมูลดังนี้:
```

**Application Tab:**
- **Path**: `C:\inetpub\LibLogin\venv\Scripts\python.exe`
- **Startup directory**: `C:\inetpub\LibLogin`
- **Arguments**: `run_server.py`

**Details Tab:**
- **Display name**: `LibLogin Service`
- **Description**: `Library WiFi Login Management System`
- **Startup type**: `Automatic`

**Log on Tab:**
- เลือก `Local System account` หรือ user account ที่มีสิทธิ์

**I/O Tab:**
- **Output (stdout)**: `C:\inetpub\LibLogin\logs\output.log`
- **Error (stderr)**: `C:\inetpub\LibLogin\logs\error.log`

**(สร้างโฟลเดอร์ logs ก่อน)**
```powershell
mkdir C:\inetpub\LibLogin\logs
```

คลิก **Install service**

---

### 9. จัดการ Service

#### เริ่ม Service
```powershell
# เริ่มต้น Service
nssm start LibLogin

# หรือใช้ Services.msc
services.msc
# หา "LibLogin Service" แล้วคลิกขวา -> Start
```

#### ตรวจสอบสถานะ
```powershell
# ดูสถานะ
nssm status LibLogin

# ดู logs
type C:\inetpub\LibLogin\logs\output.log
type C:\inetpub\LibLogin\logs\error.log
```

#### หยุด/รีสตาร์ท Service
```powershell
# หยุด
nssm stop LibLogin

# รีสตาร์ท
nssm restart LibLogin

# ลบ Service (ถ้าต้องการ)
nssm remove LibLogin confirm
```

---

### 10. ตั้งค่า Windows Firewall

เปิด PowerShell แบบ Administrator:

```powershell
# อนุญาต port 8000
New-NetFirewallRule -DisplayName "LibLogin HTTP" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# ตรวจสอบ
Get-NetFirewallRule -DisplayName "LibLogin HTTP"
```

หรือผ่าน GUI:
1. เปิด **Windows Defender Firewall with Advanced Security**
2. คลิก **Inbound Rules** -> **New Rule**
3. เลือก **Port** -> **TCP** -> **Specific local ports: 8000**
4. เลือก **Allow the connection**
5. เลือก **Domain, Private, Public** (ตามต้องการ)
6. ตั้งชื่อ: **LibLogin HTTP**

---

### 11. ตั้งค่า MikroTik

#### 11.1 แก้ไขไฟล์ mikrotik_login.html

เปิดไฟล์ `mikrotik_login.html` แก้ไข:

```javascript
// Configuration - แก้ไขส่วนนี้
const API_BASE_URL = 'http://192.168.1.100:8000';  // ใส่ IP จริงของ Server
const ROUTER_ID = '';  // ใส่ router_id ถ้าต้องการ (เช่น 'FLOOR1')
```

บันทึกไฟล์

#### 11.2 อัปโหลดไปยัง MikroTik

**ผ่าน WinBox:**
1. เปิด WinBox เชื่อมต่อกับ Router
2. ไปที่ **Files**
3. ลากไฟล์ `mikrotik_login.html` วางลงใน Files
4. เปลี่ยนชื่อเป็น `login.html`

**ผ่าน FTP:**
```powershell
# ใช้ FTP Client เช่น FileZilla
# หรือ Windows Explorer:
# ftp://192.168.1.1
# Username: admin
# Password: ********
```

อัปโหลด `mikrotik_login.html` และเปลี่ยนชื่อเป็น `login.html`

---

### 12. ทดสอบระบบ

#### 12.1 ทดสอบ API
```powershell
# ใช้ PowerShell
Invoke-WebRequest -Uri "http://192.168.1.100:8000/api/login-background/" | Select-Object -Expand Content

# หรือเปิดใน Browser
http://192.168.1.100:8000/api/login-background/
```

ควรได้ JSON:
```json
{
  "success": true,
  "imageUrl": "http://192.168.1.100:8000/media/backgrounds/image.jpg",
  "title": "test"
}
```

#### 12.2 ทดสอบ Web Interface
```
http://192.168.1.100:8000/login/
```

Login ด้วย admin/password ที่สร้างไว้

#### 12.3 ทดสอบ MikroTik Login Page

1. เชื่อมต่อ WiFi ของ MikroTik
2. เปิดเบราว์เซอร์ (จะถูกนำไปหน้า Login อัตโนมัติ)
3. ตรวจสอบว่ารูปพื้นหลังโหลดมาจาก API ได้หรือไม่

---

## การอัปเดตระบบ

### ขั้นตอนการอัปเดต Code

```powershell
# หยุด Service
nssm stop LibLogin

# ไปที่โฟลเดอร์โปรเจกต์
cd C:\inetpub\LibLogin

# Pull code ใหม่
git pull origin main

# เปิด venv
.\venv\Scripts\activate

# อัปเดต dependencies (ถ้ามี)
pip install -r requirements.txt

# Run migrations (ถ้ามี)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# เริ่ม Service ใหม่
nssm start LibLogin
```

---

## Backup & Restore

### Backup Database (SQLite)

```powershell
# สร้าง backup script: backup.bat
@echo off
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

cd C:\inetpub\LibLogin
copy db.sqlite3 "backups\db_%TIMESTAMP%.sqlite3"

echo Backup completed: db_%TIMESTAMP%.sqlite3
```

### Backup Media Files

```powershell
# Backup media folder
xcopy C:\inetpub\LibLogin\media C:\inetpub\LibLogin\backups\media\ /E /I /Y
```

### ตั้ง Scheduled Task สำหรับ Auto Backup

1. เปิด **Task Scheduler**
2. **Create Basic Task**
3. ตั้งชื่อ: **LibLogin Daily Backup**
4. Trigger: **Daily** เวลา 02:00 AM
5. Action: **Start a program**
6. Program: `C:\inetpub\LibLogin\backup.bat`

---

## Troubleshooting

### ปัญหา: Service ไม่ start

```powershell
# ดู error logs
type C:\inetpub\LibLogin\logs\error.log

# ตรวจสอบ Python path
nssm edit LibLogin
# ตรวจสอบ Path และ Arguments
```

### ปัญหา: ไม่สามารถเข้าถึงจากเครื่องอื่น

```powershell
# ตรวจสอบ Firewall
Get-NetFirewallRule -DisplayName "LibLogin HTTP"

# ทดสอบ port
netstat -ano | findstr :8000

# Ping Server
ping 192.168.1.100
```

### ปัญหา: Static files ไม่แสดง

```powershell
# ไปที่โฟลเดอร์โปรเจกต์
cd C:\inetpub\LibLogin
.\venv\Scripts\activate

# Collect static files ใหม่
python manage.py collectstatic --clear --noinput

# ตรวจสอบว่ามีโฟลเดอร์ staticfiles
dir staticfiles
```

### ปัญหา: Permission denied

```powershell
# ให้สิทธิ์ IIS_IUSRS (ถ้าใช้ IIS)
icacls C:\inetpub\LibLogin /grant IIS_IUSRS:(OI)(CI)F /T

# หรือให้สิทธิ์ทุกคน (ไม่แนะนำสำหรับ production)
icacls C:\inetpub\LibLogin /grant Everyone:(OI)(CI)F /T
```

---

## Performance Tuning

### Waitress Configuration

แก้ไขไฟล์ `run_server.py`:

```python
from waitress import serve
from backend.wsgi import application
import os

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    serve(
        application,
        host='0.0.0.0',
        port=8000,
        threads=8,              # เพิ่ม threads (แนะนำ: CPU cores x 2)
        channel_timeout=60,     # Timeout (วินาที)
        cleanup_interval=10,    # Cleanup interval
        url_scheme='http'
    )
```

---

## Security Checklist

### Production
- [ ] `DEBUG = False`
- [ ] สร้าง `SECRET_KEY` ใหม่
- [ ] ตั้ง `ALLOWED_HOSTS` เฉพาะเจาะจง
- [ ] ตั้ง `CORS_ALLOWED_ORIGINS` เฉพาะ MikroTik
- [ ] เปลี่ยนรหัสผ่าน admin
- [ ] ตั้งค่า Firewall
- [ ] ปิด RDP จากภายนอก (ถ้าไม่จำเป็น)
- [ ] Backup ฐานข้อมูลเป็นประจำ
- [ ] อัปเดต Windows Security patches

---

## Monitoring

### ดู Logs

```powershell
# Real-time logs (ใช้ PowerShell)
Get-Content C:\inetpub\LibLogin\logs\output.log -Wait

# หรือใช้ Notepad++
notepad++ C:\inetpub\LibLogin\logs\output.log
```

### ตรวจสอบ Service

```powershell
# ดูสถานะ
Get-Service | Where-Object {$_.DisplayName -like "*LibLogin*"}

# หรือ
nssm status LibLogin
```

---

## หลังจากติดตั้งเสร็จ

### Checklist
1. ✅ Service รันอัตโนมัติเมื่อ reboot
2. ✅ เข้า Web Interface ได้จากเครื่องอื่น
3. ✅ API ตอบกลับถูกต้อง
4. ✅ อัปโหลดรูปพื้นหลังได้
5. ✅ MikroTik Login Page แสดงรูปพื้นหลังได้
6. ✅ Firewall เปิด port 8000
7. ✅ Backup script ทำงาน

---

## Quick Reference

### URL สำคัญ

| Service | URL |
|---------|-----|
| Web Admin | `http://192.168.1.100:8000/login/` |
| Dashboard | `http://192.168.1.100:8000/` |
| Admin Panel | `http://192.168.1.100:8000/admin/` |
| API Endpoint | `http://192.168.1.100:8000/api/login-background/` |

### คำสั่งที่ใช้บ่อย

```powershell
# Start/Stop/Restart Service
nssm start LibLogin
nssm stop LibLogin
nssm restart LibLogin

# ดูสถานะ
nssm status LibLogin

# ดู logs
type C:\inetpub\LibLogin\logs\output.log

# อัปเดต code
cd C:\inetpub\LibLogin
git pull origin main
nssm restart LibLogin
```

---

## Contact & Support

หากมีปัญหา:
1. ตรวจสอบ logs: `C:\inetpub\LibLogin\logs\error.log`
2. ตรวจสอบ Firewall และ Network
3. ทดสอบ API ด้วย Browser
4. ตรวจสอบ Service status

---

**สำเร็จ!** ระบบพร้อมใช้งานบน Windows Server 🎉
