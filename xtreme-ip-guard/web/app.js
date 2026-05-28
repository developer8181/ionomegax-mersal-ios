const I18N = {
  ar: {
    brandName: "Ionomegax Mersal Guard",
    brandSubtitle: "مركز قيادة ميرسال",
    navOverview: "نظرة عامة",
    navEndpoints: "نقاط النهاية",
    navAgents: "الوكلاء",
    navEvents: "الأحداث",
    navPolicies: "السياسات",
    navAI: "الذكاء الاصطناعي",
    navAudit: "التدقيق",
    liveLabel: "منصة حية",
    liveHint: "Linux · Windows · macOS",
    heroEyebrow: "Ionomegax — حماية مؤسسية",
    heroTitle: "Mersal Guard",
    heroBody: "منصة متكاملة لحماية نقاط النهاية ومنع تسرب البيانات مع وكلاء حقيقيين.",
    chip: "مباشر",
    statEventsLabel: "أحداث مسجلة",
    endpointsTitle: "الأجهزة المدارة",
    agentsTitle: "وكلاء نقاط النهاية",
    eventsTitle: "أحداث DLP الأخيرة",
    auditTitle: "سجل التدقيق",
    policiesTitle: "سياسات الحماية",
    cardEndpoints: "أجهزة",
    cardIsolated: "معزولة",
    cardPolicies: "سياسات",
    cardBlocked: "محظور/محتجز",
    isolated: "معزول",
    online: "متصل",
    empty: "لا توجد بيانات بعد",
    adminLogin: "تسجيل المسؤول",
    signIn: "دخول",
    signOut: "خروج",
    authGuest: "وضع ضيف — المصادقة غير مفعّلة",
    authOk: "مسؤول متصل",
    authRequired: "يلزم تسجيل الدخول",
    addPolicy: "إضافة سياسة",
    ruleNamePh: "اسم السياسة",
    isolate: "عزل",
    restore: "استعادة",
    loginFail: "فشل تسجيل الدخول",
    aiTitle: "Mersal Neural Cortex",
    aiBody: "تعلم سلوكي، كشف شذوذ، تنبؤ بالمخاطر، وقرارات دفاعية ذاتية.",
    aiTrain: "تدريب من السجل",
    aiInsightsTitle: "رؤى الذكاء الاصطناعي",
    aiPredictionsTitle: "تنبؤات المخاطر",
    aiSuggestionsTitle: "سياسات مقترحة",
    aiBaselines: "إشارات أساسية متعلّمة",
    aiTrained: "تم التدريب",
    poweredBy: "مدعوم من Extreme Technology",
  },
  en: {
    brandName: "Ionomegax Mersal Guard",
    brandSubtitle: "Mersal Command Center",
    navOverview: "Overview",
    navEndpoints: "Endpoints",
    navAgents: "Agents",
    navEvents: "Events",
    navPolicies: "Policies",
    navAI: "AI Cortex",
    navAudit: "Audit",
    liveLabel: "Live platform",
    liveHint: "Linux · Windows · macOS",
    heroEyebrow: "Ionomegax — enterprise defense",
    heroTitle: "Mersal Guard",
    heroBody: "Integrated endpoint protection with real OS agents.",
    chip: "LIVE",
    statEventsLabel: "tracked events",
    endpointsTitle: "Managed endpoints",
    agentsTitle: "Endpoint agents",
    eventsTitle: "Recent DLP events",
    auditTitle: "Audit log",
    policiesTitle: "Protection policies",
    cardEndpoints: "Endpoints",
    cardIsolated: "Isolated",
    cardPolicies: "Policies",
    cardBlocked: "Blocked/quarantined",
    isolated: "Isolated",
    online: "Online",
    empty: "No data yet",
    adminLogin: "Admin sign-in",
    signIn: "Sign in",
    signOut: "Sign out",
    authGuest: "Guest mode — auth disabled",
    authOk: "Admin signed in",
    authRequired: "Sign-in required",
    addPolicy: "Add policy",
    ruleNamePh: "Policy name",
    isolate: "Isolate",
    restore: "Restore",
    loginFail: "Login failed",
    aiTitle: "Mersal Neural Cortex",
    aiBody: "Behavioral learning, anomaly detection, risk forecasting, autonomous escalation.",
    aiTrain: "Train from history",
    aiInsightsTitle: "AI insights",
    aiPredictionsTitle: "Risk predictions",
    aiSuggestionsTitle: "Suggested policies",
    aiBaselines: "Learned baseline signals",
    aiTrained: "Training complete",
    poweredBy: "Powered by Extreme Technology",
  },
};

let lang = "ar";
let authState = { auth_required: false, admin_configured: false };

function t(key) {
  return I18N[lang][key] || key;
}

function token() {
  return window.localStorage.getItem("mersalToken") || "";
}

function authHeaders() {
  const headers = {};
  const value = token();
  if (value) headers["X-Mersal-Token"] = value;
  return headers;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  if (response.status === 401) {
    document.getElementById("authStatus").textContent = t("authRequired");
    throw new Error("unauthorized");
  }
  if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
  return response.json();
}

async function apiPost(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function applyLanguage(next) {
  lang = next;
  document.documentElement.lang = next;
  document.documentElement.dir = next === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (key) node.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.getAttribute("data-i18n-placeholder");
    if (key) node.placeholder = t(key);
  });
  document.querySelectorAll(".lang-toggle button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === next);
  });
  refresh();
}

function updateAuthUi() {
  const loggedIn = Boolean(token());
  document.getElementById("logoutBtn").classList.toggle("hidden", !loggedIn);
  document.getElementById("loginBtn").classList.toggle("hidden", loggedIn);
  const status = document.getElementById("authStatus");
  if (!authState.auth_required) status.textContent = t("authGuest");
  else if (loggedIn) status.textContent = t("authOk");
  else status.textContent = t("authRequired");
}

async function loadAuthStatus() {
  authState = await fetch("/api/auth/status").then((r) => r.json());
  if (authState.admin_username) {
    document.getElementById("adminUser").placeholder = authState.admin_username;
  }
  updateAuthUi();
}

async function login() {
  try {
    const payload = await apiPost("/api/auth/login", {
      username: document.getElementById("adminUser").value,
      password: document.getElementById("adminPass").value,
    });
    window.localStorage.setItem("mersalToken", payload.token);
    updateAuthUi();
    refresh();
  } catch {
    document.getElementById("authStatus").textContent = t("loginFail");
  }
}

function logout() {
  window.localStorage.removeItem("mersalToken");
  updateAuthUi();
}

window.isolateEndpoint = async (endpointId) => {
  await apiPost(`/api/endpoints/${endpointId}/isolate`, {});
  refresh();
};

window.restoreEndpoint = async (endpointId) => {
  await apiPost(`/api/endpoints/${endpointId}/restore`, {});
  refresh();
};

function renderCards(totals) {
  const cards = [
    [t("cardEndpoints"), totals.endpoints],
    [t("cardIsolated"), totals.isolated_endpoints],
    [t("cardPolicies"), totals.policies],
    [t("cardBlocked"), totals.blocked_or_quarantined],
  ];
  document.getElementById("cards").innerHTML = cards
    .map(([label, value]) => `<div class="card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
  document.getElementById("statEvents").textContent = totals.events;
}

function renderEndpoints(rows) {
  const el = document.getElementById("endpointsTable");
  if (!rows.length) {
    el.innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  el.innerHTML = `<table><thead><tr><th>ID</th><th>OS</th><th>Trust</th><th>Status</th><th></th></tr></thead><tbody>${rows
    .map(
      (row) => `<tr>
        <td>${row.endpoint_id}</td>
        <td>${row.os_name || "-"}</td>
        <td>${row.trust_score}</td>
        <td><span class="tag ${row.isolated ? "danger" : "ok"}">${row.isolated ? t("isolated") : t("online")}</span></td>
        <td class="actions">${
          row.isolated
            ? `<button type="button" onclick="restoreEndpoint('${row.endpoint_id}')">${t("restore")}</button>`
            : `<button type="button" class="danger" onclick="isolateEndpoint('${row.endpoint_id}')">${t("isolate")}</button>`
        }</td></tr>`
    )
    .join("")}</tbody></table>`;
}

function renderAgents(rows) {
  const el = document.getElementById("agentsTable");
  if (!rows.length) {
    el.innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  el.innerHTML = `<table><thead><tr><th>Agent</th><th>Host</th><th>OS</th><th>Version</th></tr></thead><tbody>${rows
    .map(
      (row) => `<tr>
        <td>${row.agent_id}</td>
        <td>${row.hostname}</td>
        <td>${row.os_name || "-"}</td>
        <td>${row.version || "-"}</td>
      </tr>`
    )
    .join("")}</tbody></table>`;
}

function renderEvents(rows) {
  const el = document.getElementById("eventsTable");
  if (!rows.length) {
    el.innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  el.innerHTML = `<table><thead><tr><th>Action</th><th>Risk</th><th>Channel</th><th>Resource</th></tr></thead><tbody>${rows
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

function renderAudit(rows) {
  const el = document.getElementById("auditTable");
  if (!rows.length) {
    el.innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  el.innerHTML = `<table><thead><tr><th>Actor</th><th>Action</th><th>Target</th><th>Time</th></tr></thead><tbody>${rows
    .slice(0, 15)
    .map(
      (row) => `<tr>
        <td>${row.actor}</td>
        <td>${row.action}</td>
        <td>${row.target || "-"}</td>
        <td>${row.created_at}</td>
      </tr>`
    )
    .join("")}</tbody></table>`;
}

function renderAI(dashboard) {
  const caps = dashboard.capabilities || [];
  document.getElementById("aiCapabilities").innerHTML = `
    <div class="ai-stat"><span>${t("aiBaselines")}</span><strong>${dashboard.baseline_signals || 0}</strong></div>
    ${caps.map((c) => `<span class="ai-chip">${c}</span>`).join("")}`;

  const insights = dashboard.recent_insights || [];
  const insightsEl = document.getElementById("aiInsightsTable");
  if (!insights.length) insightsEl.innerHTML = `<p>${t("empty")}</p>`;
  else {
    insightsEl.innerHTML = `<table><thead><tr><th>Endpoint</th><th>Type</th><th>Severity</th><th>Summary</th></tr></thead><tbody>${insights
      .slice(0, 10)
      .map(
        (row) => `<tr>
          <td>${row.endpoint_id}</td>
          <td>${row.insight_type}</td>
          <td>${Math.round(row.severity)}</td>
          <td>${row.summary}</td>
        </tr>`
      )
      .join("")}</tbody></table>`;
  }

  const predictions = dashboard.predictions || [];
  const predEl = document.getElementById("aiPredictionsTable");
  if (!predictions.length) predEl.innerHTML = `<p>${t("empty")}</p>`;
  else {
    predEl.innerHTML = `<table><thead><tr><th>Endpoint</th><th>Risk</th><th>Breach %</th><th>Time</th></tr></thead><tbody>${predictions
      .slice(0, 10)
      .map(
        (row) => `<tr>
          <td>${row.endpoint_id}</td>
          <td>${Math.round(row.predicted_risk)}</td>
          <td>${(row.breach_probability * 100).toFixed(1)}%</td>
          <td>${row.created_at}</td>
        </tr>`
      )
      .join("")}</tbody></table>`;
  }

  const suggestions = dashboard.recommended_policies || [];
  const sugEl = document.getElementById("aiSuggestionsTable");
  if (!suggestions.length) sugEl.innerHTML = `<p>${t("empty")}</p>`;
  else {
    sugEl.innerHTML = `<table><thead><tr><th>Rule</th><th>Action</th><th>Channel</th><th>Reason</th></tr></thead><tbody>${suggestions
      .map(
        (row) => `<tr>
          <td>${row.name}</td>
          <td>${row.action}</td>
          <td>${row.channel}</td>
          <td>${row.reason}</td>
        </tr>`
      )
      .join("")}</tbody></table>`;
  }
}

function renderPolicies(rows) {
  const el = document.getElementById("policiesTable");
  if (!rows.length) {
    el.innerHTML = `<p>${t("empty")}</p>`;
    return;
  }
  el.innerHTML = `<table><thead><tr><th>Rule</th><th>Action</th><th>Class</th><th>Channel</th></tr></thead><tbody>${rows
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
  if (authState.auth_required && !token()) return;
  try {
    const [dashboard, endpoints, agents, events, policies, audit, brand, aiDashboard] = await Promise.all([
      api("/api/dashboard"),
      api("/api/endpoints"),
      api("/api/agents"),
      api("/api/events"),
      api("/api/policies"),
      api("/api/audit"),
      api("/api/brand"),
      api("/api/ai/dashboard"),
    ]);
    renderCards(dashboard.totals);
    renderEndpoints(endpoints);
    renderAgents(agents);
    renderEvents(events);
    renderPolicies(policies.filter((p) => p.enabled));
    renderAudit(audit);
    renderAI(aiDashboard);
    document.getElementById("platforms").textContent = (brand.supported_platforms || []).join(" · ");
  } catch (error) {
    console.error(error);
  }
}

document.getElementById("aiTrainBtn").addEventListener("click", async () => {
  const result = await apiPost("/api/ai/train", { limit: 200 });
  document.getElementById("authStatus").textContent = `${t("aiTrained")}: ${result.trained_samples}`;
  refresh();
});

document.getElementById("loginBtn").addEventListener("click", login);
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("policyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  await apiPost("/api/policies", {
    rule_id: document.getElementById("ruleId").value,
    name: document.getElementById("ruleName").value,
    action: document.getElementById("ruleAction").value,
    classification: document.getElementById("ruleClass").value || "*",
    channel: document.getElementById("ruleChannel").value || "*",
    reason: "Created from Mersal Command Center",
  });
  event.target.reset();
  refresh();
});

document.querySelectorAll(".lang-toggle button").forEach((btn) => {
  btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
});

loadAuthStatus().then(() => applyLanguage("ar"));
setInterval(refresh, 15000);
