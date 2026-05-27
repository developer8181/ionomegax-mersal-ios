const I18N = {
  ar: {
    brandName: "Ionomegax Mersal Guard",
    brandSubtitle: "مركز قيادة ميرسال",
    navOverview: "نظرة عامة",
    navEndpoints: "نقاط النهاية",
    navEvents: "الأحداث",
    navPolicies: "السياسات",
    liveLabel: "منصة حية",
    liveHint: "Linux · Windows · macOS",
    heroEyebrow: "Ionomegax — حماية مؤسسية",
    heroTitle: "Mersal Guard",
    heroBody:
      "منصة متكاملة لحماية نقاط النهاية ومنع تسرب البيانات مع وكلاء حقيقيين وفرض سياسات محلي.",
    chip: "مباشر",
    statEventsLabel: "أحداث مسجلة",
    endpointsTitle: "الأجهزة المدارة",
    eventsTitle: "أحداث DLP الأخيرة",
    policiesTitle: "سياسات الحماية",
    cardEndpoints: "أجهزة",
    cardIsolated: "معزولة",
    cardPolicies: "سياسات",
    cardBlocked: "محظور/محتجز",
    isolated: "معزول",
    online: "متصل",
    empty: "لا توجد بيانات بعد",
  },
  en: {
    brandName: "Ionomegax Mersal Guard",
    brandSubtitle: "Mersal Command Center",
    navOverview: "Overview",
    navEndpoints: "Endpoints",
    navEvents: "Events",
    navPolicies: "Policies",
    liveLabel: "Live platform",
    liveHint: "Linux · Windows · macOS",
    heroEyebrow: "Ionomegax — enterprise defense",
    heroTitle: "Mersal Guard",
    heroBody:
      "Integrated endpoint protection and DLP with real OS agents and local policy enforcement.",
    chip: "LIVE",
    statEventsLabel: "tracked events",
    endpointsTitle: "Managed endpoints",
    eventsTitle: "Recent DLP events",
    policiesTitle: "Protection policies",
    cardEndpoints: "Endpoints",
    cardIsolated: "Isolated",
    cardPolicies: "Policies",
    cardBlocked: "Blocked/quarantined",
    isolated: "Isolated",
    online: "Online",
    empty: "No data yet",
  },
};

let lang = "ar";

function t(key) {
  return I18N[lang][key] || key;
}

function applyLanguage(next) {
  lang = next;
  document.documentElement.lang = next;
  document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (key) node.textContent = t(key);
  });
  document.querySelectorAll(".lang-toggle button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === next);
  });
  refresh();
}

async function api(path) {
  const headers = {};
  const token = window.localStorage.getItem("mersalToken");
  if (token) headers["X-Mersal-Token"] = token;
  const response = await fetch(path, { headers });
  if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
  return response.json();
}

function renderCards(totals) {
  const cards = [
    [t("cardEndpoints"), totals.endpoints],
    [t("cardIsolated"), totals.isolated_endpoints],
    [t("cardPolicies"), totals.policies],
    [t("cardBlocked"), totals.blocked_or_quarantined],
  ];
  document.getElementById("cards").innerHTML = cards
    .map(
      ([label, value]) =>
        `<div class="card"><span>${label}</span><strong>${value}</strong></div>`
    )
    .join("");
  document.getElementById("statEvents").textContent = totals.events;
}

function renderEndpoints(rows) {
  if (!rows.length) {
    document.getElementById("endpointsTable").innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  document.getElementById("endpointsTable").innerHTML = `
    <table><thead><tr><th>ID</th><th>OS</th><th>Owner</th><th>Trust</th><th>Status</th></tr></thead>
    <tbody>${rows
      .map(
        (row) => `<tr>
          <td>${row.endpoint_id}</td>
          <td>${row.os_name || "-"}</td>
          <td>${row.owner || "-"}</td>
          <td>${row.trust_score}</td>
          <td><span class="tag ${row.isolated ? "danger" : "ok"}">${row.isolated ? t("isolated") : t("online")}</span></td>
        </tr>`
      )
      .join("")}</tbody></table>`;
}

function renderEvents(rows) {
  if (!rows.length) {
    document.getElementById("eventsTable").innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  document.getElementById("eventsTable").innerHTML = `
    <table><thead><tr><th>Action</th><th>Risk</th><th>Channel</th><th>Resource</th></tr></thead>
    <tbody>${rows
      .slice(0, 12)
      .map(
        (row) => `<tr>
          <td><span class="tag ${row.action === "allow" ? "ok" : "danger"}">${row.action}</span></td>
          <td>${row.risk_score}</td>
          <td>${row.channel}</td>
          <td>${row.resource}</td>
        </tr>`
      )
      .join("")}</tbody></table>`;
}

function renderPolicies(rows) {
  if (!rows.length) {
    document.getElementById("policiesTable").innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  document.getElementById("policiesTable").innerHTML = `
    <table><thead><tr><th>Rule</th><th>Action</th><th>Classification</th><th>Channel</th></tr></thead>
    <tbody>${rows
      .map(
        (row) => `<tr>
          <td>${row.name}</td>
          <td>${row.action}</td>
          <td>${row.classification}</td>
          <td>${row.channel}</td>
        </tr>`
      )
      .join("")}</tbody></table>`;
}

async function refresh() {
  try {
    const [dashboard, endpoints, events, policies, brand] = await Promise.all([
      api("/api/dashboard"),
      api("/api/endpoints"),
      api("/api/events"),
      api("/api/policies"),
      api("/api/brand"),
    ]);
    renderCards(dashboard.totals);
    renderEndpoints(endpoints);
    renderEvents(events);
    renderPolicies(policies.filter((p) => p.enabled));
    document.getElementById("platforms").textContent = (brand.supported_platforms || []).join(" · ");
  } catch (error) {
    console.error(error);
  }
}

document.querySelectorAll(".lang-toggle button").forEach((btn) => {
  btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
});

applyLanguage("ar");
setInterval(refresh, 15000);
