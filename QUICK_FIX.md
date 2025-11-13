# 🚀 Quick Fix: Git Merge Conflict

## ปัญหา
```
error: Your local changes to the following files would be overwritten by merge:
        backend/settings.py
Please commit your changes or stash them before you merge.
```

## แก้ไขด่วน (เลือก 1 วิธี)

### วิธีที่ 1: Stash Changes (แนะนำ - ปลอดภัย)
```powershell
# เก็บ local changes ไว้ชั่วคราว
git stash

# Pull code ใหม่
git pull origin main

# เอา local changes กลับมา
git stash pop
```

**ถ้ามี conflict หลัง stash pop:**
```powershell
# ดูว่า conflict ที่ไหน
git status

# แก้ไขไฟล์ backend/settings.py ด้วยมือ (เอาส่วนที่ต้องการ)
# หรือใช้ theirs (เอาจาก remote)
git checkout --theirs backend/settings.py

# Add และ commit
git add backend/settings.py
git commit -m "Resolve merge conflict"
```

---

### วิธีที่ 2: ดูว่าแก้อะไรใน settings.py
```powershell
# ดู changes ที่ทำไว้
git diff backend/settings.py
```

**ถ้าเป็นการแก้ไข ALLOWED_HOSTS หรือ DEBUG:**
```powershell
# Backup settings.py
copy backend\settings.py backend\settings.py.backup

# Pull code
git checkout backend/settings.py
git pull origin main

# เปรียบเทียบและคัดลอกการตั้งค่าที่ต้องการจาก backup กลับมา
```

---

### วิธีที่ 3: Reset แล้ว Pull (ง่ายที่สุด - แต่จะเสีย local changes)
```powershell
# ⚠️ คำเตือน: จะสูญเสียการแก้ไขใน backend/settings.py

# Backup settings.py ก่อน
copy backend\settings.py C:\Temp\settings.py.backup

# Reset
git reset --hard origin/main

# Pull
git pull origin main

# คัดลอกการตั้งค่าสำคัญจาก backup กลับมา (ถ้าจำเป็น)
notepad C:\Temp\settings.py.backup
notepad backend\settings.py
```

---

## ขั้นตอนที่แนะนำ (วิธีที่ 1 - Stash)

```powershell
# 1. เก็บ changes
git stash

# 2. Pull code
git pull origin main

# 3. เอา changes กลับมา
git stash pop

# 4. ถ้ามี conflict ให้ใช้ theirs
git checkout --theirs backend/settings.py
git add backend/settings.py

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Restart service
nssm restart LibLogin

# 7. ทดสอบ
```

---

## การตั้งค่าที่สำคัญใน backend/settings.py (Production)

**อย่าลืมตรวจสอบหลัง pull:**

```python
# backend/settings.py

DEBUG = False  # Production ต้องเป็น False

ALLOWED_HOSTS = [
    '202.29.55.222',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'http://202.29.55.222:8291',
    'http://localhost:8291',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = 'static/'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = 'media/'
```

---

## หลังจาก Pull แล้ว

```powershell
# Collect static files
python manage.py collectstatic --noinput

# Restart service
nssm restart LibLogin

# ตรวจสอบ status
nssm status LibLogin

# ทดสอบ
start http://202.29.55.222:8291/hotspot/login/
```

---

## ถ้ายังไม่ได้ - ตรวจสอบ Settings

```powershell
# เปิดไฟล์ settings.py
notepad backend\settings.py
```

**ตรวจสอบว่ามี:**
1. `STATIC_ROOT = BASE_DIR / 'staticfiles'`
2. `ALLOWED_HOSTS` มี `'202.29.55.222'`
3. `INSTALLED_APPS` มี `'webapp'` และ `'api'`

---

## Debug: ดูว่า Pull ได้อะไรบ้าง

```powershell
# ดู commits ล่าสุด
git log --oneline -5

# ดู files ที่เปลี่ยน
git log -1 --stat

# ตรวจสอบว่ามี hotspot views หรือไม่
findstr /C:"def hotspot_login" webapp\views.py
```

**ควรเห็น:**
```
def hotspot_login(request):
```

---

## คำสั่งรวม (Copy-Paste ได้เลย)

```powershell
# All-in-one command
git stash && git pull origin main && git stash pop && git checkout --theirs backend/settings.py && git add backend/settings.py && python manage.py collectstatic --noinput && nssm restart LibLogin && timeout 5 && start http://202.29.55.222:8291/hotspot/login/
```

**หรือทีละขั้นตอน:**
```powershell
git stash
git pull origin main
git stash pop
python manage.py collectstatic --noinput
nssm restart LibLogin
```
