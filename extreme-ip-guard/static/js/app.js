/**
 * Extreme IP Guard - Dashboard Application
 * Client-side logic for the command center.
 */

const API_BASE = '/api/v1';
let token = localStorage.getItem('xipg_token');
let ws = null;
let liveEventCount = 0;

// ── Auth ────────────────────────────────────────────────────────

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
    };
}

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`, { headers: getHeaders() });
    if (res.status === 401) { logout(); return null; }
    return res.json();
}

async function apiPost(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
    });
    if (res.status === 401) { logout(); return null; }
    return res.json();
}

async function apiDelete(path) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'DELETE',
        headers: getHeaders(),
    });
    if (res.status === 401) { logout(); return null; }
    return res.json();
}

function logout() {
    localStorage.removeItem('xipg_token');
    window.location.href = '/login';
}

// ── Navigation ──────────────────────────────────────────────────

function switchView(viewName) {
    document.querySelectorAll('.section-view').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    const view = document.getElementById(`view-${viewName}`);
    if (view) view.classList.add('active');

    const navItem = document.querySelector(`.nav-item[data-view="${viewName}"]`);
    if (navItem) navItem.classList.add('active');

    const loaders = {
        'dashboard': refreshDashboard,
        'ip-management': loadIPs,
        'events': loadEvents,
        'modules': loadModules,
        'rules': loadRules,
        'audit': loadAudit,
    };
    if (loaders[viewName]) loaders[viewName]();
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        switchView(item.dataset.view);
    });
});

// ── Dashboard ───────────────────────────────────────────────────

async function refreshDashboard() {
    const data = await apiGet('/dashboard/stats');
    if (!data) return;

    document.getElementById('statTotalIPs').textContent = formatNum(data.total_ips_tracked);
    document.getElementById('statActiveThreats').textContent = formatNum(data.active_threats);
    document.getElementById('statBlockedIPs').textContent = formatNum(data.blocked_ips);
    document.getElementById('statWhitelisted').textContent = formatNum(data.whitelisted_ips);
    document.getElementById('statEvents24h').textContent = formatNum(data.events_last_24h);
    document.getElementById('statActiveRules').textContent = formatNum(data.active_rules);

    const avgThreat = data.avg_threat_score || 0;
    document.getElementById('globalThreatFill').style.width = `${avgThreat}%`;
    document.getElementById('globalThreatScore').textContent = avgThreat.toFixed(1);
    updateThreatBadge(avgThreat);

    renderRecentEvents(data.recent_events || []);
    renderCountryList(data.top_threat_countries || []);
}

function updateThreatBadge(score) {
    const badge = document.getElementById('globalThreatBadge');
    if (score >= 80) {
        badge.textContent = 'CRITICAL';
        badge.className = 'badge badge-critical';
    } else if (score >= 60) {
        badge.textContent = 'HIGH';
        badge.className = 'badge badge-high';
    } else if (score >= 40) {
        badge.textContent = 'ELEVATED';
        badge.className = 'badge badge-medium';
    } else if (score >= 20) {
        badge.textContent = 'GUARDED';
        badge.className = 'badge badge-low';
    } else {
        badge.textContent = 'NOMINAL';
        badge.className = 'badge badge-safe';
    }
}

function renderRecentEvents(events) {
    const tbody = document.getElementById('recentEventsBody');
    tbody.innerHTML = events.map(e => `
        <tr class="event-row">
            <td class="mono text-muted" style="font-size:11px;">${formatTime(e.timestamp)}</td>
            <td><span class="badge badge-info">${e.event_type}</span></td>
            <td><span class="badge badge-${e.threat_level}">${e.threat_level}</span></td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${e.description || '-'}</td>
        </tr>
    `).join('') || '<tr><td colspan="4" class="text-muted" style="text-align:center;padding:20px;">No recent events</td></tr>';
}

function renderCountryList(countries) {
    const el = document.getElementById('countryList');
    el.innerHTML = countries.map(c => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-color);">
            <span style="font-weight:600;">${c.country || 'Unknown'}</span>
            <span class="mono text-amber">${c.count}</span>
        </div>
    `).join('') || '<p class="text-muted" style="padding:20px;text-align:center;">No threat data</p>';
}

// ── IP Management ───────────────────────────────────────────────

async function loadIPs() {
    const status = document.getElementById('ipFilterStatus')?.value || '';
    const threat = document.getElementById('ipFilterThreat')?.value || '';
    let url = '/ips?per_page=100';
    if (status) url += `&status=${status}`;
    if (threat) url += `&min_threat=${threat}`;

    const data = await apiGet(url);
    if (!data) return;

    const tbody = document.getElementById('ipTableBody');
    tbody.innerHTML = (data.items || []).map(ip => `
        <tr>
            <td><span class="ip-addr">${ip.ip}</span></td>
            <td><span class="badge badge-${ip.status}">${ip.status}</span></td>
            <td>
                <span class="mono ${getThreatColor(ip.threat_score)}">${ip.threat_score.toFixed(1)}</span>
                <div class="threat-bar"><div class="threat-bar-fill" style="width:${ip.threat_score}%;background:${getThreatGradient(ip.threat_score)}"></div></div>
            </td>
            <td>${ip.country || '-'}</td>
            <td class="mono">${formatNum(ip.total_requests)}</td>
            <td class="text-muted" style="font-size:11px;">${formatTime(ip.last_seen)}</td>
            <td>
                <div style="display:flex;gap:4px;">
                    <button class="btn" style="padding:4px 8px;font-size:11px;" onclick="analyzeIPDirect('${ip.ip}')">Analyze</button>
                    ${ip.status !== 'blocked'
                        ? `<button class="btn btn-danger" style="padding:4px 8px;font-size:11px;" onclick="blockIP('${ip.ip}')">Block</button>`
                        : `<button class="btn" style="padding:4px 8px;font-size:11px;" onclick="unblockIP('${ip.ip}')">Unblock</button>`
                    }
                </div>
            </td>
        </tr>
    `).join('') || '<tr><td colspan="7" class="text-muted" style="text-align:center;padding:30px;">No IP addresses found</td></tr>';
}

async function blockIP(ip) {
    await apiPost(`/ips/${ip}/block`);
    loadIPs();
}

async function unblockIP(ip) {
    await apiPost(`/ips/${ip}/unblock`);
    loadIPs();
}

function showAddIPModal() {
    const ip = prompt('Enter IP address:');
    if (ip) {
        apiPost('/ips', { ip, status: 'monitored', tags: [] }).then(loadIPs);
    }
}

// ── Threat Analysis ─────────────────────────────────────────────

function analyzeIPDirect(ip) {
    switchView('threat-analysis');
    document.getElementById('analysisIP').value = ip;
    analyzeIP();
}

async function analyzeIP() {
    const ip = document.getElementById('analysisIP').value.trim();
    if (!ip) return;

    const data = await apiGet(`/ips/${ip}/analyze`);
    if (!data) return;

    const panel = document.getElementById('analysisPanel');
    panel.classList.add('visible');

    const scoreEl = document.getElementById('analysisScore');
    scoreEl.textContent = data.threat_score.toFixed(0);
    scoreEl.style.border = `3px solid ${getThreatColorHex(data.threat_score)}`;
    scoreEl.style.color = getThreatColorHex(data.threat_score);

    document.getElementById('analysisIPDisplay').textContent = data.ip;

    const levelEl = document.getElementById('analysisThreatLevel');
    levelEl.textContent = data.threat_level.toUpperCase();
    levelEl.className = `badge badge-${data.threat_level}`;

    const geo = data.geo_info || {};
    document.getElementById('analysisGeo').textContent =
        `${geo.country_name || geo.country || 'Unknown'} ${geo.city ? '/ ' + geo.city : ''} ${geo.is_datacenter ? '(Datacenter: ' + geo.datacenter_name + ')' : ''}`;

    document.getElementById('riskFactors').innerHTML =
        (data.risk_factors || []).map(f => `<div class="risk-factor">${f}</div>`).join('')
        || '<p class="text-muted">No risk factors identified</p>';

    document.getElementById('recommendations').innerHTML =
        (data.recommendations || []).map(r => `<div class="recommendation">${r}</div>`).join('')
        || '<p class="text-muted">No specific recommendations</p>';

    const net = data.network_info || {};
    document.getElementById('networkInfo').innerHTML = `
        <div style="display:grid;gap:8px;">
            <div><span class="text-muted">ASN:</span> <span class="mono">${net.asn || 'N/A'}</span></div>
            <div><span class="text-muted">Organization:</span> ${net.org || 'N/A'}</div>
            <div><span class="text-muted">ISP:</span> ${net.isp || 'N/A'}</div>
            <div><span class="text-muted">VPN:</span> ${net.is_vpn ? '<span class="text-amber">Yes</span>' : 'No'}</div>
            <div><span class="text-muted">TOR:</span> ${net.is_tor ? '<span class="text-red">Yes</span>' : 'No'}</div>
            <div><span class="text-muted">Proxy:</span> ${net.is_proxy ? '<span class="text-amber">Yes</span>' : 'No'}</div>
        </div>
    `;

    const beh = data.behavioral_analysis || {};
    document.getElementById('behavioralInfo').innerHTML = `
        <div style="display:grid;gap:8px;">
            <div><span class="text-muted">Total Requests:</span> <span class="mono">${formatNum(beh.total_requests || 0)}</span></div>
            <div><span class="text-muted">Blocked Requests:</span> <span class="mono text-red">${formatNum(beh.blocked_requests || 0)}</span></div>
            <div><span class="text-muted">Block Ratio:</span> <span class="mono">${((beh.block_ratio || 0) * 100).toFixed(1)}%</span></div>
            <div><span class="text-muted">Reputation:</span> <span class="mono text-green">${data.reputation_score?.toFixed(1) || 'N/A'}</span></div>
        </div>
    `;
}

// ── Events ──────────────────────────────────────────────────────

async function loadEvents() {
    const data = await apiGet('/events?per_page=100');
    if (!data) return;

    const tbody = document.getElementById('eventsTableBody');
    tbody.innerHTML = (data.items || []).map(e => `
        <tr>
            <td class="mono text-muted" style="font-size:11px;">${e.id}</td>
            <td class="mono text-muted" style="font-size:11px;">${formatTime(e.timestamp)}</td>
            <td><span class="badge badge-info">${e.event_type}</span></td>
            <td><span class="badge badge-${e.threat_level}">${e.threat_level}</span></td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${e.description || '-'}</td>
            <td>${e.action_taken ? `<span class="badge badge-medium">${e.action_taken}</span>` : '-'}</td>
        </tr>
    `).join('') || '<tr><td colspan="6" class="text-muted" style="text-align:center;padding:30px;">No events recorded</td></tr>';
}

// ── Security Modules ────────────────────────────────────────────

async function loadModules() {
    const [ddos, rateLimit, portScans, bruteForce, anomalies] = await Promise.all([
        apiGet('/security/ddos'),
        apiGet('/security/rate-limiter'),
        apiGet('/security/port-scans'),
        apiGet('/security/brute-force'),
        apiGet('/security/anomalies'),
    ]);

    if (ddos) {
        document.getElementById('ddosStatus').innerHTML = ddos.under_attack
            ? '<span class="text-red">ATTACK DETECTED</span>'
            : '<span class="text-green">No attacks detected</span>';
        document.getElementById('ddosDetails').innerHTML = `
            <div style="display:grid;gap:8px;">
                <div><span class="text-muted">Under Attack:</span> ${ddos.under_attack ? '<span class="text-red">YES</span>' : '<span class="text-green">NO</span>'}</div>
                <div><span class="text-muted">Mitigation:</span> ${ddos.mitigation_active ? 'Active' : 'Standby'}</div>
                <div><span class="text-muted">Current RPS:</span> <span class="mono">${ddos.metrics?.current_rps || 0}</span></div>
                <div><span class="text-muted">Baseline RPS:</span> <span class="mono">${ddos.metrics?.baseline_rps || 0}</span></div>
                <div><span class="text-muted">Unique Sources:</span> <span class="mono">${ddos.metrics?.unique_sources || 0}</span></div>
                <div><span class="text-muted">Source Entropy:</span> <span class="mono">${ddos.metrics?.source_entropy || 0}</span></div>
            </div>
        `;
    }

    if (rateLimit) {
        document.getElementById('rateLimitStatus').innerHTML =
            `<span class="text-green">${rateLimit.active_buckets || 0} active buckets</span>`;
    }

    if (portScans) {
        const stats = portScans.stats || {};
        document.getElementById('portScanStatus').innerHTML =
            `<span class="text-cyan">${stats.total_detections || 0} detections</span>`;
        document.getElementById('portScanDetails').innerHTML = (portScans.active_scans || []).length > 0
            ? portScans.active_scans.map(s => `
                <div style="padding:8px 0;border-bottom:1px solid var(--border-color);">
                    <span class="ip-addr">${s.ip}</span> - ${s.unique_ports} ports, ${s.total_probes} probes
                </div>
            `).join('')
            : '<p class="text-muted" style="padding:12px 0;">No active port scans</p>';
    }

    if (bruteForce) {
        const stats = bruteForce.stats || {};
        document.getElementById('bruteForceStatus').innerHTML =
            `<span class="${stats.locked_ips > 0 ? 'text-red' : 'text-green'}">${stats.locked_ips || 0} IPs locked</span>`;
    }

    if (anomalies) {
        const stats = anomalies.stats || {};
        document.getElementById('anomalyStatus').innerHTML =
            `<span class="text-cyan">${stats.total_anomalies || 0} anomalies</span>`;
    }
}

// ── Rules ───────────────────────────────────────────────────────

async function loadRules() {
    const data = await apiGet('/rules');
    if (!data) return;

    const tbody = document.getElementById('rulesTableBody');
    tbody.innerHTML = (data || []).map(r => `
        <tr>
            <td style="font-weight:600;">${r.name}</td>
            <td class="mono text-muted">${r.rule_type}</td>
            <td><span class="badge badge-medium">${r.action}</span></td>
            <td class="mono">${r.priority}</td>
            <td class="mono text-cyan">${formatNum(r.hit_count)}</td>
            <td>${r.enabled ? '<span class="text-green">Active</span>' : '<span class="text-muted">Disabled</span>'}</td>
            <td><button class="btn btn-danger" style="padding:4px 8px;font-size:11px;" onclick="deleteRule(${r.id})">Delete</button></td>
        </tr>
    `).join('') || '<tr><td colspan="7" class="text-muted" style="text-align:center;padding:30px;">No rules configured</td></tr>';
}

async function deleteRule(id) {
    if (confirm('Delete this rule?')) {
        await apiDelete(`/rules/${id}`);
        loadRules();
    }
}

function showCreateRuleModal() {
    const name = prompt('Rule name:');
    if (!name) return;
    const ruleType = prompt('Rule type (ip_filter, rate_limit, geo_block, custom):') || 'custom';
    const action = prompt('Action (block, allow, rate_limit, quarantine, alert, log):') || 'block';
    const field = prompt('Condition field (e.g., ip, threat_score, country):') || 'threat_score';
    const op = prompt('Operator (eq, gt, lt, ge, le, contains, ip_in_range):') || 'ge';
    const value = prompt('Value:') || '80';

    let parsedValue = value;
    if (!isNaN(parseFloat(value))) parsedValue = parseFloat(value);

    apiPost('/rules', {
        name,
        rule_type: ruleType,
        action,
        priority: 100,
        conditions: { logic: 'and', rules: [{ field, operator: op, value: parsedValue }] },
    }).then(loadRules);
}

// ── Audit ───────────────────────────────────────────────────────

async function loadAudit() {
    const data = await apiGet('/audit');
    if (!data) return;

    const tbody = document.getElementById('auditTableBody');
    tbody.innerHTML = (data.items || []).map(l => `
        <tr>
            <td class="mono text-muted" style="font-size:11px;">${formatTime(l.timestamp)}</td>
            <td>${l.actor || 'system'}</td>
            <td><span class="badge badge-info">${l.action}</span></td>
            <td class="mono">${l.target_type ? l.target_type + ':' + (l.target_id || '') : '-'}</td>
            <td class="text-muted" style="font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;">${l.details ? JSON.stringify(l.details) : '-'}</td>
        </tr>
    `).join('') || '<tr><td colspan="5" class="text-muted" style="text-align:center;padding:30px;">No audit entries</td></tr>';
}

// ── WebSocket ───────────────────────────────────────────────────

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/live`);

    ws.onopen = () => {
        document.getElementById('wsStatus').className = 'pulse-dot active';
        document.getElementById('wsStatusText').textContent = 'Connected';
        ws.send(JSON.stringify({ type: 'subscribe', channels: ['threats', 'metrics', 'alerts'] }));
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleWSMessage(msg);
    };

    ws.onclose = () => {
        document.getElementById('wsStatus').className = 'pulse-dot warning';
        document.getElementById('wsStatusText').textContent = 'Reconnecting...';
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
        document.getElementById('wsStatus').className = 'pulse-dot danger';
        document.getElementById('wsStatusText').textContent = 'Error';
    };
}

function handleWSMessage(msg) {
    if (msg.type === 'threat_event') {
        liveEventCount++;
        document.getElementById('liveEventCount').textContent = liveEventCount;
        addToLiveFeed(msg);
    } else if (msg.type === 'alert') {
        const count = parseInt(document.getElementById('alertCount').textContent) + 1;
        document.getElementById('alertCount').textContent = count;
    }
}

function addToLiveFeed(msg) {
    const container = document.getElementById('liveFeedContent');
    const data = msg.data || {};
    const line = document.createElement('div');
    line.style.cssText = 'padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03);animation:fadeIn 0.3s;';
    line.innerHTML = `
        <span class="text-muted">[${formatTime(msg.timestamp)}]</span>
        <span class="badge badge-${data.threat_level || 'info'}" style="margin:0 4px;">${data.event_type || 'event'}</span>
        <span class="text-cyan">${data.ip || '-'}</span>
        <span class="text-muted"> - ${data.description || ''}</span>
    `;
    container.prepend(line);

    while (container.children.length > 500) {
        container.removeChild(container.lastChild);
    }
}

// ── Utilities ───────────────────────────────────────────────────

function formatNum(n) {
    if (n == null) return '0';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
}

function formatTime(ts) {
    if (!ts) return '-';
    const d = new Date(ts);
    if (isNaN(d.getTime())) return ts;
    return d.toLocaleTimeString('en-US', { hour12: false }) + ' ' + d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getThreatColor(score) {
    if (score >= 80) return 'text-red';
    if (score >= 60) return 'text-amber';
    if (score >= 30) return 'text-purple';
    return 'text-green';
}

function getThreatColorHex(score) {
    if (score >= 80) return '#ff375f';
    if (score >= 60) return '#ffaa00';
    if (score >= 30) return '#a855f7';
    return '#00ff88';
}

function getThreatGradient(score) {
    if (score >= 80) return 'linear-gradient(90deg, #ff375f, #ff6b81)';
    if (score >= 60) return 'linear-gradient(90deg, #ffaa00, #ffc34d)';
    if (score >= 30) return 'linear-gradient(90deg, #a855f7, #c084fc)';
    return 'linear-gradient(90deg, #00ff88, #4ade80)';
}

// ── Clock ───────────────────────────────────────────────────────

function updateClock() {
    const now = new Date();
    document.getElementById('currentTime').textContent =
        now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC';
}

// ── Global Search ───────────────────────────────────────────────

document.getElementById('globalSearch').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(val) || val.includes(':')) {
            analyzeIPDirect(val);
        }
    }
});

// ── Init ────────────────────────────────────────────────────────

(async function init() {
    if (!token) {
        window.location.href = '/login';
        return;
    }

    updateClock();
    setInterval(updateClock, 1000);

    await refreshDashboard();
    connectWebSocket();

    setInterval(refreshDashboard, 30000);
})();
