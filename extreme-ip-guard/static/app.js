async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

function pill(value, extra = "") {
  const cls = (value || "info").toLowerCase().replace(/\s+/g, "");
  return `<span class="pill ${cls} ${extra}">${value}</span>`;
}

function riskBar(score) {
  return `<div class="risk-bar"><span style="width:${Math.min(100, score)}%"></span></div>`;
}

async function loadDashboard() {
  const dash = await api("/api/dashboard");
  document.getElementById("cards").innerHTML = [
    ["نقاط النهاية", dash.endpoints],
    ["الوكلاء", dash.agents],
    ["أحداث 24 ساعة", dash.events_24h],
    ["حوادث مفتوحة", dash.open_incidents],
    ["محظور / عزل", dash.blocked_events],
    ["في الحجر", dash.quarantined_endpoints],
  ]
    .map(
      ([label, value]) =>
        `<article class="card"><span>${label}</span><strong>${value}</strong></article>`
    )
    .join("");
}

async function loadEndpoints() {
  const endpoints = await api("/api/endpoints");
  const rows = endpoints
    .map(
      (ep) => `<tr>
        <td>${ep.hostname}</td>
        <td>${ep.user_name || "—"}</td>
        <td>${ep.segment}</td>
        <td>${ep.is_quarantined ? pill("quarantine") : pill("allow")}</td>
        <td>${ep.risk?.score ?? 0} ${riskBar(ep.risk?.score ?? 0)}</td>
        <td>${ep.risk?.level ?? "—"}</td>
        <td>${
          ep.is_quarantined
            ? `<button class="secondary" data-release="${ep.id}">إلغاء الحجر</button>`
            : ""
        }</td>
      </tr>`
    )
    .join("");
  document.getElementById("endpoints").innerHTML = `<table>
    <thead><tr><th>Hostname</th><th>User</th><th>Segment</th><th>State</th><th>Risk</th><th>Level</th><th></th></tr></thead>
    <tbody>${rows || "<tr><td colspan='7'>لا توجد أجهزة</td></tr>"}</tbody>
  </table>`;
  document.querySelectorAll("[data-release]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/endpoints/${btn.dataset.release}/release`, { method: "POST" });
      await refreshAll();
    });
  });
}

async function loadAgents() {
  const agents = await api("/api/agents");
  document.getElementById("agents").innerHTML = `<table>
    <thead><tr><th>Agent ID</th><th>Type</th><th>Host</th><th>Trust</th><th>Last seen</th></tr></thead>
    <tbody>${agents
      .map(
        (a) => `<tr>
          <td class="mono">${a.agent_id}</td>
          <td>${a.agent_type}</td>
          <td>${a.hostname}</td>
          <td>${a.trust_score}</td>
          <td>${a.last_seen}</td>
        </tr>`
      )
      .join("") || "<tr><td colspan='5'>لا وكلاء بعد — شغّل client_agent.py</td></tr>"}
    </tbody>
  </table>`;
}

async function loadEvents() {
  const events = await api("/api/events");
  document.getElementById("events").innerHTML = `<table>
    <thead><tr><th>Time</th><th>Host</th><th>Category</th><th>Summary</th><th>Action</th><th>Severity</th><th>MITRE</th><th>Anomaly</th></tr></thead>
    <tbody>${events
      .map(
        (e) => `<tr>
          <td>${e.created_at}</td>
          <td>${e.hostname || "—"}</td>
          <td>${e.category}</td>
          <td>${e.summary}</td>
          <td>${pill(e.action)}</td>
          <td>${pill(e.severity)}</td>
          <td class="mono">${e.mitre_technique || "—"}</td>
          <td>${e.anomaly_score}</td>
        </tr>`
      )
      .join("") || "<tr><td colspan='8'>لا أحداث</td></tr>"}
    </tbody>
  </table>`;
}

async function loadIncidents() {
  const incidents = await api("/api/incidents");
  document.getElementById("incidents").innerHTML = `<table>
    <thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>Status</th><th>Host</th><th></th></tr></thead>
    <tbody>${incidents
      .map(
        (i) => `<tr>
          <td>${i.id}</td>
          <td>${i.title}</td>
          <td>${pill(i.severity)}</td>
          <td>${i.status}</td>
          <td>${i.hostname || "—"}</td>
          <td>${
            i.status === "open"
              ? `<button class="secondary" data-resolve="${i.id}">إغلاق</button>`
              : ""
          }</td>
        </tr>`
      )
      .join("") || "<tr><td colspan='6'>لا حوادث</td></tr>"}
    </tbody>
  </table>`;
  document.querySelectorAll("[data-resolve]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/incidents/${btn.dataset.resolve}/resolve`, {
        method: "POST",
        body: JSON.stringify({ note: "Closed from SOC dashboard" }),
      });
      await refreshAll();
    });
  });
}

async function loadAudit() {
  const audit = await api("/api/audit");
  document.getElementById("audit").innerHTML = `
    <p>السلسلة ${audit.valid ? "سليمة ✓" : "مكسورة ✗"} — ${audit.entries} سجل</p>
    <p class="mono">Head: ${audit.head_hash || "—"}</p>
  `;
}

async function refreshAll() {
  await Promise.all([
    loadDashboard(),
    loadEndpoints(),
    loadAgents(),
    loadEvents(),
    loadIncidents(),
    loadAudit(),
  ]);
}

document.getElementById("eventForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  const result = await api("/api/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  document.getElementById("eventResult").textContent = JSON.stringify(result, null, 2);
  await refreshAll();
});

document.getElementById("ztCheck").addEventListener("click", async () => {
  const result = await api("/api/zero-trust/check", {
    method: "POST",
    body: JSON.stringify({
      posture: {
        encrypted_disk: true,
        av_updated: true,
        patch_level_ok: true,
        agent_healthy: true,
      },
      user_mfa: true,
      segment: "corporate",
    }),
  });
  document.getElementById("ztResult").textContent = JSON.stringify(result, null, 2);
});

document.getElementById("refreshBtn").addEventListener("click", refreshAll);

refreshAll().catch((err) => alert(err.message));
