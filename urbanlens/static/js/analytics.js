// ════════════════════════════════════════
// ANALYTICS & REPORTS
// ════════════════════════════════════════

async function loadAnalytics() {
  try {
    const res = await fetch('/analytics/stats');
    if (!res.ok) return;
    const data = await res.json();
    renderAnalytics(data);
  } catch(e) { showToast('Failed to load analytics', true); }
}

function renderAnalytics(data) {
  const s = data.settlements;
  const inf = data.infrastructure;

  // Summary cards
  document.getElementById('stat-total-settlements').textContent = s.total;
  document.getElementById('stat-total-pop').textContent = s.total_population.toLocaleString();
  document.getElementById('stat-total-area').textContent = s.total_area_km2 + ' km\u00B2';
  document.getElementById('stat-avg-density').textContent = s.avg_density.toLocaleString() + '/km\u00B2';
  document.getElementById('stat-total-infra').textContent = inf.total;

  // Risk breakdown
  const riskHtml = Object.entries(s.by_risk).map(([level, count]) =>
    `<div class="breakdown-row">
      <span class="risk-badge risk-${level}">${level}</span>
      <span class="breakdown-bar"><span class="bar-fill bar-${level.toLowerCase()}" style="width:${s.total ? (count/s.total*100) : 0}%"></span></span>
      <span class="breakdown-val">${count}</span>
    </div>`
  ).join('');
  document.getElementById('risk-breakdown').innerHTML = riskHtml;

  // Status breakdown
  const statusHtml = Object.entries(s.by_status).map(([status, count]) =>
    `<div class="breakdown-row">
      <span class="status-badge status-${status}">${status}</span>
      <span class="breakdown-bar"><span class="bar-fill bar-${status.toLowerCase()}" style="width:${s.total ? (count/s.total*100) : 0}%"></span></span>
      <span class="breakdown-val">${count}</span>
    </div>`
  ).join('');
  document.getElementById('status-breakdown').innerHTML = statusHtml;

  // Infrastructure by type
  const typeOrder = ['Road', 'Water Point', 'Sanitation', 'Waste Point', 'School', 'Health Center'];
  const typeColors = {
    'Road': '#9ca3af', 'Water Point': '#3b82f6', 'Sanitation': '#22c55e',
    'Waste Point': '#f97316', 'School': '#eab308', 'Health Center': '#ef4444'
  };
  const infraHtml = typeOrder.map(type => {
    const count = inf.by_type[type] || 0;
    return `<div class="breakdown-row">
      <span class="infra-type-label"><span class="layer-color" style="background:${typeColors[type]}"></span> ${type}</span>
      <span class="breakdown-bar"><span class="bar-fill" style="width:${inf.total ? (count/inf.total*100) : 0}%;background:${typeColors[type]}"></span></span>
      <span class="breakdown-val">${count}</span>
    </div>`;
  }).join('');
  document.getElementById('infra-breakdown').innerHTML = infraHtml;

  // Condition breakdown
  const condOrder = ['Good', 'Fair', 'Poor', 'Critical'];
  const condColors = { Good: '#22c55e', Fair: '#eab308', Poor: '#f97316', Critical: '#ef4444' };
  const condTotal = Object.values(inf.by_condition).reduce((a, b) => a + b, 0);
  const condHtml = condOrder.map(cond => {
    const count = inf.by_condition[cond] || 0;
    return `<div class="breakdown-row">
      <span class="cond-label" style="color:${condColors[cond]}">${cond}</span>
      <span class="breakdown-bar"><span class="bar-fill" style="width:${condTotal ? (count/condTotal*100) : 0}%;background:${condColors[cond]}"></span></span>
      <span class="breakdown-val">${count}</span>
    </div>`;
  }).join('');
  document.getElementById('condition-breakdown').innerHTML = condHtml;
}

function exportCSV() {
  window.open('/analytics/report/csv', '_blank');
}

function printReport() {
  const content = document.getElementById('analytics-content').innerHTML;
  const win = window.open('', '_blank');
  win.document.write(`<!DOCTYPE html><html><head><title>UrbanLens Planning Report</title>
    <style>
      body { font-family: Arial, sans-serif; padding: 40px; color: #1a1a1a; }
      h1 { font-size: 24px; margin-bottom: 4px; }
      h2 { font-size: 16px; margin-top: 24px; border-bottom: 2px solid #f59e0b; padding-bottom: 6px; }
      .report-date { color: #666; font-size: 12px; margin-bottom: 24px; }
      .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 16px 0; }
      .stat-card { border: 1px solid #ddd; padding: 16px; text-align: center; }
      .stat-number { font-size: 28px; font-weight: 800; color: #f59e0b; }
      .stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #666; margin-top: 4px; }
      .breakdown-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
      .breakdown-bar { flex: 1; height: 8px; background: #eee; }
      .bar-fill { height: 100%; display: block; }
      .breakdown-val { font-weight: 700; min-width: 30px; text-align: right; }
      .analytics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
      .analytics-card { border: 1px solid #ddd; padding: 16px; }
      .analytics-card h3 { font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #666; margin-bottom: 12px; }
      @media print { body { padding: 20px; } }
    </style>
  </head><body>
    <h1>UrbanLens Planning Report</h1>
    <div class="report-date">Generated: ${new Date().toLocaleDateString('en-GB', { day:'2-digit', month:'long', year:'numeric' })}</div>
    ${content}
  </body></html>`);
  win.document.close();
  setTimeout(() => win.print(), 500);
}
