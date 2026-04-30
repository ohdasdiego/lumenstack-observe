// ─────────────────────────────────────────────
// State
// ─────────────────────────────────────────────
let currentDays = 7;
let chart = null;
let allCalls = [];
let activeSource = "";

// ─────────────────────────────────────────────
// Live clock
// ─────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById("live-clock");
  if (el) el.textContent = new Date().toUTCString().replace(" GMT", " UTC");
}
setInterval(updateClock, 1000);
updateClock();

// ─────────────────────────────────────────────
// Summary cards
// ─────────────────────────────────────────────
async function loadSummary(days) {
  const res = await fetch(`/api/summary?days=${days}`);
  const d = await res.json();
  document.getElementById("stat-total").textContent = d.total_calls.toLocaleString();
  document.getElementById("stat-latency").textContent = d.avg_latency_ms.toLocaleString();
  document.getElementById("stat-cost").textContent = `$${d.total_cost_usd.toFixed(4)}`;
  document.getElementById("stat-errors").textContent = d.error_rate;
  document.getElementById("stat-tokens").textContent = d.total_tokens.toLocaleString();
}

// ─────────────────────────────────────────────
// Timeline chart
// ─────────────────────────────────────────────
async function loadTimeline(days) {
  const res = await fetch(`/api/calls/timeline?days=${days}`);
  const data = await res.json();

  const labels = data.map(d => d.date);
  const calls  = data.map(d => d.calls);
  const errors = data.map(d => d.errors);

  if (chart) chart.destroy();

  const ctx = document.getElementById("timeline-chart").getContext("2d");
  chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Calls",
          data: calls,
          backgroundColor: "rgba(77, 159, 255, 0.15)",
          borderColor: "#4d9fff",
          borderWidth: 1,
        },
        {
          label: "Errors",
          data: errors,
          backgroundColor: "rgba(255, 95, 95, 0.15)",
          borderColor: "#ff5f5f",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          labels: { color: "#6b82a8", font: { family: "IBM Plex Mono", size: 11 } },
        },
      },
      scales: {
        x: {
          ticks: { color: "#6b82a8", font: { family: "IBM Plex Mono", size: 10 } },
          grid: { color: "#1a2a45" },
        },
        y: {
          ticks: { color: "#6b82a8", font: { family: "IBM Plex Mono", size: 10 } },
          grid: { color: "#1a2a45" },
          beginAtZero: true,
        },
      },
    },
  });
}

// ─────────────────────────────────────────────
// Model breakdown
// ─────────────────────────────────────────────
function renderModelBreakdown(calls) {
  const container = document.getElementById("model-breakdown");

  if (!calls.length) {
    container.innerHTML = `<p class="model-empty">No data yet.</p>`;
    return;
  }

  // Aggregate by model
  const models = {};
  for (const c of calls) {
    if (!models[c.model]) models[c.model] = { calls: 0, cost: 0 };
    models[c.model].calls++;
    models[c.model].cost += c.cost_usd;
  }

  const maxCalls = Math.max(...Object.values(models).map(m => m.calls));

  container.innerHTML = Object.entries(models)
    .sort((a, b) => b[1].calls - a[1].calls)
    .map(([name, stats]) => {
      const pct = maxCalls > 0 ? (stats.calls / maxCalls) * 100 : 0;
      return `
        <div class="model-row">
          <div class="model-row-header">
            <span class="model-name">${name}</span>
            <span class="model-stats">${stats.calls} calls · $${stats.cost.toFixed(5)}</span>
          </div>
          <div class="model-bar-track">
            <div class="model-bar-fill" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    }).join("");
}

// ─────────────────────────────────────────────
// Call log + source filter
// ─────────────────────────────────────────────
function populateSourceFilter(calls) {
  const sel = document.getElementById("source-filter");
  const sources = [...new Set(calls.map(c => c.source))].sort();
  const current = sel.value;

  // Keep "All sources" option, rebuild rest
  sel.innerHTML = `<option value="">All sources</option>` +
    sources.map(s => `<option value="${s}" ${s === current ? "selected" : ""}>${s}</option>`).join("");
}

function applyFilter() {
  activeSource = document.getElementById("source-filter").value;
  renderLog(allCalls);
}

function renderLog(calls) {
  const filtered = activeSource ? calls.filter(c => c.source === activeSource) : calls;
  const body  = document.getElementById("log-body");
  const count = document.getElementById("log-count");

  count.textContent = `${filtered.length} calls`;

  if (!filtered.length) {
    body.innerHTML = `<tr><td colspan="9" class="empty">No calls match the current filter.</td></tr>`;
    return;
  }

  body.innerHTML = filtered.map(c => `
    <tr onclick="openModal(${c.id})">
      <td>${new Date(c.timestamp).toLocaleTimeString()}</td>
      <td>${c.model}</td>
      <td>${c.source}</td>
      <td><div class="prompt-preview" title="${escHtml(c.prompt_preview)}">${escHtml(c.prompt_preview)}</div></td>
      <td>${c.input_tokens.toLocaleString()}</td>
      <td>${c.output_tokens.toLocaleString()}</td>
      <td>${c.latency_ms}ms</td>
      <td>$${c.cost_usd.toFixed(5)}</td>
      <td class="status-${c.status}">${c.status}</td>
    </tr>
  `).join("");
}

async function loadLog() {
  const res = await fetch("/api/calls/recent?limit=100");
  allCalls = await res.json();
  populateSourceFilter(allCalls);
  renderLog(allCalls);
  renderModelBreakdown(allCalls);
}

// ─────────────────────────────────────────────
// Call detail modal
// ─────────────────────────────────────────────
async function openModal(callId) {
  const res = await fetch(`/api/calls/${callId}`);
  if (!res.ok) return;
  const d = await res.json();

  const statusClass = d.status === "error" ? "status-error" : "status-success";
  const ts = new Date(d.timestamp).toLocaleString();

  document.getElementById("modal-body").innerHTML = `
    <div class="modal-meta">
      <div class="modal-meta-item">
        <div class="modal-meta-label">Time</div>
        <div class="modal-meta-value" style="font-size:11px">${ts}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Model</div>
        <div class="modal-meta-value" style="font-size:11px">${d.model}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Source</div>
        <div class="modal-meta-value" style="font-size:11px">${d.source}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Status</div>
        <div class="modal-meta-value ${statusClass}" style="font-size:11px">${d.status}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Tokens In</div>
        <div class="modal-meta-value">${d.input_tokens.toLocaleString()}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Tokens Out</div>
        <div class="modal-meta-value">${d.output_tokens.toLocaleString()}</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Latency</div>
        <div class="modal-meta-value">${d.latency_ms}ms</div>
      </div>
      <div class="modal-meta-item">
        <div class="modal-meta-label">Cost</div>
        <div class="modal-meta-value">$${d.cost_usd.toFixed(6)}</div>
      </div>
    </div>

    <div>
      <div class="modal-field-label">Prompt</div>
      <div class="modal-text">${escHtml(d.prompt)}</div>
    </div>

    <div>
      <div class="modal-field-label">Response</div>
      <div class="modal-text ${d.status === 'error' ? 'error-text' : ''}">${
        d.status === 'error'
          ? escHtml(d.error_message || 'Unknown error')
          : escHtml(d.response)
      }</div>
    </div>
  `;

  document.getElementById("modal-overlay").classList.add("open");
  document.body.style.overflow = "hidden";
}

function closeModal(e) {
  if (e.target === document.getElementById("modal-overlay")) closeModalBtn();
}

function closeModalBtn() {
  document.getElementById("modal-overlay").classList.remove("open");
  document.body.style.overflow = "";
}

document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeModalBtn();
});

// ─────────────────────────────────────────────
// Send test query
// ─────────────────────────────────────────────
async function sendQuery() {
  const prompt = document.getElementById("prompt-input").value.trim();
  const model  = document.getElementById("model-select").value;
  const btn    = document.getElementById("send-btn");
  const result = document.getElementById("query-result");

  if (!prompt) return;

  btn.disabled = true;
  btn.textContent = "Sending…";
  result.className = "query-result";
  result.textContent = "Waiting for response…";

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model, source: "dashboard" }),
    });

    if (res.status === 429) {
      result.className = "query-result error";
      result.textContent = "Rate limit reached — max 5 queries per minute. Please wait a moment and try again.";
      return;
    }

    const data = await res.json();

    if (data.status === "error") {
      result.className = "query-result error";
      result.textContent = `Error: ${data.error}`;
    } else {
      result.className = "query-result success";
      result.textContent = `${data.response}\n\n─── ${data.input_tokens} in / ${data.output_tokens} out · ${data.latency_ms}ms · $${data.cost_usd}`;
    }

    await loadAll();
  } catch (e) {
    result.className = "query-result error";
    result.textContent = `Request failed: ${e.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Send";
  }
}

// ─────────────────────────────────────────────
// Range tab switching
// ─────────────────────────────────────────────
document.querySelectorAll(".range-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentDays = parseInt(btn.dataset.days);
    await loadSummary(currentDays);
    await loadTimeline(currentDays);
  });
});

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────
function escHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─────────────────────────────────────────────
// Init + auto-refresh
// ─────────────────────────────────────────────
async function loadAll() {
  await Promise.all([
    loadSummary(currentDays),
    loadTimeline(currentDays),
    loadLog(),
  ]);
}

loadAll();
setInterval(loadAll, 30000);
