"""Returns a self-refreshing HTML dashboard (Chart.js) reading the /metrics JSON
endpoint. Serves the same purpose as the Grafana panels in the project spec,
without needing a separate Grafana server running inside the Colab session."""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>FinRAG Live Metrics</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
    h1 { font-size: 20px; margin-bottom: 4px; }
    .sub { color: #94a3b8; font-size: 13px; margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
    .card { background: #1e293b; border-radius: 12px; padding: 16px; }
    .card h2 { font-size: 13px; color: #94a3b8; margin: 0 0 8px 0; font-weight: 500; }
    .big { font-size: 32px; font-weight: 700; }
    canvas { max-height: 220px; }
  </style>
</head>
<body>
  <h1>FinRAG — Live Metrics</h1>
  <div class="sub">Auto-refreshes every 5s from /metrics</div>
  <div class="grid">
    <div class="card"><h2>Total Queries</h2><div class="big" id="total_queries">-</div></div>
    <div class="card"><h2>Cache Hit Rate</h2><div class="big" id="cache_hit_rate">-</div></div>
    <div class="card"><h2>Tokens Saved (cumulative)</h2><div class="big" id="tokens_saved">-</div></div>
    <div class="card"><h2>Documents Indexed</h2><div class="big" id="documents_indexed">-</div></div>
    <div class="card"><h2>Routing Distribution</h2><canvas id="routingChart"></canvas></div>
  </div>

<script>
let routingChart = null;

async function refresh() {
  const res = await fetch('/metrics');
  const data = await res.json();

  document.getElementById('total_queries').textContent = data.total_queries ?? 0;
  document.getElementById('cache_hit_rate').textContent = ((data.cache_hit_rate ?? 0) * 100).toFixed(1) + '%';
  document.getElementById('tokens_saved').textContent = data.total_tokens_saved ?? 0;
  document.getElementById('documents_indexed').textContent = data.documents_indexed ?? 0;

  const dist = data.routing_distribution || {};
  const labels = Object.keys(dist);
  const values = Object.values(dist).map(v => (v * 100).toFixed(1));

  if (!routingChart) {
    const ctx = document.getElementById('routingChart').getContext('2d');
    routingChart = new Chart(ctx, {
      type: 'doughnut',
      data: { labels: labels, datasets: [{ data: values, backgroundColor: ['#38bdf8', '#a78bfa', '#fb923c'] }] },
      options: { plugins: { legend: { labels: { color: '#e2e8f0' } } } }
    });
  } else {
    routingChart.data.labels = labels;
    routingChart.data.datasets[0].data = values;
    routingChart.update();
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""
