let currentDays = 7;
let chart = null;

// Live clock
function updateClock() {
  const el = document.getElementById("live-clock");
  if (el) el.textContent = new Date().toUTCString().replace(" GMT", " UTC");
}
setInterval(updateClock, 1000);
updateClock();

// Fetch and render summary cards
async function loadSummary(days) {
  const res = await fetch(`/api/summary?days=${days}`);
  const d = await res.json();
  document.getElementById("stat-total").textContent = d.total_calls.toLocaleString();
  document.getElementById("stat-latency").textContent = d.avg_latency_ms.toLocaleString();
  document.getElementById("stat-cost").textContent = `$${d.total_cost_usd.toFixed(4)}`;
  document.getElementById("stat-errors").textContent = d.error_rate;
  document.getElementById("stat-tokens").textContent = d.total_tokens.toLocaleString();
}

// Fetch and render timeline chart
async function loadTimeline(days) {
  const res = await fetch(`/api/calls/timeline?days=${days}`);
  const data = await res.json();

  const labels = data.map(d => d.date);
  const calls = data.map(d => d.calls);
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
          backgroundColor: "#c8f54233",
          borderColor: "#c8f542",
          borderWidth: 1,
        },
        {
          label: "Errors",
          data: errors,
          backgroundColor: "#ff444433",
          borderColor: "#ff4444",
          borderWidth: 1,
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#555", font: { family: "IBM Plex Mono", size: 11 } } }
      },
      scales: {
        x: { ticks: { color: "#555", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#1a1a1a" } },
        y: { ticks: { color: "#555", font: { family: "IBM Plex Mono", size: 10 } }, grid: { color: "#1a1a1a" }, beginAtZero: true }
      }
    }
  });
}

// Fetch and render call log
async function loadLog() {
  const res = await fetch("/api/calls/recent?limit=50");
  const calls = await res.json();

  const body = document.getElementById("log-body");
  const count = document.getElementById("log-count");

  count.textContent = `${calls.length} calls`;

  if (!calls.length) {
    body.innerHTML = `<tr><td colspan="8" class="empty">No calls logged yet.</td></tr>`;
    return;
  }

  body.innerHTML = calls.map(c => `
    <tr>
      <td>${new Date(c.timestamp).toLocaleTimeString()}</td>
      <td>${c.model}</td>
      <td>${c.source}</td>
      <td>${c.input_tokens.toLocaleString()}</td>
      <td>${c.output_tokens.toLocaleString()}</td>
      <td>${c.latency_ms}ms</td>
      <td>$${c.cost_usd.toFixed(5)}</td>
      <td class="status-${c.status}">${c.status}</td>
    </tr>
  `).join("");
}

// Send test query
async function sendQuery() {
  const prompt = document.getElementById("prompt-input").value.trim();
  const model = document.getElementById("model-select").value;
  const btn = document.getElementById("send-btn");
  const result = document.getElementById("query-result");

  if (!prompt) return;

  btn.disabled = true;
  btn.textContent = "Sending...";
  result.className = "query-result";
  result.textContent = "Waiting for response...";

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model, source: "dashboard" })
    });
    const data = await res.json();

    if (data.status === "error") {
      result.className = "query-result error";
      result.textContent = `Error: ${data.error}`;
    } else {
      result.className = "query-result success";
      result.textContent = `Response:\n${data.response}\n\n— ${data.input_tokens} in / ${data.output_tokens} out · ${data.latency_ms}ms · $${data.cost_usd}`;
    }

    // Refresh dashboard
    await loadAll();
  } catch (e) {
    result.className = "query-result error";
    result.textContent = `Request failed: ${e.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Send";
  }
}

// Range tab switching
document.querySelectorAll(".range-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll(".range-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentDays = parseInt(btn.dataset.days);
    await loadSummary(currentDays);
    await loadTimeline(currentDays);
  });
});

async function loadAll() {
  await Promise.all([
    loadSummary(currentDays),
    loadTimeline(currentDays),
    loadLog()
  ]);
}

// Init
loadAll();
// Auto-refresh every 30s
setInterval(loadAll, 30000);
