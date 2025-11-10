# 📚 LibLogin - Library WiFi Login Management System

ระบบจัดการหน้า Login WiFi สำหรับห้องสมุด พร้อมระบบเปลี่ยนพื้นหลังได้แบบ Real-time

[![Django](https://img.shields.io/badge/Django-5.2.8-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/DRF-3.16.1-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 จุดเด่นของระบบ

- ✅ **ใช้งานง่าย** - บรรณารักษ์สามารถเปลี่ยนพื้นหลังได้เองผ่านหน้าเว็บ ไม่ต้องแก้ code
- ✅ **Real-time Update** - เปลี่ยนพื้นหลังแล้วเห็นผลทันที ไม่ต้องรีสตาร์ท MikroTik
- ✅ **รองรับหลาย Router** - สามารถตั้งค่ารูปพื้นหลังต่างกันสำหรับแต่ละ Router
- ✅ **Auto Image Optimization** - ระบบปรับขนาดรูปอัตโนมัติเพื่อประสิทธิภาพสูงสุด
- ✅ **Responsive Design** - รองรับการแสดงผลบนทุกอุปกรณ์ (Desktop, Tablet, Mobile)
- ✅ **Secure** - มีระบบ Authentication สำหรับผู้ดูแลระบบ

---

## 📋 สารบัญ

- [ภาพรวมของระบบ](#ภาพรวมของระบบ)
- [สถาปัตยกรรมระบบ](#สถาปตยกรรมระบบ)
- [ความต้องการของระบบ](#ความตองการของระบบ)
- [การติดตั้ง](#การตดตง)
- [การใช้งาน](#การใชงาน)
- [API Documentation](#api-documentation)
- [การ Deploy Production](#การ-deploy-production)
- [Troubleshooting](#troubleshooting)
- [เอกสารเพิ่มเติม](#เอกสารเพมเตม)

---

## 📖 ภาพรวมของระบบ

LibLogin เป็นระบบจัดการหน้า Login สำหรับ MikroTik Hotspot ที่ออกแบบมาเพื่อให้บรรณารักษ์หรือผู้ดูแลระบบสามารถ:

1. **อัปโหลดรูปพื้นหลัง** สำหรับหน้า Login WiFi
2. **เปลี่ยนรูปพื้นหลัง** ได้ทันทีผ่านหน้าเว็บ
3. **จัดการรูปหลายรูป** และสลับใช้งานได้ตามต้องการ
4. **ตั้งค่าเฉพาะ Router** สำหรับ Router หลายตัว (Multi-Router Support)

### การทำงานของระบบ

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Librarian     │      │  Django Backend  │      │   MikroTik      │
│  (Web Admin)    │─────▶│  + REST API      │◀─────│  Hotspot Page   │
│                 │      │                  │      │                 │
│ - Upload images │      │ - Store images   │      │ - Fetch BG      │
│ - Set active    │      │ - Serve API      │      │ - Show to users │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Media Storage  │
                         │  (Background    │
                         │   Images)       │
                         └─────────────────┘
```

---

## 🏗️ สถาปัตยกรรมระบบ

### Backend (Django + DRF)
- **Framework**: Django 5.2.8
- **API**: Django REST Framework 3.16.1
- **Database**: SQLite3 (สามารถเปลี่ยนเป็น MySQL/PostgreSQL ได้)
- **Image Processing**: Pillow
- **CORS**: django-cors-headers

### Frontend (Web Admin)
- **UI Framework**: Bootstrap 5
- **Template Engine**: Django Templates
- **JavaScript**: Vanilla JS (ไม่ต้องใช้ Framework)

### MikroTik Integration
- **Login Page**: HTML + CSS + JavaScript
- **API Communication**: Fetch API
- **Image Loading**: Dynamic background loading

---

## 💻 ความต้องการของระบบ

### Development Environment
- **OS**: Windows, Linux, macOS
- **Python**: 3.8 ขึ้นไป
- **pip**: Latest version
- **Git**: For version control

### Production Server
- **OS**: Ubuntu 20.04 LTS หรือใหม่กว่า
- **RAM**: 2GB ขึ้นไป
- **Storage**: 10GB ขึ้นไป
- **Python**: 3.8+
- **Web Server**: Nginx (แนะนำ)

### MikroTik Router
- **RouterOS**: 6.x หรือ 7.x
- **Hotspot**: ต้องเปิดใช้งาน Hotspot feature
- **Storage**: มีพื้นที่เพียงพอสำหรับเก็บ HTML file

---

## 🚀 การติดตั้ง

### 1. Clone Repository

```bash
git clone https://github.com/azimuthotg/LibLogin.git
cd LibLogin
```

### 2. สร้าง Virtual Environment

```bash
python3 -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. สร้าง Superuser

```bash
python manage.py createsuperuser
```

กรอกข้อมูล:
- Username: `admin` (หรือชื่ือที่ต้องการ)
- Email: `admin@library.local`
- Password: `********` (ตั้งรหัสผ่านที่ปลอดภัย)

### 6. รัน Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

เปิดเบราว์เซอร์ไปที่: `http://localhost:8000/login/`

---

## 📱 การใช้งาน

### สำหรับบรรณารักษ์ (Web Admin)

1. **เข้าสู่ระบบ**
   ```
   URL: http://your-server-ip/login/
   Username: admin
   Password: (รหัสผ่านที่ตั้งไว้)
   ```

2. **อัปโหลดรูปพื้นหลัง**
   - คลิก "Background Images" ในเมนูด้านซ้าย
   - คลิก "+ Upload New Background"
   - เลือกรูปจากคอมพิวเตอร์
   - ตั้งชื่อและกำหนด Router ID (ถ้าต้องการ)
   - เลือก "Set as Active" หากต้องการใช้งานทันที
   - คลิก "Upload"

3. **เปลี่ยนรูปพื้นหลัง**
   - ไปที่หน้า "Background Images"
   - คลิก "Activate" ในรูปที่ต้องการใช้งาน
   - รูปจะเปลี่ยนทันทีบนหน้า Login WiFi

### สำหรับผู้ดูแลระบบ (Admin Panel)

เข้าใช้งาน Django Admin Panel:
```
URL: http://your-server-ip/admin/
```

จัดการข้อมูลเพิ่มเติม:
- Users & Permissions
- Background Images
- System Settings

---

## 🔌 API Documentation

### Public Endpoint (ไม่ต้อง Authentication)

#### GET /api/login-background/
ดึงข้อมูลรูปพื้นหลังที่กำลังใช้งาน

**Parameters:**
- `router_id` (optional): รหัส Router สำหรับดึงรูปเฉพาะ Router

**Request:**
```bash
# ดึงรูป default
curl http://your-server-ip/api/login-background/

# ดึงรูปสำหรับ Router เฉพาะ
curl http://your-server-ip/api/login-background/?router_id=FLOOR1
```

**Response (Success):**
```json
{
  "success": true,
  "imageUrl": "http://your-server-ip/media/backgrounds/image.jpg",
  "title": "สงกรานต์ 2568"
}
```

**Response (No Active Background):**
```json
{
  "success": false,
  "message": "No active background image found"
}
```

---

### Protected Endpoints (ต้อง Authentication)

#### GET /api/backgrounds/
ดึงรายการรูปพื้นหลังทั้งหมด

#### POST /api/backgrounds/
อัปโหลดรูปพื้นหลังใหม่

#### PUT /api/backgrounds/{id}/
แก้ไขข้อมูลรูปพื้นหลัง

#### DELETE /api/backgrounds/{id}/
ลบรูปพื้นหลัง

---

## 🌐 การ Deploy Production

### Quick Deploy with ngrok (For Testing)

```bash
# Terminal 1: Run Django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Run ngrok
ngrok http 8000
```

คุณจะได้ URL สำหรับทดสอบ:
```
https://xxxxx.ngrok-free.app
```

### Full Production Deployment

อ่านรายละเอียดใน: **[DEPLOYMENT.md](DEPLOYMENT.md)**

**สรุปขั้นตอน:**

1. **เตรียม Server** (Ubuntu 20.04+)
2. **ติดตั้ง Dependencies** (Python, Nginx, etc.)
3. **Clone & Setup** Project
4. **Configure Settings** (DEBUG=False, ALLOWED_HOSTS, etc.)
5. **Setup Gunicorn** สำหรับรัน Django
6. **Configure Nginx** เป็น Reverse Proxy
7. **Setup SSL** (HTTPS) ด้วย Let's Encrypt
8. **Configure Firewall**

---

## 🔧 MikroTik Configuration

### 1. แก้ไขไฟล์ mikrotik_login.html

เปิดไฟล์ `mikrotik_login.html` และแก้ไข:

```javascript
// Configuration
const API_BASE_URL = 'http://192.168.1.100:8000';  // เปลี่ยนเป็น IP ของ Backend Server
const ROUTER_ID = 'FLOOR1';  // ใส่ router_id (หรือเว้นว่างสำหรับ default)
```

### 2. อัปโหลดไปยัง MikroTik

**ผ่าน WinBox:**
1. เปิด WinBox และเชื่อมต่อกับ Router
2. ไปที่ Files
3. ลากไฟล์ `mikrotik_login.html` วางลงใน Files
4. เปลี่ยนชื่อเป็น `login.html` (หรือตามที่ตั้งค่าใน Hotspot)

**ผ่าน FTP:**
```bash
# Upload via FTP
ftp 192.168.1.1
Username: admin
Password: ********

put mikrotik_login.html login.html
quit
```

### 3. ตั้งค่า Hotspot Server Profile

```
/ip hotspot profile
set [find default=yes] html-directory=hotspot
```

---

## 🧪 Testing

### ทดสอบ API

```bash
# Test API endpoint
curl http://localhost:8000/api/login-background/

# Test with router_id
curl http://localhost:8000/api/login-background/?router_id=TEST
```

### ทดสอบหน้า Login (Local)

เปิดไฟล์ `test_login.html` ในเบราว์เซอร์:
```
file:///path/to/LibLogin/test_login.html
```

### ทดสอบผ่าน ngrok

เปิดไฟล์ `test_ngrok.html` ในเบราว์เซอร์:
```
file:///path/to/LibLogin/test_ngrok.html
```

---

## ❗ Troubleshooting

### ปัญหา: CSRF Verification Failed

**แก้ไข:** เพิ่ม URL ใน `backend/settings.py`
```python
CSRF_TRUSTED_ORIGINS = [
    'https://your-ngrok-url.ngrok-free.app',
    'http://your-server-ip',
]
```

### ปัญหา: CORS Error

**แก้ไข:** ตรวจสอบ `backend/settings.py`
```python
CORS_ALLOW_ALL_ORIGINS = True  # Development
# หรือ
CORS_ALLOWED_ORIGINS = [
    "http://mikrotik-ip",
    "http://192.168.1.1",
]
```

### ปัญหา: รูปพื้นหลังไม่โหลด

1. ตรวจสอบว่า `API_BASE_URL` ใน `mikrotik_login.html` ถูกต้อง
2. ตรวจสอบว่า MikroTik เข้าถึง Backend Server ได้
3. ตรวจสอบว่ามีรูปพื้นหลังที่ตั้งเป็น Active ในระบบ
4. ตรวจสอบ CORS settings

### ปัญหา: Media Files ไม่แสดง (Production)

```bash
# Collect static files
python manage.py collectstatic --noinput

# ตรวจสอบ permissions
sudo chown -R www-data:www-data /var/www/LibLogin/media
```

---

## 📚 เอกสารเพิ่มเติม

- **[USER_GUIDE.md](USER_GUIDE.md)** - คู่มือการใช้งานสำหรับบรรณารักษ์
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - คู่มือการ Deploy Production
- **[CLAUDE.md](CLAUDE.md)** - Project Instructions สำหรับ Claude Code

---

## 📂 โครงสร้างไฟล์

```
LibLogin/
├── backend/                  # Django Project Settings
│   ├── settings.py          # Configuration
│   ├── urls.py              # URL Routing
│   └── wsgi.py              # WSGI config
│
├── api/                      # REST API App
│   ├── models.py            # Database Models
│   ├── serializers.py       # DRF Serializers
│   ├── views.py             # API Views
│   ├── urls.py              # API URLs
│   └── admin.py             # Admin Configuration
│
├── webapp/                   # Web Admin Interface
│   ├── views.py             # Web Views
│   ├── urls.py              # Web URLs
│   └── templates/           # HTML Templates
│       └── webapp/
│           ├── base.html
│           ├── login.html
│           ├── dashboard.html
│           ├── backgrounds.html
│           └── settings.html
│
├── media/                    # Uploaded Images (auto-created)
│   ├── backgrounds/         # Background images
│   └── logos/               # System logos
│
├── venv/                     # Virtual Environment
│
├── mikrotik_login.html      # Production MikroTik Login Page
├── test_login.html          # Local Testing Page
├── test_ngrok.html          # ngrok Testing Page
│
├── requirements.txt         # Python Dependencies
├── .gitignore              # Git Ignore Rules
├── README.md               # This file
├── USER_GUIDE.md           # User Guide (Thai)
├── DEPLOYMENT.md           # Deployment Guide (Thai)
└── CLAUDE.md               # Project Instructions
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | Django 5.2.8 |
| API Framework | Django REST Framework 3.16.1 |
| Database | SQLite3 (Development) / MySQL (Production) |
| Image Processing | Pillow 12.0.0 |
| CORS Handling | django-cors-headers 4.9.0 |
| Frontend Framework | Bootstrap 5 |
| Template Engine | Django Templates |
| JavaScript | Vanilla ES6+ |
| Web Server | Gunicorn + Nginx |
| Version Control | Git |

---

## 🔐 Security Considerations

### Development
- ✅ DEBUG = True (OK สำหรับ Development)
- ✅ ALLOWED_HOSTS = ['*']
- ✅ CORS_ALLOW_ALL_ORIGINS = True

### Production
- ⚠️ DEBUG = False (จำเป็น!)
- ⚠️ SECRET_KEY = 'ต้องเปลี่ยนใหม่'
- ⚠️ ALLOWED_HOSTS = ['specific-domain.com']
- ⚠️ CORS_ALLOWED_ORIGINS = ['specific-origins']
- ⚠️ ใช้ HTTPS (SSL Certificate)
- ⚠️ ตั้งค่า Firewall
- ⚠️ เปลี่ยนรหัสผ่าน admin

---

## 📈 Performance Optimization

### Image Optimization
- ระบบปรับขนาดรูปอัตโนมัติเป็น 1920x1080 (max)
- Compression quality: 85%
- รองรับ: JPG, PNG, JPEG

### Caching (Optional)
```python
# เพิ่มใน settings.py สำหรับ Production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Database
- ใช้ PostgreSQL หรือ MySQL สำหรับ Production
- SQLite เหมาะสำหรับ Development และ traffic ต่ำ

---

## 🤝 Contributing

หากต้องการมีส่วนร่วมในการพัฒนา:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Authors

- **Development Team** - [azimuthotg](https://github.com/azimuthotg)

---

## 🙏 Acknowledgments

- Django Project
- Django REST Framework
- Bootstrap Team
- MikroTik Community

---

## 📞 Support

หากมีปัญหาหรือคำถาม:

1. ตรวจสอบ [Troubleshooting](#troubleshooting) section
2. อ่าน [USER_GUIDE.md](USER_GUIDE.md)
3. เปิด Issue ใน GitHub Repository
4. ติดต่อผู้ดูแลระบบ

---

## 🔄 Version History

### v1.0.0 (2025-11-10)
- ✅ Initial Release
- ✅ Basic Background Management
- ✅ Multi-Router Support
- ✅ Auto Image Optimization
- ✅ REST API
- ✅ Web Admin Interface
- ✅ MikroTik Integration
- ✅ ngrok Testing Support

---

**Happy Coding! 🚀**

Made with ❤️ for Libraries
