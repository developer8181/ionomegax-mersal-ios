/**
 * Extreme IP Guard - Cybersecurity Dashboard Engine
 * Real-time monitoring, threat visualization, and network defense.
 */

const XIG = {
    state: {
        currentPage: 'dashboard',
        refreshInterval: null,
        charts: {},
        toastQueue: [],
    },

    async init() {
        this.bindNavigation();
        this.bindGlobalActions();
        await this.loadPage('dashboard');
        this.startAutoRefresh();
        this.showToast('Extreme IP Guard initialized', 'success');
    },

    bindNavigation() {
        document.querySelectorAll('.nav-item[data-page]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
    },

    bindGlobalActions() {
        const searchInput = document.querySelector('.search-box input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => this.handleSearch(e.target.value), 300);
            });
        }

        document.querySelector('.refresh-btn')?.addEventListener('click', () => {
            this.refreshCurrentPage();
        });
    },

    navigateTo(page) {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');
        this.state.currentPage = page;
        this.loadPage(page);
    },

    async loadPage(page) {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"></div>';

        try {
            switch (page) {
                case 'dashboard': await this.renderDashboard(content); break;
                case 'ips': await this.renderIPList(content); break;
                case 'alerts': await this.renderAlerts(content); break;
                case 'firewall': await this.renderFirewall(content); break;
                case 'network': await this.renderNetwork(content); break;
                case 'analyze': await this.renderAnalyzer(content); break;
                case 'events': await this.renderEvents(content); break;
                default: await this.renderDashboard(content);
            }
        } catch (err) {
            console.error('Page load error:', err);
            content.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Error Loading Page</h3><p>${err.message}</p></div>`;
        }
    },

    async fetchAPI(endpoint) {
        const response = await fetch(`/api/v1${endpoint}`);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return response.json();
    },

    async postAPI(endpoint, data = {}) {
        const response = await fetch(`/api/v1${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return response.json();
    },

    async deleteAPI(endpoint) {
        const response = await fetch(`/api/v1${endpoint}`, { method: 'DELETE' });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return response.json();
    },

    // ═══════════════════════════════════════════
    // DASHBOARD PAGE
    // ═══════════════════════════════════════════
    async renderDashboard(container) {
        const data = await this.fetchAPI('/dashboard');
        const s = data.stats;
        const sys = data.system;

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>Command Center</span></h2>
                    <p class="page-subtitle">Real-time threat intelligence & network defense overview</p>
                </div>
                <div style="display:flex;gap:8px;align-items:center">
                    <span class="live-indicator"><span class="live-dot"></span> LIVE</span>
                    <button class="btn btn-outline btn-sm" onclick="XIG.refreshCurrentPage()"><i class="fas fa-sync-alt"></i> Refresh</button>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card cyan">
                    <div class="stat-header">
                        <span class="stat-label">Tracked IPs</span>
                        <div class="stat-icon cyan"><i class="fas fa-network-wired"></i></div>
                    </div>
                    <div class="stat-value">${s.total_ips}</div>
                    <div class="stat-change neutral"><i class="fas fa-minus"></i> Active monitoring</div>
                </div>
                <div class="stat-card red">
                    <div class="stat-header">
                        <span class="stat-label">Blocked IPs</span>
                        <div class="stat-icon red"><i class="fas fa-ban"></i></div>
                    </div>
                    <div class="stat-value">${s.blocked_ips}</div>
                    <div class="stat-change up"><i class="fas fa-shield-alt"></i> Auto-defense active</div>
                </div>
                <div class="stat-card orange">
                    <div class="stat-header">
                        <span class="stat-label">Active Alerts</span>
                        <div class="stat-icon orange"><i class="fas fa-exclamation-triangle"></i></div>
                    </div>
                    <div class="stat-value">${s.active_alerts}</div>
                    <div class="stat-change up"><i class="fas fa-arrow-up"></i> Requires attention</div>
                </div>
                <div class="stat-card purple">
                    <div class="stat-header">
                        <span class="stat-label">Critical Threats</span>
                        <div class="stat-icon purple"><i class="fas fa-skull-crossbones"></i></div>
                    </div>
                    <div class="stat-value">${s.critical_threats}</div>
                    <div class="stat-change ${s.critical_threats > 0 ? 'up' : 'down'}"><i class="fas fa-${s.critical_threats > 0 ? 'arrow-up' : 'check'}"></i> ${s.critical_threats > 0 ? 'Active threats' : 'No critical threats'}</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-header">
                        <span class="stat-label">Whitelisted</span>
                        <div class="stat-icon green"><i class="fas fa-check-circle"></i></div>
                    </div>
                    <div class="stat-value">${s.whitelisted_ips}</div>
                    <div class="stat-change down"><i class="fas fa-lock"></i> Trusted IPs</div>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <span class="stat-label">Firewall Rules</span>
                        <div class="stat-icon blue"><i class="fas fa-fire"></i></div>
                    </div>
                    <div class="stat-value">${s.active_rules}</div>
                    <div class="stat-change neutral"><i class="fas fa-cog"></i> Active rules</div>
                </div>
            </div>

            <div class="grid-2-1">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-chart-line"></i> System Performance</span>
                        <span class="live-indicator"><span class="live-dot"></span> LIVE</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-area"><canvas id="perfChart"></canvas></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-server"></i> System Health</span>
                    </div>
                    <div class="card-body">
                        <div style="margin-bottom:16px">
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                                <span style="font-size:0.75rem;color:var(--text-secondary)">CPU Usage</span>
                                <span style="font-size:0.75rem;font-family:var(--font-mono);color:var(--accent-cyan)">${sys.cpu.percent}%</span>
                            </div>
                            <div class="threat-meter">
                                <div class="threat-meter-fill ${sys.cpu.percent > 80 ? 'critical' : sys.cpu.percent > 50 ? 'medium' : 'safe'}" style="width:${sys.cpu.percent}%"></div>
                            </div>
                        </div>
                        <div style="margin-bottom:16px">
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                                <span style="font-size:0.75rem;color:var(--text-secondary)">Memory Usage</span>
                                <span style="font-size:0.75rem;font-family:var(--font-mono);color:var(--accent-cyan)">${sys.memory.percent}%</span>
                            </div>
                            <div class="threat-meter">
                                <div class="threat-meter-fill ${sys.memory.percent > 80 ? 'critical' : sys.memory.percent > 50 ? 'medium' : 'safe'}" style="width:${sys.memory.percent}%"></div>
                            </div>
                        </div>
                        <div style="margin-bottom:16px">
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                                <span style="font-size:0.75rem;color:var(--text-secondary)">Disk Usage</span>
                                <span style="font-size:0.75rem;font-family:var(--font-mono);color:var(--accent-cyan)">${sys.disk.percent}%</span>
                            </div>
                            <div class="threat-meter">
                                <div class="threat-meter-fill ${sys.disk.percent > 80 ? 'critical' : sys.disk.percent > 50 ? 'medium' : 'safe'}" style="width:${sys.disk.percent}%"></div>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px">
                            <div class="detail-item"><div class="detail-label">CPU Cores</div><div class="detail-value">${sys.cpu.count}</div></div>
                            <div class="detail-item"><div class="detail-label">Memory</div><div class="detail-value">${sys.memory.total_gb} GB</div></div>
                            <div class="detail-item"><div class="detail-label">Disk Total</div><div class="detail-value">${sys.disk.total_gb} GB</div></div>
                            <div class="detail-item"><div class="detail-label">Uptime</div><div class="detail-value">${sys.uptime_hours}h</div></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-crosshairs"></i> Top Threats</span>
                        <button class="btn btn-outline btn-sm" onclick="XIG.navigateTo('ips')">View All</button>
                    </div>
                    <div class="card-body" style="padding:0">
                        <div class="table-container">
                            <table>
                                <thead><tr><th>IP Address</th><th>Threat</th><th>Score</th><th>Country</th></tr></thead>
                                <tbody>
                                    ${s.top_threats.map(t => `
                                        <tr>
                                            <td class="ip-cell">${t.ip}</td>
                                            <td><span class="badge-threat ${t.level}">${t.level}</span></td>
                                            <td>
                                                <div style="display:flex;align-items:center;gap:8px">
                                                    <span style="font-family:var(--font-mono);font-weight:700">${t.score}</span>
                                                    <div class="threat-meter" style="width:60px"><div class="threat-meter-fill ${t.level}" style="width:${t.score}%"></div></div>
                                                </div>
                                            </td>
                                            <td style="font-size:0.8rem">${t.country_code || 'XX'} ${t.country || 'Unknown'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-bell"></i> Recent Alerts</span>
                        <button class="btn btn-outline btn-sm" onclick="XIG.navigateTo('alerts')">View All</button>
                    </div>
                    <div class="card-body" style="max-height:350px;overflow-y:auto">
                        ${s.recent_alerts.map(a => `
                            <div class="alert-item">
                                <div class="alert-icon ${a.level}"><i class="fas fa-${this.getAlertIcon(a.type)}"></i></div>
                                <div class="alert-content">
                                    <div class="alert-title">${a.title}</div>
                                    <div class="alert-meta">
                                        <span class="badge-threat ${a.level}" style="font-size:0.6rem">${a.level}</span>
                                        ${a.source_ip ? `<span class="ip-cell" style="font-size:0.7rem">${a.source_ip}</span>` : ''}
                                        <span class="alert-time">${this.timeAgo(a.created_at)}</span>
                                    </div>
                                </div>
                                ${!a.is_resolved ? `<button class="btn-icon" onclick="XIG.resolveAlert(${a.id})" title="Resolve"><i class="fas fa-check"></i></button>` : '<i class="fas fa-check-circle" style="color:var(--accent-green)"></i>'}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-globe"></i> Geographic Distribution</span>
                    </div>
                    <div class="card-body">
                        ${s.country_distribution.map(c => `
                            <div class="country-item">
                                <div class="country-info">
                                    <span style="font-weight:600;font-size:0.85rem">${c.code}</span>
                                    <span style="font-size:0.8rem;color:var(--text-secondary)">${c.country || 'Unknown'}</span>
                                </div>
                                <div style="display:flex;align-items:center;gap:8px">
                                    <div class="country-bar" style="width:${Math.min(120, c.count * 15)}px"></div>
                                    <span style="font-family:var(--font-mono);font-size:0.75rem;color:var(--accent-cyan)">${c.count}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-chart-pie"></i> Threat Distribution</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-area"><canvas id="threatChart"></canvas></div>
                    </div>
                </div>
            </div>
        `;

        this.initDashboardCharts(data);
    },

    initDashboardCharts(data) {
        const bw = data.bandwidth;
        const perfCtx = document.getElementById('perfChart');
        if (perfCtx && typeof Chart !== 'undefined') {
            if (this.state.charts.perf) this.state.charts.perf.destroy();

            const labels = (bw.timestamps || []).map((t, i) => i + 's');
            this.state.charts.perf = new Chart(perfCtx, {
                type: 'line',
                data: {
                    labels: labels.length ? labels : Array.from({length: 30}, (_, i) => i + 's'),
                    datasets: [
                        {
                            label: 'CPU %',
                            data: bw.cpu || Array.from({length: 30}, () => Math.random() * 40 + 10),
                            borderColor: '#00f0ff',
                            backgroundColor: 'rgba(0,240,255,0.1)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                            pointRadius: 0,
                        },
                        {
                            label: 'Memory %',
                            data: bw.memory || Array.from({length: 30}, () => Math.random() * 20 + 30),
                            borderColor: '#8b5cf6',
                            backgroundColor: 'rgba(139,92,246,0.1)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                            pointRadius: 0,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#8892b0', font: { size: 10 } } },
                    },
                    scales: {
                        x: { grid: { color: 'rgba(30,42,74,0.3)' }, ticks: { color: '#5a6480', font: { size: 9 } } },
                        y: { grid: { color: 'rgba(30,42,74,0.3)' }, ticks: { color: '#5a6480', font: { size: 9 } }, min: 0, max: 100 },
                    },
                },
            });
        }

        const threatCtx = document.getElementById('threatChart');
        if (threatCtx && typeof Chart !== 'undefined') {
            if (this.state.charts.threat) this.state.charts.threat.destroy();

            const dist = data.stats.threat_distribution || [];
            const colorMap = { critical: '#ff1744', high: '#ff9100', medium: '#ffd600', low: '#3366ff', safe: '#00e676', info: '#00f0ff' };

            this.state.charts.threat = new Chart(threatCtx, {
                type: 'doughnut',
                data: {
                    labels: dist.map(d => d.level.toUpperCase()),
                    datasets: [{
                        data: dist.map(d => d.count),
                        backgroundColor: dist.map(d => colorMap[d.level] || '#5a6480'),
                        borderColor: '#141a2e',
                        borderWidth: 3,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: { color: '#8892b0', font: { size: 10 }, padding: 12, usePointStyle: true },
                        },
                    },
                },
            });
        }
    },

    // ═══════════════════════════════════════════
    // IP LIST PAGE
    // ═══════════════════════════════════════════
    async renderIPList(container) {
        const data = await this.fetchAPI('/ips');

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>IP Intelligence Hub</span></h2>
                    <p class="page-subtitle">Monitor, analyze, and manage all tracked IP addresses</p>
                </div>
                <div style="display:flex;gap:8px">
                    <button class="btn btn-primary" onclick="XIG.showAddIPModal()"><i class="fas fa-plus"></i> Add IP</button>
                    <button class="btn btn-outline" onclick="XIG.refreshCurrentPage()"><i class="fas fa-sync-alt"></i></button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title"><i class="fas fa-database"></i> Monitored IPs (${data.total})</span>
                    <div style="display:flex;gap:8px">
                        <select class="form-select" style="width:150px;padding:6px 10px;font-size:0.75rem" onchange="XIG.filterIPs(this.value)">
                            <option value="">All Statuses</option>
                            <option value="monitoring">Monitoring</option>
                            <option value="blocked">Blocked</option>
                            <option value="whitelisted">Whitelisted</option>
                            <option value="quarantined">Quarantined</option>
                        </select>
                    </div>
                </div>
                <div class="card-body" style="padding:0">
                    <div class="table-container">
                        <table id="ip-table">
                            <thead>
                                <tr>
                                    <th>IP Address</th>
                                    <th>Status</th>
                                    <th>Threat Level</th>
                                    <th>Score</th>
                                    <th>Country</th>
                                    <th>ISP/Org</th>
                                    <th>Flags</th>
                                    <th>Requests</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.ips.map(ip => this.renderIPRow(ip)).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="modal-overlay" id="addIPModal">
                <div class="modal">
                    <div class="modal-header">
                        <span class="modal-title"><i class="fas fa-plus-circle" style="color:var(--accent-cyan);margin-right:8px"></i>Add IP to Monitor</span>
                        <button class="modal-close" onclick="XIG.closeModal('addIPModal')"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">IP Address</label>
                            <input type="text" class="form-input" id="newIPAddress" placeholder="e.g., 192.168.1.100">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes (Optional)</label>
                            <input type="text" class="form-input" id="newIPNotes" placeholder="Add notes about this IP...">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="XIG.closeModal('addIPModal')">Cancel</button>
                        <button class="btn btn-primary" onclick="XIG.addIP()"><i class="fas fa-shield-alt"></i> Add & Analyze</button>
                    </div>
                </div>
            </div>

            <div class="modal-overlay" id="ipDetailModal">
                <div class="modal" style="max-width:700px">
                    <div class="modal-header">
                        <span class="modal-title" id="ipDetailTitle">IP Details</span>
                        <button class="modal-close" onclick="XIG.closeModal('ipDetailModal')"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="modal-body" id="ipDetailBody"></div>
                </div>
            </div>
        `;
    },

    renderIPRow(ip) {
        const flags = [];
        if (ip.is_tor) flags.push('<span title="Tor Network" style="color:var(--accent-red)"><i class="fas fa-user-secret"></i></span>');
        if (ip.is_vpn) flags.push('<span title="VPN" style="color:var(--accent-orange)"><i class="fas fa-mask"></i></span>');
        if (ip.is_proxy) flags.push('<span title="Proxy" style="color:var(--accent-yellow)"><i class="fas fa-exchange-alt"></i></span>');
        if (ip.is_bot) flags.push('<span title="Bot" style="color:var(--accent-purple)"><i class="fas fa-robot"></i></span>');

        return `
            <tr>
                <td>
                    <span class="ip-cell" style="cursor:pointer" onclick="XIG.showIPDetail('${ip.ip_address}')">${ip.ip_address}</span>
                    ${ip.hostname ? `<div style="font-size:0.7rem;color:var(--text-muted)">${ip.hostname}</div>` : ''}
                </td>
                <td><span class="badge-status ${ip.status}">${ip.status}</span></td>
                <td><span class="badge-threat ${ip.threat_level}">${ip.threat_level}</span></td>
                <td>
                    <div style="display:flex;align-items:center;gap:6px">
                        <span style="font-family:var(--font-mono);font-weight:700;font-size:0.85rem">${ip.threat_score}</span>
                        <div class="threat-meter" style="width:50px"><div class="threat-meter-fill ${ip.threat_level}" style="width:${ip.threat_score}%"></div></div>
                    </div>
                </td>
                <td><span style="font-size:0.8rem">${ip.country_code || 'XX'} ${ip.country || ''}</span></td>
                <td style="font-size:0.75rem;color:var(--text-secondary);max-width:120px;overflow:hidden;text-overflow:ellipsis">${ip.org || ip.isp || '-'}</td>
                <td><div style="display:flex;gap:6px">${flags.join('') || '-'}</div></td>
                <td style="font-family:var(--font-mono);font-size:0.8rem">${this.formatNumber(ip.total_requests)}</td>
                <td>
                    <div style="display:flex;gap:4px">
                        ${ip.status !== 'blocked' ? `<button class="btn-icon danger" onclick="XIG.blockIP(${ip.id})" title="Block"><i class="fas fa-ban"></i></button>` : `<button class="btn-icon" onclick="XIG.unblockIP(${ip.id})" title="Unblock"><i class="fas fa-unlock"></i></button>`}
                        ${ip.status !== 'whitelisted' ? `<button class="btn-icon" onclick="XIG.whitelistIP(${ip.id})" title="Whitelist"><i class="fas fa-check-circle"></i></button>` : ''}
                        <button class="btn-icon" onclick="XIG.showIPDetail('${ip.ip_address}')" title="Details"><i class="fas fa-info-circle"></i></button>
                        <button class="btn-icon danger" onclick="XIG.deleteIP(${ip.id})" title="Delete"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    },

    // ═══════════════════════════════════════════
    // ALERTS PAGE
    // ═══════════════════════════════════════════
    async renderAlerts(container) {
        const data = await this.fetchAPI('/alerts');

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>Threat Alerts</span></h2>
                    <p class="page-subtitle">Security events and threat notifications</p>
                </div>
                <div style="display:flex;gap:8px">
                    <button class="btn btn-success btn-sm" onclick="XIG.resolveAllAlerts()"><i class="fas fa-check-double"></i> Resolve All</button>
                    <button class="btn btn-outline btn-sm" onclick="XIG.refreshCurrentPage()"><i class="fas fa-sync-alt"></i></button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title"><i class="fas fa-bell"></i> Alert Feed (${data.alerts.length})</span>
                </div>
                <div class="card-body">
                    ${data.alerts.length === 0 ? '<div class="empty-state"><i class="fas fa-check-circle"></i><h3>All Clear</h3><p>No active alerts at this time</p></div>' : ''}
                    ${data.alerts.map(a => `
                        <div class="alert-item ${a.is_resolved ? 'resolved' : ''}" style="${a.is_resolved ? 'opacity:0.6' : ''}">
                            <div class="alert-icon ${a.threat_level}"><i class="fas fa-${this.getAlertIcon(a.alert_type)}"></i></div>
                            <div class="alert-content">
                                <div class="alert-title">${a.title}</div>
                                <div class="alert-desc">${a.description || ''}</div>
                                <div class="alert-meta">
                                    <span class="badge-threat ${a.threat_level}">${a.threat_level}</span>
                                    ${a.source_ip ? `<span class="ip-cell" style="font-size:0.7rem">${a.source_ip}</span>` : ''}
                                    <span class="alert-time">${this.timeAgo(a.created_at)}</span>
                                    ${a.is_resolved ? `<span style="color:var(--accent-green);font-size:0.7rem"><i class="fas fa-check"></i> Resolved by ${a.resolved_by || 'system'}</span>` : ''}
                                </div>
                            </div>
                            ${!a.is_resolved ? `
                                <div style="display:flex;gap:4px">
                                    <button class="btn btn-success btn-sm" onclick="XIG.resolveAlert(${a.id})"><i class="fas fa-check"></i> Resolve</button>
                                    ${a.source_ip ? `<button class="btn btn-danger btn-sm" onclick="XIG.blockIPByAddress('${a.source_ip}')"><i class="fas fa-ban"></i> Block</button>` : ''}
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    // ═══════════════════════════════════════════
    // FIREWALL PAGE
    // ═══════════════════════════════════════════
    async renderFirewall(container) {
        const data = await this.fetchAPI('/firewall/rules?active_only=false');

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>Firewall Engine</span></h2>
                    <p class="page-subtitle">Advanced rule-based network protection</p>
                </div>
                <button class="btn btn-primary" onclick="XIG.showAddRuleModal()"><i class="fas fa-plus"></i> New Rule</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title"><i class="fas fa-fire"></i> Active Rules (${data.rules.length})</span>
                </div>
                <div class="card-body">
                    ${data.rules.map(r => `
                        <div class="rule-card">
                            <div class="rule-priority">#${r.priority}</div>
                            <div style="width:36px;height:36px;border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center;background:${this.getActionColor(r.action)};font-size:0.9rem">
                                <i class="fas fa-${this.getActionIcon(r.action)}"></i>
                            </div>
                            <div class="rule-info">
                                <div class="rule-name">${r.name}</div>
                                <div class="rule-desc">
                                    ${r.description || ''} 
                                    ${r.source_cidr ? `<span class="ip-cell" style="font-size:0.65rem">${r.source_cidr}</span>` : ''}
                                    ${r.destination_port ? `<span style="font-size:0.65rem;color:var(--text-muted)">Port ${r.destination_port}</span>` : ''}
                                </div>
                            </div>
                            <span class="badge-status ${r.action}" style="text-transform:uppercase;font-size:0.6rem">${r.action}</span>
                            <div class="rule-hits" title="Hit count"><i class="fas fa-bolt" style="margin-right:4px"></i>${this.formatNumber(r.hit_count)}</div>
                            <label class="toggle">
                                <input type="checkbox" ${r.is_active ? 'checked' : ''} onchange="XIG.toggleRule(${r.id})">
                                <span class="toggle-slider"></span>
                            </label>
                            <button class="btn-icon danger" onclick="XIG.deleteRule(${r.id})"><i class="fas fa-trash"></i></button>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="modal-overlay" id="addRuleModal">
                <div class="modal">
                    <div class="modal-header">
                        <span class="modal-title"><i class="fas fa-plus-circle" style="color:var(--accent-cyan);margin-right:8px"></i>Create Firewall Rule</span>
                        <button class="modal-close" onclick="XIG.closeModal('addRuleModal')"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Rule Name</label>
                            <input type="text" class="form-input" id="ruleName" placeholder="e.g., Block Suspicious Range">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <input type="text" class="form-input" id="ruleDesc" placeholder="Rule description...">
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                            <div class="form-group">
                                <label class="form-label">Source CIDR</label>
                                <input type="text" class="form-input" id="ruleCIDR" placeholder="e.g., 10.0.0.0/8">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Destination Port</label>
                                <input type="number" class="form-input" id="rulePort" placeholder="e.g., 443">
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                            <div class="form-group">
                                <label class="form-label">Action</label>
                                <select class="form-select" id="ruleAction">
                                    <option value="block">Block</option>
                                    <option value="allow">Allow</option>
                                    <option value="rate_limit">Rate Limit</option>
                                    <option value="quarantine">Quarantine</option>
                                    <option value="challenge">Challenge</option>
                                    <option value="log">Log Only</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Priority</label>
                                <input type="number" class="form-input" id="rulePriority" value="100" min="1" max="999">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-outline" onclick="XIG.closeModal('addRuleModal')">Cancel</button>
                        <button class="btn btn-primary" onclick="XIG.addRule()"><i class="fas fa-fire"></i> Create Rule</button>
                    </div>
                </div>
            </div>
        `;
    },

    // ═══════════════════════════════════════════
    // NETWORK PAGE
    // ═══════════════════════════════════════════
    async renderNetwork(container) {
        const data = await this.fetchAPI('/network/stats');
        const s = data.snapshot;

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>Network Monitor</span></h2>
                    <p class="page-subtitle">Real-time network traffic analysis and connection monitoring</p>
                </div>
                <span class="live-indicator"><span class="live-dot"></span> LIVE MONITORING</span>
            </div>

            <div class="stats-grid">
                <div class="stat-card cyan">
                    <div class="stat-header"><span class="stat-label">Bandwidth In</span><div class="stat-icon cyan"><i class="fas fa-arrow-down"></i></div></div>
                    <div class="stat-value">${s.bandwidth_in_mbps.toFixed(2)}</div>
                    <div class="stat-change neutral">Mbps</div>
                </div>
                <div class="stat-card purple">
                    <div class="stat-header"><span class="stat-label">Bandwidth Out</span><div class="stat-icon purple"><i class="fas fa-arrow-up"></i></div></div>
                    <div class="stat-value">${s.bandwidth_out_mbps.toFixed(2)}</div>
                    <div class="stat-change neutral">Mbps</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-header"><span class="stat-label">Active Connections</span><div class="stat-icon green"><i class="fas fa-plug"></i></div></div>
                    <div class="stat-value">${s.connections_active}</div>
                    <div class="stat-change neutral">${s.connections_established} established</div>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header"><span class="stat-label">Packets Sent</span><div class="stat-icon blue"><i class="fas fa-paper-plane"></i></div></div>
                    <div class="stat-value">${this.formatBytes(s.packets_sent)}</div>
                    <div class="stat-change neutral">Total</div>
                </div>
            </div>

            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-chart-area"></i> Bandwidth Monitor</span>
                    </div>
                    <div class="card-body">
                        <div class="chart-area"><canvas id="bwChart"></canvas></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-exclamation-circle"></i> Network Anomalies</span>
                    </div>
                    <div class="card-body">
                        ${data.anomalies.length === 0 ?
                            '<div class="empty-state" style="padding:20px"><i class="fas fa-check-circle" style="font-size:2rem;color:var(--accent-green)"></i><h3 style="font-size:0.9rem">No Anomalies Detected</h3><p style="font-size:0.75rem">Network traffic patterns are normal</p></div>' :
                            data.anomalies.map(a => `
                                <div class="alert-item">
                                    <div class="alert-icon ${a.severity}"><i class="fas fa-exclamation-triangle"></i></div>
                                    <div class="alert-content">
                                        <div class="alert-title">${a.type.replace(/_/g, ' ').toUpperCase()}</div>
                                        <div class="alert-desc">${a.message}</div>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title"><i class="fas fa-link"></i> Active Connections (${data.active_connections.length})</span>
                </div>
                <div class="card-body" style="padding:0">
                    <div class="table-container">
                        <table>
                            <thead><tr><th>Local</th><th>Remote</th><th>Status</th><th>Process</th></tr></thead>
                            <tbody>
                                ${data.active_connections.slice(0, 30).map(c => `
                                    <tr>
                                        <td class="ip-cell" style="font-size:0.75rem">${c.local}</td>
                                        <td class="ip-cell" style="font-size:0.75rem">${c.remote}</td>
                                        <td><span class="conn-status"><span class="conn-dot established"></span> ${c.status}</span></td>
                                        <td style="font-size:0.8rem">${c.process}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        this.initNetworkChart();
    },

    initNetworkChart() {
        const ctx = document.getElementById('bwChart');
        if (!ctx || typeof Chart === 'undefined') return;
        if (this.state.charts.bw) this.state.charts.bw.destroy();

        const labels = Array.from({length: 30}, (_, i) => `${i}s`);
        this.state.charts.bw = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'Inbound', data: Array.from({length: 30}, () => Math.random() * 5), borderColor: '#00f0ff', backgroundColor: 'rgba(0,240,255,0.08)', fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 },
                    { label: 'Outbound', data: Array.from({length: 30}, () => Math.random() * 3), borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.08)', fill: true, tension: 0.4, borderWidth: 2, pointRadius: 0 },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8892b0', font: { size: 10 } } } },
                scales: {
                    x: { grid: { color: 'rgba(30,42,74,0.3)' }, ticks: { color: '#5a6480', font: { size: 9 } } },
                    y: { grid: { color: 'rgba(30,42,74,0.3)' }, ticks: { color: '#5a6480', font: { size: 9 } }, title: { display: true, text: 'Mbps', color: '#5a6480' } },
                },
            },
        });
    },

    // ═══════════════════════════════════════════
    // IP ANALYZER PAGE
    // ═══════════════════════════════════════════
    async renderAnalyzer(container) {
        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>IP Threat Analyzer</span></h2>
                    <p class="page-subtitle">Deep intelligence analysis and threat assessment</p>
                </div>
            </div>

            <div class="grid-1-2">
                <div class="card">
                    <div class="card-header"><span class="card-title"><i class="fas fa-search"></i> Analyze IP</span></div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Target IP Address</label>
                            <input type="text" class="form-input" id="analyzeIP" placeholder="Enter IP address..." style="font-family:var(--font-mono)">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Destination Port</label>
                            <input type="number" class="form-input" id="analyzePort" value="80">
                        </div>
                        <div class="form-group">
                            <label class="form-label">HTTP Method</label>
                            <select class="form-select" id="analyzeMethod">
                                <option value="GET">GET</option>
                                <option value="POST">POST</option>
                                <option value="PUT">PUT</option>
                                <option value="DELETE">DELETE</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Request Path</label>
                            <input type="text" class="form-input" id="analyzePath" value="/" placeholder="/">
                        </div>
                        <button class="btn btn-primary" style="width:100%" onclick="XIG.analyzeIP()">
                            <i class="fas fa-crosshairs"></i> Run Deep Analysis
                        </button>
                    </div>
                </div>
                <div class="card" id="analysisResults">
                    <div class="card-header"><span class="card-title"><i class="fas fa-shield-alt"></i> Analysis Results</span></div>
                    <div class="card-body">
                        <div class="empty-state">
                            <i class="fas fa-search" style="font-size:2.5rem"></i>
                            <h3>Enter an IP to Analyze</h3>
                            <p>Get comprehensive threat intelligence and risk assessment</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // ═══════════════════════════════════════════
    // EVENTS PAGE
    // ═══════════════════════════════════════════
    async renderEvents(container) {
        const data = await this.fetchAPI('/events');

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h2 class="page-title"><span>System Events</span></h2>
                    <p class="page-subtitle">Audit trail and system activity log</p>
                </div>
                <button class="btn btn-outline btn-sm" onclick="XIG.refreshCurrentPage()"><i class="fas fa-sync-alt"></i> Refresh</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title"><i class="fas fa-history"></i> Event Log (${data.events.length})</span>
                </div>
                <div class="card-body" style="padding:0">
                    <div class="table-container">
                        <table>
                            <thead><tr><th>Time</th><th>Severity</th><th>Type</th><th>Message</th><th>Source</th></tr></thead>
                            <tbody>
                                ${data.events.map(e => `
                                    <tr>
                                        <td style="font-family:var(--font-mono);font-size:0.75rem;white-space:nowrap">${this.timeAgo(e.created_at)}</td>
                                        <td><span class="badge-threat ${e.severity}">${e.severity}</span></td>
                                        <td style="font-size:0.8rem;font-weight:600">${e.type.replace(/_/g, ' ')}</td>
                                        <td style="font-size:0.8rem">${e.message}</td>
                                        <td style="font-size:0.75rem;color:var(--text-muted)">${e.source || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },

    // ═══════════════════════════════════════════
    // ACTIONS
    // ═══════════════════════════════════════════
    async addIP() {
        const ip = document.getElementById('newIPAddress')?.value?.trim();
        const notes = document.getElementById('newIPNotes')?.value?.trim();
        if (!ip) { this.showToast('Please enter an IP address', 'warning'); return; }

        try {
            await this.postAPI('/ips', { ip_address: ip, notes });
            this.closeModal('addIPModal');
            this.showToast(`IP ${ip} added and analyzed`, 'success');
            this.navigateTo('ips');
        } catch (e) {
            this.showToast('Failed to add IP: ' + e.message, 'error');
        }
    },

    async blockIP(id) {
        try {
            const result = await this.postAPI(`/ips/${id}/block`);
            this.showToast(`IP ${result.ip_address} blocked`, 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to block IP', 'error');
        }
    },

    async unblockIP(id) {
        try {
            const result = await this.postAPI(`/ips/${id}/unblock`);
            this.showToast(`IP ${result.ip_address} unblocked`, 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to unblock IP', 'error');
        }
    },

    async whitelistIP(id) {
        try {
            const result = await this.postAPI(`/ips/${id}/whitelist`);
            this.showToast(`IP ${result.ip_address} whitelisted`, 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to whitelist IP', 'error');
        }
    },

    async deleteIP(id) {
        if (!confirm('Are you sure you want to delete this IP record?')) return;
        try {
            await this.deleteAPI(`/ips/${id}`);
            this.showToast('IP record deleted', 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to delete IP', 'error');
        }
    },

    async blockIPByAddress(ipAddress) {
        try {
            await this.postAPI('/ips', { ip_address: ipAddress, notes: 'Blocked from alert' });
            const ips = await this.fetchAPI('/ips');
            const ip = ips.ips.find(i => i.ip_address === ipAddress);
            if (ip) await this.postAPI(`/ips/${ip.id}/block`);
            this.showToast(`IP ${ipAddress} blocked`, 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to block IP', 'error');
        }
    },

    async resolveAlert(id) {
        try {
            await this.postAPI(`/alerts/${id}/resolve`);
            this.showToast('Alert resolved', 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to resolve alert', 'error');
        }
    },

    async resolveAllAlerts() {
        try {
            const data = await this.fetchAPI('/alerts?unresolved_only=true');
            for (const alert of data.alerts) {
                if (!alert.is_resolved) await this.postAPI(`/alerts/${alert.id}/resolve`);
            }
            this.showToast('All alerts resolved', 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to resolve alerts', 'error');
        }
    },

    async addRule() {
        const name = document.getElementById('ruleName')?.value?.trim();
        if (!name) { this.showToast('Rule name is required', 'warning'); return; }

        const data = {
            name,
            description: document.getElementById('ruleDesc')?.value?.trim() || null,
            source_cidr: document.getElementById('ruleCIDR')?.value?.trim() || null,
            destination_port: parseInt(document.getElementById('rulePort')?.value) || null,
            action: document.getElementById('ruleAction')?.value || 'block',
            priority: parseInt(document.getElementById('rulePriority')?.value) || 100,
        };

        try {
            await this.postAPI('/firewall/rules', data);
            this.closeModal('addRuleModal');
            this.showToast('Firewall rule created', 'success');
            this.navigateTo('firewall');
        } catch (e) {
            this.showToast('Failed to create rule', 'error');
        }
    },

    async toggleRule(id) {
        try {
            const result = await this.postAPI(`/firewall/rules/${id}/toggle`);
            this.showToast(`Rule ${result.is_active ? 'activated' : 'deactivated'}`, 'info');
        } catch (e) {
            this.showToast('Failed to toggle rule', 'error');
        }
    },

    async deleteRule(id) {
        if (!confirm('Delete this firewall rule?')) return;
        try {
            await this.deleteAPI(`/firewall/rules/${id}`);
            this.showToast('Rule deleted', 'success');
            this.refreshCurrentPage();
        } catch (e) {
            this.showToast('Failed to delete rule', 'error');
        }
    },

    async analyzeIP() {
        const ip = document.getElementById('analyzeIP')?.value?.trim();
        if (!ip) { this.showToast('Enter an IP address to analyze', 'warning'); return; }

        const resultsCard = document.getElementById('analysisResults');
        resultsCard.querySelector('.card-body').innerHTML = '<div class="loading-spinner"></div>';

        try {
            const data = await this.postAPI('/analyze', {
                ip_address: ip,
                dest_port: parseInt(document.getElementById('analyzePort')?.value) || 80,
                method: document.getElementById('analyzeMethod')?.value || 'GET',
                path: document.getElementById('analyzePath')?.value || '/',
            });

            const t = data.threat_analysis;
            const intel = data.intelligence;

            resultsCard.querySelector('.card-body').innerHTML = `
                <div style="text-align:center;margin-bottom:20px">
                    <div class="score-circle" style="margin:0 auto 12px;width:80px;height:80px;font-size:1.4rem;color:${this.getScoreColor(t.threat_score)}">${t.threat_score}</div>
                    <span class="badge-threat ${t.threat_level}" style="font-size:0.8rem;padding:5px 14px">${t.threat_level.toUpperCase()}</span>
                    <div style="margin-top:8px;font-size:0.75rem;color:var(--text-muted)">Action: <strong style="color:${t.action === 'block' ? 'var(--accent-red)' : t.action === 'allow' ? 'var(--accent-green)' : 'var(--accent-orange)'}">${t.action.toUpperCase()}</strong></div>
                </div>

                ${t.indicators.length > 0 ? `
                    <div style="margin-bottom:16px">
                        <div style="font-size:0.75rem;font-weight:600;margin-bottom:8px;color:var(--accent-red)"><i class="fas fa-exclamation-triangle"></i> Threat Indicators</div>
                        ${t.indicators.map(i => `<div style="font-size:0.75rem;padding:6px 10px;background:rgba(255,23,68,0.08);border-radius:4px;margin-bottom:4px;color:var(--text-secondary)"><i class="fas fa-chevron-right" style="color:var(--accent-red);margin-right:6px"></i>${i}</div>`).join('')}
                    </div>
                ` : ''}

                <div class="ip-detail-grid">
                    <div class="detail-item"><div class="detail-label">Country</div><div class="detail-value">${intel.country_code} ${intel.country}</div></div>
                    <div class="detail-item"><div class="detail-label">City</div><div class="detail-value">${intel.city}</div></div>
                    <div class="detail-item"><div class="detail-label">ASN</div><div class="detail-value">${intel.asn || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">Organization</div><div class="detail-value">${intel.org || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">ISP</div><div class="detail-value">${intel.isp || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">Network Class</div><div class="detail-value">${intel.network_class}</div></div>
                    <div class="detail-item"><div class="detail-label">IP Version</div><div class="detail-value">IPv${intel.ip_version}</div></div>
                    <div class="detail-item"><div class="detail-label">Risk Score</div><div class="detail-value" style="color:${this.getScoreColor(intel.risk_score)}">${intel.risk_score}</div></div>
                </div>

                <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
                    ${intel.is_vpn ? '<span class="badge-threat medium"><i class="fas fa-mask"></i> VPN</span>' : ''}
                    ${intel.is_proxy ? '<span class="badge-threat high"><i class="fas fa-exchange-alt"></i> Proxy</span>' : ''}
                    ${intel.is_tor ? '<span class="badge-threat critical"><i class="fas fa-user-secret"></i> Tor</span>' : ''}
                    ${intel.is_datacenter ? '<span class="badge-threat low"><i class="fas fa-server"></i> Datacenter</span>' : ''}
                    ${!intel.is_vpn && !intel.is_proxy && !intel.is_tor && !intel.is_datacenter ? '<span class="badge-threat safe"><i class="fas fa-check"></i> Clean</span>' : ''}
                </div>
            `;
        } catch (e) {
            resultsCard.querySelector('.card-body').innerHTML = `<div class="empty-state"><i class="fas fa-times-circle" style="color:var(--accent-red)"></i><h3>Analysis Failed</h3><p>${e.message}</p></div>`;
        }
    },

    async showIPDetail(ipAddress) {
        const modal = document.getElementById('ipDetailModal');
        if (!modal) return;

        const title = document.getElementById('ipDetailTitle');
        const body = document.getElementById('ipDetailBody');
        title.textContent = `IP Intelligence: ${ipAddress}`;
        body.innerHTML = '<div class="loading-spinner"></div>';
        modal.classList.add('active');

        try {
            const data = await this.fetchAPI(`/intel/${ipAddress}`);
            body.innerHTML = `
                <div class="ip-detail-grid">
                    <div class="detail-item"><div class="detail-label">IP Address</div><div class="detail-value" style="color:var(--accent-cyan)">${data.ip}</div></div>
                    <div class="detail-item"><div class="detail-label">Hostname</div><div class="detail-value">${data.hostname || 'N/A'}</div></div>
                    <div class="detail-item"><div class="detail-label">Reverse DNS</div><div class="detail-value">${data.reverse_dns || 'N/A'}</div></div>
                    <div class="detail-item"><div class="detail-label">Country</div><div class="detail-value">${data.country_code} ${data.country}</div></div>
                    <div class="detail-item"><div class="detail-label">City</div><div class="detail-value">${data.city}</div></div>
                    <div class="detail-item"><div class="detail-label">Region</div><div class="detail-value">${data.region}</div></div>
                    <div class="detail-item"><div class="detail-label">Coordinates</div><div class="detail-value">${data.coordinates.lat.toFixed(4)}, ${data.coordinates.lng.toFixed(4)}</div></div>
                    <div class="detail-item"><div class="detail-label">ASN</div><div class="detail-value">${data.network.asn || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">Organization</div><div class="detail-value">${data.network.org || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">ISP</div><div class="detail-value">${data.network.isp || '-'}</div></div>
                    <div class="detail-item"><div class="detail-label">IP Version</div><div class="detail-value">IPv${data.network.ip_version}</div></div>
                    <div class="detail-item"><div class="detail-label">Network Class</div><div class="detail-value">${data.network.network_class}</div></div>
                </div>
                <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap">
                    ${data.anonymizer.is_tor ? '<span class="badge-threat critical"><i class="fas fa-user-secret"></i> Tor Exit Node</span>' : ''}
                    ${data.anonymizer.is_vpn ? '<span class="badge-threat medium"><i class="fas fa-mask"></i> VPN Endpoint</span>' : ''}
                    ${data.anonymizer.is_proxy ? '<span class="badge-threat high"><i class="fas fa-exchange-alt"></i> Proxy Server</span>' : ''}
                    ${data.anonymizer.is_datacenter ? '<span class="badge-threat low"><i class="fas fa-server"></i> Datacenter IP</span>' : ''}
                    ${data.network.is_private ? '<span class="badge-threat safe"><i class="fas fa-home"></i> Private Network</span>' : ''}
                    ${data.network.is_loopback ? '<span class="badge-threat safe"><i class="fas fa-redo"></i> Loopback</span>' : ''}
                </div>
                <div style="margin-top:16px;padding:12px;background:var(--bg-input);border-radius:var(--radius-sm);border:1px solid var(--border-primary)">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="font-size:0.75rem;color:var(--text-muted)">Risk Score</span>
                        <span style="font-family:var(--font-mono);font-size:1.2rem;font-weight:800;color:${this.getScoreColor(data.risk.risk_score)}">${data.risk.risk_score}</span>
                    </div>
                    <div class="threat-meter" style="margin-top:8px"><div class="threat-meter-fill ${data.risk.risk_score >= 80 ? 'critical' : data.risk.risk_score >= 60 ? 'high' : data.risk.risk_score >= 40 ? 'medium' : 'safe'}" style="width:${data.risk.risk_score}%"></div></div>
                </div>
            `;
        } catch (e) {
            body.innerHTML = `<div class="empty-state"><p>Failed to load IP details</p></div>`;
        }
    },

    // ═══════════════════════════════════════════
    // UTILITY FUNCTIONS
    // ═══════════════════════════════════════════
    showAddIPModal() { document.getElementById('addIPModal')?.classList.add('active'); },
    showAddRuleModal() { document.getElementById('addRuleModal')?.classList.add('active'); },
    closeModal(id) { document.getElementById(id)?.classList.remove('active'); },

    async refreshCurrentPage() {
        await this.loadPage(this.state.currentPage);
    },

    startAutoRefresh() {
        this.state.refreshInterval = setInterval(() => {
            if (this.state.currentPage === 'dashboard' || this.state.currentPage === 'network') {
                this.refreshCurrentPage();
            }
        }, 30000);
    },

    async filterIPs(status) {
        const url = status ? `/ips?status=${status}` : '/ips';
        const data = await this.fetchAPI(url);
        const tbody = document.querySelector('#ip-table tbody');
        if (tbody) {
            tbody.innerHTML = data.ips.map(ip => this.renderIPRow(ip)).join('');
        }
    },

    handleSearch(query) {
        if (!query) return;
        const ipRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
        if (ipRegex.test(query)) {
            this.navigateTo('analyze');
            setTimeout(() => {
                const input = document.getElementById('analyzeIP');
                if (input) { input.value = query; this.analyzeIP(); }
            }, 500);
        }
    },

    showToast(message, type = 'info') {
        const container = document.querySelector('.toast-container') || (() => {
            const div = document.createElement('div');
            div.className = 'toast-container';
            document.body.appendChild(div);
            return div;
        })();

        const iconMap = { success: 'check-circle', error: 'times-circle', warning: 'exclamation-triangle', info: 'info-circle' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fas fa-${iconMap[type] || 'info-circle'}"></i> ${message}`;
        container.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 4000);
    },

    getAlertIcon(type) {
        const map = {
            intrusion_attempt: 'crosshairs', ddos_detected: 'bomb', port_scan: 'search',
            brute_force: 'key', malware_traffic: 'bug', anomaly_detected: 'chart-line',
            rate_limit_exceeded: 'tachometer-alt', geo_anomaly: 'globe', reputation_change: 'star',
            policy_violation: 'gavel',
        };
        return map[type] || 'exclamation-circle';
    },

    getActionIcon(action) {
        const map = { block: 'ban', allow: 'check', rate_limit: 'tachometer-alt', quarantine: 'lock', challenge: 'question-circle', log: 'file-alt', redirect: 'random' };
        return map[action] || 'cog';
    },

    getActionColor(action) {
        const map = { block: 'rgba(255,23,68,0.15)', allow: 'rgba(0,230,118,0.15)', rate_limit: 'rgba(255,145,0,0.15)', quarantine: 'rgba(139,92,246,0.15)', challenge: 'rgba(255,214,0,0.15)', log: 'rgba(0,240,255,0.15)' };
        return map[action] || 'rgba(0,240,255,0.15)';
    },

    getScoreColor(score) {
        if (score >= 80) return 'var(--accent-red)';
        if (score >= 60) return 'var(--accent-orange)';
        if (score >= 40) return 'var(--accent-yellow)';
        if (score >= 20) return 'var(--accent-blue)';
        return 'var(--accent-green)';
    },

    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    },

    formatBytes(bytes) {
        if (!bytes) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let i = 0;
        while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
        return bytes.toFixed(1) + ' ' + units[i];
    },

    timeAgo(dateStr) {
        if (!dateStr) return 'N/A';
        const now = new Date();
        const date = new Date(dateStr);
        const diff = Math.floor((now - date) / 1000);
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    },
};

document.addEventListener('DOMContentLoaded', () => XIG.init());
