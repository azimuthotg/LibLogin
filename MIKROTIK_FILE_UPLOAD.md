# 📤 อัปโหลดไฟล์ Redirect ไปยัง MikroTik

## ขั้นตอนที่ 1: ลบไฟล์เก่า

### ผ่าน WinBox:
1. เปิด WinBox → เชื่อมต่อกับ Router
2. ไปที่เมนู **Files**
3. **ลบไฟล์เก่าทั้งหมดใน hotspot folder:**
   - ไฟล์ HTML เก่า
   - ไฟล์ CSS เก่า
   - รูปภาพเก่า (ถ้ามี)
   - โฟลเดอร์ที่ไม่ใช้แล้ว (css/, img/, font/)

### ผ่าน Terminal:
```
/file print
# ดูไฟล์ทั้งหมด หาเลขที่ของไฟล์เก่า

# ลบไฟล์ hotspot เก่า
/file remove hotspot/login.html
/file remove hotspot/logout.html
/file remove hotspot/status.html
/file remove hotspot/error.html

# ลบโฟลเดอร์เก่า (ถ้ามี)
/file remove hotspot/css
/file remove hotspot/img
/file remove hotspot/images
/file remove hotspot/font
```

---

## ขั้นตอนที่ 2: อัปโหลดไฟล์ใหม่

### ไฟล์ที่ต้องอัปโหลด (4 ไฟล์):

จากโฟลเดอร์ `C:\inetpub\wwwroot\Liblogin\mikrotik_files\`:

1. `login.html` (~500 bytes)
2. `logout.html` (~500 bytes)
3. `status.html` (~500 bytes)
4. `error.html` (~500 bytes)

### ผ่าน WinBox (แนะนำ):

1. **เปิด WinBox → Files**
2. **ไปที่โฟลเดอร์ hotspot** (double-click เข้าไป)
3. **ลากไฟล์ 4 ไฟล์** จาก `C:\inetpub\wwwroot\Liblogin\mikrotik_files\` วางลงในหน้าต่าง Files
4. **รอให้อัปโหลดเสร็จ**

**ตรวจสอบว่าไฟล์อยู่ใน:**
- `hotspot/login.html`
- `hotspot/logout.html`
- `hotspot/status.html`
- `hotspot/error.html`

### ผ่าน FTP:

```powershell
# เปิด Command Prompt หรือ PowerShell
cd C:\inetpub\wwwroot\Liblogin\mikrotik_files

ftp 192.168.x.x
# Username: admin
# Password: ********

cd hotspot
put login.html
put logout.html
put status.html
put error.html
quit
```

### ผ่าน SFTP (ถ้าเปิดไว้):

```powershell
# ใช้ WinSCP หรือ FileZilla
# เชื่อมต่อผ่าน SFTP
# อัปโหลดไฟล์ไปยัง /hotspot/
```

---

## ขั้นตอนที่ 3: ตรวจสอบไฟล์

### ผ่าน Terminal:

```
/file print where name~"hotspot"
```

**ควรเห็น:**
```
 # NAME                TYPE         SIZE
 0 hotspot             directory
 1 hotspot/login.html  html file    ~500
 2 hotspot/logout.html html file    ~500
 3 hotspot/status.html html file    ~500
 4 hotspot/error.html  html file    ~500
```

### ดูเนื้อหาไฟล์:

```
/file print file=test.txt where name="hotspot/login.html"
/file print
# เปิดไฟล์ test.txt ดูว่ามี redirect URL ถูกต้อง
```

---

## ขั้นตอนที่ 4: ตั้งค่า Hotspot Profile

### ตรวจสอบว่าใช้ directory ไหน:

```
/ip hotspot profile print
```

**ควรเห็น:**
```
name="hsprof1" html-directory=hotspot ...
```

### ถ้ายังไม่ได้ตั้งค่า ให้รัน:

```
/ip hotspot profile
set [find default=yes] html-directory=hotspot
```

**หรือระบุชื่อ profile:**

```
/ip hotspot profile
set hsprof1 html-directory=hotspot
```

---

## ขั้นตอนที่ 5: ทดสอบ

### ทดสอบ Redirect:

1. **เชื่อมต่อ WiFi MikroTik**
2. **เปิด Browser**
3. **ไปที่เว็บใดก็ได้** (เช่น google.com)
4. **ควรถูก redirect ไปยัง:**
   ```
   http://202.29.55.222:8291/hotspot/login/?link-login-only=...&link-orig=...
   ```

### ตรวจสอบว่า Redirect ทำงาน:

- ✅ เห็นหน้า Login ของ Django (ไม่ใช่ MikroTik)
- ✅ มีรูปพื้นหลัง
- ✅ มีข้อความ "ยินดีต้อนรับ"
- ✅ มีชื่อ "สำนักวิทยบริการ มหาวิทยาลัยนครพนม"

---

## 🐛 แก้ปัญหา

### ปัญหา: ยังเห็นหน้า Login เก่าของ MikroTik

**แก้ไข:**
```
# ล้าง cache ของ MikroTik
/ip hotspot profile
set [find] html-directory-override=""
set [find] html-directory=hotspot

# Restart hotspot service
/ip hotspot
disable [find]
enable [find]
```

**หรือรีสตาร์ท Router:**
```
/system reboot
```

### ปัญหา: Redirect ไม่ทำงาน

**ตรวจสอบ:**
```
# 1. ตรวจสอบไฟล์อยู่ใน hotspot folder
/file print where name~"hotspot"

# 2. ตรวจสอบ Hotspot Profile
/ip hotspot profile print

# 3. ตรวจสอบว่า Hotspot ทำงานอยู่
/ip hotspot print

# 4. ดู logs
/log print where topics~"hotspot"
```

### ปัญหา: เข้า Django ไม่ได้

**ตรวจสอบ:**
```
# 1. Walled Garden
/ip hotspot walled-garden print

# 2. Ping Django Server
/ping 202.29.55.222

# 3. Telnet ไปยัง port 8291
/tool telnet 202.29.55.222 8291
```

---

## 📋 Checklist

- [ ] ลบไฟล์เก่าใน MikroTik ทั้งหมด
- [ ] อัปโหลด login.html
- [ ] อัปโหลด logout.html
- [ ] อัปโหลด status.html
- [ ] อัปโหลด error.html
- [ ] ตรวจสอบไฟล์อยู่ใน hotspot/ folder
- [ ] ตั้งค่า html-directory=hotspot
- [ ] ตั้งค่า Walled Garden (202.29.55.222:8291)
- [ ] ทดสอบ redirect
- [ ] ทดสอบ login flow

---

## 📝 สรุป

**ไฟล์เก่าที่ควรลบ:**
- hotspot/login.html (เก่า)
- hotspot/logout.html (เก่า)
- hotspot/css/* (ถ้ามี)
- hotspot/img/* (ถ้ามี)
- hotspot/images/* (ถ้ามี)
- hotspot/font/* (ถ้ามี)

**ไฟล์ใหม่ที่ต้องอัปโหลด (จาก mikrotik_files/):**
- login.html (ใหม่ - redirect to Django)
- logout.html (ใหม่ - redirect to Django)
- status.html (ใหม่ - redirect to Django)
- error.html (ใหม่ - redirect to Django)

**ขนาดไฟล์:**
- แต่ละไฟล์ประมาณ 300-500 bytes
- รวมแค่ ~2 KB (เล็กมาก!)

**ข้อดี:**
- ✅ ไม่กิน Storage ของ MikroTik
- ✅ แก้ไขหน้าตาได้ที่ Django Server
- ✅ ไม่ต้องแตะ MikroTik อีก

---

## 🎯 คำสั่งรวมสำหรับ MikroTik Terminal

```
# ลบไฟล์เก่า
/file remove hotspot/login.html
/file remove hotspot/logout.html
/file remove hotspot/status.html
/file remove hotspot/error.html

# ตั้งค่า Profile
/ip hotspot profile set [find default=yes] html-directory=hotspot

# ตรวจสอบ Walled Garden
/ip hotspot walled-garden print

# ทดสอบ connection
/ping 202.29.55.222
```

**พร้อมอัปโหลดแล้ว! 🚀**
