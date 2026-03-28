const outletSearch = document.getElementById('outlet-search');
const outletActive = document.getElementById('outlet-active');
const outletRefresh = document.getElementById('outlet-refresh');
const outletCount = document.getElementById('outlet-count');
const dedupeSearch = document.getElementById('dedupe-search');
const historySearch = document.getElementById('history-search');

const loadOutlets = async () => {
  const search = outletSearch.value || '';
  const includeInactive = outletActive.value === 'all' ? 1 : 0;
  const data = await AppUI.fetchJSON(`/api/outlets?search=${encodeURIComponent(search)}&include_inactive=${includeInactive}`);
  const rows = data.outlets || [];
  outletCount.textContent = `${rows.length} shown`;
  const tbody = document.querySelector('#outlet-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.outlet_name_mm || r.outlet_name_en || r.outlet_id || '-'}</td>
      <td>${r.outlet_type || '-'}</td>
      <td>${r.township_name_raw || '-'}</td>
      <td>${r.contact_phone || '-'}</td>
      <td>${r.status || 'active'}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="5" class="empty">No outlets found.</td>`;
    tbody.appendChild(tr);
  }
};

const loadDedupe = async () => {
  const data = await AppUI.fetchJSON('/api/outlets/dedupe');
  const groups = data.groups || [];
  const query = (dedupeSearch.value || '').toLowerCase();
  const list = document.getElementById('dedupe-list');
  list.innerHTML = '';
  const filtered = query
    ? groups.filter((g) => g.outlets.some((o) => (o.outlet_name_mm || '').toLowerCase().includes(query) || (o.outlet_name_en || '').toLowerCase().includes(query)))
    : groups;
  if (!filtered.length) {
    list.innerHTML = `<div class="empty">No dedupe candidates found.</div>`;
    return;
  }
  filtered.forEach((group, idx) => {
    const item = document.createElement('div');
    item.className = `accordion-item ${idx === 0 ? 'open' : ''}`;
    const names = group.outlets.map((o) => o.outlet_name_mm || o.outlet_name_en || o.outlet_id).join(', ');
    item.innerHTML = `
      <div class="accordion-header">
        <h4>${group.reason.replace('_', ' ')} · ${group.outlets.length} outlets</h4>
        <span class="tag">${group.key}</span>
      </div>
      <div class="accordion-body">
        <div class="card-sub">${names}</div>
        <div class="table-wrap" style="margin-top:12px;">
          <table class="table">
            <thead>
              <tr>
                <th>Outlet</th>
                <th>Township</th>
                <th>Phone</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              ${group.outlets.map((o) => `
                <tr>
                  <td>${o.outlet_name_mm || o.outlet_name_en || o.outlet_id || '-'}</td>
                  <td>${o.township_name_raw || '-'}</td>
                  <td>${o.contact_phone || '-'}</td>
                  <td>${o.outlet_type || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
    list.appendChild(item);
  });
  AppUI.initAccordions();
};

const loadHistory = async () => {
  const query = historySearch.value || '';
  const data = await AppUI.fetchJSON(`/api/outlets/history_all?limit=200&q=${encodeURIComponent(query)}`);
  const rows = data.rows || [];
  const tbody = document.querySelector('#history-table tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.outlet_id || '-'}</td>
      <td>${r.outlet_name_mm || r.outlet_name_en || '-'}</td>
      <td>${r.outlet_type || '-'}</td>
      <td>${r.region_id || '-'}</td>
      <td>${r.effective_from || '-'}</td>
      <td>${r.effective_to || '-'}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="6" class="empty">No history records.</td>`;
    tbody.appendChild(tr);
  }
};

outletSearch.addEventListener('input', loadOutlets);
outletActive.addEventListener('change', loadOutlets);
outletRefresh.addEventListener('click', () => {
  loadOutlets();
  loadDedupe();
  loadHistory();
});
dedupeSearch.addEventListener('input', loadDedupe);
historySearch.addEventListener('input', loadHistory);

loadOutlets();
loadDedupe();
loadHistory();
