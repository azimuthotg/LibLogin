// Hotspot Management JavaScript
let refreshInterval = 10; // Default 10 minutes
let refreshTimer = null;
let countdownTimer = null;
let nextRefreshTime = null;

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Load hotspots on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Hotspot Management] Initializing...');
    loadHotspots();
    startAutoRefresh();

    // Add event delegation for hotspot action buttons
    const tbody = document.getElementById('hotspotsTableBody');
    if (tbody) {
        tbody.addEventListener('click', function(e) {
            const button = e.target.closest('button[data-action]');
            if (!button) return;

            const action = button.dataset.action;
            const id = parseInt(button.dataset.id);
            const name = button.dataset.name;

            if (action === 'test') {
                testConnection(id);
            } else if (action === 'edit') {
                editHotspot(id);
            } else if (action === 'delete') {
                deleteHotspot(id, name);
            } else if (action === 'generate') {
                generateLoginPage(id, name);
            } else if (action === 'download_zip') {
                downloadLoginZip(id, name);
            }
        });
    }
});

// Load hotspots from API
function loadHotspots() {
    console.log('[Hotspot Management] Loading hotspots...');
    fetch((window.BASE_URL || '') + '/api/hotspots/', {
        headers: {
            'X-CSRFToken': csrftoken
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        console.log('[Hotspot Management] Loaded', data.length, 'hotspots');
        renderHotspots(data);
    })
    .catch(error => {
        console.error('[Hotspot Management] Error loading hotspots:', error);
        document.getElementById('hotspotsTableBody').innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger py-4">
                    <i class="bi bi-exclamation-circle"></i> Error loading hotspots: ${error.message}
                </td>
            </tr>
        `;
    });
}

// Render hotspots table
function renderHotspots(hotspots) {
    const tbody = document.getElementById('hotspotsTableBody');

    if (!hotspots || hotspots.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="bi bi-inbox"></i> ยังไม่มี Hotspot — คลิก "เพิ่ม Hotspot" เพื่อเพิ่ม
                </td>
            </tr>
        `;
        return;
    }

    const isStaff = window.IS_STAFF === true;
    tbody.innerHTML = hotspots.map(hotspot => `
        <tr>
            <td class="text-center">${hotspot.status_icon}</td>
            <td><code>${hotspot.hotspot_name}</code></td>
            <td>${hotspot.display_name}</td>
            <td>
                ${getStatusBadge(hotspot.status)}
                ${getStatusDetails(hotspot)}
            </td>
            <td>${formatDateTime(hotspot.last_checked)}</td>
            <td>${formatActivity(hotspot.last_impression_at)}</td>
            <td>
                <div class="d-flex flex-wrap gap-1">
                <button class="btn btn-sm btn-info" data-action="test" data-id="${hotspot.id}" title="ตรวจสอบสถานะ">
                    <i class="bi bi-check-circle"></i> Test
                </button>
                ${isStaff ? `
                <button class="btn btn-sm btn-success" data-action="generate" data-id="${hotspot.id}" data-name="${hotspot.hotspot_name}" title="สร้าง login.html จาก Master Template">
                    <i class="bi bi-gear"></i> Generate
                </button>
                <button class="btn btn-sm btn-secondary" data-action="download_zip" data-id="${hotspot.id}" data-name="${hotspot.hotspot_name}" title="ดาวน์โหลด ZIP สำหรับอัปโหลดไป MikroTik">
                    <i class="bi bi-file-zip"></i> ZIP
                </button>
                <button class="btn btn-sm btn-primary" data-action="edit" data-id="${hotspot.id}" title="แก้ไข">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" data-action="delete" data-id="${hotspot.id}" data-name="${hotspot.display_name}" title="ลบ">
                    <i class="bi bi-trash"></i>
                </button>
                ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

// Get status badge HTML
function getStatusBadge(status) {
    const badges = {
        'ready': '<span class="badge bg-success">พร้อม</span>',
        'warning': '<span class="badge bg-warning text-dark">คำเตือน</span>',
        'error': '<span class="badge bg-danger">ข้อผิดพลาด</span>',
        'unchecked': '<span class="badge bg-secondary">ยังไม่ตรวจ</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">ไม่ทราบ</span>';
}

// Get status details HTML (6 checks)
function getStatusDetails(hotspot) {
    if (!hotspot.last_checked) return '';

    const c = (ok, title) => ok
        ? `<i class="bi bi-check-circle-fill text-success" title="${title} ✅"></i>`
        : `<i class="bi bi-x-circle-fill text-danger" title="${title} ❌"></i>`;
    const w = (ok, title) => ok
        ? `<i class="bi bi-check-circle-fill text-success" title="${title} ✅"></i>`
        : `<i class="bi bi-dash-circle text-warning" title="${title} ⚠️ ไม่มี"></i>`;

    return '<br><small style="letter-spacing:2px;">' + [
        c(hotspot.folder_exists,       'Folder'),
        c(hotspot.login_file_exists,   'login.html'),
        c(hotspot.config_matched,      'Config'),
        c(hotspot.has_active_background, 'Background'),
        c(hotspot.has_active_template,   'Template'),
        w(hotspot.has_landing_url,       'Landing URL'),
    ].join(' ') + '</small>';
}

// Format datetime
function formatDateTime(dateStr) {
    if (!dateStr) return '<span class="text-muted">ยังไม่ตรวจ</span>';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

// Format last activity
function formatActivity(dateStr) {
    if (!dateStr) return '<span class="text-muted" style="font-size:.8rem;">ยังไม่มี</span>';
    const date = new Date(dateStr);
    const diffMs = Date.now() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    const label = diffDays === 0 ? 'วันนี้'
        : diffDays === 1 ? 'เมื่อวาน'
        : `${diffDays} วันที่แล้ว`;
    return `<span style="font-size:.8rem;" title="${date.toLocaleString()}">${label}</span>`;
}

// Test all hotspots sequentially
async function testAllHotspots() {
    const btn = document.getElementById('btnTestAll');
    const rows = document.querySelectorAll('#hotspotsTableBody tr');
    const ids = [];

    // Collect hotspot IDs from action buttons
    document.querySelectorAll('#hotspotsTableBody button[data-action="test"]').forEach(b => {
        ids.push(parseInt(b.dataset.id));
    });

    if (ids.length === 0) { showAlert('warning', 'ไม่พบ Hotspot ที่จะตรวจสอบ'); return; }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> กำลังตรวจ...';

    let done = 0;
    for (const id of ids) {
        try {
            await fetch((window.BASE_URL || '') + `/api/hotspots/${id}/test_connection/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' },
                credentials: 'include'
            });
        } catch (e) { /* continue */ }
        done++;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> ตรวจ ${done}/${ids.length}...`;
    }

    btn.innerHTML = '<i class="bi bi-check2-all"></i> ตรวจทั้งหมด';
    btn.disabled = false;
    showAlert('success', `✅ ตรวจสอบครบ ${ids.length} Hotspot`);
    loadHotspots();
}

// Generate login.html from master template
function generateLoginPage(hotspotId, hotspotName) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    btn.disabled = true;

    fetch((window.BASE_URL || '') + `/api/hotspots/${hotspotId}/generate_login_page/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `✅ สร้าง login.html สำเร็จสำหรับ <strong>${hotspotName}</strong> — ${data.hotspot.status_icon} ${data.hotspot.status}`);
            loadHotspots();
        } else {
            showAlert('danger', 'เกิดข้อผิดพลาด: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        showAlert('danger', 'Error: ' + error.message);
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// Download login ZIP for MikroTik upload
function downloadLoginZip(hotspotId, hotspotName) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    btn.disabled = true;

    // Trigger download via anchor element
    const url = (window.BASE_URL || '') + `/api/hotspots/${hotspotId}/download_login_zip/`;
    fetch(url, {
        headers: { 'X-CSRFToken': csrftoken },
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) return response.json().then(d => Promise.reject(d.message || 'Error'));
        return response.blob();
    })
    .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `hotspot_${hotspotName}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
        showAlert('success', `📦 ดาวน์โหลด hotspot_${hotspotName}.zip สำเร็จ`);
    })
    .catch(error => {
        showAlert('danger', 'Error downloading ZIP: ' + error);
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// Test connection
function testConnection(hotspotId) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> กำลังทดสอบ...';
    btn.disabled = true;

    fetch((window.BASE_URL || '') + `/api/hotspots/${hotspotId}/test_connection/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', `Connection test completed: ${data.hotspot.status_icon} ${data.hotspot.status.toUpperCase()}`);
            loadHotspots(); // Reload to show updated status
        } else {
            showAlert('danger', 'Connection test failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        showAlert('danger', 'Error testing connection: ' + error.message);
    })
    .finally(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
}

// Add hotspot
function addHotspot() {
    const hotspot_name = document.getElementById('add_hotspot_name').value.trim();
    const display_name = document.getElementById('add_display_name').value.trim();
    const description = document.getElementById('add_description').value.trim();
    const is_active = document.getElementById('add_is_active').checked;

    if (!hotspot_name || !display_name) {
        showAlert('warning', 'กรุณากรอกข้อมูลที่จำเป็นให้ครบ');
        return;
    }

    // Validate hotspot_name pattern
    const pattern = /^hotspot(_[a-z0-9]+)?$/;
    if (!pattern.test(hotspot_name)) {
        showAlert('warning', 'ชื่อ Hotspot ต้องขึ้นต้นด้วย "hotspot" และใช้ตัวพิมพ์เล็ก, ตัวเลข, และ _ เท่านั้น');
        return;
    }

    fetch((window.BASE_URL || '') + '/api/hotspots/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
            hotspot_name,
            display_name,
            description,
            is_active
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            showAlert('success', `Hotspot "${display_name}" added successfully`);
            bootstrap.Modal.getInstance(document.getElementById('addHotspotModal')).hide();
            document.getElementById('addHotspotForm').reset();
            loadHotspots();
        } else {
            showAlert('danger', 'Error adding hotspot: ' + (data.hotspot_name ? data.hotspot_name[0] : 'Unknown error'));
        }
    })
    .catch(error => {
        showAlert('danger', 'Error adding hotspot: ' + error.message);
    });
}

// Edit hotspot
function editHotspot(hotspotId) {
    fetch((window.BASE_URL || '') + `/api/hotspots/${hotspotId}/`, {
        headers: {
            'X-CSRFToken': csrftoken
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(hotspot => {
        document.getElementById('edit_hotspot_id').value = hotspot.id;
        document.getElementById('edit_hotspot_name').value = hotspot.hotspot_name;
        document.getElementById('edit_display_name').value = hotspot.display_name;
        document.getElementById('edit_description').value = hotspot.description || '';
        document.getElementById('edit_is_active').checked = hotspot.is_active;

        new bootstrap.Modal(document.getElementById('editHotspotModal')).show();
    })
    .catch(error => {
        showAlert('danger', 'Error loading hotspot: ' + error.message);
    });
}

// Save hotspot
function saveHotspot() {
    const hotspotId = document.getElementById('edit_hotspot_id').value;
    const display_name = document.getElementById('edit_display_name').value.trim();
    const description = document.getElementById('edit_description').value.trim();
    const is_active = document.getElementById('edit_is_active').checked;

    if (!display_name) {
        showAlert('warning', 'กรุณากรอก Display Name');
        return;
    }

    fetch((window.BASE_URL || '') + `/api/hotspots/${hotspotId}/`, {
        method: 'PATCH',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
            display_name,
            description,
            is_active
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            showAlert('success', `Hotspot "${display_name}" updated successfully`);
            bootstrap.Modal.getInstance(document.getElementById('editHotspotModal')).hide();
            loadHotspots();
        } else {
            showAlert('danger', 'Error updating hotspot');
        }
    })
    .catch(error => {
        showAlert('danger', 'Error updating hotspot: ' + error.message);
    });
}

// Delete hotspot
function deleteHotspot(hotspotId, displayName) {
    document.getElementById('delete_hotspot_id').value = hotspotId;
    document.getElementById('delete_hotspot_name').textContent = displayName;
    new bootstrap.Modal(document.getElementById('deleteHotspotModal')).show();
}

// Confirm delete hotspot
function confirmDeleteHotspot() {
    const hotspotId = document.getElementById('delete_hotspot_id').value;

    fetch((window.BASE_URL || '') + `/api/hotspots/${hotspotId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken
        },
        credentials: 'include'
    })
    .then(response => {
        if (response.status === 204) {
            showAlert('success', 'Hotspot deleted successfully');
            bootstrap.Modal.getInstance(document.getElementById('deleteHotspotModal')).hide();
            loadHotspots();
        } else {
            return response.json().then(data => {
                throw new Error(data.detail || 'Unknown error');
            });
        }
    })
    .catch(error => {
        showAlert('danger', 'Error deleting hotspot: ' + error.message);
    });
}

// Auto-refresh functionality
function startAutoRefresh() {
    // Get refresh interval from window variable set by Django template
    if (typeof window.HOTSPOT_REFRESH_INTERVAL !== 'undefined') {
        refreshInterval = window.HOTSPOT_REFRESH_INTERVAL;
    }

    // Set next refresh time
    nextRefreshTime = Date.now() + (refreshInterval * 60 * 1000);

    // Start countdown
    updateCountdown();
    countdownTimer = setInterval(updateCountdown, 1000);

    // Start auto-refresh
    refreshTimer = setInterval(() => {
        console.log('[Auto-refresh] Refreshing hotspots...');
        loadHotspots();
        nextRefreshTime = Date.now() + (refreshInterval * 60 * 1000);
    }, refreshInterval * 60 * 1000);
}

function updateCountdown() {
    const countdown = document.getElementById('refreshCountdown');
    if (!countdown) return;

    const remaining = Math.max(0, nextRefreshTime - Date.now());
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);

    countdown.textContent = `รีเฟรชถัดไป: ${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Show alert
function showAlert(type, message) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const container = document.querySelector('.main-content') || document.querySelector('.container-fluid') || document.body;
    container.insertAdjacentHTML('afterbegin', alertHtml);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            bootstrap.Alert.getInstance(alert)?.close();
        }
    }, 5000);
}
