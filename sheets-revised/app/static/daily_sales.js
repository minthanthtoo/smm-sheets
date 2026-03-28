const dayInput = document.getElementById('day-input');
const rangeStart = document.getElementById('range-start');
const rangeEnd = document.getElementById('range-end');
const refreshBtn = document.getElementById('refresh-btn');
const todayBtn = document.getElementById('today-btn');
const txnSearch = document.getElementById('txn-search');

const setDefaultDates = () => {
  const today = new Date();
  const iso = today.toISOString().slice(0, 10);
  if (!dayInput.value) dayInput.value = iso;
  if (!rangeEnd.value) rangeEnd.value = iso;
  if (!rangeStart.value) {
    const start = new Date();
    start.setDate(start.getDate() - 6);
    rangeStart.value = start.toISOString().slice(0, 10);
  }
};

const setText = (id, value) => {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
};

const loadSummary = async () => {
  const start = rangeStart.value;
  const end = rangeEnd.value;
  if (!start || !end) return;
  const summary = await AppUI.fetchJSON(`/api/reports/summary?start=${start}&end=${end}`);
  setText('stat-pack', AppUI.formatNumber(summary.total_pack));
  setText('stat-bottle', AppUI.formatNumber(summary.total_bottle));
  setText('stat-liter', AppUI.formatNumber(summary.total_liter));
  setText('stat-outlet', AppUI.formatNumber(summary.active_outlets));
  const quality = await AppUI.fetchJSON(`/api/quality/summary?start=${start}&end=${end}`);
  setText('stat-missing-outlet', AppUI.formatNumber(quality.missing_outlet));
  setText('stat-missing-product', AppUI.formatNumber(quality.missing_product));
  setText('stat-missing-route', AppUI.formatNumber(quality.missing_route));
};

const fillTable = (tbody, rows, renderRow) => {
  tbody.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = renderRow(row);
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="8" class="empty">No data found.</td>`;
    tbody.appendChild(tr);
  }
};

const loadTransactions = async () => {
  const day = dayInput.value;
  if (!day) return;
  const data = await AppUI.fetchJSON(`/api/sales?date=${day}`);
  const rows = data.rows || [];
  const query = (txnSearch.value || '').toLowerCase();
  const filtered = query
    ? rows.filter((r) => {
        const hay = `${r.outlet_name_mm || ''} ${r.outlet_name_en || ''} ${r.product_name || ''} ${r.voucher_no || ''}`.toLowerCase();
        return hay.includes(query);
      })
    : rows;
  const tbody = document.querySelector('#txn-table tbody');
  fillTable(tbody, filtered, (r) => `
    <td>${r.date || '-'}</td>
    <td>${r.outlet_name_mm || r.outlet_name_en || r.outlet_id || '-'}</td>
    <td>${r.product_name || r.product_id || '-'}</td>
    <td>${AppUI.formatNumber(r.qty_pack)}</td>
    <td>${AppUI.formatNumber(r.qty_bottle)}</td>
    <td>${AppUI.formatNumber(r.qty_liter)}</td>
    <td>${r.route_id || '-'}</td>
    <td>${r.voucher_no || '-'}</td>
  `);
};

const loadSku = async () => {
  const start = rangeStart.value;
  const end = rangeEnd.value;
  if (!start || !end) return;
  const data = await AppUI.fetchJSON(`/api/sales/sku_breakdown?start=${start}&end=${end}`);
  const tbody = document.querySelector('#sku-table tbody');
  fillTable(tbody, data.rows || [], (r) => `
    <td>${r.product_name || r.product_id || '-'}</td>
    <td>${AppUI.formatNumber(r.total_pack)}</td>
    <td>${AppUI.formatNumber(r.total_bottle)}</td>
    <td>${AppUI.formatNumber(r.total_liter)}</td>
    <td>${AppUI.formatNumber(r.txn_count)}</td>
  `);
};

const loadOutletPerf = async () => {
  const start = rangeStart.value;
  const end = rangeEnd.value;
  if (!start || !end) return;
  const data = await AppUI.fetchJSON(`/api/sales/outlet_performance?start=${start}&end=${end}`);
  const tbody = document.querySelector('#outlet-table tbody');
  fillTable(tbody, data.rows || [], (r) => `
    <td>${r.outlet_name_mm || r.outlet_name_en || r.outlet_id || '-'}</td>
    <td>${r.outlet_type || '-'}</td>
    <td>${AppUI.formatNumber(r.total_pack)}</td>
    <td>${AppUI.formatNumber(r.total_bottle)}</td>
    <td>${AppUI.formatNumber(r.total_liter)}</td>
    <td>${AppUI.formatNumber(r.txn_count)}</td>
  `);
};

const loadRoutePerf = async () => {
  const start = rangeStart.value;
  const end = rangeEnd.value;
  if (!start || !end) return;
  const data = await AppUI.fetchJSON(`/api/sales/route_performance?start=${start}&end=${end}`);
  const tbody = document.querySelector('#route-table tbody');
  fillTable(tbody, data.rows || [], (r) => `
    <td>${r.route_name || r.route_id || '-'}</td>
    <td>${r.van_id || r.way_code || '-'}</td>
    <td>${AppUI.formatNumber(r.total_pack)}</td>
    <td>${AppUI.formatNumber(r.total_bottle)}</td>
    <td>${AppUI.formatNumber(r.total_liter)}</td>
    <td>${AppUI.formatNumber(r.txn_count)}</td>
  `);
};

const refreshAll = async () => {
  await loadSummary();
  await loadTransactions();
  await loadSku();
  await loadOutletPerf();
  await loadRoutePerf();
};

refreshBtn.addEventListener('click', refreshAll);
todayBtn.addEventListener('click', () => {
  const today = new Date().toISOString().slice(0, 10);
  dayInput.value = today;
  rangeEnd.value = today;
  const start = new Date();
  start.setDate(start.getDate() - 6);
  rangeStart.value = start.toISOString().slice(0, 10);
  refreshAll();
});

[dayInput, rangeStart, rangeEnd].forEach((input) => {
  input.addEventListener('change', refreshAll);
});

txnSearch.addEventListener('input', loadTransactions);

setDefaultDates();
refreshAll();
