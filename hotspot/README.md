# 📁 Hotspot Login Files

## 📄 ไฟล์ในโฟลเดอร์นี้

### **login.html** ⭐ (ไฟล์หลัก - แก้ไขแล้ว Phase 1)

**วัตถุประสงค์**: หน้า login สำหรับ MikroTik Hotspot พร้อม dynamic background

**การเปลี่ยนแปลง Phase 1**:
- ✅ เพิ่ม `<div id="dynamic-background">` สำหรับแสดงพื้นหลัง
- ✅ เพิ่ม CSS styling สำหรับ background container
- ✅ เพิ่ม JavaScript fetch API จาก Django Server
- ✅ Dynamic background loading จาก `http://202.29.55.222:8291/api/login-background/`

**ขนาดไฟล์**: ~6 KB (เพิ่มจาก 3 KB เดิม)

**อัพโหลดไปบน MikroTik**:
```
WinBox → Files → hotspot/ → Upload login.html
```

**MikroTik ที่ต้องอัพโหลด**:
- ✅ MikroTik #1 (202.29.55.180)
- ✅ MikroTik #2 (202.29.55.30)

---

## 🔧 การทำงานของ login.html

### 1. Structure
```html
<!doctype html>
<html>
<head>
    <style>
        #dynamic-background {
            /* Fixed background layer */
        }
    </style>
</head>
<body>
    <div id="dynamic-background"></div>

    <!-- MikroTik Login Form -->
    <form action="$(link-login-only)" method="post">
        ...
    </form>

    <script>
        // Fetch background from Django API
        fetch('http://202.29.55.222:8291/api/login-background/')
            .then(...)
    </script>
</body>
</html>
```

### 2. Flow
```
หน้าโหลด
    ↓
JavaScript execute
    ↓
Fetch API: GET /api/login-background/
    ↓
รับ JSON: {"success": true, "imageUrl": "..."}
    ↓
เปลี่ยน background-image CSS
    ↓
แสดงพื้นหลัง
```

### 3. Graceful Degradation
```javascript
.catch(function(error) {
    console.error('Error loading background:', error);
    // Silently fail - page will show without custom background
});
```

ถ้า API fail → หน้า login ยังทำงานได้ปกติ (แค่ไม่มีพื้นหลัง)

---

## 🌐 API Configuration

### API Server
```
URL: http://202.29.55.222:8291
Endpoint: /api/login-background/
Method: GET
```

### Parameters (Optional)
```
?router_id=mt1  # สำหรับ MikroTik #1
?router_id=mt2  # สำหรับ MikroTik #2
(ไม่ระบุ)        # ใช้ default background
```

### Response
```json
{
  "success": true,
  "imageUrl": "http://202.29.55.222:8291/media/backgrounds/pic1.jpg",
  "title": "ชื่อรูปภาพ"
}
```

---

## 🔐 MikroTik Configuration Required

### Walled Garden (สำคัญ!)
```bash
/ip hotspot walled-garden
add dst-host=202.29.55.222 comment="Django API Server"
```

**เหตุผล**: ให้ JavaScript ดึง API จาก 202.29.55.222 ได้โดยไม่ต้อง login ก่อน

### File Structure บน MikroTik
```
/hotspot/
├── login.html          ← ไฟล์นี้ (อัพโหลดใหม่)
├── logout.html         (เดิม)
├── status.html         (เดิม)
├── error.html          (เดิม)
├── css/
│   └── style.css       (เดิม - ไม่ต้องแก้)
├── img/
│   ├── user.svg        (เดิม)
│   └── password.svg    (เดิม)
└── md5.js              (เดิม)
```

---

## 📝 การอัพโหลดไฟล์

### วิธีที่ 1: WinBox (แนะนำ)
```
1. เปิด WinBox → Connect ไปยัง MikroTik
2. Menu → Files
3. เข้าโฟลเดอร์ hotspot/
4. Backup login.html เดิม (rename → login.html.backup)
5. Upload login.html ใหม่จากโฟลเดอร์นี้
6. ทดสอบ: เชื่อมต่อ WiFi → เปิดเบราว์เซอร์
```

### วิธีที่ 2: FTP
```
1. เปิดใช้ FTP บน MikroTik: /ip service set ftp disabled=no
2. ใช้ FTP Client (FileZilla) connect ไปยัง MikroTik
3. Upload login.html ไปที่ hotspot/
4. ปิด FTP: /ip service set ftp disabled=yes
```

**รายละเอียดเพิ่มเติม**: ดูใน `/MIKROTIK_UPLOAD_GUIDE.md`

---

## 🧪 การทดสอบ

### 1. ทดสอบ API
```bash
curl http://202.29.55.222:8291/api/login-background/
```

### 2. ทดสอบหน้า Test
```
http://202.29.55.222:8291/test_hotspot_background.html
```

### 3. ทดสอบบน MikroTik จริง
```
1. เชื่อมต่อ WiFi hotspot
2. เปิดเบราว์เซอร์
3. F12 → เปิด Developer Console
4. ดู Console log:
   - "Fetching background from: ..."
   - "Background loaded: ..."
5. ตรวจสอบว่ามีรูปพื้นหลังแสดง
```

---

## 🐛 Troubleshooting

### ปัญหา: ไม่มีพื้นหลังแสดง

**สาเหตุ**:
1. ❌ ไม่มี Walled Garden
   ```
   แก้: /ip hotspot walled-garden add dst-host=202.29.55.222
   ```

2. ❌ Django server ไม่ได้รัน
   ```
   แก้: python manage.py runserver 0.0.0.0:8291
   ```

3. ❌ ไม่มีรูป active ในฐานข้อมูล
   ```
   แก้: เข้า http://202.29.55.222:8291/backgrounds/ → อัพโหลดรูป
   ```

4. ❌ CORS ไม่อนุญาต
   ```
   แก้: ตรวจสอบ backend/settings.py → CORS_ALLOW_ALL_ORIGINS = True
   ```

### ปัญหา: Form login ไม่ทำงาน

**ตรวจสอบ**:
- ✅ ไฟล์ login.html ไม่เสียหาย
- ✅ ไฟล์ css/style.css, md5.js ยังอยู่
- ✅ MikroTik variables ยังทำงาน: $(link-login-only), $(username)

### ปัญหา: Console มี Error

**เปิด Developer Console (F12) ดู Error**:
```
CORS Error → แก้ CORS settings
Network Error → แก้ Django server
404 Not Found → แก้ ไม่มีรูป active
```

---

## 📚 เอกสารที่เกี่ยวข้อง

- `../MIKROTIK_UPLOAD_GUIDE.md` - คู่มือการอัพโหลดแบบละเอียด
- `../PHASE1_IMPLEMENTATION_SUMMARY.md` - สรุปการพัฒนา Phase 1
- `../test_hotspot_background.html` - หน้าทดสอบ API
- `../README.md` - คู่มือโปรเจกต์หลัก

---

## ✅ Checklist ก่อนอัพโหลด

### Pre-Upload
- ✅ Django server รันที่ 202.29.55.222:8291
- ✅ มีรูปพื้นหลังอย่างน้อย 1 รูป (is_active=True)
- ✅ ทดสอบ API แล้ว (curl หรือ test page)

### Upload
- ✅ Backup ไฟล์ login.html เดิม
- ✅ อัพโหลด login.html ใหม่
- ✅ ตรวจสอบขนาดไฟล์ (~6 KB)

### Post-Upload
- ✅ ตั้งค่า Walled Garden
- ✅ ทดสอบเชื่อมต่อ WiFi
- ✅ ตรวจสอบหน้า login และพื้นหลัง
- ✅ เช็ค Console log (F12)

---

## 🎯 Version

**Phase**: 1
**Date**: 2025-11-12
**Status**: ✅ Ready for Production

---

**คำเตือน**: ไฟล์นี้ถูกแก้ไขให้ทำงานร่วมกับ Django API Server อย่าอัพโหลดไฟล์ login.html เวอร์ชันอื่นทับไฟล์นี้
