const reportStart = document.getElementById('report-start');
const reportEnd = document.getElementById('report-end');
const reportRegion = document.getElementById('report-region');
const reportsRefresh = document.getElementById('reports-refresh');
const downloadLatest = document.getElementById('download-latest');

const setDefaultDates = () => {
  const today = new Date();
  const iso = today.toISOString().slice(0, 10);
  if (!reportEnd.value) reportEnd.value = iso;
  if (!reportStart.value) {
    const start = new Date();
    start.setDate(start.getDate() - 6);
    reportStart.value = start.toISOString().slice(0, 10);
  }
};

const loadRegions = async () => {
  const data = await AppUI.fetchJSON('/api/regions');
  (data.regions || []).forEach((r) => {
    const opt = document.createElement('option');
    opt.value = r;
    opt.textContent = r;
    reportRegion.appendChild(opt);
  });
};

const loadSummary = async () => {
  const start = reportStart.value;
  const end = reportEnd.value;
  if (!start || !end) return;
  const summary = await AppUI.fetchJSON(`/api/reports/summary?start=${start}&end=${end}`);
  document.getElementById('rep-pack').textContent = AppUI.formatNumber(summary.total_pack);
  document.getElementById('rep-liter').textContent = AppUI.formatNumber(summary.total_liter);
  document.getElementById('rep-outlet').textContent = AppUI.formatNumber(summary.active_outlets);
  const errors = await AppUI.fetchJSON('/api/imports/errors?limit=50');
  document.getElementById('rep-errors').textContent = AppUI.formatNumber(errors.rows.length);
};

const drawTrendChart = (rows) => {
  const svg = document.getElementById('trend-chart');
  if (!svg) return;
  const width = 640;
  const height = 240;
  const pad = 30;
  svg.innerHTML = '';
  if (!rows.length) {
    svg.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#9aa1ab">No data</text>`;
    return;
  }
  const liters = rows.map((r) => Number(r.total_liter || 0));
  const packs = rows.map((r) => Number(r.total_pack || 0));
  const maxVal = Math.max(...liters, ...packs, 1);
  const xStep = (width - pad * 2) / Math.max(rows.length - 1, 1);
  const scaleY = (val) => height - pad - (val / maxVal) * (height - pad * 2);
  const pathFor = (vals) => vals.map((val, idx) => `${idx === 0 ? 'M' : 'L'} ${pad + idx * xStep} ${scaleY(val)}`).join(' ');

  const grid = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  for (let i = 0; i < 4; i += 1) {
    const y = pad + (i * (height - pad * 2)) / 3;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', pad);
    line.setAttribute('x2', width - pad);
    line.setAttribute('y1', y);
    line.setAttribute('y2', y);
    line.setAttribute('stroke', '#ebe6df');
    line.setAttribute('stroke-width', '1');
    grid.appendChild(line);
  }
  svg.appendChild(grid);

  const litersPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  litersPath.setAttribute('d', pathFor(liters));
  litersPath.setAttribute('fill', 'none');
  litersPath.setAttribute('stroke', '#146e62');
  litersPath.setAttribute('stroke-width', '2.5');
  svg.appendChild(litersPath);

  const packsPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  packsPath.setAttribute('d', pathFor(packs));
  packsPath.setAttribute('fill', 'none');
  packsPath.setAttribute('stroke', '#2f405a');
  packsPath.setAttribute('stroke-width', '2');
  svg.appendChild(packsPath);
};

const loadTrendInsights = (rows) => {
  const wrap = document.getElementById('trend-insights');
  if (!wrap) return;
  if (!rows.length) {
    wrap.innerHTML = `<div class="empty">No insights yet.</div>`;
    return;
  }
  const liters = rows.map((r) => Number(r.total_liter || 0));
  const total = liters.reduce((acc, v) => acc + v, 0);
  const avg = total / Math.max(liters.length, 1);
  let maxIdx = 0;
  let minIdx = 0;
  liters.forEach((v, idx) => {
    if (v > liters[maxIdx]) maxIdx = idx;
    if (v < liters[minIdx]) minIdx = idx;
  });
  wrap.innerHTML = `
    <div class="card slim">
      <div class="card-sub">Avg Liters / Day</div>
      <div class="card-title">${avg.toFixed(1)}</div>
    </div>
    <div class="card slim">
      <div class="card-sub">Best Day</div>
      <div class="card-title">${rows[maxIdx].date || '-'}</div>
    </div>
    <div class="card slim">
      <div class="card-sub">Lowest Day</div>
      <div class="card-title">${rows[minIdx].date || '-'}</div>
    </div>
    <div class="card slim">
      <div class="card-sub">Total Liters</div>
      <div class="card-title">${AppUI.formatNumber(total)}</div>
    </div>
  `;
};

const loadTopProducts = async () => {
  const start = reportStart.value;
  const end = reportEnd.value;
  if (!start || !end) return;
  const data = await AppUI.fetchJSON(`/api/sales/sku_breakdown?start=${start}&end=${end}`);
  const rows = (data.rows || []).sort((a, b) => Number(b.total_liter || 0) - Number(a.total_liter || 0)).slice(0, 6);
  const maxVal = Math.max(...rows.map((r) => Number(r.total_liter || 0)), 1);
  const list = document.getElementById('top-products');
  list.innerHTML = '';
  rows.forEach((r) => {
    const width = (Number(r.total_liter || 0) / maxVal) * 100;
    const item = document.createElement('div');
    item.className = 'bar-item';
    item.innerHTML = `
      <div>
        <div class="card-title" style="font-size:14px;">${r.product_name || r.product_id || '-'}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${width}%;"></div></div>
      </div>
      <div class="card-title" style="font-size:14px;">${AppUI.formatNumber(r.total_liter)}</div>
    `;
    list.appendChild(item);
  });
  if (!rows.length) {
    list.innerHTML = `<div class="empty">No products found.</div>`;
  }
};

const loadOutputLibrary = async () => {
  const data = await AppUI.fetchJSON('/api/reports/output_library');
  const rows = data.rows || [];
  const tbody = document.querySelector('#output-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    const status = r.status || 'generated';
    tr.innerHTML = `
      <td>${r.region || '-'}</td>
      <td>${r.file || '-'}</td>
      <td>${r.category || '-'}</td>
      <td><span class="tag ${status === 'generated' ? 'success' : ''}">${status}</span></td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" class="empty">No outputs yet.</td>`;
    tbody.appendChild(tr);
  }
};

const loadExportHistory = async () => {
  const data = await AppUI.fetchJSON('/api/reports/export_history?limit=25');
  const rows = data.rows || [];
  const tbody = document.querySelector('#export-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.dataset.exportId = r.export_id;
    tr.style.cursor = 'pointer';
    tr.innerHTML = `
      <td>${r.export_id}</td>
      <td>${r.region || '-'}</td>
      <td>${r.status}</td>
      <td>${AppUI.formatRelative(r.requested_at)}</td>
    `;
    tr.addEventListener('click', () => {
      if (r.export_id) {
        window.location = `/api/reports/export_download?export_id=${r.export_id}`;
      }
    });
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" class="empty">No exports yet.</td>`;
    tbody.appendChild(tr);
  }
};

const loadManifests = async () => {
  const data = await AppUI.fetchJSON('/api/reports/export_manifests');
  const rows = data.regions || [];
  const tbody = document.querySelector('#manifest-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.region || '-'}</td>
      <td>${AppUI.formatNumber(r.total_files)}</td>
      <td>${AppUI.formatNumber(r.generated)}</td>
      <td>${AppUI.formatNumber(r.passthrough)}</td>
      <td>${(r.categories || []).join(', ')}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan=\"5\" class=\"empty\">No manifests yet.</td>`;
    tbody.appendChild(tr);
  }
};

const refreshAll = async () => {
  await loadSummary();
  const trend = await AppUI.fetchJSON(`/api/reports/trends?start=${reportStart.value}&end=${reportEnd.value}`);
  drawTrendChart(trend.rows || []);
  loadTrendInsights(trend.rows || []);
  await loadTopProducts();
  await loadOutputLibrary();
  await loadExportHistory();
  await loadManifests();
};

reportsRefresh.addEventListener('click', refreshAll);
[reportStart, reportEnd].forEach((input) => input.addEventListener('change', loadSummary));

setDefaultDates();
loadRegions();
refreshAll();

if (downloadLatest) {
  downloadLatest.addEventListener('click', async () => {
    const history = await AppUI.fetchJSON('/api/reports/export_history?limit=1');
    if (history.rows && history.rows[0]) {
      window.location = `/api/reports/export_download?export_id=${history.rows[0].export_id}`;
    } else {
      alert('No export available yet.');
    }
  });
}
