const state = {
  users: [],
  printers: [],
  jobs: [],
  agents: [],
  dashboard: {},
};

const money = (cents) => `$${(Number(cents || 0) / 100).toFixed(2)}`;
const yesNo = (value) => (value ? "Yes" : "No");
const titleCase = (value) =>
  String(value || "")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

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
  const [dashboard, users, printers, jobs, agents] = await Promise.all([
    api("/api/dashboard"),
    api("/api/users"),
    api("/api/printers"),
    api("/api/jobs"),
    api("/api/agents"),
  ]);
  Object.assign(state, { dashboard, users, printers, jobs, agents });
  render();
}

function render() {
  renderCards();
  renderSelects();
  renderUsers();
  renderPrinters();
  renderJobs();
  renderAgents();
  renderReadiness();
  renderReports();
  document.querySelector("#heroJobs").textContent = state.dashboard.jobs ?? 0;
}

function renderCards() {
  const dashboard = state.dashboard;
  document.querySelector("#cards").innerHTML = [
    ["Identities", dashboard.users],
    ["Printer Fleet", dashboard.printers],
    ["Active Agents", dashboard.agents],
    ["Printed Jobs", dashboard.printed_jobs],
    ["Held Jobs", dashboard.held_jobs],
    ["Total Pages", dashboard.pages],
    ["Charged", money(dashboard.charged_cents)],
    ["Eco Savings", money(dashboard.estimated_savings_cents)],
  ]
    .map(([label, value]) => `<article class="card"><span>${label}</span><strong>${value ?? 0}</strong></article>`)
    .join("");
}

function renderSelects() {
  document.querySelector("#jobUser").innerHTML = state.users
    .map((user) => `<option value="${user.id}">${escapeHtml(user.display_name)} - ${money(user.balance_cents)}</option>`)
    .join("");
  document.querySelector("#jobPrinter").innerHTML = state.printers
    .map((printer) => `<option value="${printer.id}">${escapeHtml(printer.name)} (${escapeHtml(printer.location)})</option>`)
    .join("");
}

function renderUsers() {
  document.querySelector("#users").innerHTML = table(
    ["Name", "Department", "Balance", "Monthly quota", "Overdraft", "Action"],
    state.users.map((user) => [
      `<strong>${escapeHtml(user.display_name)}</strong><br><span class="muted">@${escapeHtml(user.username)}</span>`,
      escapeHtml(user.department),
      money(user.balance_cents),
      money(user.monthly_quota_cents),
      money(user.overdraft_cents),
      `<button class="small" data-credit="${user.id}">Add $5</button>`,
    ]),
  );
}

function renderPrinters() {
  document.querySelector("#printers").innerHTML = table(
    ["Device", "Location", "Color", "Duplex", "BW", "Color", "Status"],
    state.printers.map((printer) => [
      `<strong>${escapeHtml(printer.name)}</strong>`,
      escapeHtml(printer.location),
      yesNo(printer.color_supported),
      yesNo(printer.duplex_supported),
      money(printer.bw_page_cents),
      money(printer.color_page_cents),
      `<span class="status ${printer.status}">${escapeHtml(printer.status)}</span>`,
    ]),
  );
}

function renderJobs() {
  document.querySelector("#jobsTable").innerHTML = table(
    ["ID", "Document", "Identity", "Printer", "Pages", "Cost", "Source", "Status", "Action"],
    state.jobs.map((job) => [
      `#${job.id}`,
      `<strong>${escapeHtml(job.document_name)}</strong><br><span class="muted">${escapeHtml(job.account)}</span>`,
      escapeHtml(job.user_name),
      escapeHtml(job.printer_name),
      `${job.pages} x ${job.copies}`,
      money(job.cost_cents),
      `<span class="badge">${escapeHtml(job.source || "web")}</span>`,
      `<span class="status ${job.status}">${job.status}</span><br><span class="muted">${escapeHtml(job.reason)}</span>`,
      job.status === "held"
        ? `<button class="small" data-release="${job.id}">Release</button> <button class="small danger" data-deny="${job.id}">Deny</button>`
        : "",
    ]),
  );
}

function renderAgents() {
  document.querySelector("#agentsTable").innerHTML = table(
    ["Agent", "Type", "Host", "Version", "Metadata"],
    state.agents.map((agent) => [
      `<strong>${escapeHtml(agent.agent_id)}</strong>`,
      `<span class="badge">${escapeHtml(agent.agent_type)}</span>`,
      `${escapeHtml(agent.hostname)}<br><span class="muted">${escapeHtml(agent.os_name)}</span>`,
      escapeHtml(agent.version),
      escapeHtml(compactMetadata(agent.metadata)),
    ]),
  );
}

function renderReadiness() {
  const readiness = state.dashboard.readiness || {};
  const labels = {
    server: "Extreme Server",
    client_agent: "Client Agent",
    print_provider: "Print Provider",
    printer_controller: "Printer Controller",
    site_server_planned: "Site Server Architecture",
  };
  document.querySelector("#readiness").innerHTML = Object.entries(labels)
    .map(([key, label]) => {
      const ready = Boolean(readiness[key]);
      return `
        <div class="ready-row">
          <strong>${label}</strong>
          <span class="badge ${ready ? "ready" : "not-ready"}">${ready ? "Ready" : "Pending"}</span>
        </div>
      `;
    })
    .join("");
}

function renderReports() {
  document.querySelector("#userReport").innerHTML = table(
    ["User", "Printed jobs", "Cost"],
    (state.dashboard.by_user || []).map((row) => [escapeHtml(row.display_name), row.jobs, money(row.cost_cents)]),
  );
  document.querySelector("#printerReport").innerHTML = table(
    ["Printer", "Printed jobs", "Pages"],
    (state.dashboard.by_printer || []).map((row) => [escapeHtml(row.name), row.jobs, row.pages]),
  );
  document.querySelector("#sourceReport").innerHTML = table(
    ["Source", "Jobs", "Cost"],
    (state.dashboard.by_source || []).map((row) => [titleCase(row.source), row.jobs, money(row.cost_cents)]),
  );
}

function table(headers, rows) {
  if (!rows.length) {
    return `<p class="muted">No records yet. Load the enterprise demo to populate the control plane.</p>`;
  }
  return `
    <table>
      <thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>
  `;
}

function compactMetadata(metadata) {
  if (!metadata || typeof metadata !== "object") {
    return "";
  }
  return Object.entries(metadata)
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join(" | ");
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

document.querySelector("#jobForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    user_id: Number(form.get("user_id")),
    printer_id: Number(form.get("printer_id")),
    document_name: form.get("document_name"),
    pages: Number(form.get("pages")),
    copies: Number(form.get("copies")),
    account: form.get("account"),
    source: form.get("source"),
    agent_id: form.get("agent_id"),
    color: form.get("color") === "on",
    duplex: form.get("duplex") === "on",
  };
  try {
    const job = await api("/api/jobs", { method: "POST", body: JSON.stringify(payload) });
    toast(`Job #${job.id} ${job.status}: ${job.reason}`);
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.body.addEventListener("click", async (event) => {
  const creditId = event.target.dataset.credit;
  const releaseId = event.target.dataset.release;
  const denyId = event.target.dataset.deny;
  try {
    if (creditId) {
      await api(`/api/users/${creditId}/credit`, { method: "POST", body: JSON.stringify({ amount: "5.00" }) });
      toast("Emergency credit added");
      await refresh();
    }
    if (releaseId) {
      await api(`/api/jobs/${releaseId}/release`, { method: "POST", body: "{}" });
      toast("Held job released");
      await refresh();
    }
    if (denyId) {
      await api(`/api/jobs/${denyId}/deny`, { method: "POST", body: JSON.stringify({ reason: "Denied from command center" }) });
      toast("Held job denied");
      await refresh();
    }
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#resetQuotas").addEventListener("click", async () => {
  try {
    await api("/api/quotas/reset", { method: "POST", body: "{}" });
    toast("Monthly quotas reset");
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#loadDemo").addEventListener("click", async () => {
  try {
    await api("/api/demo/reset", { method: "POST", body: "{}" });
    toast("Enterprise demo data loaded");
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

refresh().catch((error) => toast(error.message));
