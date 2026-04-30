# รายงานวิเคราะห์ระบบ LibLogin — Code Analysis Report

**วันที่วิเคราะห์:** 30 เมษายน 2569
**เวอร์ชัน:** Django 5.2.8 / DRF / SQLite3 / Waitress
**ผู้วิเคราะห์:** Claude Sonnet 4.6 (AI Code Review)

---

## สารบัญ

1. [ภาพรวมระบบ](#1-ภาพรวมระบบ)
2. [โค้ดไม่สอดคล้อง (Inconsistencies)](#2-โค้ดไม่สอดคล้อง)
3. [ค่า Hardcoded](#3-ค่า-hardcoded)
4. [ปัญหาด้าน Security](#4-ปัญหาด้าน-security)
5. [ฟีเจอร์ที่ขาด (Enterprise Grade)](#5-ฟีเจอร์ที่ขาด)
6. [วิเคราะห์: การเชื่อมต่อ Server ↔ login.html (MikroTik)](#6-วิเคราะห์-การเชื่อมต่อ-server--loginhtml-mikrotik)
7. [สิ่งที่ดีแล้ว](#7-สิ่งที่ดีแล้ว)
8. [ลำดับความสำคัญในการแก้ไข](#8-ลำดับความสำคัญในการแก้ไข)

---

## 1. ภาพรวมระบบ

LibLogin เป็นระบบจัดการหน้า Login WiFi Hotspot สำหรับห้องสมุด ประกอบด้วย:

| Layer | เทคโนโลยี |
|---|---|
| Backend | Django 5.2.8 + Django REST Framework |
| Database | SQLite3 |
| Server | Waitress (port 8002 production) |
| Frontend | Bootstrap 5 + Vanilla JS |
| Deployment | Windows Server 2019 + IIS ARR (sub-path `/liblogin/`) |

### โครงสร้าง Models

```
BackgroundImage   → รูปพื้นหลังหน้า Login
TemplateConfig    → รูปแบบ Layout ของหน้า Login
SlideContent      → เนื้อหา Slideshow
CardContent       → เนื้อหา Card Gallery
Hotspot           → การตั้งค่า MikroTik Hotspot
SystemSettings    → ตั้งค่าระบบ (ชื่อห้องสมุด, โลโก้)
Department        → หน่วยงาน + Access Control
PageImpression    → บันทึกการเข้าชม (Analytics)
DailyReachStats   → สถิติรายวัน (Aggregated)
LandingPageURL    → URL ปลายทางหลัง Login สำเร็จ
```

---

## 2. โค้ดไม่สอดคล้อง

### 2.1 CRUD Pattern ไม่สม่ำเสมอ

ระบบมีวิธีจัดการข้อมูล 2 แบบผสมกันโดยไม่มีเหตุผลชัดเจน:

| Model | Django Form POST | REST API ViewSet |
|---|:---:|:---:|
| BackgroundImage | ✅ | ✅ |
| SlideContent | ✅ | ✅ |
| TemplateConfig | ✅ | ❌ **ขาด** |
| CardContent | ✅ | ❌ **ขาด** |
| LandingPageURL | ❌ | ✅ |
| Hotspot | ❌ | ✅ |

**ผลกระทบ:**
- `TemplateConfig` และ `CardContent` ไม่มี REST API ViewSet — ถ้าต้องการทำ Mobile App หรือ Integration ภายนอกในอนาคตจะทำไม่ได้
- `LandingPageURL` และ `Hotspot` ไม่มี Form POST fallback — ถ้า JS ไม่โหลดจะใช้งานไม่ได้เลย

**แนวทางแก้ไข:** เพิ่ม `CardContentViewSet` และ `TemplateConfigViewSet` ใน `api/views.py` และลงทะเบียนใน `api/urls.py`

---

### 2.2 Helper Function ซ้ำซ้อน (DRY Violation)

โค้ดตรวจสอบสิทธิ์หน่วยงานมี 2 ที่ที่เหมือนกันทุกประการ:

**`webapp/views.py`:**
```python
def get_user_allowed_hotspots(user):
    if user.is_staff:
        return None
    names = Hotspot.objects.filter(
        departments__users=user,
        departments__is_active=True,
        is_active=True
    ).values_list('hotspot_name', flat=True)
    return [n for n in names if n]
```

**`api/views.py`:**
```python
def _get_allowed_hotspot_names(user):
    if user.is_staff:
        return None
    return list(
        Hotspot.objects.filter(
            departments__users=user,
            departments__is_active=True,
            is_active=True,
        ).distinct().values_list('hotspot_name', flat=True)
    )
```

**ผลกระทบ:** ถ้าแก้ logic ที่หนึ่ง ต้องจำไปแก้อีกที่หนึ่งด้วย — เสี่ยง bug divergence
**แนวทางแก้ไข:** ย้ายไปที่ `api/utils.py` แล้ว import ทั้งสองที่

---

### 2.3 `hotspot_filter_q()` มีแค่ที่เดียว แต่ Logic ซ้ำใน api/views.py

`webapp/views.py` มี helper:
```python
def hotspot_filter_q(allowed):
    return Q(hotspot_name__in=allowed) | Q(hotspot_name__isnull=True) | Q(hotspot_name='')
```

แต่ `api/views.py` เขียน Q expression ซ้ำในทุก `get_queryset()`:
```python
# BackgroundImageViewSet
Q(hotspot_name__in=allowed) | Q(hotspot_name__isnull=True) | Q(hotspot_name='')

# SlideContentViewSet
Q(hotspot_name__in=allowed) | Q(hotspot_name__isnull=True) | Q(hotspot_name='')

# LandingPageURLViewSet
# ... ซ้ำอีกครั้ง
```

**แนวทางแก้ไข:** ย้าย `hotspot_filter_q` ไปอยู่ใน `api/utils.py` ด้วย

---

### 2.4 `is_active` Default ไม่สม่ำเสมอ

| Model | `is_active` default | เหตุผลที่ต่าง? |
|---|---|---|
| BackgroundImage | `False` | ต้องเลือก Activate เอง |
| TemplateConfig | `False` | ต้องเลือก Activate เอง |
| SlideContent | **`True`** | แสดงทันทีหลังสร้าง |
| CardContent | **`True`** | แสดงทันทีหลังสร้าง |
| LandingPageURL | `False` | ต้องเลือก Activate เอง |
| Department | `True` | ใช้งานได้ทันที |

Slide/Card เปิด active อัตโนมัติ แต่ Background/Template/Landing ไม่เปิด — พฤติกรรมต่างกันทำให้ user งงได้
**แนวทางแก้ไข:** เพิ่ม comment ใน code อธิบายเหตุผล หรือทำให้สอดคล้องกัน

---

### 2.5 XFrameOptions Middleware ปิดอยู่แต่ยังมี Setting

**`backend/settings.py`:**
```python
MIDDLEWARE = [
    ...
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Disabled for iframe preview
]

X_FRAME_OPTIONS = 'SAMEORIGIN'  # ← setting นี้ไม่มีผล เพราะ middleware ถูก comment ออก
```

**ผลกระทบ:** `X_FRAME_OPTIONS = 'SAMEORIGIN'` ไม่มีผลใด ๆ ในทางปฏิบัติ เพราะ middleware ที่จะอ่าน setting นี้ถูกปิดอยู่
**แนวทางแก้ไข:** ลบ `X_FRAME_OPTIONS = 'SAMEORIGIN'` ทิ้ง หรืออธิบายให้ชัดเจนกว่าเดิม

---

### 2.6 `cache_page` Import แต่ไม่ได้ใช้

**`api/views.py` line 9:**
```python
from django.views.decorators.cache import cache_page  # ← import มา แต่ไม่มีที่ใดใน views ใช้
```

**แนวทางแก้ไข:** ลบ import ที่ไม่ใช้ออก หรือนำมาใช้จริงกับ public endpoints

---

## 3. ค่า Hardcoded

### 3.1 Image Processing Constants (`api/models.py`)

```python
max_size = (1920, 1080)          # line 36 — hardcoded
img.save(img_path, optimize=True, quality=85)  # line 39 — hardcoded
```

ค่าเหล่านี้ควรเป็น settings หรือ constants ที่แก้ไขได้ เช่น:
```python
# settings.py
IMAGE_MAX_WIDTH  = int(os.getenv('IMAGE_MAX_WIDTH',  '1920'))
IMAGE_MAX_HEIGHT = int(os.getenv('IMAGE_MAX_HEIGHT', '1080'))
IMAGE_QUALITY    = int(os.getenv('IMAGE_QUALITY',    '85'))
```

---

### 3.2 `LANGUAGE_CODE = 'en-us'` (`backend/settings.py`)

```python
LANGUAGE_CODE = 'en-us'  # ← ระบบไทยควรใช้ 'th'
```

ส่งผลต่อ Django Admin, Error messages, และ built-in form validation messages ที่จะแสดงเป็นภาษาอังกฤษแทนภาษาไทย

---

### 3.3 ngrok URL เป็น Default CSRF Trusted Origins

```python
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.ngrok-free.app,https://*.ngrok.io'  # ← ngrok เป็น default ใน production code
).split(',') if o.strip()]
```

ngrok เป็น development tool — ไม่ควรเป็น fallback default บน production
**แนวทางแก้ไข:** เปลี่ยน default เป็น `''` แล้วให้ production ตั้งค่าเองผ่าน `.env`

---

### 3.4 Google.com เป็น Fallback URL

**`webapp/views.py` — `hotspot_login`:**
```python
'link_orig': request.GET.get('link-orig', 'http://www.google.com'),
```

URL ของ Google ถูก hardcode เป็น fallback — ควรอ่านจาก `SystemSettings` หรือ settings

---

## 4. ปัญหาด้าน Security

### 4.1 ❌ ไม่มี Rate Limiting / Throttling

Public endpoints ที่ MikroTik เรียกทุก request ไม่มี rate limit เลย:

```
GET /api/login-background/    — ไม่มี throttle
GET /api/slide-content/       — ไม่มี throttle
GET /api/template-config/     — ไม่มี throttle
POST /api/track-impression/   — ไม่มี throttle  ← เสี่ยงถูก flood มากที่สุด
```

**ผลกระทบ:** บุคคลภายนอกสามารถส่ง request หลายแสนครั้งต่อนาทีได้ ทำให้ CPU/Disk (SQLite) ทำงานหนักจนเซิร์ฟเวอร์ตอบสนองช้าหรือหยุดทำงาน

**แนวทางแก้ไข:** เพิ่ม DRF Throttle classes:
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '300/minute',
    }
}
```

---

### 4.2 ❌ ไม่มี Login Brute-Force Protection

หน้า `/login/` ใน `webapp/views.py` ไม่มีการนับครั้งที่ login ผิด ไม่มีการล็อค account และไม่มี CAPTCHA

**ผลกระทบ:** สามารถใช้ dictionary attack โจมตี admin account ได้

**แนวทางแก้ไข:** ใช้ `django-axes` package หรือเขียน middleware นับ failed login และ block IP ชั่วคราว

---

### 4.3 ❌ ไม่ได้ตั้งค่า Session Timeout

```python
# settings.py — ไม่มี SESSION_COOKIE_AGE
```

Django default session อยู่ได้นาน 2 สัปดาห์ หรือจนกว่า browser จะปิด ซึ่งนานเกินไปสำหรับระบบ admin

**แนวทางแก้ไข:**
```python
SESSION_COOKIE_AGE = 28800        # 8 ชั่วโมง (หน่วย: วินาที)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True  # รีเซ็ต timeout ทุกครั้งที่มี activity
```

---

### 4.4 ❌ ไม่มี Audit Log

ไม่มีการบันทึกว่าใคร เปลี่ยนแปลงอะไร เมื่อไหร่ เช่น:
- ใครเป็นคนลบ Background Image
- ใคร deactivate Template
- ใครเพิ่ม/ลบ User

มีแค่ `created_by` / `uploaded_by` บน model บางตัว แต่ไม่มี log การเปลี่ยนแปลง

**แนวทางแก้ไข:** ใช้ `django-simple-history` หรือสร้าง `AuditLog` model เก็บ action/user/timestamp/detail

---

### 4.5 ❌ ไม่มี LOGGING Configuration

ทั้ง `webapp/views.py` และ `api/views.py` มีการเรียก `logger.info()`, `logger.warning()`, `logger.error()` อยู่มาก แต่ `settings.py` ไม่มี `LOGGING` dictionary เลย

**ผลกระทบ:** บน production — log ทั้งหมดหายไปหรือไปที่ stderr เท่านั้น ไม่มีไฟล์ log เก็บไว้

**แนวทางแก้ไข:** เพิ่ม LOGGING config ใน settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'liblogin.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'api': {'handlers': ['file'], 'level': 'INFO'},
        'webapp': {'handlers': ['file'], 'level': 'INFO'},
    },
}
```

---

## 5. ฟีเจอร์ที่ขาด

### 5.1 ❌ Pagination บน REST API

ทุก ViewSet ไม่มี pagination — ถ้าจำนวนข้อมูลเติบโตขึ้น (Background 100+ รูป, Impression หลายหมื่น record) response จะหนักมากและ browser อาจค้าง

**แนวทางแก้ไข:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

### 5.2 ❌ Search / Filter บน REST API

ไม่มี `filter_backends` บน ViewSet ใด — ค้นหาหรือกรองข้อมูลผ่าน API ไม่ได้

**แนวทางแก้ไข:** เพิ่ม `django-filter` หรือ DRF built-in `SearchFilter`:
```python
from rest_framework.filters import SearchFilter, OrderingFilter

class BackgroundImageViewSet(viewsets.ModelViewSet):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'hotspot_name']
    ordering_fields = ['uploaded_at', 'title']
```

---

### 5.3 ❌ Password Reset ผ่าน Email

ไม่มี `EMAIL_BACKEND` ตั้งค่าไว้ — ถ้า admin ลืมรหัสผ่านต้องให้ superuser reset ให้ผ่าน Django shell หรือ Django Admin

---

### 5.4 ❌ Health Check Endpoint

ไม่มี `/api/health/` endpoint — Monitoring tools, Load Balancer, หรือ NSSM watchdog ไม่สามารถตรวจสอบสถานะระบบได้อัตโนมัติ

**แนวทางแก้ไข:** เพิ่ม endpoint เรียบง่าย:
```python
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'version': '1.0'})
```

---

### 5.5 ❌ API Documentation (Swagger/OpenAPI)

ไม่มี auto-generated API docs — developer ต้องอ่านโค้ดเพื่อเข้าใจ API

**แนวทางแก้ไข:** เพิ่ม `drf-spectacular` หรือ `drf-yasg`

---

### 5.6 ❌ Data Import/Export

ไม่มีระบบ export/import ข้อมูล (Backgrounds, Slides, Cards, Templates) — การย้ายข้อมูลระหว่าง server ต้องทำผ่าน Django `dumpdata`/`loaddata` เท่านั้น ซึ่ง admin ทั่วไปทำเองไม่ได้

---

### 5.7 ❌ `CardContentViewSet` ใน REST API

`CardContent` มี serializer และ webapp view รองรับแล้ว แต่ยังไม่มี REST API ViewSet — ทำให้ pattern ไม่ consistent กับ Background, Slide, LandingPageURL

---

## 6. วิเคราะห์: การเชื่อมต่อ Server ↔ login.html (MikroTik)

### 6.1 สถาปัตยกรรมการทำงานจริง (End-to-End Flow)

```
[Client WiFi Device]
    │
    │ [1] เชื่อมต่อ WiFi
    ▼
[MikroTik Router]
    │ [2] ดัก HTTP request ที่ไปหา internet (walled garden)
    │ [3] Redirect → https://lib.npu.ac.th/liblogin/hotspot_xxx/login.html
    ▼
[IIS + Django/Waitress — lib.npu.ac.th]
    │ [4] URL pattern: re_path(r'^(hotspot[^/]*)/(.*)$', serve_hotspot_file)
    │     Django serve() ไฟล์จาก BASE_DIR/hotspot_xxx/login.html
    ▼
[Browser ฝั่ง Client]
    │ [5] JavaScript ใน login.html ทำ fetch() ไปยัง API:
    │     GET  /api/login-background/?hotspot_name=hotspot_xxx   → รูปพื้นหลัง
    │     GET  /api/template-config/?hotspot_name=hotspot_xxx    → Slide/Card content
    │     GET  /api/landing-url/?hotspot_name=hotspot_xxx        → URL ปลายทาง
    │     POST /api/track-impression/                            → บันทึก analytics
    │
    │ [6] User กรอก Username/Password
    │ [7] Form POST → $(link-login-only) ← MikroTik template variable
    ▼
[MikroTik Router]
    │ [8] Authenticate user กับ RADIUS / user list
    │ [9] Redirect → Landing Page URL (จาก API)
    ▼
[Internet ✓]
```

> **สำคัญ:** `$(if chap-id)`, `$(link-login-only)`, `$(mac)` ฯลฯ เป็น **MikroTik template syntax**
> ไม่ใช่ Django template — ถูก inject โดย MikroTik RouterOS ก่อนส่ง response ให้ client
> Django เพียงแค่ `serve()` ไฟล์แบบ static โดยไม่ process เนื้อหาไฟล์เลย

---

### 6.2 สิ่งที่หน้า /hotspots/ ตรวจสอบได้และไม่ได้

`HotspotViewSet.test_connection()` ตรวจสอบเฉพาะ **filesystem บนเครื่อง server** เท่านั้น:

| Check | Logic | ผล |
|---|---|---|
| `folder_exists` | `os.path.isdir(BASE_DIR/hotspot_xxx)` | ✅ ตรวจได้จริง |
| `login_file_exists` | `os.path.isfile(.../login.html)` | ✅ ตรวจได้จริง |
| `config_matched` | regex หา `window.HOTSPOT_NAME = 'xxx'` ใน file | ✅ ตรวจได้จริง |
| HTTP URL เข้าถึงได้? | ❌ ไม่มี | ❌ ตรวจไม่ได้ |
| MikroTik redirect ถูกต้อง? | ❌ ไม่มี | ❌ ตรวจไม่ได้ |
| API reachable จาก client? | ❌ ไม่มี | ❌ ตรวจไม่ได้ |
| CSS/JS โหลดได้? | ❌ ไม่มี | ❌ ตรวจไม่ได้ |

**สรุป:** Status `🟢 ready` บนหน้า /hotspots/ หมายความว่า **"ไฟล์มีอยู่และ config ตรง"** เท่านั้น
ไม่ใช่ "hotspot ทำงานปกติ" — ยังอาจมีปัญหา network, CORS, หรือ MikroTik config ก็ได้

---

### 6.3 ปัญหาหลัก: login.html 5 ไฟล์ที่เป็น Copy เดียวกัน

ทุก hotspot มีไฟล์ `login.html` ขนาด 802 บรรทัดที่เหมือนกันทุกประการ ต่างกันเพียง **1 บรรทัด**:

```
hotspot/login.html        802 บรรทัด  →  window.HOTSPOT_NAME = 'hotspot'
hotspot_lab/login.html    802 บรรทัด  →  window.HOTSPOT_NAME = 'hotspot_lab'
hotspot_lan/login.html    802 บรรทัด  →  window.HOTSPOT_NAME = 'hotspot_lan'
hotspot_office/login.html 802 บรรทัด  →  window.HOTSPOT_NAME = 'hotspot_office'
hotspot_wifi/login.html   802 บรรทัด  →  window.HOTSPOT_NAME = 'hotspot_wifi'
```

นอกจากนี้ URL ยังถูก hardcode ซ้ำในทุกไฟล์:

```javascript
// บรรทัดนี้ปรากฏ 4 ครั้งต่อไฟล์ × 5 ไฟล์ = 20 จุด hardcode
: 'https://lib.npu.ac.th/liblogin';
```

รวมถึง CSS และ Logo URL:
```html
<link rel="stylesheet" href="https://lib.npu.ac.th/liblogin/static/css/login.css?v=8">
<img src="https://lib.npu.ac.th/liblogin/static/logo_arc.png" ...>
```

**ผลกระทบ:**
- แก้ bug หรือเพิ่มฟีเจอร์ใน login.html → ต้องแก้ 5 ไฟล์ทุกครั้งด้วยมือ
- ลืมแก้ไฟล์ใดไฟล์หนึ่ง → hotspot นั้นใช้โค้ดเวอร์ชันเก่า
- เพิ่ม hotspot ใหม่ → ต้อง copy + แก้ชื่อเอง ไม่มี automation
- อัปเดต server URL (เช่น ย้าย domain) → ต้องแก้ทุกไฟล์

---

### 6.4 ข้อจำกัดของ test_connection ในปัจจุบัน

เนื่องจาก `test_connection` อ่านไฟล์จาก filesystem เท่านั้น สิ่งที่ยังตรวจไม่ได้มีดังนี้:

1. **CORS ทำงานถูกต้อง?**
   login.html ถูกโหลดจาก MikroTik IP (เช่น `192.168.88.1`) แล้ว JS fetch ไป `lib.npu.ac.th` — CORS ต้องเปิดอยู่ (`CORS_ALLOW_ALL_ORIGINS = True` ตั้งแล้ว แต่ไม่มีการ verify)

2. **CSS และรูปภาพโหลดได้?**
   login.html โหลด CSS จาก `https://lib.npu.ac.th/liblogin/static/...` — ถ้า static files ไม่ทำงานหน้าเพจจะพังแต่ test_connection จะยัง pass

3. **API endpoints ตอบสนอง?**
   `/api/login-background/`, `/api/template-config/` ไม่ถูกทดสอบจาก test_connection

4. **version ไฟล์ตรงกับ DB หรือเปล่า?**
   ถ้ามีคนแก้ login.html บน server โดยตรง (ไม่ผ่าน deployment) อาจมีเวอร์ชันที่ไม่ sync

---

### 6.5 แนวทางพัฒนา Phase ต่อไป

#### Option A: Auto-Deploy Login Page (แนะนำ)

เพิ่ม feature ใหม่ใน Django: เมื่อ Admin สร้าง Hotspot ใหม่ หรือกด "Deploy" — ระบบ generate และเขียนไฟล์อัตโนมัติ

```
[Admin สร้าง Hotspot 'hotspot_new' ในระบบ]
            ↓
Django render template: hotspot_login_template.html
+ inject: window.HOTSPOT_NAME = 'hotspot_new'
            ↓
เขียนไฟล์ → BASE_DIR/hotspot_new/login.html
คัดลอก   → BASE_DIR/hotspot_new/md5.js
            ↓
test_connection() verify ผล
            ↓
Status: 🟢 Deployed
```

ไฟล์ที่ต้องสร้าง/แก้ไข:
- `hotspot/login_template.html` — master template (1 ไฟล์)
- `api/views.py` → `HotspotViewSet.deploy()` action ใหม่
- `webapp/templates/webapp/hotspots.html` → ปุ่ม "Deploy" ต่อ hotspot

#### Option B: Enhanced test_connection

เพิ่มการตรวจสอบเพิ่มเติมใน `test_connection`:

```python
# ตรวจสอบ API endpoints ว่าตอบสนอง
api_ok = requests.get(f"{base_url}/api/login-background/?hotspot_name={name}", timeout=5).ok

# ตรวจสอบ Static CSS ว่าโหลดได้
css_ok = requests.get(f"{base_url}/static/css/login.css", timeout=5).ok

# ตรวจสอบ version hash ของ login.html
file_hash = hashlib.md5(open(login_file_path).read().encode()).hexdigest()
```

#### สรุปการเปรียบเทียบ

| | ปัจจุบัน | Option A | Option B |
|---|---|---|---|
| เพิ่ม hotspot ใหม่ | Copy ไฟล์เอง | อัตโนมัติ ✅ | Copy ไฟล์เอง |
| แก้ bug ใน login.html | แก้ 5 ไฟล์ | แก้ 1 template ✅ | แก้ 5 ไฟล์ |
| ตรวจสอบ connectivity | File system only | File system only | HTTP test ✅ |
| ความยากในการพัฒนา | — | ปานกลาง | ง่าย |
| **แนะนำ** | — | ✅ Phase ต่อไป | ✅ ทำควบคู่ |

---

## 7. สิ่งที่ดีแล้ว

| รายการ | รายละเอียด |
|---|---|
| ✅ Environment Variables | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `FORCE_SCRIPT_NAME` อ่านจาก `.env` ทั้งหมด |
| ✅ Sub-path Deployment | `FORCE_SCRIPT_NAME` + `USE_X_FORWARDED_HOST` + `SECURE_PROXY_SSL_HEADER` ตั้งค่าถูกต้อง |
| ✅ Image Auto-Resize | `BackgroundImage.save()` resize อัตโนมัติ ≤1920×1080 |
| ✅ Department Access Control | `get_user_allowed_hotspots()` + `hotspot_filter_q()` ป้องกัน data leakage ระหว่าง department |
| ✅ Thai Timezone | `TIME_ZONE = 'Asia/Bangkok'` |
| ✅ Password Validation | `AUTH_PASSWORD_VALIDATORS` ครบ 4 ตัว |
| ✅ CSRF Protection | CSRF token ทุก form POST และ API call |
| ✅ Row-level Permission | ทุก ViewSet มี `get_queryset()` override กรองตาม department |
| ✅ Cascade Delete | `Hotspot.delete()` ลบ Templates/Backgrounds/Slides/Cards ที่เกี่ยวข้องอัตโนมัติ |
| ✅ Analytics | `PageImpression` + `DailyReachStats` เก็บ impression และ reach ได้ |
| ✅ Thai Date Standard | `thai_date` templatetag + `formatThaiDate()` JS utility สอดคล้องกันทุกหน้า |
| ✅ Multi-hotspot Support | Background/Template/Slide/Card แต่ละตัวระบุ `hotspot_name` ได้หรือ null = ทุก hotspot |

---

## 8. ลำดับความสำคัญในการแก้ไข

### 🔴 Priority 1 — Security (ควรแก้ก่อน deploy ต่อไป)

| # | งาน | ไฟล์ | ความยาก |
|---|---|---|---|
| 1 | เพิ่ม DRF Throttle บน public endpoints | `settings.py` | ง่าย |
| 2 | เพิ่ม `LOGGING` config | `settings.py` | ง่าย |
| 3 | ตั้ง `SESSION_COOKIE_AGE` | `settings.py` | ง่าย |
| 4 | เปลี่ยน `LANGUAGE_CODE = 'th'` | `settings.py` | ง่าย |
| 5 | ลบ ngrok default จาก CSRF_TRUSTED_ORIGINS | `settings.py` | ง่าย |

### 🟡 Priority 2 — Code Quality

| # | งาน | ไฟล์ | ความยาก |
|---|---|---|---|
| 6 | สร้าง `api/utils.py` รวม helper functions | `api/utils.py` | ปานกลาง |
| 7 | เพิ่ม Pagination บน REST API | `settings.py` | ง่าย |
| 8 | ลบ unused import `cache_page` | `api/views.py` | ง่าย |
| 9 | เพิ่ม `CardContentViewSet` | `api/views.py`, `api/urls.py` | ปานกลาง |

### 🔵 Priority 3 — Features

| # | งาน | ไฟล์ | ความยาก |
|---|---|---|---|
| 10 | Health Check endpoint | `api/views.py`, `api/urls.py` | ง่าย |
| 11 | Login Brute-Force Protection | `django-axes` package | ปานกลาง |
| 12 | Audit Log | model ใหม่ + middleware | ยาก |
| 13 | Image constants ย้ายเข้า settings | `settings.py`, `api/models.py` | ง่าย |

---

## Appendix: สรุปจำนวนปัญหา

| ประเภท | จำนวน |
|---|---|
| โค้ดไม่สอดคล้อง (Inconsistencies) | 6 จุด |
| ค่า Hardcoded | 4 จุด (+20 จุดใน login.html files) |
| ปัญหา Security | 5 จุด |
| ฟีเจอร์ที่ขาด | 7 จุด |
| ปัญหา login.html architecture | 4 จุด |
| **รวม** | **26 จุด** |

---

## Phase Development Roadmap

| Phase | งาน | ผลลัพธ์ |
|---|---|---|
| **Phase 1** (ปัจจุบัน) | Multi-dept access control, Image Library, Date format | เสร็จแล้ว ✅ |
| **Phase 2** | Priority 1 Security fixes (throttle, logging, session) | ระบบ production-ready |
| **Phase 3** | Auto-Deploy login.html + Enhanced test_connection | จัดการ hotspot ได้สะดวก |
| **Phase 4** | Pagination, CardContentViewSet, Health Check | API completeness |
| **Phase 5** | Audit Log, Brute-force protection | Enterprise security |

---

*รายงานนี้จัดทำโดย AI Code Review เพื่อใช้เป็นแนวทางในการพัฒนาระบบต่อไป*
*ไม่ใช่ข้อบังคับ — ทีมพัฒนาสามารถพิจารณาตามความเหมาะสมและทรัพยากรที่มี*
