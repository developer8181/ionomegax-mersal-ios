const state = {
  dashboard: {},
  zones: [],
  devices: [],
  policies: [],
  blocks: [],
  events: [],
  accessLog: [],
  agents: [],
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function refresh() {
  const [dashboard, zones, devices, policies, blocks, events, accessLog, agents] = await Promise.all([
    api("/api/dashboard"),
    api("/api/zones"),
    api("/api/devices"),
    api("/api/policies"),
    api("/api/blocks"),
    api("/api/events"),
    api("/api/access-log"),
    api("/api/agents"),
  ]);
  Object.assign(state, { dashboard, zones, devices, policies, blocks, events, accessLog, agents });
  render();
}

function render() {
  renderCards();
  renderSelects();
  renderDevices();
  renderPolicies();
  renderBlocks();
  renderEvents();
  renderAccessLog();
  renderThreatReport();
  renderAgents();
  document.querySelector("#policyVersion").textContent = `Policy v${state.dashboard.policy_version || 0}`;
}

function renderCards() {
  const d = state.dashboard;
  document.querySelector("#cards").innerHTML = [
    ["الأجهزة", d.devices],
    ["موافق عليها", d.approved_devices],
    ["قيد المراجعة", d.pending_devices],
    ["السياسات", d.policies],
    ["حظر نشط", d.active_blocks],
    ["Agents", d.agents],
    ["مسموح", d.allowed_access],
    ["مرفوض", d.denied_access],
  ]
    .map(([label, value]) => `<article class="card"><span>${label}</span><strong>${value ?? 0}</strong></article>`)
    .join("");
}

function renderSelects() {
  document.querySelector("#zoneSelect").innerHTML = state.zones
    .map((z) => `<option value="${escapeHtml(z.name)}">${escapeHtml(z.name)}</option>`)
    .join("");
  document.querySelector("#deviceSelect").innerHTML =
    `<option value="">— بدون جهاز —</option>` +
    state.devices.map((d) => `<option value="${escapeHtml(d.device_id)}">${escapeHtml(d.hostname)} (${escapeHtml(d.device_id)})</option>`).join("");
}

function trustClass(score) {
  if (score >= 70) return "trust-high";
  if (score >= 40) return "trust-mid";
  return "trust-low";
}

function renderDevices() {
  document.querySelector("#devices").innerHTML = table(
    ["الجهاز", "IP", "MAC", "المنطقة", "الثقة", "الحالة", "إجراء"],
    state.devices.map((d) => [
      escapeHtml(d.hostname),
      escapeHtml(d.ip_address),
      escapeHtml(d.mac_address),
      escapeHtml(d.zone),
      `<span class="${trustClass(d.trust_score)}">${d.trust_score}</span>`,
      `<span class="status ${d.status}">${d.status}</span>`,
      d.status === "pending"
        ? `<button class="small" data-approve="${escapeHtml(d.device_id)}">موافقة</button>`
        : "",
    ]),
  );
}

function renderPolicies() {
  document.querySelector("#policies").innerHTML = table(
    ["الاسم", "الإجراء", "الأولوية", "المصدر", "الوجهة", "المناطق"],
    state.policies.map((p) => [
      escapeHtml(p.name),
      `<span class="status ${p.action}">${p.action}</span>`,
      p.priority,
      escapeHtml(p.source_cidr || "—"),
      escapeHtml(p.destination_cidr || "—"),
      escapeHtml(p.zones || "—"),
    ]),
  );
}

function renderBlocks() {
  document.querySelector("#blocks").innerHTML = table(
    ["الهدف", "النوع", "السبب", "المصدر", "الخطورة"],
    state.blocks.map((b) => [
      escapeHtml(b.target),
      escapeHtml(b.target_type),
      escapeHtml(b.reason),
      escapeHtml(b.source),
      b.severity,
    ]),
  );
}

function renderEvents() {
  document.querySelector("#events").innerHTML = table(
    ["النوع", "IP المصدر", "الخطورة", "الوقت"],
    state.events.slice(0, 20).map((e) => [
      escapeHtml(e.event_type),
      escapeHtml(e.source_ip),
      e.severity,
      escapeHtml(e.created_at),
    ]),
  );
}

function renderAccessLog() {
  document.querySelector("#accessLog").innerHTML = table(
    ["المصدر", "الوجهة", "المنفذ", "الإجراء", "السبب"],
    state.accessLog.slice(0, 20).map((l) => [
      escapeHtml(l.source_ip),
      escapeHtml(l.destination_ip),
      l.destination_port,
      `<span class="status ${l.allowed ? "allow" : "deny"}">${l.action}</span>`,
      escapeHtml(l.reason),
    ]),
  );
}

function renderThreatReport() {
  document.querySelector("#threatReport").innerHTML = table(
    ["نوع التهديد", "العدد"],
    (state.dashboard.recent_threats || []).map((r) => [escapeHtml(r.event_type), r.count]),
  );
}

function renderAgents() {
  document.querySelector("#agents").innerHTML = table(
    ["Agent ID", "النوع", "Hostname", "آخر ظهور"],
    state.agents.map((a) => [
      escapeHtml(a.agent_id),
      escapeHtml(a.agent_type),
      escapeHtml(a.hostname),
      escapeHtml(a.last_seen),
    ]),
  );
}

function table(headers, rows) {
  if (!rows.length) return "<p>لا توجد بيانات</p>";
  return `
    <table>
      <thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function toast(message) {
  const el = document.querySelector("#toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2800);
}

document.querySelector("#evaluateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    source_ip: form.get("source_ip"),
    destination_ip: form.get("destination_ip"),
    destination_port: Number(form.get("destination_port")),
    protocol: form.get("protocol"),
    zone: form.get("zone"),
  };
  const deviceId = form.get("device_id");
  if (deviceId) payload.device_id = deviceId;
  try {
    const result = await api("/api/evaluate", { method: "POST", body: JSON.stringify(payload) });
    const box = document.querySelector("#evaluateResult");
    box.classList.remove("hidden", "allow", "deny");
    box.classList.add(result.allowed ? "allow" : "deny");
    box.innerHTML = `
      <strong>${result.allowed ? "✓ مسموح" : "✗ مرفوض"}</strong> — ${escapeHtml(result.reason)}<br/>
      الثقة: ${result.trust_score} | التهديد: ${result.threat_score}
      ${result.matched_rule_name ? `<br/>السياسة: ${escapeHtml(result.matched_rule_name)}` : ""}
    `;
    toast(result.allowed ? "Access allowed" : "Access denied");
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#blockForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    target: form.get("target"),
    target_type: form.get("target_type"),
    reason: form.get("reason"),
  };
  const ttl = form.get("ttl_hours");
  if (ttl) payload.ttl_hours = Number(ttl);
  try {
    await api("/api/blocks", { method: "POST", body: JSON.stringify(payload) });
    toast("تم الحظر");
    event.target.reset();
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.body.addEventListener("click", async (event) => {
  const deviceId = event.target.dataset.approve;
  if (!deviceId) return;
  try {
    await api(`/api/devices/${deviceId}/approve`, { method: "POST", body: "{}" });
    toast("تمت الموافقة على الجهاز");
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

refresh().catch((error) => toast(error.message));
