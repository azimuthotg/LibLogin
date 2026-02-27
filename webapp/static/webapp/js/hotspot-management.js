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
            }
        });
    }
});

// Load hotspots from API
function loadHotspots() {
    console.log('[Hotspot Management] Loading hotspots...');
    fetch('/api/hotspots/', {
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
                    <i class="bi bi-inbox"></i> No hotspots found. Click "Add New Hotspot" to create one.
                </td>
            </tr>
        `;
        return;
    }

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
            <td>
                <button class="btn btn-sm btn-info" data-action="test" data-id="${hotspot.id}" title="Test Connection">
                    <i class="bi bi-check-circle"></i> Test
                </button>
                <button class="btn btn-sm btn-primary" data-action="edit" data-id="${hotspot.id}" title="Edit">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" data-action="delete" data-id="${hotspot.id}" data-name="${hotspot.display_name}" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Get status badge HTML
function getStatusBadge(status) {
    const badges = {
        'ready': '<span class="badge bg-success">READY</span>',
        'warning': '<span class="badge bg-warning">WARNING</span>',
        'error': '<span class="badge bg-danger">ERROR</span>',
        'unchecked': '<span class="badge bg-secondary">UNCHECKED</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">UNKNOWN</span>';
}

// Get status details HTML
function getStatusDetails(hotspot) {
    if (!hotspot.last_checked) return '';

    const checks = [];
    if (hotspot.folder_exists) checks.push('<i class="bi bi-folder-check text-success" title="Folder exists"></i>');
    else checks.push('<i class="bi bi-folder-x text-danger" title="Folder not found"></i>');

    if (hotspot.login_file_exists) checks.push('<i class="bi bi-file-check text-success" title="login.html exists"></i>');
    else checks.push('<i class="bi bi-file-x text-danger" title="login.html not found"></i>');

    if (hotspot.config_matched) checks.push('<i class="bi bi-check-circle text-success" title="Config matched"></i>');
    else checks.push('<i class="bi bi-x-circle text-warning" title="Config mismatch"></i>');

    return '<br><small>' + checks.join(' ') + '</small>';
}

// Format datetime
function formatDateTime(dateStr) {
    if (!dateStr) return '<span class="text-muted">Never</span>';
    const date = new Date(dateStr);
    return date.toLocaleString();
}

// Test connection
function testConnection(hotspotId) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Testing...';
    btn.disabled = true;

    fetch(`/api/hotspots/${hotspotId}/test_connection/`, {
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
        showAlert('warning', 'Please fill in all required fields');
        return;
    }

    // Validate hotspot_name pattern
    const pattern = /^hotspot(_[a-z0-9]+)?$/;
    if (!pattern.test(hotspot_name)) {
        showAlert('warning', 'Hotspot name must start with "hotspot" and use lowercase letters, numbers, and underscores only');
        return;
    }

    fetch('/api/hotspots/', {
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
    fetch(`/api/hotspots/${hotspotId}/`, {
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
        showAlert('warning', 'Please fill in all required fields');
        return;
    }

    fetch(`/api/hotspots/${hotspotId}/`, {
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

    fetch(`/api/hotspots/${hotspotId}/`, {
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

    countdown.textContent = `Next refresh: ${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Show alert
function showAlert(type, message) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const container = document.querySelector('.container-fluid');
    container.insertAdjacentHTML('afterbegin', alertHtml);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            bootstrap.Alert.getInstance(alert)?.close();
        }
    }, 5000);
}
