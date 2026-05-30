const API_BASE = 'http://127.0.0.1:8000';

const TOKEN_STORAGE_KEY = 'devtrack.token';
const USERNAME_STORAGE_KEY = 'devtrack.username';

function getAuthToken() {
    try {
        return localStorage.getItem(TOKEN_STORAGE_KEY);
    } catch (_) {
        return null;
    }
}

function getStoredUsername() {
    try {
        return localStorage.getItem(USERNAME_STORAGE_KEY);
    } catch (_) {
        return null;
    }
}

function setAuthSession({ token, username }) {
    try {
        localStorage.setItem(TOKEN_STORAGE_KEY, token);
        localStorage.setItem(USERNAME_STORAGE_KEY, username);
    } catch (_) {
        // ignore storage errors
    }
    updateAuthUI();
}

function clearAuthSession() {
    try {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USERNAME_STORAGE_KEY);
    } catch (_) {
        // ignore
    }
    updateAuthUI();
}

function isAuthenticated() {
    return Boolean(getAuthToken());
}

function updateAuthUI() {

    const username = getStoredUsername();

    const authUserEl = document.getElementById('auth-user');
    const logoutBtn = document.getElementById('logout-btn');

    const loggedOutView = document.getElementById('logged-out-view');
    const loggedInView = document.getElementById('logged-in-view');

    const accountUsername = document.getElementById('account-username');

    if (authUserEl) {
        authUserEl.textContent = username
            ? `Signed in as ${username}`
            : 'Not signed in';
    }

    if (logoutBtn) {
        logoutBtn.style.display = username
            ? 'inline-block'
            : 'none';
    }

    if (username) {

        if (loggedOutView) {
            loggedOutView.style.display = 'none';
        }

        if (loggedInView) {
            loggedInView.style.display = 'block';
        }

        if (accountUsername) {
            accountUsername.textContent =
                `Welcome, ${username} 👋`;
        }

    } else {

        if (loggedOutView) {
            loggedOutView.style.display = 'block';
        }

        if (loggedInView) {
            loggedInView.style.display = 'none';
        }
    }
}
function apiFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = new Headers(options.headers || {});
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    return fetch(url, { ...options, headers }).then(res => {
        if (res.status === 401) {
            clearAuthSession();
            showNotification('Please login to continue.', 'info');
            showSection('auth');
            throw new Error('Unauthorized');
        }
        return res;
    });
}

// Endpoint name cache for rendering logs
let endpointNameById = {};

function getEndpointName(endpointId) {
    const endpoint = endpointNameById[String(endpointId)];

    if (!endpoint) {
        return `Endpoint`;
    }

    return `${endpoint.name} (#${endpoint.displayId})`;
}

// Auto-refresh logs while the Logs tab is active
const LOGS_AUTO_REFRESH_MS = 5000;
let logsAutoRefreshTimerId = null;
let lastLogsSignature = null;

function startLogsAutoRefresh() {

    if (logsAutoRefreshTimerId) return;

    logsAutoRefreshTimerId = setInterval(() => {

        const authSection =
            document.getElementById('auth');

        if (!authSection ||
            !authSection.classList.contains('active')) {
            return;
        }

        loadLogs({ skipIfUnchanged: true });

    }, LOGS_AUTO_REFRESH_MS);
}

function stopLogsAutoRefresh() {
    if (!logsAutoRefreshTimerId) return;
    clearInterval(logsAutoRefreshTimerId);
    logsAutoRefreshTimerId = null;
}

// Show/hide sections
function showSection(sectionId) {

    if (sectionId !== 'auth' &&
        !isAuthenticated()) {

        sectionId = 'auth';

        showNotification(
            'Please login to continue.',
            'info'
        );
    }

    try {
        localStorage.setItem(
            'devtrack.activeSection',
            sectionId
        );
    } catch (_) {}

    document.querySelectorAll('.section')
        .forEach(section => {
            section.classList.remove('active');
        });

    document
        .getElementById(sectionId)
        .classList.add('active');

    if (sectionId === 'dashboard') {
        loadEndpoints();
    }

    if (sectionId === 'auth' &&
        isAuthenticated()) {

        loadEndpointsForFilter();

        loadLogs();

        startLogsAutoRefresh();

    } else {

        stopLogsAutoRefresh();
    }
}
function getEffectiveIntervalSeconds(endpoint) {
    if (!endpoint) return null;
    if (endpoint.interval_seconds !== undefined && endpoint.interval_seconds !== null) {
        return endpoint.interval_seconds;
    }
    if (endpoint.interval_minutes !== undefined && endpoint.interval_minutes !== null) {
        return endpoint.interval_minutes * 60;
    }
    return null;
}

function formatIntervalLabel(intervalSeconds) {
    if (!intervalSeconds) return 'Manual';
    if (intervalSeconds < 60) return `${intervalSeconds}s`;
    return `${Math.round(intervalSeconds / 60)}m`;
}

// Load endpoints for dashboard
function loadEndpoints() {
    apiFetch(`${API_BASE}/endpoints/`)
        .then(res => res.json())
        .then(endpoints => {
            const list = document.getElementById('endpoints-list');

            // Update name cache
            endpointNameById = {};
            endpoints.forEach(ep => {
                endpointNameById[String(ep.id)] = {
                    name: ep.name,
                    displayId: ep.display_id
                };
            });
            
            if (endpoints.length === 0) {
                list.innerHTML = '<p class="loading">No endpoints registered yet.</p>';
                return;
            }
            
            let html = '<table>';
            html += '<tr><th>ID</th><th>Name</th><th>URL</th><th>Interval</th><th>Created</th><th>Actions</th></tr>';
            
            endpoints.forEach(ep => {
                const created = new Date(ep.created_at).toLocaleDateString();
                const intervalSeconds = getEffectiveIntervalSeconds(ep);
                const interval = formatIntervalLabel(intervalSeconds);
                html += `<tr>
                    <td>${ep.display_id}</td>
                    <td>${escapeHtml(ep.name)}</td>
                    <td><small>${escapeHtml(ep.url)}</small></td>
                    <td>
                        <select onchange="updateInterval(${ep.id}, this.value)" class="interval-select">
                            <option value="">Manual</option>
                            <option value="10" ${intervalSeconds === 10 ? 'selected' : ''}>10 sec</option>
                            <option value="120" ${intervalSeconds === 120 ? 'selected' : ''}>2 min</option>
                            <option value="300" ${intervalSeconds === 300 ? 'selected' : ''}>5 min</option>
                            <option value="600" ${intervalSeconds === 600 ? 'selected' : ''}>10 min</option>
                            <option value="900" ${intervalSeconds === 900 ? 'selected' : ''}>15 min</option>
                        </select>
                    </td>
                    <td>${created}</td>
                    <td class="endpoint-actions">
                        <button class="btn btn-small" onclick="triggerCheck(${ep.id})">Check</button>
                        <button class="btn btn-small" onclick="viewSummary(${ep.id})">Summary</button>
                        <button class="btn btn-small btn-danger" onclick="deleteEndpoint(${ep.id})">Delete</button>
                    </td>
                </tr>`;
            });
            
            html += '</table>';
            list.innerHTML = html;
        })
        .catch(err => {
            document.getElementById('endpoints-list').innerHTML = '<p class="loading">Error loading endpoints.</p>';
            console.error(err);
        });
}

// Register endpoint
document.getElementById('register-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const name = document.getElementById('endpoint-name').value;
    const url = document.getElementById('endpoint-url').value;
    const interval = document.getElementById('endpoint-interval').value;
    
    const payload = {
        name,
        url,
        interval_seconds: interval ? parseInt(interval) : null
    };
    
    apiFetch(`${API_BASE}/endpoints/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => {
                throw new Error(data.detail || 'Error registering endpoint.');
            });
        }
        return res.json();
    })
    .then(data => {
        if (data.id) {
            showNotification('Endpoint registered successfully!', 'success');
            document.getElementById('register-form').reset();
            setTimeout(() => {
                showSection('dashboard');
            }, 1500);
        }
    })
    .catch(err => {
        showNotification(err.message, 'error');
        console.error(err);
    });
});

// Trigger health check
function triggerCheck(endpointId) {
    apiFetch(`${API_BASE}/endpoints/${endpointId}/check/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        showNotification(`Check triggered! Status: ${data.status} | Response Time: ${data.response_time_ms}ms`, 'success');
        loadEndpoints();
    })
    .catch(err => {
        showNotification('Error triggering check.', 'error');
        console.error(err);
    });
}

// View endpoint summary
function viewSummary(endpointId) {
    apiFetch(`${API_BASE}/endpoints/${endpointId}/summary/`)
        .then(res => res.json())
        .then(data => {
            const uptime = (data.uptime_percentage || 0).toFixed(2);
            const avgTime = (data.avg_response_time_ms || 0).toFixed(2);
            const summary = `Uptime: ${uptime}% | Avg Response Time: ${avgTime}ms | Total Checks: ${data.total_checks}`;
            showNotification(summary, 'info');
        })
        .catch(err => {
            showNotification('Error loading summary.', 'error');
            console.error(err);
        });
}

// Delete endpoint
function deleteEndpoint(endpointId) {
    showConfirmModal(
        'Delete Endpoint?',
        'Are you sure you want to delete this endpoint and all its logs? This action cannot be undone.',
        () => {
            apiFetch(`${API_BASE}/endpoints/${endpointId}/`, {
                method: 'DELETE'
            })
            .then(() => {
                showNotification('Endpoint deleted.', 'success');
                loadEndpoints();
            })
            .catch(err => {
                showNotification('Error deleting endpoint.', 'error');
                console.error(err);
            });
        }
    );
}

// Load endpoints for filter
function loadEndpointsForFilter() {
    apiFetch(`${API_BASE}/endpoints/`)
        .then(res => res.json())
        .then(endpoints => {
            const filter = document.getElementById('endpoint-filter');
            filter.innerHTML = '<option value="">All Endpoints</option>';

            // Update name cache
            endpointNameById = {};
            endpoints.forEach(ep => {
                endpointNameById[String(ep.id)] = {
                    name: ep.name,
                    displayId: ep.display_id
                };
            });
            
            endpoints.forEach(ep => {
                const option = document.createElement('option');
                option.value = ep.id;
                option.textContent = ep.name;
                filter.appendChild(option);
            });

            // If we're on the Logs tab and logs are already rendered, re-render so names appear
            const authSection = document.getElementById('auth');
            if (authSection && authSection.classList.contains('active')) {
                lastLogsSignature = null;
                loadLogs();
            }
        })
        .catch(err => console.error(err));
}

// Load logs
function loadLogs(options = {}) {
    const { skipIfUnchanged = false } = options || {};
    const endpointId = document.getElementById('endpoint-filter').value;
    const url = endpointId ? `${API_BASE}/endpoints/${endpointId}/logs/` : `${API_BASE}/logs/`;
    
    apiFetch(url)
        .then(res => res.json())
        .then(logs => {
            const list = document.getElementById('logs-list');

            const signature = `${endpointId || 'all'}:${logs.length}:${logs[0]?.id || ''}`;
            if (skipIfUnchanged && signature === lastLogsSignature) {
                return;
            }
            lastLogsSignature = signature;
            
            if (logs.length === 0) {
                list.innerHTML = '<p class="loading">No logs found.</p>';
                return;
            }
            
            let html = '<table>';
            html += '<tr><th>Endpoint</th><th>Status</th><th>Response Time</th><th>Status Code</th><th>Error Message</th><th>Created</th></tr>';
            
            logs.forEach(log => {
                const created = new Date(log.created_at).toLocaleString();
                const statusClass = log.status === 'UP' ? 'status-up' : 'status-down';
                const responseTime = log.response_time_ms ? log.response_time_ms.toFixed(2) + 'ms' : '-';
                const statusCode = log.status_code || '-';
                const errorMsg = log.error_message || '-';
                const endpointName = getEndpointName(log.endpoint_id);
                
                html += `<tr>
                    <td>${escapeHtml(endpointName)}</td>
                    <td class="${statusClass}">${log.status}</td>
                    <td>${responseTime}</td>
                    <td>${statusCode}</td>
                    <td><small>${escapeHtml(errorMsg)}</small></td>
                    <td><small>${created}</small></td>
                </tr>`;
            });
            
            html += '</table>';
            list.innerHTML = html;
        })
        .catch(err => {
            document.getElementById('logs-list').innerHTML = '<p class="loading">Error loading logs.</p>';
            console.error(err);
        });
}

// Show notification on page
function showNotification(message, type = 'info') {
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'notification';
        document.body.insertBefore(notification, document.body.firstChild);
    }
    
    notification.textContent = message;
    notification.className = `notification notification-${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 4000);
}

// Show confirmation modal
function showConfirmModal(title, message, onConfirm) {
    let overlay = document.getElementById('confirm-modal-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'confirm-modal-overlay';
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal">
                <h3></h3>
                <p></p>
                <div class="modal-buttons">
                    <button class="btn btn-cancel" onclick="closeConfirmModal()">Cancel</button>
                    <button class="btn btn-confirm" id="confirm-btn">Delete</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    overlay.querySelector('h3').textContent = title;
    overlay.querySelector('p').textContent = message;
    overlay.classList.add('show');
    
    const confirmBtn = document.getElementById('confirm-btn');
    confirmBtn.onclick = () => {
        closeConfirmModal();
        onConfirm();
    };
}

// Close confirmation modal
function closeConfirmModal() {
    const overlay = document.getElementById('confirm-modal-overlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// Download logs as text file
function downloadLogs() {
    const endpointId = document.getElementById('endpoint-filter').value;
    const url = endpointId ? `${API_BASE}/endpoints/${endpointId}/logs/` : `${API_BASE}/logs/`;
    
    apiFetch(url)
        .then(res => res.json())
        .then(logs => {
            if (logs.length === 0) {
                showNotification('No logs to download.', 'info');
                return;
            }
            
            let content = 'DevTrack - Check Logs Export\n';
            content += `Generated: ${new Date().toLocaleString()}\n`;
            content += '='.repeat(80) + '\n\n';
            
            logs.forEach(log => {
                const endpointName = getEndpointName(log.endpoint_id);
                content += `Endpoint: ${endpointName} (ID: ${log.endpoint_id})\n`;
                content += `Status: ${log.status}\n`;
                content += `Response Time: ${log.response_time_ms ? log.response_time_ms.toFixed(2) + 'ms' : 'N/A'}\n`;
                content += `Status Code: ${log.status_code || 'N/A'}\n`;
                content += `Error Message: ${log.error_message || 'None'}\n`;
                content += `Created: ${new Date(log.created_at).toLocaleString()}\n`;
                content += '-'.repeat(80) + '\n\n';
            });
            
            const blob = new Blob([content], { type: 'text/plain' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `devtrack-logs-${new Date().toISOString().slice(0, 10)}.txt`;
            link.click();
            URL.revokeObjectURL(link.href);
            
            showNotification('Logs downloaded successfully.', 'success');
        })
        .catch(err => {
            showNotification('Error downloading logs.', 'error');
            console.error(err);
        });
}

// Download logs as CSV file
function downloadLogsAsCSV() {
    const endpointId = document.getElementById('endpoint-filter').value;
    const url = endpointId ? `${API_BASE}/endpoints/${endpointId}/logs/` : `${API_BASE}/logs/`;
    
    apiFetch(url)
        .then(res => res.json())
        .then(logs => {
            if (logs.length === 0) {
                showNotification('No logs to download.', 'info');
                return;
            }
            
            // Create CSV header
            const headers = ['Endpoint Name', 'Endpoint ID', 'Status', 'Response Time (ms)', 'Status Code', 'Error Message', 'Created'];
            let csv = headers.map(h => `"${h}"`).join(',') + '\n';
            
            // Add rows
            logs.forEach(log => {
                const endpointName = getEndpointName(log.endpoint_id);
                const row = [
                    endpointName,
                    log.endpoint_id,
                    log.status,
                    log.response_time_ms ? log.response_time_ms.toFixed(2) : 'N/A',
                    log.status_code || 'N/A',
                    (log.error_message || 'None').replace(/"/g, '""'), // Escape quotes
                    new Date(log.created_at).toLocaleString()
                ];
                csv += row.map(cell => `"${cell}"`).join(',') + '\n';
            });
            
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `devtrack-logs-${new Date().toISOString().slice(0, 10)}.csv`;
            link.click();
            URL.revokeObjectURL(link.href);
            
            showNotification('Logs downloaded as CSV successfully.', 'success');
        })
        .catch(err => {
            showNotification('Error downloading logs.', 'error');
            console.error(err);
        });
}

// Update endpoint check interval
function updateInterval(endpointId, interval) {
    const payload = {
        interval_seconds: interval ? parseInt(interval) : null
    };
    
    apiFetch(`${API_BASE}/endpoints/${endpointId}/interval`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Failed to update interval');
        }
        return res.json();
    })
    .then(data => {
        const intervalSeconds = getEffectiveIntervalSeconds(data);
        const intervalText = intervalSeconds ? (intervalSeconds < 60 ? `${intervalSeconds} seconds` : `${Math.round(intervalSeconds / 60)} minutes`) : 'manual checks only';
        showNotification(`Check interval updated to ${intervalText}`, 'success');
        loadEndpoints();
    })
    .catch(err => {
        showNotification('Error updating interval.', 'error');
        console.error(err);
        loadEndpoints(); // Reload to reset the dropdown
    });
}

// 
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Load dashboard on page load
window.addEventListener('load', () => {
    updateAuthUI();

    document.getElementById('logout-btn')?.addEventListener('click', () => {
        clearAuthSession();
        showNotification('Logged out.', 'success');
        showSection('auth');
    });

    document.getElementById('login-form')?.addEventListener('submit', (e) => {
        e.preventDefault();

        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        apiFetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.detail || 'Login failed.');
                });
            }
            return res.json();
        })
        .then(data => {
            setAuthSession({ token: data.access_token, username: data.user?.username || username });
            showNotification('Login successful!', 'success');
            document.getElementById('login-form').reset();
            showSection('dashboard');
        })
        .catch(err => {
            showNotification(err.message, 'error');
            console.error(err);
        });
    });

    document.getElementById('signup-form')?.addEventListener('submit', (e) => {
        e.preventDefault();

        const username = document.getElementById('signup-username').value;
        const password = document.getElementById('signup-password').value;

        apiFetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.detail || 'Registration failed.');
                });
            }
            return res.json();
        })
        .then(() => {
            showNotification('Account created. You can now login.', 'success');
            document.getElementById('signup-form').reset();
        })
        .catch(err => {
            showNotification(err.message, 'error');
            console.error(err);
        });
    });
    // If user changes endpoint filter while on Logs, update immediately
    document.getElementById('endpoint-filter')?.addEventListener('change', () => {
        const authSection = document.getElementById('auth');
        if (authSection && authSection.classList.contains('active')){
            // reset signature so the table updates even if the first fetch matches an old signature
            lastLogsSignature = null;
            loadLogs();
        }
    });

    let initialSection = isAuthenticated() ? 'dashboard' : 'auth';
    try {
        const saved = localStorage.getItem('devtrack.activeSection');
        if (saved && document.getElementById(saved) && (saved === 'auth' || isAuthenticated())) {
            initialSection = saved;
        }
    } catch (_) {
        // ignore storage errors
    }

    showSection(initialSection);
});
