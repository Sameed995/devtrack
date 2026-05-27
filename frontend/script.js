const API_BASE = 'http://127.0.0.1:8000';

// Show/hide sections
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    if (sectionId === 'dashboard') {
        loadEndpoints();
    } else if (sectionId === 'logs') {
        loadEndpointsForFilter();
        loadLogs();
    }
}

// Load endpoints for dashboard
function loadEndpoints() {
    fetch(`${API_BASE}/endpoints/`)
        .then(res => res.json())
        .then(endpoints => {
            const list = document.getElementById('endpoints-list');
            
            if (endpoints.length === 0) {
                list.innerHTML = '<p class="loading">No endpoints registered yet.</p>';
                return;
            }
            
            let html = '<table>';
            html += '<tr><th>ID</th><th>Name</th><th>URL</th><th>Interval</th><th>Created</th><th>Actions</th></tr>';
            
            endpoints.forEach(ep => {
                const created = new Date(ep.created_at).toLocaleDateString();
                const interval = ep.interval_minutes ? `${ep.interval_minutes}m` : 'Manual';
                html += `<tr>
                    <td>${ep.id}</td>
                    <td>${escapeHtml(ep.name)}</td>
                    <td><small>${escapeHtml(ep.url)}</small></td>
                    <td>
                        <select onchange="updateInterval(${ep.id}, this.value)" class="interval-select">
                            <option value="">Manual</option>
                            <option value="2" ${ep.interval_minutes === 2 ? 'selected' : ''}>2 min</option>
                            <option value="5" ${ep.interval_minutes === 5 ? 'selected' : ''}>5 min</option>
                            <option value="10" ${ep.interval_minutes === 10 ? 'selected' : ''}>10 min</option>
                            <option value="15" ${ep.interval_minutes === 15 ? 'selected' : ''}>15 min</option>
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
        interval_minutes: interval ? parseInt(interval) : null
    };
    
    fetch(`${API_BASE}/endpoints/`, {
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
    fetch(`${API_BASE}/endpoints/${endpointId}/check/`, {
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
    fetch(`${API_BASE}/endpoints/${endpointId}/summary/`)
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
            fetch(`${API_BASE}/endpoints/${endpointId}/`, {
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
    fetch(`${API_BASE}/endpoints/`)
        .then(res => res.json())
        .then(endpoints => {
            const filter = document.getElementById('endpoint-filter');
            filter.innerHTML = '<option value="">All Endpoints</option>';
            
            endpoints.forEach(ep => {
                const option = document.createElement('option');
                option.value = ep.id;
                option.textContent = ep.name;
                filter.appendChild(option);
            });
        })
        .catch(err => console.error(err));
}

// Load logs
function loadLogs() {
    const endpointId = document.getElementById('endpoint-filter').value;
    const url = endpointId ? `${API_BASE}/endpoints/${endpointId}/logs/` : `${API_BASE}/logs/`;
    
    fetch(url)
        .then(res => res.json())
        .then(logs => {
            const list = document.getElementById('logs-list');
            
            if (logs.length === 0) {
                list.innerHTML = '<p class="loading">No logs found.</p>';
                return;
            }
            
            let html = '<table>';
            html += '<tr><th>Endpoint ID</th><th>Status</th><th>Response Time</th><th>Status Code</th><th>Error Message</th><th>Created</th></tr>';
            
            logs.forEach(log => {
                const created = new Date(log.created_at).toLocaleString();
                const statusClass = log.status === 'UP' ? 'status-up' : 'status-down';
                const responseTime = log.response_time_ms ? log.response_time_ms.toFixed(2) + 'ms' : '-';
                const statusCode = log.status_code || '-';
                const errorMsg = log.error_message || '-';
                
                html += `<tr>
                    <td>${log.endpoint_id}</td>
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
    
    fetch(url)
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
                content += `Endpoint ID: ${log.endpoint_id}\n`;
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
    
    fetch(url)
        .then(res => res.json())
        .then(logs => {
            if (logs.length === 0) {
                showNotification('No logs to download.', 'info');
                return;
            }
            
            // Create CSV header
            const headers = ['Endpoint ID', 'Status', 'Response Time (ms)', 'Status Code', 'Error Message', 'Created'];
            let csv = headers.map(h => `"${h}"`).join(',') + '\n';
            
            // Add rows
            logs.forEach(log => {
                const row = [
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
        interval_minutes: interval ? parseInt(interval) : null
    };
    
    fetch(`${API_BASE}/endpoints/${endpointId}/interval`, {
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
        const intervalText = data.interval_minutes ? `${data.interval_minutes} minutes` : 'manual checks only';
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
    showSection('dashboard');
});
