const jobsEl = document.getElementById("jobs");
const messageEl = document.getElementById("message");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function renderJobs(jobs) {
  jobsEl.innerHTML = "";
  if (!jobs.length) {
    jobsEl.innerHTML = "<p>لا توجد مهام معلّقة.</p>";
    return;
  }
  for (const job of jobs) {
    const card = document.createElement("article");
    card.className = "job-card";
    card.innerHTML = `
      <h3>${job.document_name}</h3>
      <p>${job.printer_name} · ${job.pages} صفحة · ${(job.cost_cents / 100).toFixed(2)}</p>
      <button data-id="${job.id}">تحرير الطباعة</button>
    `;
    card.querySelector("button").addEventListener("click", async () => {
      try {
        await api(`/api/release/jobs/${job.id}/release`, {
          method: "POST",
          body: JSON.stringify({ username: document.getElementById("username").value.trim() }),
        });
        messageEl.textContent = `تم تحرير المهمة #${job.id}`;
        document.getElementById("load-held").click();
      } catch (error) {
        messageEl.textContent = error.message;
      }
    });
    jobsEl.appendChild(card);
  }
}

document.getElementById("load-held").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  if (!username) {
    messageEl.textContent = "أدخل اسم المستخدم.";
    return;
  }
  try {
    const jobs = await api(`/api/release/held/${encodeURIComponent(username)}`);
    renderJobs(jobs);
    messageEl.textContent = "";
  } catch (error) {
    messageEl.textContent = error.message;
  }
});
