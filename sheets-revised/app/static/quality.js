const issueKind = document.getElementById('issue-kind');
const issueStart = document.getElementById('issue-start');
const issueEnd = document.getElementById('issue-end');
const qualityRefresh = document.getElementById('quality-refresh');
const actionSearch = document.getElementById('action-search');

const loadIssues = async () => {
  const kind = issueKind.value;
  const start = issueStart.value;
  const end = issueEnd.value;
  let url = `/api/quality/issues?kind=${kind}&limit=200`;
  if (start && end) url += `&start=${start}&end=${end}`;
  const data = await AppUI.fetchJSON(url);
  const rows = data.rows || [];
  const tbody = document.querySelector('#issue-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.date || '-'}</td>
      <td>${r.outlet_name_raw || r.outlet_id || '-'}</td>
      <td>${r.stock_name_raw || r.product_id || '-'}</td>
      <td>${r.route_id || '-'}</td>
      <td>${AppUI.formatNumber(r.qty_pack)}</td>
      <td>${AppUI.formatNumber(r.qty_bottle)}</td>
      <td>${AppUI.formatNumber(r.qty_liter)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="7" class="empty">No issues in selected range.</td>`;
    tbody.appendChild(tr);
  }
};

const loadHealth = async () => {
  const data = await AppUI.fetchJSON('/api/quality/import_health');
  const rows = data.rows || [];
  const tbody = document.querySelector('#health-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.region || '-'}</td>
      <td>${AppUI.formatNumber(r.success_count)}</td>
      <td>${AppUI.formatNumber(r.failed_count)}</td>
      <td>${AppUI.formatNumber(r.total_count)}</td>
      <td>${AppUI.formatRelative(r.last_requested)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="5" class="empty">No import jobs yet.</td>`;
    tbody.appendChild(tr);
  }
};

const loadActions = async () => {
  const query = actionSearch.value || '';
  const data = await AppUI.fetchJSON(`/api/quality/actions?limit=200&q=${encodeURIComponent(query)}`);
  const rows = data.rows || [];
  const tbody = document.querySelector('#action-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.table_name || '-'}</td>
      <td>${r.record_id || '-'}</td>
      <td>${r.action || '-'}</td>
      <td>${AppUI.formatRelative(r.changed_at)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" class="empty">No audit actions yet.</td>`;
    tbody.appendChild(tr);
  }
};

const refreshAll = async () => {
  await loadIssues();
  await loadHealth();
  await loadActions();
};

qualityRefresh.addEventListener('click', refreshAll);
issueKind.addEventListener('change', loadIssues);
issueStart.addEventListener('change', loadIssues);
issueEnd.addEventListener('change', loadIssues);
actionSearch.addEventListener('input', loadActions);

refreshAll();
