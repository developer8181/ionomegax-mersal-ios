const state = {
  users: [],
  printers: [],
  jobs: [],
  dashboard: {},
};

const money = (cents) => `$${(Number(cents || 0) / 100).toFixed(2)}`;
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
  const [dashboard, users, printers, jobs] = await Promise.all([
    api("/api/dashboard"),
    api("/api/users"),
    api("/api/printers"),
    api("/api/jobs"),
  ]);
  Object.assign(state, { dashboard, users, printers, jobs });
  render();
}

function render() {
  renderCards();
  renderSelects();
  renderUsers();
  renderPrinters();
  renderJobs();
  renderReports();
}

function renderCards() {
  const dashboard = state.dashboard;
  document.querySelector("#cards").innerHTML = [
    ["Users", dashboard.users],
    ["Printers", dashboard.printers],
    ["Print jobs", dashboard.jobs],
    ["Held jobs", dashboard.held_jobs],
    ["Pages", dashboard.pages],
    ["Charged", money(dashboard.charged_cents)],
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
    ["Name", "Department", "Balance", "Monthly quota", "Credit"],
    state.users.map((user) => [
      escapeHtml(user.display_name),
      escapeHtml(user.department),
      money(user.balance_cents),
      money(user.monthly_quota_cents),
      `<button class="small" data-credit="${user.id}">Add $5</button>`,
    ]),
  );
}

function renderPrinters() {
  document.querySelector("#printers").innerHTML = table(
    ["Name", "Location", "Color", "Duplex", "BW", "Color"],
    state.printers.map((printer) => [
      escapeHtml(printer.name),
      escapeHtml(printer.location),
      yesNo(printer.color_supported),
      yesNo(printer.duplex_supported),
      money(printer.bw_page_cents),
      money(printer.color_page_cents),
    ]),
  );
}

function renderJobs() {
  document.querySelector("#jobs").innerHTML = table(
    ["ID", "Document", "User", "Printer", "Pages", "Cost", "Status", "Reason", "Actions"],
    state.jobs.map((job) => [
      job.id,
      escapeHtml(job.document_name),
      escapeHtml(job.user_name),
      escapeHtml(job.printer_name),
      `${job.pages} x ${job.copies}`,
      money(job.cost_cents),
      `<span class="status ${job.status}">${job.status}</span>`,
      escapeHtml(job.reason),
      job.status === "held"
        ? `<button class="small" data-release="${job.id}">Release</button> <button class="small danger" data-deny="${job.id}">Deny</button>`
        : "",
    ]),
  );
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
  setTimeout(() => element.classList.remove("show"), 2500);
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
      toast("Credit added");
      await refresh();
    }
    if (releaseId) {
      await api(`/api/jobs/${releaseId}/release`, { method: "POST", body: "{}" });
      toast("Job released");
      await refresh();
    }
    if (denyId) {
      await api(`/api/jobs/${denyId}/deny`, { method: "POST", body: JSON.stringify({ reason: "Denied from dashboard" }) });
      toast("Job denied");
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

refresh().catch((error) => toast(error.message));
