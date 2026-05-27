const SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"];

async function http(method, url, body) {
  const init = { method, headers: {} };
  if (body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const response = await fetch(url, init);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = data && data.error ? data.error : `HTTP ${response.status}`;
    throw new Error(message);
  }
  return data;
}

function toast(message, kind = "success") {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.className = "show " + kind;
  setTimeout(() => {
    el.className = "";
  }, 3200);
}

function pad(n) {
  return n < 10 ? "0" + n : "" + n;
}

function relativeTime(iso) {
  if (!iso) return "—";
  const ts = new Date(iso);
  if (Number.isNaN(ts.valueOf())) return iso;
  const diff = Math.round((Date.now() - ts.getTime()) / 1000);
  if (diff < 0) return ts.toISOString().replace("T", " ").slice(0, 19);
  if (diff < 60) return diff + "s ago";
  if (diff < 3600) return Math.floor(diff / 60) + "m ago";
  if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
  return Math.floor(diff / 86400) + "d ago";
}

function renderCards(totals) {
  const el = document.getElementById("cards");
  const items = [
    { label: "Endpoints", value: totals.agents, accent: true },
    { label: "Assets", value: totals.assets },
    { label: "Users", value: totals.users },
    { label: "Events", value: totals.events },
    { label: "Open alerts", value: totals.open_alerts },
    { label: "High / Critical", value: totals.high_alerts },
  ];
  el.innerHTML = items
    .map(
      (item) => `
        <div class="card ${item.accent ? "accent" : ""}">
          <span class="label">${item.label}</span>
          <strong>${item.value ?? 0}</strong>
          <span class="delta">live</span>
        </div>
      `,
    )
    .join("");
}

function renderAlerts(alerts) {
  const el = document.getElementById("alerts");
  if (!alerts.length) {
    el.innerHTML = `<div class="empty">No alerts yet. Run the agent in <code>storm</code> mode to populate.</div>`;
    return;
  }
  el.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Severity</th>
          <th>Title</th>
          <th>Rule</th>
          <th>MITRE</th>
          <th>Endpoint</th>
          <th>When</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        ${alerts
          .map(
            (a) => `
              <tr>
                <td><span class="status ${a.severity}">${a.severity}</span></td>
                <td><strong>${a.title}</strong><br /><span class="mono">${a.summary || ""}</span></td>
                <td><code>${a.rule_id}</code></td>
                <td>${a.mitre ? `<span class="mitre-tag">${a.mitre}</span>` : "—"}</td>
                <td><span class="mono">${a.agent_id}</span></td>
                <td>${relativeTime(a.ts)}</td>
                <td>${a.status}</td>
                <td>
                  <button class="small secondary" data-ack="${a.alert_uid}">Acknowledge</button>
                </td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
  el.querySelectorAll("button[data-ack]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await http("POST", `/api/alerts/${btn.dataset.ack}/status`, { status: "acknowledged", actor: "console-ui" });
        toast("Alert acknowledged.");
        await refresh();
      } catch (err) {
        toast(err.message, "error");
      }
    });
  });
}

function severityBar(score) {
  const pct = Math.max(0, Math.min(100, Math.round(score)));
  return `<div class="bar" style="--w:${pct}%"></div>`;
}

function classifyBand(score) {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 35) return "medium";
  if (score >= 15) return "low";
  return "info";
}

function renderRanking(elId, rows, key) {
  const el = document.getElementById(elId);
  if (!rows.length) {
    el.innerHTML = `<div class="empty">No data yet.</div>`;
    return;
  }
  el.innerHTML = `
    <ul class="bare">
      ${rows
        .map(
          (r) => `
            <li>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:0.5rem;">
                <div>
                  <div><strong>${r[key]}</strong> <span style="color: var(--muted);">${r.department || r.criticality || ""}</span></div>
                  <span class="status ${classifyBand(r.risk_score)}">${classifyBand(r.risk_score)} · ${r.risk_score.toFixed(1)}</span>
                </div>
              </div>
              ${severityBar(r.risk_score)}
            </li>
          `,
        )
        .join("")}
    </ul>
  `;
}

function renderMitre(rows) {
  const el = document.getElementById("mitre");
  if (!rows.length) {
    el.innerHTML = `<div class="empty">No techniques recorded yet.</div>`;
    return;
  }
  const max = Math.max(...rows.map((r) => r.hits)) || 1;
  el.innerHTML = `
    <ul class="bare">
      ${rows
        .map(
          (r) => `
            <li>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="mitre-tag">${r.mitre}</span>
                <span class="mono">${r.hits}×</span>
              </div>
              <div class="bar" style="--w:${Math.round((r.hits / max) * 100)}%"></div>
            </li>
          `,
        )
        .join("")}
    </ul>
  `;
}

function renderAudit(rows) {
  const el = document.getElementById("audit");
  if (!rows.length) {
    el.innerHTML = `<div class="empty">No audit entries yet.</div>`;
    return;
  }
  el.innerHTML = `
    <table>
      <thead>
        <tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (r) => `
              <tr>
                <td>${relativeTime(r.ts)}</td>
                <td><span class="mono">${r.actor}</span></td>
                <td>${r.action}</td>
                <td><span class="mono">${r.target}</span></td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderAgents(rows) {
  const el = document.getElementById("agents");
  if (!rows.length) {
    el.innerHTML = `<div class="empty">No endpoint agents enrolled yet.</div>`;
    return;
  }
  el.innerHTML = `
    <table>
      <thead>
        <tr><th>Agent</th><th>Host</th><th>OS</th><th>Status</th><th>Risk</th><th>Last seen</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (r) => `
              <tr>
                <td><span class="mono">${r.agent_id}</span></td>
                <td>${r.hostname || "—"}</td>
                <td>${r.os_name || "—"}</td>
                <td><span class="status ${r.status === "active" ? "low" : "medium"}">${r.status}</span></td>
                <td><span class="status ${classifyBand(r.risk_score || 0)}">${(r.risk_score || 0).toFixed(1)}</span></td>
                <td>${relativeTime(r.last_seen)}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderIocs(rows) {
  const el = document.getElementById("iocs");
  if (!rows.length) {
    el.innerHTML = `<div class="empty">No IOCs registered yet.</div>`;
    return;
  }
  el.innerHTML = `
    <table>
      <thead><tr><th>Kind</th><th>Value</th><th>Source</th><th>Added</th></tr></thead>
      <tbody>
        ${rows
          .map(
            (r) => `
              <tr>
                <td><span class="mitre-tag">${r.kind}</span></td>
                <td><span class="mono">${r.value}</span></td>
                <td>${r.source}</td>
                <td>${relativeTime(r.added_at)}</td>
              </tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

async function refresh() {
  try {
    const [dashboard, alerts, agents, iocs] = await Promise.all([
      http("GET", "/api/dashboard"),
      http("GET", "/api/alerts"),
      http("GET", "/api/agents"),
      http("GET", "/api/iocs"),
    ]);
    renderCards(dashboard.totals);
    renderAlerts(alerts);
    renderRanking("topUsers", dashboard.top_users, "display_name");
    renderRanking("topAssets", dashboard.top_assets, "hostname");
    renderMitre(dashboard.mitre);
    renderAudit(dashboard.audit);
    renderAgents(agents);
    renderIocs(iocs);
  } catch (err) {
    toast(err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  refresh();
  setInterval(refresh, 5000);

  document.getElementById("publishPolicy").addEventListener("click", async () => {
    try {
      const result = await http("POST", "/api/policies/publish");
      toast(`Policy bundle v${result.version} published.`);
      refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  document.getElementById("verifyChains").addEventListener("click", async () => {
    try {
      const [events, audit] = await Promise.all([
        http("GET", "/api/events/verify"),
        http("GET", "/api/audit/verify"),
      ]);
      const ok = events.intact && audit.intact;
      toast(
        ok
          ? `Both chains verified · events:${events.count}, audit:${audit.count}`
          : `Chain integrity FAILED · events:${events.intact}, audit:${audit.intact}`,
        ok ? "success" : "error",
      );
    } catch (err) {
      toast(err.message, "error");
    }
  });

  document.getElementById("tokenForm").addEventListener("submit", async (evt) => {
    evt.preventDefault();
    const form = evt.target;
    const payload = {
      hostname: form.hostname.value.trim(),
      criticality: form.criticality.value,
    };
    try {
      const result = await http("POST", "/api/agents/enrol-tokens", payload);
      toast(`One-time token for ${payload.hostname}: ${result.enrol_token}`);
      form.reset();
      refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  document.getElementById("iocForm").addEventListener("submit", async (evt) => {
    evt.preventDefault();
    const form = evt.target;
    try {
      await http("POST", "/api/iocs", {
        kind: form.kind.value,
        value: form.value.value.trim(),
      });
      toast("IOC added.");
      form.reset();
      refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  });
});
