# 🌐 MikroTik Hotspot Redirect to Django Server

คู่มือการตั้งค่า MikroTik ให้ Redirect ไปยัง Django Server แทนการเก็บไฟล์ใน MikroTik

---

## 🎯 เป้าหมาย

**เดิม (ไม่สะดวก):**
```
MikroTik Hotspot
├── css/ (เก็บใน MikroTik)
├── js/ (เก็บใน MikroTik)
├── images/ (เก็บใน MikroTik)
└── login.html (เก็บใน MikroTik)
```
- ❌ แก้ไขยาก ต้องเข้า WinBox
- ❌ Upload ทีละไฟล์
- ❌ ไม่มี Version Control

**ใหม่ (สะดวก):**
```
MikroTik → Redirect → Django Server
                      ├── CSS (ปรับได้ทันที)
                      ├── JS (ปรับได้ทันที)
                      ├── Images (อัปโหลดผ่าน Web)
                      └── Login Page (แก้ไขง่าย)
```
- ✅ แก้ไขผ่าน Web Interface
- ✅ Version Control ด้วย Git
- ✅ อัปโหลดรูปผ่าน Dashboard
- ✅ แก้ไข CSS/JS แล้วเห็นผลทันที

---

## 📋 วิธีการทำงาน

### แบบเดิม (MikroTik Serve Login Page):
```
User → เชื่อมต่อ WiFi
    → MikroTik ดัก HTTP request
    → แสดง login.html จาก MikroTik
    → โหลด CSS, JS จาก MikroTik
    → ส่ง login ไปยัง MikroTik
```

### แบบใหม่ (Django Serve Login Page):
```
User → เชื่อมต่อ WiFi
    → MikroTik ดัก HTTP request
    → Redirect ไปยัง Django Server
    → Django แสดง Login Page
    → โหลด CSS, JS, Images จาก Django
    → โหลด Background จาก API
    → ส่ง login กลับไปยัง MikroTik
```

---

## 🔧 ขั้นตอนการตั้งค่า

### ขั้นตอนที่ 1: สร้าง Login View ใน Django

ไฟล์: `webapp/views.py`

```python
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def hotspot_login(request):
    """
    Hotspot Login Page สำหรับ MikroTik
    รับ parameters จาก MikroTik และแสดงหน้า Login
    """
    # รับ parameters จาก MikroTik
    context = {
        'link_login': request.GET.get('link-login', ''),
        'link_login_only': request.GET.get('link-login-only', ''),
        'link_orig': request.GET.get('link-orig', ''),
        'mac': request.GET.get('mac', ''),
        'ip': request.GET.get('ip', ''),
        'username': request.GET.get('username', ''),
        'error': request.GET.get('error', ''),
        'trial': request.GET.get('trial', ''),
        'chap_id': request.GET.get('chap-id', ''),
        'chap_challenge': request.GET.get('chap-challenge', ''),
        'popup': request.GET.get('popup', 'false'),
    }

    return render(request, 'webapp/hotspot_login.html', context)
```

### ขั้นตอนที่ 2: เพิ่ม URL Route

ไฟล์: `webapp/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.dashboard_view, name='dashboard'),
    path('backgrounds/', views.backgrounds_view, name='backgrounds'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),

    # Hotspot Login (ไม่ต้อง authentication)
    path('hotspot/login/', views.hotspot_login, name='hotspot_login'),
]
```

### ขั้นตอนที่ 3: สร้าง Template

ไฟล์: `webapp/templates/webapp/hotspot_login.html`

```html
{% load static %}
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiFi Login - Nakhon Phanom University</title>

    <!-- CSS -->
    <link rel="stylesheet" href="{% static 'css/hotspot.css' %}">
</head>
<body>
    <div id="login-background"></div>
    <div class="overlay"></div>

    <div class="login-container">
        <div class="login-box">
            <!-- Logo -->
            <img src="{% static 'images/logo.png' %}" alt="NPU Logo" class="logo">

            <h1>ยินดีต้อนรับ</h1>
            <p class="subtitle">สำนักวิทยบริการ มหาวิทยาลัยนครพนม</p>
            <p class="subtitle-en">Office of Academic Resources, Nakhon Phanom University</p>

            <!-- Error Message -->
            {% if error %}
            <div class="error-message">
                {% if error == 'invalid username or password' %}
                    ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง
                {% elif error == 'user is already connected' %}
                    ผู้ใช้นี้เชื่อมต่ออยู่แล้ว
                {% else %}
                    {{ error }}
                {% endif %}
            </div>
            {% endif %}

            <!-- MikroTik Login Form -->
            <form name="login" action="{{ link_login_only }}" method="post">
                <input type="hidden" name="dst" value="{{ link_orig }}" />
                <input type="hidden" name="popup" value="{{ popup }}" />

                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" name="username" id="username"
                           value="{{ username }}" required autofocus>
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" name="password" id="password" required>
                </div>

                <button type="submit" class="btn-login">เข้าสู่ระบบ</button>
            </form>

            <div class="footer">
                <p>ติดต่อเจ้าหน้าที่ หากมีปัญหาในการเข้าใช้งาน</p>
                <p class="contact-info">โทร. 042-111-222 | อีเมล: support@npu.ac.th</p>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="{% static 'js/hotspot.js' %}"></script>
</body>
</html>
```

### ขั้นตอนที่ 4: สร้าง Static Files

**โครงสร้างโฟลเดอร์:**
```
webapp/
├── static/
│   ├── css/
│   │   └── hotspot.css
│   ├── js/
│   │   └── hotspot.js
│   └── images/
│       └── logo.png
└── templates/
    └── webapp/
        └── hotspot_login.html
```

**ไฟล์ CSS:** `webapp/static/css/hotspot.css`
```css
/* เอา CSS จาก test_production.html มาใส่ */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    height: 100vh;
    overflow: hidden;
}

/* ... CSS เต็มๆ */
```

**ไฟล์ JS:** `webapp/static/js/hotspot.js`
```javascript
// Fetch background image from API
const API_BASE_URL = window.location.origin; // ใช้ same origin

function loadBackgroundImage() {
    const apiUrl = `${API_BASE_URL}/api/login-background/`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.imageUrl) {
                document.getElementById('login-background').style.backgroundImage =
                    `url(${data.imageUrl})`;
            }
        })
        .catch(error => {
            console.error('Error loading background:', error);
        });
}

document.addEventListener('DOMContentLoaded', loadBackgroundImage);
```

### ขั้นตอนที่ 5: Collect Static Files

```powershell
cd C:\inetpub\wwwroot\Liblogin
python manage.py collectstatic --noinput
```

---

## 🔧 ตั้งค่า MikroTik

### วิธีที่ 1: Walled Garden + HTTP Redirect

**1. เพิ่ม Django Server เป็น Walled Garden:**

```
/ip hotspot walled-garden
add dst-host=202.29.55.222 comment="Django Login Server"
```

**2. สร้างไฟล์ Redirect ขนาดเล็กใน MikroTik:**

ไฟล์: `login.html` (เก็บใน MikroTik - ไฟล์เล็กมาก)

```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=http://202.29.55.222:8291/hotspot/login/?link-login-only=$(link-login-only)&link-orig=$(link-orig)&mac=$(mac)&ip=$(ip)&username=$(username)&error=$(error)">
</head>
<body>
    <p>Redirecting to login page...</p>
</body>
</html>
```

### วิธีที่ 2: HTTP CHAP (แนะนำ)

**ตั้งค่า Hotspot Profile:**

```
/ip hotspot profile
set [find default=yes] html-directory=hotspot \
    http-cookie-lifetime=1d \
    login-by=http-chap,http-pap
```

**สร้างไฟล์ redirect.html:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=http://202.29.55.222:8291/hotspot/login/?$(link-redirect)">
</head>
<body></body>
</html>
```

---

## ✅ ข้อดีของวิธีนี้

### 1. **แก้ไขง่าย**
```powershell
# แก้ไข CSS
edit webapp/static/css/hotspot.css
# Collect static
python manage.py collectstatic --noinput
# รีสตาร์ท service
nssm restart LibLogin
```

### 2. **อัปโหลดรูปผ่าน Web**
- เข้า http://202.29.55.222:8291/login/
- คลิก Background Images
- Upload รูปใหม่
- เห็นผลทันที

### 3. **Version Control**
```powershell
git add .
git commit -m "Update login page design"
git push origin main
```

### 4. **Testing ง่าย**
```
http://202.29.55.222:8291/hotspot/login/
```
ไม่ต้องเชื่อมต่อ WiFi ก็ทดสอบได้

---

## 🔄 Migration จาก MikroTik

### ขั้นตอนการย้าย:

1. **Backup ไฟล์เก่าจาก MikroTik**
   - Download css/, js/, images/ ทั้งหมด
   - เก็บไว้เป็น backup

2. **ย้ายไฟล์มา Django**
   ```
   MikroTik/css/*.css → webapp/static/css/
   MikroTik/js/*.js → webapp/static/js/
   MikroTik/images/* → webapp/static/images/
   ```

3. **แก้ไข Path ใน Template**
   - เปลี่ยนจาก `<link href="css/style.css">`
   - เป็น `<link href="{% static 'css/style.css' %}">`

4. **Test**
   - เข้า http://202.29.55.222:8291/hotspot/login/
   - ตรวจสอบ CSS, JS, Images โหลดได้

5. **Deploy บน MikroTik**
   - สร้างไฟล์ redirect.html เล็กๆ
   - Upload ไปยัง MikroTik
   - ตั้งเป็น login.html

---

## 🎯 สรุป

| รายการ | เดิม (MikroTik) | ใหม่ (Django) |
|--------|-----------------|---------------|
| แก้ไข CSS | ต้องเข้า WinBox | แก้ไขผ่าน Editor |
| อัปโหลดรูป | FTP/WinBox | Web Interface |
| Version Control | ไม่มี | Git |
| Testing | ต้องเชื่อมต่อ WiFi | เปิด URL ได้เลย |
| Backup | Manual | Auto (Git) |

---

**พร้อมสร้างระบบนี้ไหมครับ?**

ผมจะสร้าง:
1. View สำหรับ Hotspot Login
2. Template พร้อม CSS/JS
3. ไฟล์ redirect.html สำหรับ MikroTik
4. คู่มือการติดตั้ง
