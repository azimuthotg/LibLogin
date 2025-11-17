// Hotspot Dropdown Loader
// This file provides functionality to load hotspot choices into select elements

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

/**
 * Load hotspot choices and populate a select element
 * @param {string} selectId - ID of the select element
 * @param {string} currentValue - Currently selected hotspot_name (optional)
 * @param {boolean} includeBlank - Whether to include "All Hotspots" option (default: true)
 */
function loadHotspotChoices(selectId, currentValue = '', includeBlank = true) {
    const selectElement = document.getElementById(selectId);
    if (!selectElement) {
        console.error(`[Hotspot Dropdown] Select element #${selectId} not found`);
        return Promise.reject(new Error(`Select element #${selectId} not found`));
    }

    console.log(`[Hotspot Dropdown] Loading choices for #${selectId}`);

    return fetch('/api/hotspot-choices/', {
        headers: {
            'X-CSRFToken': csrftoken
        },
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        // Clear existing options
        selectElement.innerHTML = '';

        // Add "All Hotspots" option if includeBlank is true
        if (includeBlank) {
            const blankOption = document.createElement('option');
            blankOption.value = '';
            blankOption.textContent = '-- All Hotspots --';
            if (currentValue === '' || currentValue === null) {
                blankOption.selected = true;
            }
            selectElement.appendChild(blankOption);
        }

        // Add hotspot options
        data.forEach(hotspot => {
            const option = document.createElement('option');
            option.value = hotspot.hotspot_name;
            option.textContent = `${hotspot.display_name} (${hotspot.hotspot_name})`;

            // Add status indicator
            option.setAttribute('data-status', hotspot.status);
            option.setAttribute('data-status-icon', hotspot.status_icon);

            // Set selected if matches current value
            if (hotspot.hotspot_name === currentValue) {
                option.selected = true;
            }

            selectElement.appendChild(option);
        });

        console.log(`[Hotspot Dropdown] Loaded ${data.length} hotspot(s) for #${selectId}`);
        return data;
    })
    .catch(error => {
        console.error('[Hotspot Dropdown] Error loading hotspot choices:', error);

        // Show error option
        selectElement.innerHTML = '<option value="">Error loading hotspots</option>';
        throw error;
    });
}

/**
 * Initialize all hotspot dropdowns on page load
 * Looks for select elements with class 'hotspot-dropdown'
 */
function initializeHotspotDropdowns() {
    const dropdowns = document.querySelectorAll('select.hotspot-dropdown');
    console.log(`[Hotspot Dropdown] Found ${dropdowns.length} dropdown(s) to initialize`);

    dropdowns.forEach(dropdown => {
        const currentValue = dropdown.getAttribute('data-current-value') || dropdown.value || '';
        const includeBlank = dropdown.getAttribute('data-include-blank') !== 'false';

        loadHotspotChoices(dropdown.id, currentValue, includeBlank);
    });
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initializeHotspotDropdowns();
});
