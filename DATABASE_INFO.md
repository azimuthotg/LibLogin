# 📊 Database Configuration

ระบบ LibLogin ใช้ **SQLite3** เป็นฐานข้อมูล

---

## ✅ SQLite3 Configuration

### ข้อมูลพื้นฐาน

| รายการ | ค่า |
|--------|-----|
| **Database Engine** | SQLite3 |
| **Database File** | `db.sqlite3` |
| **Location** | `/path/to/LibLogin/db.sqlite3` |
| **Initial Size** | ~144 KB |
| **Built-in** | ไม่ต้องติดตั้ง Database Server |

### Configuration ใน settings.py

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## 💡 ทำไมเลือก SQLite?

### ✅ ข้อดี

1. **ไม่ต้องติดตั้งเพิ่ม**
   - SQLite มาพร้อม Python อยู่แล้ว
   - ไม่ต้องติดตั้ง MySQL/PostgreSQL Server

2. **การจัดการง่าย**
   - ฐานข้อมูลเป็นไฟล์เดียว (`db.sqlite3`)
   - ย้ายง่าย แค่ copy ไฟล์

3. **Backup ง่าย**
   ```powershell
   # Backup
   copy db.sqlite3 backup\db_backup.sqlite3

   # Restore
   copy backup\db_backup.sqlite3 db.sqlite3
   ```

4. **เหมาะกับการใช้งาน**
   - ระบบ LibLogin ส่วนใหญ่เป็น **read operations** (ดึงรูปพื้นหลัง)
   - **Write operations** น้อย (เฉพาะตอนบรรณารักษ์อัปโหลดรูป)
   - รองรับผู้ใช้ 100-500 คนพร้อมกันได้สบาย

5. **Performance ดี**
   - เร็วสำหรับ read operations
   - ไม่มี network latency (ไฟล์อยู่ใน local disk)

### ⚠️ ข้อจำกัด (ไม่เป็นปัญหาสำหรับระบบนี้)

1. **Concurrent Writes**
   - Write พร้อมกันได้จำกัด
   - แต่ระบบนี้มี write น้อยมาก (เฉพาะอัปโหลดรูป)

2. **ขนาด Database**
   - เหมาะกับข้อมูลไม่เกิน 1-2 GB
   - ระบบนี้มีแค่รูปพื้นหลังและ metadata น้อยมาก

---

## 📦 Database Structure

### Tables

1. **auth_user** - ผู้ใช้งานระบบ (admin, librarians)
2. **api_backgroundimage** - รูปพื้นหลัง
3. **api_systemsettings** - การตั้งค่าระบบ
4. **Django built-in tables** - sessions, permissions, etc.

### ข้อมูลในระบบ

- **Users**: น้อยมาก (1-5 users)
- **Background Images**: 5-20 รูป (ประมาณ 2-5 MB ต่อรูป)
- **System Settings**: 1 record

**ประมาณการขนาด:** < 100 MB

---

## 🔄 Backup Strategy

### Automatic Backup (ใช้ backup.bat)

```batch
@echo off
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
copy db.sqlite3 "backups\db_%TIMESTAMP%.sqlite3"
```

### Manual Backup

```powershell
# Backup database
copy db.sqlite3 backups\db_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sqlite3

# Backup media files
xcopy media backups\media_backup\ /E /I /Y
```

### Scheduled Backup

ตั้ง Windows Task Scheduler รัน `backup.bat` ทุกวันเวลา 02:00 AM

---

## 🔧 Database Management

### View Database

ใช้เครื่องมือ:
- **DB Browser for SQLite** (แนะนำ)
  - ดาวน์โหลด: https://sqlitebrowser.org/
  - เปิดไฟล์ `db.sqlite3` เพื่อดูข้อมูล

### Django Admin

```powershell
# Django Shell
python manage.py shell

# ดูข้อมูล
>>> from api.models import BackgroundImage
>>> BackgroundImage.objects.all()
>>> BackgroundImage.objects.filter(is_active=True)
```

### Database Reset (ระวัง!)

```powershell
# ลบ database เก่า
del db.sqlite3

# สร้างใหม่
python manage.py migrate
python manage.py createsuperuser
```

---

## 📈 Performance Tips

### 1. Regular Maintenance

```powershell
# Optimize database (ทุก 1-2 เดือน)
python manage.py shell
>>> from django.db import connection
>>> connection.cursor().execute('VACUUM')
```

### 2. ลบรูปเก่าที่ไม่ใช้

- เข้า Web Interface → Background Images
- ลบรูปที่ไม่ใช้แล้ว
- จะลด database size

### 3. Backup แล้วลบ backup เก่า

- เก็บ backup ไว้ 30 วัน
- backup.bat มี auto-cleanup อยู่แล้ว

---

## 🚀 Migration to MySQL (ถ้าจำเป็นในอนาคต)

### เมื่อไหร่ควรเปลี่ยนเป็น MySQL?

- มีผู้ใช้พร้อมกัน > 500 คน
- มี concurrent writes สูง
- ต้องการ replication/clustering
- Database size > 1 GB

### วิธีย้าย

```powershell
# 1. Export data
python manage.py dumpdata > data_backup.json

# 2. แก้ไข settings.py เป็น MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'liblogin_db',
        'USER': 'liblogin_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# 3. ติดตั้ง mysqlclient
pip install mysqlclient

# 4. Import data
python manage.py migrate
python manage.py loaddata data_backup.json
```

---

## ✅ สรุป

| รายการ | ค่า |
|--------|-----|
| **Database** | SQLite3 ✅ |
| **ไฟล์** | db.sqlite3 |
| **ขนาดเริ่มต้น** | ~144 KB |
| **Backup** | Copy ไฟล์ db.sqlite3 |
| **เหมาะกับ** | ระบบ LibLogin ขนาดเล็ก-กลาง |
| **ผู้ใช้พร้อมกัน** | 100-500 คน |

**🎉 พร้อมใช้งาน ไม่ต้องติดตั้ง Database Server เพิ่ม!**
