# 🔧 แก้ไข Error 404: Hotspot Pages Not Found

## ปัญหา
```
Page not found (404)
Request URL: http://202.29.55.222:8291/hotspot/login/
```

## สาเหตุ
Production Server ยังไม่มี code ล่าสุดที่เพิ่ม hotspot views และ templates

## วิธีแก้ไข (บน Windows Server)

### ขั้นตอนที่ 1: Stop Service
```powershell
cd C:\inetpub\wwwroot\Liblogin
nssm stop LibLogin
```

### ขั้นตอนที่ 2: Pull Code ล่าสุด
```powershell
git pull origin main
```

**ตรวจสอบว่า pull ได้ไฟล์เหล่านี้:**
- `webapp/views.py` (มี hotspot views)
- `webapp/urls.py` (มี hotspot URLs)
- `webapp/templates/webapp/hotspot_login.html`
- `webapp/templates/webapp/hotspot_logout.html`
- `webapp/templates/webapp/hotspot_status.html`
- `webapp/templates/webapp/hotspot_error.html`
- `webapp/static/css/hotspot.css`

### ขั้นตอนที่ 3: Collect Static Files
```powershell
python manage.py collectstatic --noinput
```

**ตรวจสอบว่า static files ถูก copy:**
```powershell
dir staticfiles\css\hotspot.css
```

### ขั้นตอนที่ 4: Restart Service
```powershell
nssm start LibLogin
```

### ขั้นตอนที่ 5: ตรวจสอบ Service Status
```powershell
nssm status LibLogin
```

**ควรได้:** `SERVICE_RUNNING`

### ขั้นตอนที่ 6: ทดสอบใหม่
เปิด Browser:
```
http://202.29.55.222:8291/hotspot/login/
```

---

## ตรวจสอบว่า Git Pull ได้อะไรบ้าง

```powershell
git log -1 --stat
```

**ควรเห็น:**
```
commit 5714f7a...
Add comprehensive testing documentation

 3 files changed, 973 insertions(+)
 create mode 100644 TESTING_CHECKLIST.md
 create mode 100644 TESTING_GUIDE.md
 create mode 100644 TEST_RESULTS.md
```

**และ commit ก่อนหน้า:**
```powershell
git log --oneline -5
```

**ควรเห็น commits เกี่ยวกับ hotspot:**
- Add MikroTik Hotspot integration with 4 pages
- Create hotspot templates and styling
- Add hotspot views

---

## ถ้ายังไม่ได้ Pull Hotspot Code

### ตรวจสอบ Branch
```powershell
git branch -a
```

**ตรวจสอบว่าอยู่ที่ main branch:**
```powershell
git branch
```

**ควรเห็น:**
```
* main
```

### ดู Remote Status
```powershell
git remote -v
git fetch origin
git status
```

**ถ้าเห็นว่า behind:**
```
Your branch is behind 'origin/main' by X commits
```

**ให้ pull:**
```powershell
git pull origin main
```

---

## ถ้า Git Pull ไม่ได้ (มี Conflicts)

### วิธีที่ 1: Stash Changes แล้ว Pull
```powershell
git stash
git pull origin main
git stash pop
```

### วิธีที่ 2: Reset แล้ว Pull (ระวัง: จะสูญเสีย local changes)
```powershell
git reset --hard origin/main
git pull origin main
```

### วิธีที่ 3: Clone ใหม่ (ถ้าทำอะไรไม่ได้)
```powershell
cd C:\inetpub\wwwroot\
git clone https://github.com/azimuthotg/LibLogin.git Liblogin_new

# Backup old database และ media
xcopy Liblogin\db.sqlite3 Liblogin_new\
xcopy Liblogin\media Liblogin_new\media\ /E /I

# เปลี่ยนชื่อ
rename Liblogin Liblogin_old
rename Liblogin_new Liblogin

# Setup service ใหม่
cd Liblogin
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py collectstatic --noinput

# Restart service
nssm restart LibLogin
```

---

## ตรวจสอบว่า Views และ Templates มีอยู่

### ตรวจสอบ Views
```powershell
findstr /C:"def hotspot_login" webapp\views.py
findstr /C:"def hotspot_logout" webapp\views.py
findstr /C:"def hotspot_status" webapp\views.py
findstr /C:"def hotspot_error" webapp\views.py
```

**ควรเห็น:**
```
def hotspot_login(request):
def hotspot_logout(request):
def hotspot_status(request):
def hotspot_error(request):
```

### ตรวจสอบ Templates
```powershell
dir webapp\templates\webapp\hotspot_*.html
```

**ควรเห็น:**
```
hotspot_login.html
hotspot_logout.html
hotspot_status.html
hotspot_error.html
```

### ตรวจสอบ CSS
```powershell
dir webapp\static\css\hotspot.css
```

**ควรเห็นไฟล์ขนาดประมาณ 6.5KB**

---

## ตรวจสอบ Logs (ถ้ายังมีปัญหา)

### Django Logs
```powershell
type logs\error.log | more
```

### NSSM Service Logs
```powershell
type C:\ProgramData\NSSM\LibLogin\out.log | more
type C:\ProgramData\NSSM\LibLogin\err.log | more
```

**มองหา error messages เช่น:**
- `ImportError`
- `TemplateDoesNotExist`
- `NoReverseMatch`
- `ViewDoesNotExist`

---

## ทดสอบแบบ Manual (ถ้า NSSM มีปัญหา)

### รัน Development Server ชั่วคราว
```powershell
cd C:\inetpub\wwwroot\Liblogin
venv\Scripts\activate
python manage.py runserver 0.0.0.0:8291
```

**เปิด Browser ทดสอบ:**
```
http://202.29.55.222:8291/hotspot/login/
```

**ถ้าทำงานได้:**
- แสดงว่า code ถูกต้อง
- ปัญหาอยู่ที่ NSSM service configuration

**ถ้ายังไม่ได้:**
- ดู error message ใน terminal
- แก้ไขตาม error message

---

## สรุป Checklist

- [ ] Stop NSSM service
- [ ] Git pull origin main
- [ ] ตรวจสอบว่าได้ไฟล์ hotspot views/templates
- [ ] Collect static files
- [ ] Start NSSM service
- [ ] ทดสอบ URL: http://202.29.55.222:8291/hotspot/login/

**ถ้าผ่านทุกขั้นตอน → ควรแก้ไขได้! ✅**

---

## ติดต่อช่วยเหลือ

**ถ้ายังแก้ไม่ได้ ให้ส่งข้อมูลเหล่านี้มา:**

1. Output จาก `git log --oneline -10`
2. Output จาก `git status`
3. Output จาก `nssm status LibLogin`
4. Screenshot ของ error 404
5. Content จาก `logs\error.log` (20 บรรทัดล่าสุด)

```powershell
# รวบรวมข้อมูล debug
git log --oneline -10 > debug_info.txt
git status >> debug_info.txt
nssm status LibLogin >> debug_info.txt
type logs\error.log | select -last 20 >> debug_info.txt

# ส่งไฟล์ debug_info.txt มา
```
