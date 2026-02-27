# LibLogin Backend API

ระบบ Backend API สำหรับจัดการภาพพื้นหลัง Login ของ MikroTik Hotspot พัฒนาด้วย Django และ Django REST Framework

## ข้อมูลการติดตั้ง

### Requirements
- Python 3.12+
- Virtual Environment (venv)
- SQLite (หรือ MySQL สำหรับ production)

### การติดตั้งครั้งแรก

1. **เปิดใช้งาน Virtual Environment**
```bash
source venv/bin/activate  # Linux/Mac
# หรือ
venv\Scripts\activate  # Windows
```

2. **ติดตั้ง Dependencies** (ถ้ายังไม่ได้ติดตั้ง)
```bash
pip install -r requirements.txt
```

3. **รัน Migrations** (ถ้ายังไม่ได้รัน)
```bash
python manage.py migrate
```

4. **สร้าง Superuser** (ถ้ายังไม่ได้สร้าง)
```bash
python manage.py createsuperuser
```

## การรันเซิร์ฟเวอร์

### Development Mode
```bash
python manage.py runserver
```

เซิร์ฟเวอร์จะทำงานที่: `http://127.0.0.1:8000`

### เข้าใช้งาน Admin Panel
URL: `http://127.0.0.1:8000/admin/`
- Username: `admin`
- Password: `admin123`

## API Endpoints

### Public Endpoints (ไม่ต้อง Login)

#### 1. ดึงภาพพื้นหลังปัจจุบัน
```
GET /api/login-background/
GET /api/login-background/?router_id=123
```

**Response:**
```json
{
  "success": true,
  "imageUrl": "http://127.0.0.1:8000/media/backgrounds/image.jpg",
  "title": "Library Background"
}
```

### Protected Endpoints (ต้อง Login)

#### 2. จัดการภาพพื้นหลัง
```
GET    /api/backgrounds/          # ดูรายการภาพทั้งหมด
POST   /api/backgrounds/          # อัปโหลดภาพใหม่
GET    /api/backgrounds/{id}/     # ดูรายละเอียดภาพ
PUT    /api/backgrounds/{id}/     # แก้ไขข้อมูลภาพ
DELETE /api/backgrounds/{id}/     # ลบภาพ
POST   /api/backgrounds/{id}/set_active/  # ตั้งเป็นภาพพื้นหลังปัจจุบัน
GET    /api/backgrounds/by_router/?router_id=123  # กรองตาม router_id
```

#### 3. จัดการการตั้งค่าระบบ (Admin เท่านั้น)
```
GET    /api/settings/             # ดูการตั้งค่า
POST   /api/settings/             # สร้างการตั้งค่าใหม่
PUT    /api/settings/{id}/        # แก้ไขการตั้งค่า
```

#### 4. จัดการผู้ใช้ (Admin เท่านั้น)
```
GET    /api/users/                # ดูรายการผู้ใช้ทั้งหมด
GET    /api/users/{id}/           # ดูรายละเอียดผู้ใช้
```

## โครงสร้างโฟลเดอร์

```
LibLogin/
├── backend/                 # Django project settings
│   ├── settings.py         # การตั้งค่าโปรเจค
│   ├── urls.py            # URL routing หลัก
│   └── wsgi.py            # WSGI configuration
├── api/                    # API app
│   ├── models.py          # Database models
│   ├── serializers.py     # REST serializers
│   ├── views.py           # API views
│   ├── urls.py            # API URL routing
│   └── admin.py           # Admin configuration
├── media/                  # อัปโหลดไฟล์ (สร้างอัตโนมัติ)
│   ├── backgrounds/       # รูปภาพพื้นหลัง
│   └── logos/             # โลโก้
├── venv/                   # Python virtual environment
├── db.sqlite3             # ฐานข้อมูล SQLite
├── manage.py              # Django management script
└── requirements.txt       # Python dependencies
```

## Models

### BackgroundImage
- `title`: ชื่อภาพ
- `image`: ไฟล์ภาพ
- `router_id`: ID ของ Router (สำหรับแยกตามอุปกรณ์)
- `is_active`: ตั้งเป็นภาพพื้นหลังปัจจุบัน
- `uploaded_by`: ผู้อัปโหลด
- `uploaded_at`: วันที่อัปโหลด
- `updated_at`: วันที่แก้ไขล่าสุด

### SystemSettings
- `library_name`: ชื่อห้องสมุด
- `contact_info`: ข้อมูลติดต่อ
- `logo`: โลโก้
- `default_router_id`: Router ID เริ่มต้น

## การใช้งานกับ MikroTik

### แก้ไข login.html ของ MikroTik

เพิ่ม JavaScript เพื่อดึงภาพพื้นหลัง:

```javascript
<script>
// Fetch background image from API
fetch('http://YOUR_SERVER_IP:8000/api/login-background/?router_id=123')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      document.getElementById('background').style.backgroundImage =
        `url(${data.imageUrl})`;
    }
  })
  .catch(error => console.error('Error:', error));
</script>
```

## Security Notes

### Development
- `DEBUG = True` (เปิดเฉพาะ development)
- `CORS_ALLOW_ALL_ORIGINS = True` (อนุญาตทุก origin)
- SQLite database

### Production (แนะนำ)
- ตั้งค่า `DEBUG = False`
- กำหนด `ALLOWED_HOSTS`
- ปรับ `CORS_ALLOWED_ORIGINS` ให้เฉพาะเจาะจง
- ใช้ MySQL/PostgreSQL
- ตั้งค่า `SECRET_KEY` ใหม่
- ใช้ HTTPS
- ตั้งค่า Gunicorn + Nginx

## Troubleshooting

### ปัญหา: ไม่สามารถดูรูปภาพได้
- ตรวจสอบว่าโฟลเดอร์ `media/` มีสิทธิ์เขียนไฟล์
- ตรวจสอบ `MEDIA_URL` และ `MEDIA_ROOT` ใน settings.py

### ปัญหา: CORS Error
- เพิ่ม IP ของ MikroTik ใน `CORS_ALLOWED_ORIGINS`
- ตรวจสอบว่าติดตั้ง `django-cors-headers` แล้ว

### ปัญหา: Permission Denied
- ตรวจสอบว่า user ที่ใช้งาน API มีสิทธิ์เหมาะสม
- ใช้ admin account สำหรับการทดสอบ

## Development Tips

### สร้าง Migration ใหม่
```bash
python manage.py makemigrations
python manage.py migrate
```

### ทดสอบ API ด้วย curl
```bash
# Get background image
curl http://127.0.0.1:8000/api/login-background/

# Get with router_id
curl http://127.0.0.1:8000/api/login-background/?router_id=123
```

### Export requirements
```bash
pip freeze > requirements.txt
```

## Contact

สำหรับข้อสงสัยหรือปัญหาในการใช้งาน กรุณาติดต่อผู้ดูแลระบบ
