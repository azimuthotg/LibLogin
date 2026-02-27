# Multi-Hotspot Architecture

## Overview
LibLogin ได้รับการปรับปรุงให้รองรับการจัดการหลาย Hotspot บน MikroTik เครื่องเดียว โดยแต่ละ Hotspot สามารถมี Template, Slides, Cards และ Background ที่แตกต่างกันได้

## ⚙️ Architecture แบบเดิม (Before)
```
MikroTik Router
└── Hotspot "hotspot"
    └── ใช้ router_id parameter แยก content

Django Server
├── /hotspot/login.html (เดียว)
└── API: ?router_id=xxx
```

**ปัญหา:**
- ใช้ router_id parameter ซึ่งไม่ตรงกับความเป็นจริง
- ไม่รองรับ VLAN-based hotspot separation
- แต่ละ hotspot ไม่สามารถมี login.html แยกกันได้

---

## ✅ Architecture ใหม่ (After)

```
MikroTik เครื่องเดียว
├── VLAN 1 → Hotspot "hotspot"      → Folder: /hotspot/
├── VLAN 2 → Hotspot "hotspot_lib"  → Folder: /hotspot_lib/
└── VLAN 3 → Hotspot "hotspot_dorm" → Folder: /hotspot_dorm/

Django Server (202.29.55.222:8291)
├── /hotspot/login.html
├── /hotspot_lib/login.html
├── /hotspot_dorm/login.html
└── API: ?hotspot_name=xxx (auto-detect from URL path)
```

**ข้อดี:**
- แต่ละ VLAN มี hotspot profile แยกกัน
- แต่ละ hotspot มี folder และ login.html แยกกัน
- ใช้ Django Backend ตัวเดียวกัน (API centralized)
- Auto-detect hotspot name จาก URL path

---

## 🗂️ Database Schema Changes

### Models ที่เปลี่ยนแปลง:
1. **BackgroundImage**
   - `router_id` → `hotspot_name`
   - Help text: "Hotspot name (e.g., 'hotspot', 'hotspot_lib') - blank for all hotspots"

2. **TemplateConfig**
   - `router_id` → `hotspot_name`
   - One active template per hotspot

3. **SlideContent**
   - `router_id` → `hotspot_name`
   - Slides specific to each hotspot

4. **CardContent**
   - `router_id` → `hotspot_name`
   - Cards specific to each hotspot

5. **SystemSettings**
   - `default_router_id` → `default_hotspot_name`

### Migration:
```bash
python manage.py migrate
# Applied: 0005_rename_router_id_to_hotspot_name
```

---

## 📁 Folder Structure

```
LibLogin/
├── hotspot/
│   └── login.html          # Default hotspot
├── hotspot_lib/
│   └── login.html          # Library hotspot
├── hotspot_dorm/
│   └── login.html          # Dormitory hotspot
├── api/
│   ├── models.py           # Updated with hotspot_name
│   └── views.py            # Auto-detect hotspot from request
└── backend/
    └── urls.py             # Dynamic hotspot folder serving
```

---

## 🔧 How It Works

### 1. URL Path Detection
```javascript
// In login.html
function getHotspotName() {
    const path = window.location.pathname;
    // Examples:
    // /hotspot/login.html → "hotspot"
    // /hotspot_lib/login.html → "hotspot_lib"
    const match = path.match(/\/(hotspot[^\/]*)\//);
    return match ? match[1] : null;
}
```

### 2. API Request Flow
```javascript
// Auto-add hotspot_name parameter
const hotspotName = getHotspotName(); // "hotspot_lib"
const apiUrl = API_SERVER + TEMPLATE_API + '?hotspot_name=' + hotspotName;

// API returns:
// - Template for "hotspot_lib" (if exists)
// - OR default template (if no specific template)
```

### 3. Django URL Pattern
```python
# backend/urls.py
def serve_hotspot_file(request, hotspot_name, path):
    """Serve files from hotspot folders"""
    document_root = os.path.join(settings.BASE_DIR, hotspot_name)
    return serve(request, path, document_root=document_root)

urlpatterns += [
    re_path(r'^(hotspot[^/]*)/(.*)$', serve_hotspot_file),
]
```

### 4. API Priority Logic
```python
# Priority 1: Specific hotspot template
template = TemplateConfig.objects.filter(
    hotspot_name=hotspot_name,
    is_active=True
).first()

# Priority 2: Default template (fallback)
if not template:
    template = TemplateConfig.objects.filter(
        hotspot_name__isnull=True,
        is_active=True
    ).first()
```

---

## 📝 Admin Interface Changes

### Template Management
- Field: **Hotspot Name** (instead of Router ID)
- Help text: "e.g., 'hotspot', 'hotspot_lib' - leave blank for all hotspots"
- Icon: Changed from `bi-router` to `bi-hdd-network`

### Preview System
```javascript
// Preview URL now uses hotspot folder path
const hotspotPath = hotspotName || 'hotspot';
let previewUrl = '/' + hotspotPath + '/login.html?template_id=' + templateId;

// Example: /hotspot_lib/login.html?template_id=5
```

---

## 🚀 How to Add New Hotspot

### Step 1: Create Hotspot Folder
```bash
mkdir -p /path/to/LibLogin/hotspot_newname
cp hotspot/login.html hotspot_newname/login.html
```

### Step 2: Configure MikroTik
```mikrotik
# Create VLAN
/interface vlan add interface=bridge name=vlan-newname vlan-id=30

# Create IP Pool
/ip pool add name=pool-newname ranges=10.10.30.100-10.10.30.200

# Create Hotspot Profile
/ip hotspot profile
add name=hotspot_newname

# Create Hotspot Server
/ip hotspot
add address-pool=pool-newname interface=vlan-newname name=hotspot_newname profile=hotspot_newname
```

### Step 3: Create Template in Admin
1. Go to **Template Management**
2. Click **Add New Template**
3. Fill:
   - Template Name: "Library Default"
   - Component Type: "Slideshow"
   - **Hotspot Name**: `hotspot_newname`
   - Set as active: ✓
4. Save

### Step 4: Add Content
- Navigate to **Slides** or **Cards**
- Create content with **Hotspot Name**: `hotspot_newname`

---

## 🔍 API Endpoints

### Get Template Config
```
GET /api/template-config/?hotspot_name=hotspot_lib
GET /api/template-config/?template_id=5          (preview mode)
```

**Response:**
```json
{
  "success": true,
  "template_name": "Library Default",
  "left_panel_component": "slideshow",
  "slides": [...],
  "background": {...}
}
```

### Get Background Image
```
GET /api/background-image/?hotspot_name=hotspot_lib
```

---

## ⚠️ Important Notes

1. **Hotspot Name Format**: Must start with `hotspot` (e.g., `hotspot`, `hotspot_lib`, `hotspot_building3`)
2. **Folder Name = Hotspot Name**: ต้องตรงกันเสมอ
3. **Migration Required**: ต้อง run migration เพื่อ rename fields
4. **Backward Compatible**: ระบบเดิมที่ใช้ `hotspot` folder ยังทำงานได้ปกติ
5. **Fallback Logic**: ถ้าไม่มี content specific สำหรับ hotspot จะใช้ default content

---

## 📊 Example Use Cases

### Use Case 1: Library WiFi
```
Hotspot: hotspot_lib
Template: "Library Slideshow"
Slides: Library rules, opening hours, digital resources
Background: Library building image
```

### Use Case 2: Dormitory WiFi
```
Hotspot: hotspot_dorm
Template: "Dorm Card Gallery"
Cards: WiFi rules, contact support, payment info
Background: Dormitory image
```

### Use Case 3: Main Campus WiFi
```
Hotspot: hotspot (default)
Template: "Campus Welcome"
Slides: University info, announcements
Background: Campus landscape
```

---

## 🐛 Troubleshooting

### Problem: Login page shows wrong template
**Solution**: Check hotspot_name in database matches folder name

### Problem: 404 error when accessing /hotspot_lib/login.html
**Solution**: Ensure folder exists and URL pattern is configured in urls.py

### Problem: Template preview not working
**Solution**: Check that template has is_active=True and hotspot_name matches

---

## 📚 Related Files

- `api/models.py` - Database models with hotspot_name
- `api/views.py` - API endpoints with auto-detection
- `api/admin.py` - Admin interface updates
- `backend/urls.py` - URL routing for hotspot folders
- `hotspot/login.html` - Frontend with auto-detection
- `webapp/templates/webapp/templates.html` - Template management UI

---

**Last Updated**: November 14, 2025
**Migration Version**: 0005_rename_router_id_to_hotspot_name
