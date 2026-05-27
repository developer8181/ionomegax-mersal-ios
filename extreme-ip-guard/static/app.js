const state = {
  assets: [],
  policies: [],
  incidents: [],
  events: [],
  dashboard: {},
};

const formatNumber = (value) => new Intl.NumberFormat().format(Number(value || 0));
const yesNo = (value) => (value ? "Yes" : "No");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function refresh() {
  const [dashboard, assets, policies, incidents, events] = await Promise.all([
    api("/api/dashboard"),
    api("/api/assets"),
    api("/api/policies"),
    api("/api/incidents"),
    api("/api/events"),
  ]);
  Object.assign(state, { dashboard, assets, policies, incidents, events });
  render();
}

function render() {
  renderCards();
  renderSelects();
  renderAssets();
  renderPolicies();
  renderIncidents();
  renderEvents();
  renderReports();
}

function renderCards() {
  const dashboard = state.dashboard;
  document.querySelector("#cards").innerHTML = [
    ["Assets", dashboard.assets],
    ["Agents", dashboard.agents],
    ["Events", dashboard.events],
    ["Open incidents", dashboard.open_incidents],
    ["Blocked", dashboard.blocked],
    ["Quarantined", dashboard.quarantined],
    ["Avg risk", dashboard.average_risk],
    ["Quarantined assets", dashboard.quarantined_assets],
  ]
    .map(([label, value]) => `<article class="card"><span>${label}</span><strong>${value ?? 0}</strong></article>`)
    .join("");
}

function renderSelects() {
  document.querySelector("#eventAsset").innerHTML = state.assets
    .map(
      (asset) =>
        `<option value="${asset.id}">${escapeHtml(asset.hostname)} (${escapeHtml(asset.posture)}) - trust ${asset.trust_score}</option>`,
    )
    .join("");
}

function renderAssets() {
  document.querySelector("#assets").innerHTML = table(
    ["Hostname", "Owner", "Segment", "Criticality", "Trust", "Posture", "Action"],
    state.assets.map((asset) => [
      escapeHtml(asset.hostname),
      escapeHtml(asset.owner),
      escapeHtml(asset.segment),
      badge(asset.criticality, asset.criticality),
      formatNumber(asset.trust_score),
      badge(asset.posture, asset.posture),
      `<button class="small danger" data-quarantine="${asset.id}">Quarantine</button>`,
    ]),
  );
}

function renderPolicies() {
  document.querySelector("#policies").innerHTML = table(
    ["Name", "Mode", "Trusted networks", "Blocked ports", "Blocked countries", "Thresholds"],
    state.policies.map((policy) => [
      escapeHtml(policy.name),
      badge(policy.mode, policy.mode),
      escapeHtml((policy.trusted_networks || []).join(", ")),
      escapeHtml((policy.block_ports || []).join(", ")),
      escapeHtml((policy.hard_block_countries || []).join(", ")),
      `challenge ${policy.challenge_threshold} / block ${policy.block_threshold} / quarantine ${policy.quarantine_threshold}`,
    ]),
  );
}

function renderIncidents() {
  document.querySelector("#incidents").innerHTML = table(
    ["ID", "Asset", "Severity", "Action", "Destination", "Summary", "Status", "Actions"],
    state.incidents.map((incident) => [
      incident.id,
      escapeHtml(incident.asset_name),
      badge(incident.severity, incident.severity),
      badge(incident.action, incident.action),
      `${escapeHtml(incident.destination_ip)}:${incident.destination_port}`,
      escapeHtml(incident.summary),
      badge(incident.status, incident.status),
      incident.status === "open"
        ? `<button class="small" data-resolve="${incident.id}">Resolve</button>`
        : "",
    ]),
  );
}

function renderEvents() {
  document.querySelector("#events").innerHTML = table(
    ["ID", "Asset", "Destination", "Process", "Country", "Risk", "Severity", "Action", "Reasons"],
    state.events.map((event) => [
      event.id,
      escapeHtml(event.asset_name),
      `${escapeHtml(event.destination_ip)}:${event.destination_port}`,
      escapeHtml(event.process_name || "-"),
      escapeHtml(event.country),
      event.risk_score,
      badge(event.severity, event.severity),
      badge(event.action, event.action),
      escapeHtml((event.reasons || []).join("; ")),
    ]),
  );
}

function renderReports() {
  document.querySelector("#assetReport").innerHTML = table(
    ["Asset", "Events", "Max risk"],
    (state.dashboard.top_assets || []).map((row) => [escapeHtml(row.hostname), row.events, row.max_risk ?? 0]),
  );
  document.querySelector("#countryReport").innerHTML = table(
    ["Country", "Events", "Disruptive actions"],
    (state.dashboard.top_countries || []).map((row) => [escapeHtml(row.country), row.events, row.disruptive_actions]),
  );
}

function badge(text, kind) {
  return `<span class="status ${escapeHtml(kind)}">${escapeHtml(text)}</span>`;
}

function table(headers, rows) {
  return `
    <table>
      <thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>
  `;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(message) {
  const element = document.querySelector("#toast");
  element.textContent = message;
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 2800);
}

document.querySelector("#eventForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    asset_id: Number(form.get("asset_id")),
    source_ip: form.get("source_ip"),
    destination_ip: form.get("destination_ip"),
    destination_port: Number(form.get("destination_port")),
    protocol: form.get("protocol"),
    country: String(form.get("country") || "").toUpperCase(),
    process_name: form.get("process_name"),
    ip_reputation_score: Number(form.get("ip_reputation_score")),
    burst_connections: Number(form.get("burst_connections")),
    bytes_out: Number(form.get("bytes_out")),
    bytes_in: Number(form.get("bytes_in")),
    tor_exit_node: form.get("tor_exit_node") === "on",
    geo_anomaly: form.get("geo_anomaly") === "on",
  };
  try {
    const result = await api("/api/events", { method: "POST", body: JSON.stringify(payload) });
    toast(`Event #${result.id} -> ${result.action} (${result.severity})`);
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.body.addEventListener("click", async (event) => {
  const quarantineId = event.target.dataset.quarantine;
  const resolveId = event.target.dataset.resolve;
  try {
    if (quarantineId) {
      await api(`/api/assets/${quarantineId}/quarantine`, {
        method: "POST",
        body: JSON.stringify({ note: "Manual quarantine from dashboard" }),
      });
      toast("Asset quarantined");
      await refresh();
    }
    if (resolveId) {
      await api(`/api/incidents/${resolveId}/resolve`, {
        method: "POST",
        body: JSON.stringify({ note: "Resolved from dashboard" }),
      });
      toast("Incident resolved");
      await refresh();
    }
  } catch (error) {
    toast(error.message);
  }
});

refresh().catch((error) => toast(error.message));
