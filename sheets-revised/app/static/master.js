const regionSelect = document.getElementById('master-region');
const masterSearch = document.getElementById('master-search');
const pjpDate = document.getElementById('pjp-date');
const masterRefresh = document.getElementById('master-refresh');

const fillTable = (tbody, rows, renderRow, emptyCols) => {
  tbody.innerHTML = '';
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = renderRow(row);
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="${emptyCols}" class="empty">No records.</td>`;
    tbody.appendChild(tr);
  }
};

const loadRegions = async () => {
  const data = await AppUI.fetchJSON('/api/master/regions');
  data.rows.forEach((r) => {
    const opt = document.createElement('option');
    opt.value = r.region_id;
    opt.textContent = r.region_name || r.region_id;
    regionSelect.appendChild(opt);
  });
};

const loadProducts = async () => {
  const data = await AppUI.fetchJSON('/api/master/products');
  const query = (masterSearch.value || '').toLowerCase();
  const rows = query
    ? data.rows.filter((r) => `${r.product_id} ${r.product_name} ${r.brand}`.toLowerCase().includes(query))
    : data.rows;
  fillTable(document.querySelector('#products-table tbody'), rows, (r) => `
    <td>${r.product_id || '-'}</td>
    <td>${r.product_name || '-'}</td>
    <td>${r.brand || '-'}</td>
    <td>${r.category || '-'}</td>
    <td>${AppUI.formatNumber(r.sales_price)}</td>
    <td>${AppUI.formatNumber(r.pack_size)}</td>
  `, 6);
};

const loadTownships = async () => {
  const region = regionSelect.value;
  const url = region ? `/api/master/townships?region_id=${region}` : '/api/master/townships';
  const data = await AppUI.fetchJSON(url);
  const query = (masterSearch.value || '').toLowerCase();
  const rows = query
    ? data.rows.filter((r) => `${r.township_name} ${r.township_name_en} ${r.township_id}`.toLowerCase().includes(query))
    : data.rows;
  fillTable(document.querySelector('#townships-table tbody'), rows, (r) => `
    <td>${r.township_name || '-'}</td>
    <td>${r.region_id || '-'}</td>
    <td>${r.aliases || '-'}</td>
    <td>${r.source_file || '-'}</td>
  `, 4);
};

const loadRoutes = async () => {
  const region = regionSelect.value;
  const url = region ? `/api/master/routes?region_id=${region}` : '/api/master/routes';
  const data = await AppUI.fetchJSON(url);
  const query = (masterSearch.value || '').toLowerCase();
  const rows = query
    ? data.rows.filter((r) => `${r.route_name} ${r.route_id}`.toLowerCase().includes(query))
    : data.rows;
  fillTable(document.querySelector('#routes-table tbody'), rows, (r) => `
    <td>${r.route_name || r.route_id || '-'}</td>
    <td>${r.region_id || '-'}</td>
    <td>${r.van_id || '-'}</td>
    <td>${r.way_code || '-'}</td>
    <td>${r.township_id || '-'}</td>
  `, 5);
};

const loadPjp = async () => {
  const date = pjpDate.value;
  const url = date ? `/api/master/pjp?date=${date}` : '/api/master/pjp';
  const data = await AppUI.fetchJSON(url);
  const rows = data.rows || [];
  fillTable(document.querySelector('#pjp-table tbody'), rows, (r) => `
    <td>${r.date || '-'}</td>
    <td>${r.route_id || '-'}</td>
    <td>${AppUI.formatNumber(r.total_planned)}</td>
    <td>${AppUI.formatNumber(r.planned_a)}</td>
    <td>${AppUI.formatNumber(r.planned_b)}</td>
    <td>${AppUI.formatNumber(r.planned_c)}</td>
    <td>${AppUI.formatNumber(r.planned_d)}</td>
    <td>${AppUI.formatNumber(r.planned_s)}</td>
  `, 8);
};

const loadHistory = async () => {
  const query = (masterSearch.value || '').toLowerCase();
  const [productHist, townshipHist, routeHist] = await Promise.all([
    AppUI.fetchJSON('/api/master/products/history_all?limit=80'),
    AppUI.fetchJSON('/api/master/townships/history_all?limit=80'),
    AppUI.fetchJSON('/api/master/routes/history_all?limit=80'),
  ]);
  const rows = [];
  productHist.rows.forEach((r) => rows.push({ type: 'Product', id: r.product_id, region: '', from: r.effective_from, to: r.effective_to }));
  townshipHist.rows.forEach((r) => rows.push({ type: 'Township', id: r.township_id, region: r.region_id, from: r.effective_from, to: r.effective_to }));
  routeHist.rows.forEach((r) => rows.push({ type: 'Route', id: r.route_id, region: r.region_id, from: r.effective_from, to: r.effective_to }));
  const filtered = query
    ? rows.filter((r) => `${r.type} ${r.id} ${r.region}`.toLowerCase().includes(query))
    : rows;
  fillTable(document.querySelector('#history-table tbody'), filtered, (r) => `
    <td>${r.type}</td>
    <td>${r.id || '-'}</td>
    <td>${r.region || '-'}</td>
    <td>${r.from || '-'}</td>
    <td>${r.to || '-'}</td>
  `, 5);
};

const refreshAll = async () => {
  await loadProducts();
  await loadTownships();
  await loadRoutes();
  await loadPjp();
  await loadHistory();
};

masterSearch.addEventListener('input', refreshAll);
regionSelect.addEventListener('change', refreshAll);
pjpDate.addEventListener('change', refreshAll);
masterRefresh.addEventListener('click', refreshAll);

loadRegions().then(refreshAll);
