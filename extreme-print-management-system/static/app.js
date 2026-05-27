const state = {
  users: [],
  printers: [],
  jobs: [],
  agents: [],
  dashboard: {},
  lang: localStorage.getItem("epms-language") || "en",
  sessionToken: localStorage.getItem("epms-session") || "",
  adminUser: null,
};

const messages = {
  en: {
    brandName: "Extreme Print",
    brandSubtitle: "Enterprise Control",
    languageLabel: "Language",
    navCommand: "Command Center",
    navJobs: "Secure Jobs",
    navFleet: "Fleet",
    navAgents: "Agents",
    navReports: "Intelligence",
    demoOnline: "Enterprise Demo Online",
    demoOnlineText: "Server, agents, providers and controllers are visible in one console.",
    heroEyebrow: "Private print governance platform",
    heroTitle: "Extreme Print Management System",
    heroDescription:
      "Centralized print security, quotas, embedded device control, direct-print monitoring, offline provider queues, and executive-grade reporting.",
    loadDemo: "Load enterprise demo",
    resetQuotas: "Reset monthly quotas",
    adminLogin: "Admin sign-in",
    signIn: "Sign in",
    signOut: "Sign out",
    adminGuest: "Sign in required to view data",
    demoCredentialsTitle: "Live demo accounts",
    demoCredentialsHint: "Use these credentials (copy/paste):",
    adminSignedIn: "Signed in as {name} ({role})",
    toastSignedIn: "Admin session started",
    toastSignedOut: "Admin session ended",
    liveControlPlane: "Live control plane",
    trackedDecisions: "tracked print decisions",
    secureRelease: "Secure Release",
    quotaEngine: "Quota Engine",
    providerQueue: "Provider Queue",
    embeddedReady: "Embedded Ready",
    componentServer: "Extreme Server",
    componentServerText: "Policy brain, quotas, transactions, reporting, and dashboard APIs.",
    componentClient: "Client Agent",
    componentClientText: "Balance popups, account selection, direct-print monitor, and user feedback.",
    componentProvider: "Print Provider",
    componentProviderText: "Windows/CUPS gateway concept with offline JSONL replay for outages.",
    componentPrinter: "Printer Controller",
    componentPrinterText: "Vendor adapter layer for HP, Canon, Ricoh, Xerox, Sharp, Kyocera, and more.",
    policySimulator: "Policy simulator",
    submitTitle: "Submit controlled print job",
    submitDescription: "Simulate print-server or client-agent submission with live quota and device-policy checks.",
    realtimeDecisioning: "Real-time decisioning",
    fieldUser: "User",
    fieldPrinter: "Printer",
    fieldDocument: "Document",
    fieldPages: "Pages",
    fieldCopies: "Copies",
    fieldAccount: "Account / department",
    fieldSource: "Source",
    fieldAgent: "Agent ID",
    fieldColor: "Color",
    fieldDuplex: "Duplex",
    defaultDocument: "Executive dossier.pdf",
    defaultAccount: "Executive Office",
    sourceWeb: "Admin Console",
    sourceClientAgent: "Client Agent",
    sourcePrintProvider: "Print Provider",
    sourcePrinterController: "Printer Controller",
    runPolicy: "Run print policy",
    usersTitle: "Users and balances",
    usersDescription: "Quota, budget and overdraft visibility for every identity.",
    printersTitle: "Printer fleet",
    printersDescription: "Device capability, pricing and operational status.",
    jobsTitle: "Secure print decisions",
    jobsDescription: "Held jobs can be released or denied by an administrator or printer controller.",
    findMe: "Find-Me / Hold-Release",
    agentsTitle: "Agent mesh",
    agentsDescription: "Registered clients, print providers, site servers, and printer controllers.",
    readinessTitle: "System readiness",
    readinessDescription: "Demo-grade readiness across distributed components.",
    topUsersTitle: "Top users",
    printerUsageTitle: "Printer usage",
    sourceIntelTitle: "Job source intelligence",
    cardIdentities: "Identities",
    cardPrinterFleet: "Printer Fleet",
    cardActiveAgents: "Active Agents",
    cardPrintedJobs: "Printed Jobs",
    cardHeldJobs: "Held Jobs",
    cardTotalPages: "Total Pages",
    cardCharged: "Charged",
    cardEcoSavings: "Eco Savings",
    thName: "Name",
    thDepartment: "Department",
    thBalance: "Balance",
    thMonthlyQuota: "Monthly quota",
    thOverdraft: "Overdraft",
    thAction: "Action",
    thDevice: "Device",
    thLocation: "Location",
    thColor: "Color",
    thDuplex: "Duplex",
    thBw: "BW",
    thStatus: "Status",
    thId: "ID",
    thDocument: "Document",
    thIdentity: "Identity",
    thPrinter: "Printer",
    thPages: "Pages",
    thCost: "Cost",
    thSource: "Source",
    thAgent: "Agent",
    thType: "Type",
    thHost: "Host",
    thVersion: "Version",
    thMetadata: "Metadata",
    thPrintedJobs: "Printed jobs",
    thJobs: "Jobs",
    yes: "Yes",
    no: "No",
    addCredit: "Add $5",
    release: "Release",
    deny: "Deny",
    ready: "Ready",
    pending: "Pending",
    noRecords: "No records yet. Load the enterprise demo to populate the control plane.",
    extremeServer: "Extreme Server",
    clientAgent: "Client Agent",
    printProvider: "Print Provider",
    printerController: "Printer Controller",
    siteServerArchitecture: "Site Server Architecture",
    statusPrinted: "Printed",
    statusHeld: "Held",
    statusDenied: "Denied",
    statusOnline: "Online",
    statusMaintenance: "Maintenance",
    sourceWebLabel: "Admin Console",
    sourceClientAgentLabel: "Client Agent",
    sourcePrintProviderLabel: "Print Provider",
    sourcePrinterControllerLabel: "Printer Controller",
    sourceSiteServerLabel: "Site Server",
    toastCredit: "Emergency credit added",
    toastReleased: "Held job released",
    toastDenied: "Held job denied",
    toastQuotas: "Monthly quotas reset",
    toastDemo: "Enterprise demo data loaded",
    toastJob: "Job #{id} {status}: {reason}",
    deniedReason: "Denied from command center",
  },
  ar: {
    brandName: "إكستريم برنت",
    brandSubtitle: "تحكم مؤسسي",
    languageLabel: "اللغة",
    navCommand: "مركز التحكم",
    navJobs: "مهام آمنة",
    navFleet: "الأسطول",
    navAgents: "الوكلاء",
    navReports: "الذكاء التشغيلي",
    demoOnline: "العرض المؤسسي يعمل",
    demoOnlineText: "السيرفر والوكلاء ومزودو الطباعة ووحدات التحكم ظاهرة في لوحة واحدة.",
    heroEyebrow: "منصة خاصة لحوكمة الطباعة",
    heroTitle: "نظام إكستريم لإدارة الطباعة",
    heroDescription:
      "أمان مركزي للطباعة، حصص وأرصدة، تحكم بالأجهزة المدمجة، مراقبة الطباعة المباشرة، طوابير دون اتصال، وتقارير تنفيذية.",
    loadDemo: "تحميل عرض مؤسسي",
    resetQuotas: "تصفير الحصص الشهرية",
    adminLogin: "دخول المسؤول",
    signIn: "تسجيل الدخول",
    signOut: "تسجيل الخروج",
    adminGuest: "يلزم تسجيل الدخول لعرض البيانات",
    demoCredentialsTitle: "حسابات العرض الحي",
    demoCredentialsHint: "استخدم بيانات الدخول التالية:",
    adminSignedIn: "مسجّل كـ {name} ({role})",
    toastSignedIn: "بدأت جلسة المسؤول",
    toastSignedOut: "انتهت جلسة المسؤول",
    liveControlPlane: "لوحة تحكم مباشرة",
    trackedDecisions: "قرار طباعة متتبع",
    secureRelease: "إطلاق آمن",
    quotaEngine: "محرك الحصص",
    providerQueue: "طابور المزود",
    embeddedReady: "جاهز للتضمين",
    componentServer: "سيرفر إكستريم",
    componentServerText: "عقل السياسات والحصص والمعاملات والتقارير وواجهات التحكم.",
    componentClient: "برنامج العميل",
    componentClientText: "عرض الرصيد، اختيار الحساب، مراقبة الطباعة المباشرة وتنبيهات المستخدم.",
    componentProvider: "مزود الطباعة",
    componentProviderText: "بوابة Windows/CUPS مع إعادة تشغيل طابور JSONL عند الانقطاع.",
    componentPrinter: "وحدة التحكم بالطابعة",
    componentPrinterText: "طبقة مواءمة للبائعين مثل HP وCanon وRicoh وXerox وSharp وKyocera وغيرها.",
    policySimulator: "محاكي السياسات",
    submitTitle: "إرسال مهمة طباعة مراقبة",
    submitDescription: "حاكي إرسالًا من خادم الطباعة أو برنامج العميل مع فحص مباشر للحصة وسياسات الجهاز.",
    realtimeDecisioning: "قرار فوري",
    fieldUser: "المستخدم",
    fieldPrinter: "الطابعة",
    fieldDocument: "المستند",
    fieldPages: "الصفحات",
    fieldCopies: "النسخ",
    fieldAccount: "الحساب / القسم",
    fieldSource: "المصدر",
    fieldAgent: "معرف الوكيل",
    fieldColor: "ألوان",
    fieldDuplex: "وجهين",
    defaultDocument: "ملف تنفيذي.pdf",
    defaultAccount: "مكتب الإدارة",
    sourceWeb: "لوحة الإدارة",
    sourceClientAgent: "برنامج العميل",
    sourcePrintProvider: "مزود الطباعة",
    sourcePrinterController: "وحدة الطابعة",
    runPolicy: "تشغيل سياسة الطباعة",
    usersTitle: "المستخدمون والأرصدة",
    usersDescription: "رؤية الحصص والميزانيات وحد السحب لكل هوية.",
    printersTitle: "أسطول الطابعات",
    printersDescription: "إمكانيات الأجهزة والأسعار والحالة التشغيلية.",
    jobsTitle: "قرارات الطباعة الآمنة",
    jobsDescription: "يمكن إطلاق المهام المحجوزة أو رفضها من المدير أو وحدة الطابعة.",
    findMe: "Find-Me / حجز وإطلاق",
    agentsTitle: "شبكة الوكلاء",
    agentsDescription: "العملاء ومزودو الطباعة وسيرفرات المواقع ووحدات التحكم المسجلة.",
    readinessTitle: "جاهزية النظام",
    readinessDescription: "جاهزية العرض عبر المكونات الموزعة.",
    topUsersTitle: "أكثر المستخدمين",
    printerUsageTitle: "استخدام الطابعات",
    sourceIntelTitle: "تحليل مصادر المهام",
    cardIdentities: "الهويات",
    cardPrinterFleet: "أسطول الطابعات",
    cardActiveAgents: "الوكلاء النشطون",
    cardPrintedJobs: "مهام مطبوعة",
    cardHeldJobs: "مهام محجوزة",
    cardTotalPages: "إجمالي الصفحات",
    cardCharged: "المبلغ المحصل",
    cardEcoSavings: "وفورات تقديرية",
    thName: "الاسم",
    thDepartment: "القسم",
    thBalance: "الرصيد",
    thMonthlyQuota: "الحصة الشهرية",
    thOverdraft: "حد السحب",
    thAction: "الإجراء",
    thDevice: "الجهاز",
    thLocation: "الموقع",
    thColor: "ألوان",
    thDuplex: "وجهين",
    thBw: "أبيض وأسود",
    thStatus: "الحالة",
    thId: "المعرف",
    thDocument: "المستند",
    thIdentity: "الهوية",
    thPrinter: "الطابعة",
    thPages: "الصفحات",
    thCost: "التكلفة",
    thSource: "المصدر",
    thAgent: "الوكيل",
    thType: "النوع",
    thHost: "المضيف",
    thVersion: "الإصدار",
    thMetadata: "البيانات",
    thPrintedJobs: "مهام مطبوعة",
    thJobs: "المهام",
    yes: "نعم",
    no: "لا",
    addCredit: "إضافة 5$",
    release: "إطلاق",
    deny: "رفض",
    ready: "جاهز",
    pending: "قيد التجهيز",
    noRecords: "لا توجد سجلات بعد. حمّل العرض المؤسسي لملء لوحة التحكم.",
    extremeServer: "سيرفر إكستريم",
    clientAgent: "برنامج العميل",
    printProvider: "مزود الطباعة",
    printerController: "وحدة التحكم بالطابعة",
    siteServerArchitecture: "معمارية سيرفر الموقع",
    statusPrinted: "مطبوع",
    statusHeld: "محجوز",
    statusDenied: "مرفوض",
    statusOnline: "متصل",
    statusMaintenance: "صيانة",
    sourceWebLabel: "لوحة الإدارة",
    sourceClientAgentLabel: "برنامج العميل",
    sourcePrintProviderLabel: "مزود الطباعة",
    sourcePrinterControllerLabel: "وحدة الطابعة",
    sourceSiteServerLabel: "سيرفر الموقع",
    toastCredit: "تمت إضافة رصيد طارئ",
    toastReleased: "تم إطلاق المهمة المحجوزة",
    toastDenied: "تم رفض المهمة المحجوزة",
    toastQuotas: "تم تصفير الحصص الشهرية",
    toastDemo: "تم تحميل بيانات العرض المؤسسي",
    toastJob: "المهمة #{id} {status}: {reason}",
    deniedReason: "مرفوضة من مركز التحكم",
  },
};

const t = (key) => messages[state.lang][key] || messages.en[key] || key;
const money = (cents) => `$${(Number(cents || 0) / 100).toFixed(2)}`;
const yesNo = (value) => (value ? t("yes") : t("no"));

const sourceLabels = {
  web: "sourceWebLabel",
  "client-agent": "sourceClientAgentLabel",
  "print-provider": "sourcePrintProviderLabel",
  "printer-controller": "sourcePrinterControllerLabel",
  "site-server": "sourceSiteServerLabel",
};

const statusLabels = {
  printed: "statusPrinted",
  held: "statusHeld",
  denied: "statusDenied",
  online: "statusOnline",
  maintenance: "statusMaintenance",
};

function authHeaders() {
  const headers = { "Content-Type": "application/json" };
  if (state.sessionToken) {
    headers["X-EPMS-Session"] = state.sessionToken;
  }
  return headers;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { ...authHeaders(), ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function refresh() {
  try {
    const [dashboard, users, printers, jobs, agents] = await Promise.all([
      api("/api/dashboard"),
      api("/api/users"),
      api("/api/printers"),
      api("/api/jobs"),
      api("/api/agents"),
    ]);
    Object.assign(state, { dashboard, users, printers, jobs, agents });
    render();
  } catch (error) {
    if (!state.adminUser && String(error.message).toLowerCase().includes("authentication")) {
      render();
      return;
    }
    toast(error.message);
  }
}

function setLanguage(lang) {
  state.lang = lang === "ar" ? "ar" : "en";
  localStorage.setItem("epms-language", state.lang);
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  applyTranslations();
  render();
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-value]").forEach((element) => {
    element.value = t(element.dataset.i18nValue);
  });
  document.querySelectorAll(".language-toggle button").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === state.lang);
  });
}

function render() {
  applyTranslations();
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
    [t("cardIdentities"), dashboard.users],
    [t("cardPrinterFleet"), dashboard.printers],
    [t("cardActiveAgents"), dashboard.agents],
    [t("cardPrintedJobs"), dashboard.printed_jobs],
    [t("cardHeldJobs"), dashboard.held_jobs],
    [t("cardTotalPages"), dashboard.pages],
    [t("cardCharged"), money(dashboard.charged_cents)],
    [t("cardEcoSavings"), money(dashboard.estimated_savings_cents)],
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
    [t("thName"), t("thDepartment"), t("thBalance"), t("thMonthlyQuota"), t("thOverdraft"), t("thAction")],
    state.users.map((user) => [
      `<strong>${escapeHtml(user.display_name)}</strong><br><span class="muted">@${escapeHtml(user.username)}</span>`,
      escapeHtml(user.department),
      money(user.balance_cents),
      money(user.monthly_quota_cents),
      money(user.overdraft_cents),
      `<button class="small" data-credit="${user.id}">${t("addCredit")}</button>`,
    ]),
  );
}

function renderPrinters() {
  document.querySelector("#printers").innerHTML = table(
    [t("thDevice"), t("thLocation"), t("thColor"), t("thDuplex"), t("thBw"), t("thColor"), t("thStatus")],
    state.printers.map((printer) => [
      `<strong>${escapeHtml(printer.name)}</strong>`,
      escapeHtml(printer.location),
      yesNo(printer.color_supported),
      yesNo(printer.duplex_supported),
      money(printer.bw_page_cents),
      money(printer.color_page_cents),
      `<span class="status ${printer.status}">${statusText(printer.status)}</span>`,
    ]),
  );
}

function renderJobs() {
  document.querySelector("#jobsTable").innerHTML = table(
    [t("thId"), t("thDocument"), t("thIdentity"), t("thPrinter"), t("thPages"), t("thCost"), t("thSource"), t("thStatus"), t("thAction")],
    state.jobs.map((job) => [
      `#${job.id}`,
      `<strong>${escapeHtml(job.document_name)}</strong><br><span class="muted">${escapeHtml(job.account)}</span>`,
      escapeHtml(job.user_name),
      escapeHtml(job.printer_name),
      `${job.pages} x ${job.copies}`,
      money(job.cost_cents),
      `<span class="badge">${sourceText(job.source || "web")}</span>`,
      `<span class="status ${job.status}">${statusText(job.status)}</span><br><span class="muted">${escapeHtml(job.reason)}</span>`,
      job.status === "held"
        ? `<button class="small" data-release="${job.id}">${t("release")}</button> <button class="small danger" data-deny="${job.id}">${t("deny")}</button>`
        : "",
    ]),
  );
}

function renderAgents() {
  document.querySelector("#agentsTable").innerHTML = table(
    [t("thAgent"), t("thType"), t("thHost"), t("thVersion"), t("thMetadata")],
    state.agents.map((agent) => [
      `<strong>${escapeHtml(agent.agent_id)}</strong>`,
      `<span class="badge">${sourceText(agent.agent_type)}</span>`,
      `${escapeHtml(agent.hostname)}<br><span class="muted">${escapeHtml(agent.os_name)}</span>`,
      escapeHtml(agent.version),
      escapeHtml(compactMetadata(agent.metadata)),
    ]),
  );
}

function renderReadiness() {
  const readiness = state.dashboard.readiness || {};
  const labels = {
    server: t("extremeServer"),
    client_agent: t("clientAgent"),
    print_provider: t("printProvider"),
    printer_controller: t("printerController"),
    site_server_planned: t("siteServerArchitecture"),
  };
  document.querySelector("#readiness").innerHTML = Object.entries(labels)
    .map(([key, label]) => {
      const ready = Boolean(readiness[key]);
      return `
        <div class="ready-row">
          <strong>${label}</strong>
          <span class="badge ${ready ? "ready" : "not-ready"}">${ready ? t("ready") : t("pending")}</span>
        </div>
      `;
    })
    .join("");
}

function renderReports() {
  document.querySelector("#userReport").innerHTML = table(
    [t("fieldUser"), t("thPrintedJobs"), t("thCost")],
    (state.dashboard.by_user || []).map((row) => [escapeHtml(row.display_name), row.jobs, money(row.cost_cents)]),
  );
  document.querySelector("#printerReport").innerHTML = table(
    [t("fieldPrinter"), t("thPrintedJobs"), t("thPages")],
    (state.dashboard.by_printer || []).map((row) => [escapeHtml(row.name), row.jobs, row.pages]),
  );
  document.querySelector("#sourceReport").innerHTML = table(
    [t("thSource"), t("thJobs"), t("thCost")],
    (state.dashboard.by_source || []).map((row) => [sourceText(row.source), row.jobs, money(row.cost_cents)]),
  );
}

function table(headers, rows) {
  if (!rows.length) {
    return `<p class="muted">${t("noRecords")}</p>`;
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

function sourceText(value) {
  return t(sourceLabels[value] || "") || titleCase(value);
}

function statusText(value) {
  return t(statusLabels[value] || "") || titleCase(value);
}

function titleCase(value) {
  return String(value || "")
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
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

document.querySelectorAll(".language-toggle button").forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.lang));
});

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
    toast(t("toastJob").replace("{id}", job.id).replace("{status}", statusText(job.status)).replace("{reason}", job.reason));
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
      toast(t("toastCredit"));
      await refresh();
    }
    if (releaseId) {
      await api(`/api/jobs/${releaseId}/release`, { method: "POST", body: "{}" });
      toast(t("toastReleased"));
      await refresh();
    }
    if (denyId) {
      await api(`/api/jobs/${denyId}/deny`, { method: "POST", body: JSON.stringify({ reason: t("deniedReason") }) });
      toast(t("toastDenied"));
      await refresh();
    }
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#resetQuotas").addEventListener("click", async () => {
  try {
    await api("/api/quotas/reset", { method: "POST", body: "{}" });
    toast(t("toastQuotas"));
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#loadDemo").addEventListener("click", async () => {
  try {
    await api("/api/demo/reset", { method: "POST", body: "{}" });
    toast(t("toastDemo"));
    await refresh();
  } catch (error) {
    toast(error.message);
  }
});

function renderAdminAuth() {
  const status = document.querySelector("#adminAuthStatus");
  const loginBtn = document.querySelector("#adminLoginBtn");
  const logoutBtn = document.querySelector("#adminLogoutBtn");
  if (!status) return;
  if (state.adminUser) {
    status.textContent = t("adminSignedIn")
      .replace("{name}", state.adminUser.display_name)
      .replace("{role}", state.adminUser.role);
    loginBtn.classList.add("hidden");
    logoutBtn.classList.remove("hidden");
  } else {
    status.textContent = t("adminGuest");
    loginBtn.classList.remove("hidden");
    logoutBtn.classList.add("hidden");
    renderDemoCredentials();
  }
}

async function refreshAuth() {
  try {
    const me = await api("/api/auth/me");
    state.adminUser = me.authenticated ? me.user : null;
  } catch {
    state.adminUser = null;
  }
  renderAdminAuth();
  await renderDemoCredentials();
}

async function renderDemoCredentials() {
  const box = document.querySelector("#demoCredentials");
  if (!box) return;
  try {
    const info = await fetch("/api/demo/info").then((r) => r.json());
    if (!info.live_demo || state.adminUser) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    const lines = (info.accounts || [])
      .map(
        (row) =>
          `<div><code>${escapeHtml(row.username)}</code> / <code>${escapeHtml(row.password)}</code> <span class="muted">(${escapeHtml(row.role)})</span></div>`,
      )
      .join("");
    box.innerHTML = `<strong>${escapeHtml(t("demoCredentialsTitle"))}</strong><span>${escapeHtml(t("demoCredentialsHint"))}</span>${lines}`;
    box.classList.remove("hidden");
    if (!document.querySelector("#adminUsername").value) {
      document.querySelector("#adminUsername").value = "admin";
    }
  } catch {
    box.classList.add("hidden");
  }
}

document.querySelector("#adminLoginBtn")?.addEventListener("click", async () => {
  const username = document.querySelector("#adminUsername").value.trim();
  const password = document.querySelector("#adminPassword").value;
  try {
    const result = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    state.sessionToken = result.token;
    localStorage.setItem("epms-session", state.sessionToken);
    state.adminUser = result.user;
    renderAdminAuth();
    toast(t("toastSignedIn"));
  } catch (error) {
    toast(error.message);
  }
});

document.querySelector("#adminLogoutBtn")?.addEventListener("click", async () => {
  try {
    await api("/api/auth/logout", { method: "POST", body: "{}" });
  } catch {
    /* ignore */
  }
  state.sessionToken = "";
  state.adminUser = null;
  localStorage.removeItem("epms-session");
  renderAdminAuth();
  toast(t("toastSignedOut"));
});

setLanguage(state.lang);
refreshAuth()
  .then(() => refresh())
  .catch((error) => toast(error.message));
