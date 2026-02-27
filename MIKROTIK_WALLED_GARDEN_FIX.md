# 🔧 MikroTik Walled Garden Configuration สำหรับ Port 8291

## ปัญหา
- ✅ ใส่แค่ `dst-host=202.29.55.222` เข้าได้ (แต่เข้า port 80)
- ❌ พอใส่ `dst-port=8291` เข้าไม่ได้

## สาเหตุ
Django Server รันที่ port **8291** ไม่ใช่ port 80 ปกติ จึงต้องเพิ่ม Walled Garden rule สำหรับ port นี้โดยเฉพาะ

---

## ✅ วิธีแก้ไขที่ถูกต้อง

### วิธีที่ 1: เพิ่ม Walled Garden สำหรับ Port 8291 (แนะนำ)

```
/ip hotspot walled-garden
add dst-host=202.29.55.222 dst-port=8291 protocol=tcp action=accept comment="Django Server Port 8291"
```

**หรือใช้คำสั่งเต็ม:**
```
/ip hotspot walled-garden
add dst-address=202.29.55.222 dst-port=8291 protocol=tcp action=accept comment="Django Login Server"
```

### วิธีที่ 2: เพิ่มทั้ง IP และ Port แยกกัน

```
/ip hotspot walled-garden
add dst-host=202.29.55.222 comment="Django Server IP"
add dst-address=202.29.55.222 dst-port=8291 protocol=tcp comment="Django Server Port 8291"
```

### วิธีที่ 3: เปิด Port Range (ถ้าต้องการ)

```
/ip hotspot walled-garden
add dst-host=202.29.55.222 dst-port=8000-9000 protocol=tcp comment="Django Server Port Range"
```

---

## 🔍 ตรวจสอบ Configuration

### ดู Walled Garden ทั้งหมด
```
/ip hotspot walled-garden print
```

**ผลลัพธ์ที่ถูกต้องควรเห็น:**
```
Flags: X - disabled, D - dynamic
 #   DST-ADDRESS      DST-PORT PROTOCOL  ACTION  COMMENT
 0   202.29.55.222    8291     tcp       accept  "Django Server Port 8291"
```

### ลบ Rule เก่า (ถ้าผิด)
```
/ip hotspot walled-garden print
# ดูเลขที่ของ rule ที่ต้องการลบ (เช่น #0, #1)

/ip hotspot walled-garden remove 0
```

---

## 🧪 ทดสอบ

### ทดสอบจากเครื่อง Client (ก่อน Login)

1. **เชื่อมต่อ WiFi ของ MikroTik**
2. **เปิด Browser**
3. **ทดสอบ URL:**
   ```
   http://202.29.55.222:8291/hotspot/login/
   ```

**ควรเห็น:**
- ✅ หน้า Login ของ Django
- ✅ มีรูปพื้นหลัง
- ✅ มีข้อความ "ยินดีต้อนรับ"

### ทดสอบ API
```
http://202.29.55.222:8291/api/login-background/
```

**ควรได้ JSON:**
```json
{
  "success": true,
  "imageUrl": "http://202.29.55.222:8291/media/backgrounds/xxx.jpg",
  "title": "..."
}
```

### ทดสอบรูปพื้นหลัง
```
http://202.29.55.222:8291/media/backgrounds/arc_open_house1.jpg
```

**ควรเห็นรูปภาพ**

---

## 📊 Configuration สมบูรณ์

```
# MikroTik Walled Garden Configuration
/ip hotspot walled-garden

# Server IP + Port
add dst-address=202.29.55.222 dst-port=8291 protocol=tcp action=accept comment="Django Login Server"

# Media files (สำหรับรูปพื้นหลัง)
add dst-address=202.29.55.222 protocol=tcp action=accept comment="Django Media Files"

# (Optional) ถ้าใช้ HTTPS ในอนาคต
# add dst-address=202.29.55.222 dst-port=443 protocol=tcp action=accept comment="Django HTTPS"
```

---

## 🔧 การ Debug

### ปัญหา: ยังเข้าไม่ได้
```
# 1. ตรวจสอบ Walled Garden
/ip hotspot walled-garden print detail

# 2. ตรวจสอบ Firewall
/ip firewall filter print where dst-port=8291

# 3. ทดสอบ ping
/ping 202.29.55.222

# 4. ทดสอบ telnet (เช็ค port)
/tool telnet 202.29.55.222 8291
```

### ปัญหา: Redirect ไม่ทำงาน
```
# ตรวจสอบ Hotspot Profile
/ip hotspot profile print

# ตรวจสอบว่าใช้ html-directory ไหน
# ควรเป็น "hotspot" หรือ "default"

# ตรวจสอบว่ามีไฟล์ redirect หรือไม่
/file print where name~"login.html"
```

---

## 📝 Checklist

- [ ] เพิ่ม Walled Garden rule สำหรับ IP
- [ ] เพิ่ม Walled Garden rule สำหรับ Port 8291
- [ ] ทดสอบเข้า `http://202.29.55.222:8291/hotspot/login/` (ก่อน login)
- [ ] ทดสอบเข้า API endpoint
- [ ] ทดสอบโหลดรูปพื้นหลัง
- [ ] Upload ไฟล์ redirect (login.html, logout.html, status.html, error.html)
- [ ] ทดสอบ redirect จาก MikroTik

---

## 🎯 Walled Garden Rules ที่แนะนำ (สำเนา)

```
/ip hotspot walled-garden
add dst-address=202.29.55.222 dst-port=8291 protocol=tcp action=accept comment="Django Port 8291"
add dst-address=202.29.55.222 protocol=tcp action=accept comment="Django Server (All ports for media)"
```

**หมายเหตุ:**
- Rule แรก: สำหรับ Django Server port 8291
- Rule ที่สอง: สำหรับ Media files (รูปพื้นหลัง) ที่อาจใช้ port เดียวกัน

---

## 🚀 คำสั่งรวม (Copy-Paste ได้เลย)

```
/ip hotspot walled-garden
add dst-address=202.29.55.222 dst-port=8291 protocol=tcp action=accept comment="Django Login Port 8291"
add dst-address=202.29.55.222 protocol=tcp action=accept comment="Django All Ports"
```

**ทดสอบ:**
```
# จาก MikroTik Terminal
/tool fetch url="http://202.29.55.222:8291/api/login-background/" mode=http
```

**ควรได้ผลลัพธ์:**
```
status: finished
```

---

## ⚠️ หมายเหตุสำคัญ

1. **Protocol ต้องเป็น TCP** (ไม่ใช่ UDP)
2. **Port ต้องเป็น 8291** (ไม่ใช่ 80)
3. **Action ต้องเป็น accept**
4. ถ้าใช้ `dst-host` ต้องมี DNS resolution (แนะนำใช้ `dst-address` แทน)

---

## 📸 ตัวอย่าง Output ที่ถูกต้อง

```
/ip hotspot walled-garden print
Flags: X - disabled, D - dynamic
 #   DST-ADDRESS      DST-PORT PROTOCOL  ACTION  COMMENT
 0   202.29.55.222    8291     tcp       accept  "Django Port 8291"
 1   202.29.55.222               tcp       accept  "Django All Ports"
```

**สถานะ:** ✅ Ready for testing!
