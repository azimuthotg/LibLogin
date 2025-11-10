# LibLogin Deployment Guide

คู่มือการ Deploy ระบบ LibLogin บน Production Server

## ข้อกำหนดของ Server

### System Requirements
- Ubuntu 20.04 LTS หรือใหม่กว่า
- Python 3.8+
- 2GB RAM ขึ้นไป
- 10GB Storage

### Software Required
- Python 3
- pip
- Git
- Nginx (สำหรับ production)
- MySQL/PostgreSQL (ถ้าไม่ใช้ SQLite)

---

## ขั้นตอนการติดตั้ง

### 1. เตรียม Server

```bash
# อัปเดตระบบ
sudo apt update
sudo apt upgrade -y

# ติดตั้ง Python และ dependencies
sudo apt install python3 python3-pip python3-venv git nginx -y

# ติดตั้ง MySQL (optional)
sudo apt install mysql-server libmysqlclient-dev -y
```

### 2. Clone Repository

```bash
cd /var/www/
sudo git clone https://github.com/azimuthotg/LibLogin.git
cd LibLogin
sudo chown -R $USER:$USER /var/www/LibLogin
```

### 3. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Configure Settings

แก้ไขไฟล์ `backend/settings.py`:

```python
# Security
DEBUG = False
SECRET_KEY = 'your-new-secret-key-here'  # สร้าง key ใหม่
ALLOWED_HOSTS = ['your-server-ip', 'your-domain.com']

# CORS (Production)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://your-mikrotik-ip",
    "http://192.168.1.1",
]

# Database (ถ้าใช้ MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'liblogin_db',
        'USER': 'liblogin_user',
        'PASSWORD': 'your-db-password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 6. Create Systemd Service

สร้างไฟล์ `/etc/systemd/system/liblogin.service`:

```ini
[Unit]
Description=LibLogin Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/LibLogin
Environment="PATH=/var/www/LibLogin/venv/bin"
ExecStart=/var/www/LibLogin/venv/bin/gunicorn \
          --workers 3 \
          --bind 0.0.0.0:8000 \
          backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

เปิดใช้งาน service:

```bash
sudo systemctl daemon-reload
sudo systemctl start liblogin
sudo systemctl enable liblogin
sudo systemctl status liblogin
```

### 7. Configure Nginx

สร้างไฟล์ `/etc/nginx/sites-available/liblogin`:

```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/LibLogin/staticfiles/;
    }

    location /media/ {
        alias /var/www/LibLogin/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

เปิดใช้งาน site:

```bash
sudo ln -s /etc/nginx/sites-available/liblogin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Certificate (HTTPS)

```bash
# ติดตั้ง Certbot
sudo apt install certbot python3-certbot-nginx -y

# สร้าง SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## การจัดการระบบ

### Start/Stop Service

```bash
# Start
sudo systemctl start liblogin

# Stop
sudo systemctl stop liblogin

# Restart
sudo systemctl restart liblogin

# Status
sudo systemctl status liblogin
```

### ดู Logs

```bash
# Gunicorn logs
sudo journalctl -u liblogin -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Update Code

```bash
cd /var/www/LibLogin
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart liblogin
```

---

## การตั้งค่า Firewall

```bash
# อนุญาต HTTP, HTTPS, SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Backup & Restore

### Backup Database (SQLite)

```bash
cp db.sqlite3 db.sqlite3.backup
```

### Backup Media Files

```bash
tar -czf media_backup.tar.gz media/
```

### Restore

```bash
cp db.sqlite3.backup db.sqlite3
tar -xzf media_backup.tar.gz
```

---

## Troubleshooting

### ปัญหา: Permission Denied

```bash
sudo chown -R www-data:www-data /var/www/LibLogin
sudo chmod -R 755 /var/www/LibLogin
```

### ปัญหา: Static Files ไม่แสดง

```bash
python manage.py collectstatic --clear --noinput
sudo systemctl restart nginx
```

### ปัญหา: Database Connection Error

ตรวจสอบ MySQL service:
```bash
sudo systemctl status mysql
```

### ปัญหา: 502 Bad Gateway

ตรวจสอบ Gunicorn service:
```bash
sudo systemctl status liblogin
sudo journalctl -u liblogin -n 50
```

---

## หลังจาก Deploy แล้ว

1. **ทดสอบ API Endpoint:**
   ```bash
   curl http://your-server-ip/api/login-background/
   ```

2. **เข้าใช้งาน Web Interface:**
   ```
   http://your-server-ip/login/
   ```

3. **ตั้งค่า MikroTik:**
   - แก้ไข `mikrotik_login.html`
   - เปลี่ยน `API_BASE_URL` เป็น `http://your-server-ip`
   - อัปโหลดไปยัง MikroTik

4. **ทดสอบระบบ:**
   - อัปโหลดรูปพื้นหลัง
   - ตั้งเป็น active
   - ทดสอบเชื่อมต่อ WiFi

---

## Performance Tuning

### Gunicorn Workers

จำนวน workers = (2 x CPU cores) + 1

```bash
# สำหรับ 2 CPU cores
--workers 5
```

### Database Optimization

ถ้าใช้ SQLite บน production ที่มี traffic สูง แนะนำเปลี่ยนเป็น PostgreSQL หรือ MySQL

---

## Monitoring

### ติดตั้ง Monitoring Tools (Optional)

```bash
# htop - monitor processes
sudo apt install htop

# netdata - system monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

---

## Security Checklist

- [ ] DEBUG = False
- [ ] ตั้ง SECRET_KEY ใหม่
- [ ] กำหนด ALLOWED_HOSTS
- [ ] ตั้งค่า CORS ให้เฉพาะเจาะจง
- [ ] ติดตั้ง SSL Certificate
- [ ] ตั้งค่า Firewall
- [ ] ปรับ permissions ของไฟล์
- [ ] เปลี่ยนรหัส admin password
- [ ] Backup ฐานข้อมูลเป็นประจำ

---

## Contact & Support

หากมีปัญหาในการ deploy สามารถตรวจสอบ logs หรือติดต่อผู้ดูแลระบบ
