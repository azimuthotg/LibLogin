# LibLogin — CLAUDE.md

## Project Overview
Library WiFi Login Management System — ระบบจัดการหน้า Login WiFi Hotspot สำหรับห้องสมุด
Serves MikroTik hotspot login pages with dynamic backgrounds, templates, and content.

## Tech Stack
- **Backend:** Django 5.2.8, Django REST Framework, SQLite3
- **Server:** Waitress (dev: port 8001, prod: port 8002)
- **Frontend:** Bootstrap 5, vanilla JS, Google Fonts (Kanit, Sarabun)
- **Django package name:** `backend` (`backend.settings`, `backend.wsgi`)

## Project Structure
```
LibLogin/
├── backend/          # Django project settings, urls, wsgi
├── api/              # REST API (DRF) — models, serializers, views, urls
├── webapp/           # Frontend admin — views, templates, static, urls
│   ├── templates/webapp/   # All HTML templates
│   └── static/webapp/js/   # JS files (hotspot-management.js etc.)
├── hotspot/          # MikroTik login page folder (default)
├── hotspot_*/        # Additional hotspot folders (hotspot_lab, hotspot_lan, etc.)
├── media/            # Uploaded files (logos, background images)
├── deploy/           # Deployment scripts (waitress_serve.py)
├── doc/              # Deployment guides
├── venv/             # Python virtual environment
└── db.sqlite3        # SQLite database
```

## Key Models (api/models.py)
| Model | Purpose |
|-------|---------|
| `Hotspot` | MikroTik hotspot configurations |
| `Department` | หน่วยงาน — groups users with hotspot access |
| `BackgroundImage` | Background images per hotspot |
| `TemplateConfig` | Login page template layouts |
| `SlideContent` | Slide/carousel content per hotspot |
| `CardContent` | Card content per hotspot |
| `SystemSettings` | Library name, logo, refresh interval |
| `PageImpression` / `DailyReachStats` | Analytics/monitoring |
| `LandingPageURL` | Custom landing page URLs per hotspot |

## Access Control
- `is_staff=True` → full access to everything
- Regular user + Department → sees only content for department's hotspots + default content (`hotspot_name=None`)
- Regular user + no Department → sees only default content
- Helper functions in `webapp/views.py`:
  - `get_user_allowed_hotspots(user)` → returns `None` (staff) or list of hotspot_names
  - `hotspot_filter_q(allowed)` → Q object for filtering content querysets

## URL Structure
```
/               → dashboard
/login/         → admin login
/logout/        → logout
/backgrounds/   → background image management
/templates/     → template management
/slides/        → slide content management
/cards/         → card content management
/hotspots/      → hotspot management (API-based via hotspot-management.js)
/departments/   → department management
/users/         → user management
/settings/      → system settings (library info, logo, refresh interval)
/monitoring/    → statistics / monitoring
/landing-pages/ → landing page URL management

/api/           → REST API (DRF)
  /api/hotspots/                    → Hotspot CRUD
  /api/hotspots/{id}/test_connection/ → test hotspot folder/config
  /api/login-background/            → public: get active background
  /api/slide-content/               → public: get slide content
  /api/template-config/             → public: get template config
  /api/hotspot-choices/             → get hotspot list (filtered by user)
  /api/landing-url/                 → get landing URL
  /api/track-impression/            → record page impression

/hotspot/login/   → MikroTik hotspot login page
/hotspot/logout/  → MikroTik hotspot logout page
/hotspot/status/  → MikroTik hotspot status page
/hotspot/error/   → MikroTik hotspot error page
```

## Development Commands
```bash
# Run dev server (port 8001)
venv/bin/python manage.py runserver 8001

# Apply migrations
venv/bin/python manage.py migrate

# Create migration after model change
venv/bin/python manage.py makemigrations

# Create superuser
venv/bin/python manage.py createsuperuser

# Collect static files (production)
venv/bin/python manage.py collectstatic --noinput
```

## Environment / .env (production)
```
SECRET_KEY=<strong-secret>
DEBUG=False
ALLOWED_HOSTS=lib.npu.ac.th,localhost
FORCE_SCRIPT_NAME=/liblogin
STATIC_URL=/liblogin/static/
MEDIA_URL=/liblogin/media/
```
- Dev mode: no `.env` needed — defaults to `DEBUG=False`, `ALLOWED_HOSTS=localhost`
- `FORCE_SCRIPT_NAME` is critical for sub-path deployment (`/liblogin/`)

## Production Deployment
- **Server:** lib.npu.ac.th (Windows Server 2019 + IIS + ARR)
- **Service:** NSSM service `LibLogin` running `deploy/waitress_serve.py` on port 8002
- **Path prefix:** `/liblogin/`
- **Static/Media:** IIS virtual directories pointing to `staticfiles/` and `media/`
- **Guide:** `doc/server_deployment_Liblog_guide.md`

## Important Patterns
- All admin views use `@login_required` decorator
- POST guards in views check `request.user.is_staff` before allowing mutations
- Hotspot CRUD is via REST API only (no form POST) — uses `hotspot-management.js`
- `hotspot-management.js` calls `/api/hotspots/` and relies on element IDs:
  `hotspotsTableBody`, `add_hotspot_name`, `add_display_name`, `add_is_active`,
  `edit_hotspot_id`, `edit_hotspot_name`, `edit_display_name`, `edit_is_active`,
  `delete_hotspot_id`, `delete_hotspot_name`, `refreshCountdown`
- Templates extend `webapp/base.html` — provides sidebar, Bootstrap 5, BI icons, fonts

## Migration History
- `0001–0011`: BackgroundImage, TemplateConfig, Slides, Cards, Hotspot, Settings, etc.
- `0012`: Added `Department` model
- `0013`: Added `Department.users` ManyToManyField (department-based access control)
