const importRegion = document.getElementById('import-region');
const importFiles = document.getElementById('import-files');
const runImportBtn = document.getElementById('run-import');
const refreshBtn = document.getElementById('imports-refresh');
const detectedFilesEl = document.getElementById('detected-files');
const exportSelectionEl = document.getElementById('export-selection');
const clearSelectionBtn = document.getElementById('clear-selection');
const generateSelectedBtn = document.getElementById('generate-selected');
const regionFilter = document.getElementById('region-filter');
const fileFilter = document.getElementById('file-filter');
const statusFilter = document.getElementById('status-filter');
const importGuide = document.getElementById('import-guide');
const regionLibrary = document.getElementById('region-library');
const workspaceSearch = document.getElementById('workspace-search');
const workspaceResults = document.getElementById('workspace-results');
const importsTable = document.getElementById('imports-table');
const errorsTable = document.getElementById('errors-table');
const errorSearch = document.getElementById('import-error-search');
const exportsTable = document.getElementById('exports-table');
const outputsTable = document.getElementById('outputs-table');
const importsSearch = document.getElementById('imports-search');
const exportsSearch = document.getElementById('exports-search');
const outputsSearch = document.getElementById('outputs-search');
const importsStart = document.getElementById('imports-start');
const importsEnd = document.getElementById('imports-end');
const exportsStart = document.getElementById('exports-start');
const exportsEnd = document.getElementById('exports-end');
const outputsRun = document.getElementById('outputs-run');
const outputsStatus = document.getElementById('outputs-status');
const manifestRegion = document.getElementById('manifest-region');
const manifestSummary = document.getElementById('manifest-summary');
const manifestCore = document.getElementById('manifest-core');
const manifestOutputs = document.getElementById('manifest-outputs');
const downloadManifestBtn = document.getElementById('download-manifest');

const state = {
  regions: [],
  catalog: null,
  imports: [],
  errors: [],
  outputLibrary: [],
  exportHistory: [],
  selectedOutputs: new Set(),
  fileList: [],
  manifest: null,
  workspaceFilter: 'all',
};

const CORE_LABELS = {
  table_daily: 'Table + DailySales',
  pg_sales: 'PG Table + PGSales',
};

const normalizeText = (value) => String(value || '').toLowerCase();

const inDateRange = (value, start, end) => {
  if (!value) return false;
  const ts = new Date(value).getTime();
  if (Number.isNaN(ts)) return false;
  if (start && ts < start) return false;
  if (end && ts > end) return false;
  return true;
};

const buildCoreLabelMap = () => {
  const map = {};
  (state.catalog?.core_expected || []).forEach((core) => {
    map[core.kind] = core.label;
  });
  return map;
};

const escapeHtml = (value) => String(value || '')
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

const highlightMatch = (text, query) => {
  if (!query) return escapeHtml(text);
  const safeText = escapeHtml(text);
  const safeQuery = escapeHtml(query);
  const re = new RegExp(`(${safeQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'ig');
  return safeText.replace(re, '<mark class="highlight">$1</mark>');
};

const depsForOutput = (file) => {
  const key = normalize(file.file || '');
  const deps = new Set(['table_daily']);
  if (key.includes('pg')) deps.add('pg_sales');
  return Array.from(deps);
};

const normalize = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

const classifyTemplateName = (filename) => {
  const key = normalize(filename);
  if (key.includes('individual') && key.includes('sale')) return 'individual_sales';
  if (key.includes('van wise')) return 'van_wise_sku';
  if (key.includes('sku summary') || key.includes('sku wise') || key.includes('sku analysis')) return 'sku_summary';
  if (key.includes('township') && key.includes('summary')) return 'township_summary';
  if (key.includes('sales compare') || key.startsWith('compare')) return 'sales_compare';
  if (key.includes('follow up') || key.includes('followup') || key.includes('fus')) return 'follow_up_sales';
  if (key.includes('debtor')) return 'debtors';
  return 'other';
};

const coreInputKind = (filename) => {
  const key = normalize(filename);
  if (key.includes('table') && (key.includes('dailysales') || key.includes('daily sales'))) {
    return { kind: 'table_daily', label: 'Table + DailySales' };
  }
  if (key.includes('pg') && (key.includes('pg sales') || key.includes('pg daily sales') || key.includes('pg dailysales'))) {
    return { kind: 'pg_sales', label: 'PG Table + PGSales' };
  }
  return null;
};

const detectRegion = (filename) => {
  const upper = filename.toUpperCase();
  return state.regions.find((r) => upper.includes(r)) || null;
};

const refreshDetected = () => {
  const files = Array.from(importFiles.files || []);
  state.fileList = files;
  if (!files.length) {
    detectedFilesEl.className = 'empty';
    detectedFilesEl.textContent = 'Select files to see detection and preview options.';
    return;
  }
  detectedFilesEl.className = '';
  detectedFilesEl.innerHTML = '';
  files.forEach((file) => {
    const core = coreInputKind(file.name);
    const region = detectRegion(file.name) || importRegion.value || 'Unknown';
    const category = core ? core.label : classifyTemplateName(file.name);
    const row = document.createElement('div');
    row.className = 'file-row';
    row.innerHTML = `
      <div class="file-name">${file.name}</div>
      <div class="badges">
        <span class="tag">${region}</span>
        <span class="tag ${core ? 'success' : ''}">${core ? 'Core Input' : 'Template'}</span>
      </div>
      <div>${category}</div>
      <div class="file-actions">
        <button class="btn btn-outline" data-preview>Preview</button>
      </div>
    `;
    row.querySelector('[data-preview]').addEventListener('click', () => previewUpload(file));
    detectedFilesEl.appendChild(row);
  });
};

const previewUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const payload = await AppUI.fetchJSON('/api/imports/preview', { method: 'POST', body: formData });
  openPreviewDialog(payload, file.name);
};

const openPreviewDialog = (payload, title) => {
  const files = payload.files || [];
  const context = payload.context || null;
  const wrapper = document.createElement('div');
  const fileTabs = document.createElement('div');
  fileTabs.className = 'dialog-tabs';
  const sheetTabs = document.createElement('div');
  sheetTabs.className = 'dialog-tabs';
  const content = document.createElement('div');
  content.className = 'dialog-content';

  let fileIndex = 0;
  let sheetFilter = 'all';

  const fetchSheetData = async (sheetName, offset, limit, query) => {
    if (!context || context.type === 'upload') return null;
    const params = new URLSearchParams({
      sheet: sheetName,
      offset: String(offset),
      limit: String(limit),
    });
    if (query) params.set('q', query);
    let url = '';
    if (context.type === 'source') {
      params.set('region', context.region);
      params.set('file', context.file);
      url = `/api/imports/source_sheet?${params.toString()}`;
    } else if (context.type === 'output') {
      params.set('region', context.region);
      params.set('file', context.file);
      if (context.run) params.set('run', context.run);
      url = `/api/reports/output_sheet?${params.toString()}`;
    } else if (context.type === 'saved') {
      params.set('import_id', context.import_id);
      params.set('file', context.file);
      url = `/api/imports/saved_sheet?${params.toString()}`;
    }
    if (!url) return null;
    return AppUI.fetchJSON(url);
  };

  const renderFullSheet = async (sheetName) => {
    content.innerHTML = '';
    const controls = document.createElement('div');
    controls.className = 'grid cols-4';
    controls.style.marginBottom = '12px';
    controls.innerHTML = `
      <label class="field">
        Search
        <input class="input" data-sheet-search placeholder="Find text in rows" />
      </label>
      <label class="field">
        Rows per page
        <select class="select" data-sheet-limit>
          <option value="25">25</option>
          <option value="50" selected>50</option>
          <option value="100">100</option>
        </select>
      </label>
      <div class="field">
        <span>Navigation</span>
        <div class="file-actions" style="justify-content:flex-start; gap:6px;">
          <button class="btn btn-outline" data-sheet-prev>Prev</button>
          <button class="btn btn-outline" data-sheet-next>Next</button>
          <span class="tag" data-sheet-meta>Page 1</span>
        </div>
      </div>
      <div class="field">
        <span>Export</span>
        <div class="file-actions" style="justify-content:flex-start; flex-wrap:wrap;">
          <button class="btn btn-secondary" data-sheet-export><span class="icon">⬇️</span>Export View CSV</button>
          <button class="btn btn-outline" data-columns-toggle><span class="icon">☷</span>Columns</button>
        </div>
      </div>
    `;
    const columnPanel = document.createElement('div');
    columnPanel.className = 'column-panel hidden';
    const notePanel = document.createElement('div');
    notePanel.className = 'sheet-note';
    const pinnedWrap = document.createElement('div');
    pinnedWrap.className = 'pinned-wrap hidden';
    const tableWrap = document.createElement('div');
    tableWrap.className = 'table-wrap';
    tableWrap.innerHTML = `<table class="sheet-table"><thead></thead><tbody></tbody></table>`;
    content.appendChild(controls);
    content.appendChild(columnPanel);
    content.appendChild(notePanel);
    content.appendChild(pinnedWrap);
    content.appendChild(tableWrap);

    const searchInput = controls.querySelector('[data-sheet-search]');
    const limitSelect = controls.querySelector('[data-sheet-limit]');
    const prevBtn = controls.querySelector('[data-sheet-prev]');
    const nextBtn = controls.querySelector('[data-sheet-next]');
    const exportBtn = controls.querySelector('[data-sheet-export]');
    const columnsToggle = controls.querySelector('[data-columns-toggle]');
    const meta = controls.querySelector('[data-sheet-meta]');
    const thead = tableWrap.querySelector('thead');
    const tbody = tableWrap.querySelector('tbody');

    let offset = 0;
    let limit = Number(limitSelect.value);
    let query = '';
    let currentHeader = [];
    let currentRows = [];
    let currentTotal = 0;
    let headerKey = '';
    let columnFilters = [];
    let sortCol = null;
    let sortDir = null;
    let colWidths = [];
    let visibleCols = [];
    const pinnedRows = new Map();

    const viewKey = (() => {
      if (context) {
        const parts = [
          context.type || 'view',
          context.region || '',
          context.file || '',
          context.import_id || '',
          context.run || '',
          sheetName || '',
        ];
        return `sheetView:${parts.join(':')}`;
      }
      return `sheetView:${title || 'preview'}:${sheetName}`;
    })();
    const presetsKey = `${viewKey}:presets`;
    const noteKey = `${viewKey}:note`;

    const readView = () => {
      try {
        const raw = localStorage.getItem(viewKey);
        return raw ? JSON.parse(raw) : null;
      } catch (err) {
        return null;
      }
    };

    const saveView = () => {
      const payload = {
        columns: visibleCols,
        widths: colWidths,
        sortCol,
        sortDir,
      };
      localStorage.setItem(viewKey, JSON.stringify(payload));
    };

    const readNote = () => {
      try {
        return localStorage.getItem(noteKey) || '';
      } catch (err) {
        return '';
      }
    };

    const saveNote = (value) => {
      try {
        const text = value || '';
        if (!text.trim()) {
          localStorage.removeItem(noteKey);
        } else {
          localStorage.setItem(noteKey, text);
        }
      } catch (err) {
        // ignore storage errors
      }
    };

    const readPresets = () => {
      try {
        const raw = localStorage.getItem(presetsKey);
        return raw ? JSON.parse(raw) : [];
      } catch (err) {
        return [];
      }
    };

    const savePresets = (presets) => {
      localStorage.setItem(presetsKey, JSON.stringify(presets));
    };

    const normalize = (val) => {
      if (val === null || val === undefined) return '';
      return String(val).toLowerCase();
    };

    const getFilteredRows = () => {
      const active = columnFilters.some((f) => f && f.trim());
      if (!active) return currentRows;
      const filters = columnFilters.map((f) => (f || '').trim().toLowerCase());
      return currentRows.filter((row) => filters.every((filter, idx) => {
        if (!filter) return true;
        return normalize(row[idx]).includes(filter);
      }));
    };

    const compareCells = (left, right) => {
      const leftEmpty = left === null || left === undefined || left === '';
      const rightEmpty = right === null || right === undefined || right === '';
      if (leftEmpty && rightEmpty) return 0;
      if (leftEmpty) return 1;
      if (rightEmpty) return -1;
      const leftStr = String(left).trim();
      const rightStr = String(right).trim();
      const leftNum = Number(leftStr.replace(/,/g, ''));
      const rightNum = Number(rightStr.replace(/,/g, ''));
      const leftIsNum = leftStr !== '' && !Number.isNaN(leftNum);
      const rightIsNum = rightStr !== '' && !Number.isNaN(rightNum);
      if (leftIsNum && rightIsNum) return leftNum - rightNum;
      return leftStr.localeCompare(rightStr, undefined, { numeric: true, sensitivity: 'base' });
    };

    const getSortedRows = (rows) => {
      if (sortCol === null || sortDir === null) return rows;
      const dir = sortDir === 'desc' ? -1 : 1;
      return [...rows].sort((a, b) => dir * compareCells(a[sortCol], b[sortCol]));
    };

    const getVisibleRows = () => getSortedRows(getFilteredRows());

    const updateMeta = (filteredCount) => {
      const page = Math.floor(offset / limit) + 1;
      const maxPage = Math.max(Math.ceil(currentTotal / limit), 1);
      const hasFilters = columnFilters.some((f) => f && f.trim());
      const sortLabel = sortCol !== null && sortDir
        ? ` · sorted by ${currentHeader[sortCol] || `#${sortCol + 1}`} (${sortDir})`
        : '';
      meta.textContent = hasFilters
        ? `Page ${page} / ${maxPage} · ${currentTotal} rows · showing ${filteredCount}${sortLabel}`
        : `Page ${page} / ${maxPage} · ${currentTotal} rows${sortLabel}`;
    };

    const applyWidth = (idx, width) => {
      const headerCell = thead.querySelector(`tr:first-child th:nth-child(${idx + 1})`);
      const filterCell = thead.querySelector(`tr.filter-row th:nth-child(${idx + 1})`);
      if (headerCell) headerCell.style.width = `${width}px`;
      if (filterCell) filterCell.style.width = `${width}px`;
      tbody.querySelectorAll('tr').forEach((row) => {
        const cell = row.children[idx];
        if (cell) cell.style.width = `${width}px`;
      });
    };

    const applyVisibility = () => {
      if (!visibleCols.length) return;
      const headerCells = thead.querySelectorAll('tr:first-child th');
      const filterCells = thead.querySelectorAll('tr.filter-row th');
      headerCells.forEach((cell, idx) => {
        cell.style.display = visibleCols[idx] ? '' : 'none';
      });
      filterCells.forEach((cell, idx) => {
        cell.style.display = visibleCols[idx] ? '' : 'none';
      });
      tbody.querySelectorAll('tr').forEach((row) => {
        Array.from(row.children).forEach((cell, idx) => {
          cell.style.display = visibleCols[idx] ? '' : 'none';
        });
      });
      const pinnedTable = pinnedWrap.querySelector('table');
      if (pinnedTable) {
        pinnedTable.querySelectorAll('thead th').forEach((cell, idx) => {
          cell.style.display = visibleCols[idx] ? '' : 'none';
        });
        pinnedTable.querySelectorAll('tbody tr').forEach((row) => {
          Array.from(row.children).forEach((cell, idx) => {
            cell.style.display = visibleCols[idx] ? '' : 'none';
          });
        });
      }
    };

    const applyAllWidths = () => {
      colWidths.forEach((width, idx) => {
        if (!width) return;
        applyWidth(idx, width);
      });
      const pinnedTable = pinnedWrap.querySelector('table');
      if (pinnedTable) {
        pinnedTable.querySelectorAll('thead th').forEach((cell, idx) => {
          if (!colWidths[idx]) return;
          cell.style.width = `${colWidths[idx]}px`;
        });
        pinnedTable.querySelectorAll('tbody tr').forEach((row) => {
          Array.from(row.children).forEach((cell, idx) => {
            if (!colWidths[idx]) return;
            cell.style.width = `${colWidths[idx]}px`;
          });
        });
      }
    };

    const buildRow = (row, rowKey, pinned) => {
      const tr = document.createElement('tr');
      row.forEach((cell, idx) => {
        const td = document.createElement('td');
        if (idx === 0) {
          const wrap = document.createElement('div');
          wrap.className = 'cell-with-pin';
          const btn = document.createElement('button');
          btn.className = `pin-btn ${pinned ? 'active' : ''}`;
          btn.type = 'button';
          btn.textContent = pinned ? '⦿ Unpin' : '⦿ Pin';
          btn.addEventListener('click', (event) => {
            event.stopPropagation();
            if (pinned) {
              pinnedRows.delete(rowKey);
            } else {
              pinnedRows.set(rowKey, row);
            }
            renderPinned();
            renderRows();
          });
          const text = document.createElement('span');
          text.textContent = cell === null || cell === undefined || cell === '' ? '-' : String(cell);
          wrap.appendChild(btn);
          wrap.appendChild(text);
          td.appendChild(wrap);
        } else {
          td.textContent = cell === null || cell === undefined || cell === '' ? '-' : String(cell);
        }
        tr.appendChild(td);
      });
      return tr;
    };

    const renderRows = () => {
      const filtered = getVisibleRows();
      tbody.innerHTML = '';
      filtered.forEach((row, idx) => {
        const rowKey = String(offset + idx);
        if (pinnedRows.has(rowKey)) return;
        tbody.appendChild(buildRow(row, rowKey, false));
      });
      if (!filtered.length) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="${currentHeader.length || 1}" class="empty">No rows.</td>`;
        tbody.appendChild(tr);
      }
      applyAllWidths();
      applyVisibility();
      updateMeta(filtered.length);
    };

    const renderNotes = () => {
      notePanel.innerHTML = `
        <div class="sheet-note-head">
          <div>
            <div class="card-title" style="font-size:15px;">Sheet Notes</div>
            <div class="card-sub">Private notes saved in this browser.</div>
          </div>
          <div class="file-actions">
            <button class="btn btn-outline" data-note-save><span class="icon">⭳</span>Save</button>
            <button class="btn btn-ghost" data-note-clear><span class="icon">✕</span>Clear</button>
          </div>
        </div>
        <textarea class="input sheet-note-text" data-note-text placeholder="Write notes for this sheet…"></textarea>
      `;
      const noteText = notePanel.querySelector('[data-note-text]');
      noteText.value = readNote();
      noteText.addEventListener('blur', () => {
        saveNote(noteText.value);
      });
      const saveBtn = notePanel.querySelector('[data-note-save]');
      const clearBtn = notePanel.querySelector('[data-note-clear]');
      if (saveBtn) {
        saveBtn.addEventListener('click', () => {
          saveNote(noteText.value);
        });
      }
      if (clearBtn) {
        clearBtn.addEventListener('click', () => {
          noteText.value = '';
          saveNote('');
        });
      }
    };

    const renderPinned = () => {
      if (!pinnedRows.size || !currentHeader.length) {
        pinnedWrap.classList.add('hidden');
        pinnedWrap.innerHTML = '';
        return;
      }
      pinnedWrap.classList.remove('hidden');
      const rows = Array.from(pinnedRows.entries()).sort((a, b) => Number(a[0]) - Number(b[0]));
      pinnedWrap.innerHTML = `
        <div class="pinned-head">
          <span class="pinned-count">${rows.length} pinned row${rows.length > 1 ? 's' : ''}</span>
          <span>Pin rows to keep them visible while paging.</span>
        </div>
        <div class="table-wrap">
          <table class="sheet-table">
            <thead>
              <tr>${currentHeader.map((h) => `<th>${h || '-'}</th>`).join('')}</tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      `;
      const pinnedBody = pinnedWrap.querySelector('tbody');
      rows.forEach(([rowKey, row]) => {
        pinnedBody.appendChild(buildRow(row, rowKey, true));
      });
      applyAllWidths();
      applyVisibility();
    };

    const renderColumnPanel = () => {
      if (!currentHeader.length) {
        columnPanel.innerHTML = '';
        return;
      }
      columnPanel.innerHTML = `
        <div class="column-panel-head">
          <div>
            <div class="card-title" style="font-size:15px;">Columns</div>
            <div class="card-sub">Toggle columns in this view.</div>
          </div>
          <div class="file-actions">
            <button class="btn btn-outline" data-columns-save><span class="icon">⭳</span>Save View</button>
            <button class="btn btn-ghost" data-columns-reset><span class="icon">🔄</span>Reset View</button>
          </div>
        </div>
        <div class="preset-row">
          <select class="select" data-preset-select></select>
          <button class="btn btn-outline" data-preset-apply><span class="icon">✅</span>Apply</button>
          <button class="btn btn-ghost" data-preset-delete><span class="icon">✕</span>Delete</button>
        </div>
        <div class="preset-save">
          <input class="input" data-preset-name placeholder="Preset name" />
          <button class="btn btn-secondary" data-preset-save><span class="icon">⭳</span>Save Preset</button>
        </div>
        <div class="column-panel-actions">
          <button class="btn btn-outline" data-columns-showall><span class="icon">☼</span>Show All</button>
          <button class="btn btn-ghost" data-columns-hideall><span class="icon">☐</span>Hide All</button>
        </div>
        <div class="column-grid">
          ${currentHeader.map((name, idx) => `
            <label class="column-item">
              <input type="checkbox" ${visibleCols[idx] ? 'checked' : ''} data-column-toggle="${idx}" />
              <span>${name || `Column ${idx + 1}`}</span>
            </label>
          `).join('')}
        </div>
      `;
      columnPanel.querySelectorAll('[data-column-toggle]').forEach((input) => {
        input.addEventListener('change', (event) => {
          const idx = Number(event.target.dataset.columnToggle);
          const next = event.target.checked;
          const visibleCount = visibleCols.filter(Boolean).length;
          if (!next && visibleCount <= 1) {
            event.target.checked = true;
            return;
          }
          visibleCols[idx] = next;
          applyVisibility();
        });
      });
      const presetSelect = columnPanel.querySelector('[data-preset-select]');
      const presetApply = columnPanel.querySelector('[data-preset-apply]');
      const presetDelete = columnPanel.querySelector('[data-preset-delete]');
      const presetName = columnPanel.querySelector('[data-preset-name]');
      const presetSave = columnPanel.querySelector('[data-preset-save]');
      const saveBtn = columnPanel.querySelector('[data-columns-save]');
      const resetBtn = columnPanel.querySelector('[data-columns-reset]');
      const showAll = columnPanel.querySelector('[data-columns-showall]');
      const hideAll = columnPanel.querySelector('[data-columns-hideall]');

      const renderPresetOptions = () => {
        const presets = readPresets();
        presetSelect.innerHTML = '';
        const blank = document.createElement('option');
        blank.value = '';
        blank.textContent = 'Choose preset';
        presetSelect.appendChild(blank);
        presets.forEach((preset) => {
          const opt = document.createElement('option');
          opt.value = preset.name;
          opt.textContent = preset.name;
          presetSelect.appendChild(opt);
        });
      };

      const applyPreset = (preset) => {
        if (!preset) return;
        if (Array.isArray(preset.columns) && preset.columns.length === currentHeader.length) {
          visibleCols = preset.columns.map(Boolean);
          if (!visibleCols.some(Boolean)) {
            visibleCols = currentHeader.map((_, idx) => idx === 0);
          }
        }
        if (Array.isArray(preset.widths) && preset.widths.length === currentHeader.length) {
          colWidths = preset.widths.map((val) => (typeof val === 'number' ? val : 0));
        }
        sortCol = Number.isInteger(preset.sortCol) ? preset.sortCol : null;
        sortDir = preset.sortDir === 'asc' || preset.sortDir === 'desc' ? preset.sortDir : null;
        columnFilters = currentHeader.map(() => '');
        buildHeader();
        renderRows();
        renderColumnPanel();
      };

      renderPresetOptions();

      presetApply.addEventListener('click', () => {
        const presets = readPresets();
        const selected = presets.find((p) => p.name === presetSelect.value);
        if (selected) applyPreset(selected);
      });

      presetDelete.addEventListener('click', () => {
        const name = presetSelect.value;
        if (!name) return;
        const presets = readPresets().filter((p) => p.name !== name);
        savePresets(presets);
        renderPresetOptions();
      });

      presetSave.addEventListener('click', () => {
        const name = (presetName.value || '').trim();
        if (!name) return;
        const presets = readPresets();
        const payload = {
          name,
          columns: visibleCols,
          widths: colWidths,
          sortCol,
          sortDir,
        };
        const existingIdx = presets.findIndex((p) => p.name === name);
        if (existingIdx >= 0) {
          presets[existingIdx] = payload;
        } else {
          presets.push(payload);
        }
        savePresets(presets);
        renderPresetOptions();
        presetSelect.value = name;
      });
      if (saveBtn) {
        saveBtn.addEventListener('click', () => {
          saveView();
        });
      }
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          localStorage.removeItem(viewKey);
          visibleCols = currentHeader.map(() => true);
          colWidths = [];
          sortCol = null;
          sortDir = null;
          columnFilters = currentHeader.map(() => '');
          buildHeader();
          renderColumnPanel();
          renderRows();
        });
      }
      if (showAll) {
        showAll.addEventListener('click', () => {
          visibleCols = visibleCols.map(() => true);
          renderColumnPanel();
          applyVisibility();
        });
      }
      if (hideAll) {
        hideAll.addEventListener('click', () => {
          visibleCols = visibleCols.map((_, idx) => idx === 0);
          renderColumnPanel();
          applyVisibility();
        });
      }
    };

    const buildHeader = () => {
      thead.innerHTML = '';
      if (!currentHeader.length) {
        thead.innerHTML = '<tr><th>No columns</th></tr>';
        return;
      }
      const headerRow = document.createElement('tr');
      headerRow.innerHTML = currentHeader.map((h, idx) => {
        const isActive = sortCol === idx;
        const icon = isActive ? (sortDir === 'asc' ? '▲' : '▼') : '↕';
        return `
          <th class="sortable resizable ${isActive ? 'active' : ''}" data-sort-col="${idx}">
            <span>${h || '-'}</span><span class="sort-icon">${icon}</span>
          </th>
        `;
      }).join('');
      const filterRow = document.createElement('tr');
      filterRow.className = 'filter-row';
      filterRow.innerHTML = currentHeader.map((_, idx) => `
        <th><input class="filter-input" data-filter-col="${idx}" placeholder="Filter" value="${columnFilters[idx] || ''}"></th>
      `).join('');
      thead.appendChild(headerRow);
      thead.appendChild(filterRow);
      const headerCells = Array.from(headerRow.querySelectorAll('th'));
      headerCells.forEach((cell, idx) => {
        const resizer = document.createElement('span');
        resizer.className = 'col-resizer';
        resizer.addEventListener('mousedown', (event) => {
          event.preventDefault();
          event.stopPropagation();
          const startX = event.clientX;
          const startWidth = cell.getBoundingClientRect().width;
          document.body.style.cursor = 'col-resize';
          document.body.style.userSelect = 'none';

          const onMove = (moveEvent) => {
            const delta = moveEvent.clientX - startX;
            const nextWidth = Math.max(80, startWidth + delta);
            colWidths[idx] = nextWidth;
            applyWidth(idx, nextWidth);
          };

          const onUp = () => {
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
          };

          document.addEventListener('mousemove', onMove);
          document.addEventListener('mouseup', onUp);
        });
        cell.appendChild(resizer);
      });

      headerRow.querySelectorAll('[data-sort-col]').forEach((cell) => {
        cell.addEventListener('click', () => {
          const col = Number(cell.dataset.sortCol);
          if (sortCol !== col) {
            sortCol = col;
            sortDir = 'asc';
          } else if (sortDir === 'asc') {
            sortDir = 'desc';
          } else if (sortDir === 'desc') {
            sortCol = null;
            sortDir = null;
          } else {
            sortDir = 'asc';
          }
          buildHeader();
          renderRows();
        });
      });
      thead.querySelectorAll('[data-filter-col]').forEach((input) => {
        input.addEventListener('input', (event) => {
          const col = Number(event.target.dataset.filterCol);
          columnFilters[col] = event.target.value;
          renderRows();
        });
      });

      if (colWidths.length !== currentHeader.length) {
        colWidths = new Array(currentHeader.length).fill(0);
        requestAnimationFrame(() => {
          const measured = headerRow.querySelectorAll('th');
          colWidths = Array.from(measured).map((th) => th.getBoundingClientRect().width || 120);
          applyAllWidths();
        });
      } else {
        applyAllWidths();
      }
      applyVisibility();
    };

    const escapeCSV = (value) => {
      if (value === null || value === undefined) return '';
      const str = String(value);
      if (/[",\n]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
      return str;
    };

    const exportCSV = () => {
      if (!currentHeader.length) return;
      const filtered = getVisibleRows();
      const visibleIdx = currentHeader.map((_, idx) => idx).filter((idx) => visibleCols[idx]);
      const headerOut = visibleIdx.map((idx) => currentHeader[idx]);
      const rowsOut = filtered.map((row) => visibleIdx.map((idx) => row[idx]));
      const rows = [headerOut, ...rowsOut];
      const csv = rows.map((row) => row.map(escapeCSV).join(',')).join('\n');
      const fileLabel = (files[fileIndex] && files[fileIndex].file) || title || 'sheet';
      const page = Math.floor(offset / limit) + 1;
      const safe = `${fileLabel}-${sheetName}-page${page}`.replace(/[^\w\-]+/g, '_');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${safe}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
    };

    const load = async () => {
      const data = await fetchSheetData(sheetName, offset, limit, query);
      if (!data) {
        tbody.innerHTML = `<tr><td class="empty">Full view not available.</td></tr>`;
        return;
      }
      currentHeader = data.header || [];
      currentRows = data.rows || [];
      currentTotal = data.total || 0;
      const nextKey = currentHeader.join('|');
      if (nextKey !== headerKey) {
        headerKey = nextKey;
        columnFilters = currentHeader.map((_, idx) => columnFilters[idx] || '');
        sortCol = null;
        sortDir = null;
        colWidths = [];
        visibleCols = currentHeader.map(() => true);
        const saved = readView();
        if (saved && Array.isArray(saved.columns) && saved.columns.length === currentHeader.length) {
          visibleCols = saved.columns.map(Boolean);
          if (!visibleCols.some(Boolean)) {
            visibleCols = currentHeader.map((_, idx) => idx === 0);
          }
        }
        if (saved && Array.isArray(saved.widths) && saved.widths.length === currentHeader.length) {
          colWidths = saved.widths.map((val) => (typeof val === 'number' ? val : 0));
        }
        if (saved && Number.isInteger(saved.sortCol) && saved.sortCol >= 0 && saved.sortCol < currentHeader.length) {
          if (saved.sortDir === 'asc' || saved.sortDir === 'desc') {
            sortCol = saved.sortCol;
            sortDir = saved.sortDir;
          }
        }
        pinnedRows.clear();
        buildHeader();
        renderColumnPanel();
        renderNotes();
        renderPinned();
      }
      renderRows();
    };

    searchInput.addEventListener('input', () => {
      query = searchInput.value.trim();
      offset = 0;
      load();
    });
    limitSelect.addEventListener('change', () => {
      limit = Number(limitSelect.value);
      offset = 0;
      load();
    });
    prevBtn.addEventListener('click', () => {
      offset = Math.max(0, offset - limit);
      load();
    });
    nextBtn.addEventListener('click', () => {
      offset = offset + limit;
      load();
    });
    exportBtn.addEventListener('click', exportCSV);
    columnsToggle.addEventListener('click', () => {
      columnPanel.classList.toggle('hidden');
    });

    load();
  };

  const renderSheets = () => {
    const file = files[fileIndex];
    if (!file) return;
    sheetTabs.innerHTML = '';
    const allBtn = document.createElement('button');
    allBtn.textContent = `All (${file.sheets.length})`;
    allBtn.className = sheetFilter === 'all' ? 'active' : '';
    allBtn.addEventListener('click', () => {
      sheetFilter = 'all';
      renderSheets();
    });
    sheetTabs.appendChild(allBtn);
    file.sheets.forEach((sheet) => {
      const btn = document.createElement('button');
      btn.textContent = sheet.name;
      btn.className = sheetFilter === sheet.name ? 'active' : '';
      btn.addEventListener('click', () => {
        sheetFilter = sheet.name;
        renderSheets();
      });
      sheetTabs.appendChild(btn);
    });

    if (sheetFilter === 'all' || !context || context.type === 'upload') {
      content.innerHTML = '';
      const visible = sheetFilter === 'all' ? file.sheets : file.sheets.filter((s) => s.name === sheetFilter);
      visible.forEach((sheet) => {
        const block = document.createElement('div');
        block.className = 'sheet-block';
        block.innerHTML = `
          <div class="sheet-title">${sheet.name}</div>
          <div class="table-wrap">
            <table class="sheet-table">
              <thead>
                <tr>${(sheet.header || []).map((h) => `<th>${h || '-'}</th>`).join('')}</tr>
              </thead>
              <tbody>
                ${(sheet.sample_rows || []).map((row) => `
                  <tr>${row.map((cell) => `<td>${cell || '-'}</td>`).join('')}</tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
        content.appendChild(block);
      });
    } else {
      renderFullSheet(sheetFilter);
    }
  };

  const render = () => {
    fileTabs.innerHTML = '';
    if (files.length > 1) {
      files.forEach((f, idx) => {
        const btn = document.createElement('button');
        btn.textContent = f.file;
        btn.className = idx === fileIndex ? 'active' : '';
        btn.addEventListener('click', () => {
          fileIndex = idx;
          sheetFilter = 'all';
          render();
        });
        fileTabs.appendChild(btn);
      });
      wrapper.appendChild(fileTabs);
    }
    wrapper.appendChild(sheetTabs);
    wrapper.appendChild(content);
    renderSheets();
  };

  render();
  AppUI.openDialog(() => wrapper);
  document.getElementById('preview-title').textContent = title || 'File Preview';
};

const buildGuide = () => {
  if (!state.catalog) return;
  const core = state.catalog.core_expected || [];
  const outputCategories = new Set();
  state.catalog.regions.forEach((r) => {
    (r.exports || []).forEach((f) => outputCategories.add(f.category));
  });
  const categories = Array.from(outputCategories).sort();
  importGuide.innerHTML = `
    <div class="card-header">
      <div>
        <div class="card-title">Import Guide</div>
        <div class="card-sub">File name patterns and regeneration categories.</div>
      </div>
    </div>
    <div class="grid cols-2">
      <div>
        <div class="card-sub">Core Inputs (required/optional)</div>
        <ul>
          ${core.map((c) => `<li><strong>${c.label}</strong>: ${c.patterns.join(', ')}</li>`).join('')}
        </ul>
      </div>
      <div>
        <div class="card-sub">Output Categories</div>
        <ul>
          ${categories.map((c) => `<li>${c}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;
};

const loadManifest = async () => {
  state.manifest = await AppUI.fetchJSON('/api/imports/dependency_manifest');
  if (!state.manifest) return;
  manifestRegion.innerHTML = '';
  state.manifest.regions.forEach((r) => {
    const opt = document.createElement('option');
    opt.value = r.region;
    opt.textContent = r.region;
    manifestRegion.appendChild(opt);
  });
  if (state.manifest.regions.length) {
    manifestRegion.value = state.manifest.regions[0].region;
    renderManifest();
  }
};

const renderManifest = () => {
  if (!state.manifest) return;
  const regionId = manifestRegion.value;
  const region = state.manifest.regions.find((r) => r.region === regionId);
  if (!region) return;

  manifestSummary.innerHTML = `
    <span class="tag ${region.summary.core_missing ? 'danger' : 'success'}">${region.summary.core_missing} missing core</span>
    <span class="tag">${region.summary.outputs_total} outputs</span>
    <span class="tag ${region.summary.outputs_blocked ? 'warning' : 'success'}">${region.summary.outputs_blocked} blocked</span>
    <span class="tag ${region.summary.outputs_exported_fresh ? 'success' : ''}">${region.summary.outputs_exported_fresh} fresh</span>
    <span class="tag ${region.summary.outputs_exported_stale ? 'warning' : ''}">${region.summary.outputs_exported_stale} stale</span>
  `;

  manifestCore.innerHTML = region.core.map((core) => `
    <div class="file-row">
      <div class="file-name">${core.label}</div>
      <div class="badges">
        <span class="tag ${core.present ? 'success' : core.required ? 'danger' : 'warning'}">${core.present ? 'Present' : 'Missing'}</span>
        <span class="tag">${core.required ? 'Required' : 'Optional'}</span>
      </div>
      <div>${core.files.length ? core.files.join(', ') : core.patterns.join(', ')}</div>
      <div></div>
    </div>
  `).join('');

  manifestOutputs.innerHTML = region.outputs.map((out) => `
    <div class="file-row">
      <div class="file-name">${out.file}</div>
      <div class="badges">
        <span class="tag">${out.category}</span>
        <span class="tag ${out.status === 'blocked_missing_core' ? 'danger' : out.status === 'exported_fresh' ? 'success' : out.status === 'exported_stale' ? 'warning' : ''}">${out.status.replace(/_/g, ' ')}</span>
      </div>
      <div>Needs: ${(out.dependencies || []).map((dep) => CORE_LABELS[dep] || dep).join(' + ')}</div>
      <div></div>
    </div>
  `).join('');
};

const buildImportMap = () => {
  const map = {};
  state.imports.forEach((job) => {
    const region = (job.region || 'ALL').toUpperCase();
    if (!map[region]) map[region] = [];
    map[region].push(job);
  });
  return map;
};

const buildExportMap = () => {
  const map = {};
  state.outputLibrary.forEach((row) => {
    const region = (row.region || '').toUpperCase();
    if (!region) return;
    if (!map[region]) map[region] = [];
    map[region].push(row);
  });
  return map;
};

const buildRegionLibrary = () => {
  if (!state.catalog) return;
  const importMap = buildImportMap();
  const exportMap = buildExportMap();
  const regionQuery = (regionFilter.value || '').toLowerCase();
  const fileQuery = (fileFilter.value || '').toLowerCase();
  const status = statusFilter.value;

  regionLibrary.innerHTML = '';
  const regions = state.catalog.regions || [];

  const requiredKinds = (state.catalog.core_expected || []).filter((c) => c.required).map((c) => c.kind);

  regions.forEach((region) => {
    const regionName = region.region;
    const imports = importMap[regionName] || [];
    const exportRows = exportMap[regionName] || [];
    const corePresent = new Set((region.core || []).map((c) => c.kind));
    const lastImport = imports.reduce((acc, cur) => {
      if (!cur.requested_at) return acc;
      return !acc || cur.requested_at > acc ? cur.requested_at : acc;
    }, null);
    const lastExport = exportRows.reduce((acc, cur) => {
      if (!cur.run_at) return acc;
      return !acc || cur.run_at > acc ? cur.run_at : acc;
    }, null);
    const hasSuccess = imports.some((j) => j.status === 'success');
    const missingRequired = (region.missing_core || []).some((kind) => requiredKinds.includes(kind));
    const exportFresh = lastExport && (!lastImport || lastExport >= lastImport);

    if (regionQuery && !regionName.toLowerCase().includes(regionQuery)) {
      return;
    }
    if (status === 'imported' && !hasSuccess) {
      return;
    }
    if (status === 'missing' && !missingRequired) {
      return;
    }
    if (status === 'exported' && !exportFresh) {
      return;
    }
    if (status === 'stale' && exportFresh) {
      return;
    }
    if (fileQuery) {
      const allFiles = [...(region.core || []).map((c) => c.file), ...(region.exports || []).map((e) => e.file)];
      const match = allFiles.some((f) => (f || '').toLowerCase().includes(fileQuery));
      if (!match) return;
    }

    const dependencySummary = {};
    (region.exports || []).forEach((file) => {
      depsForOutput(file).forEach((dep) => {
        dependencySummary[dep] = (dependencySummary[dep] || 0) + 1;
      });
    });
    const depTags = Object.entries(dependencySummary).map(([dep, count]) => {
      const label = CORE_LABELS[dep] || dep;
      const ok = corePresent.has(dep);
      return `<span class="tag ${ok ? 'success' : 'danger'}">${label} → ${count}</span>`;
    });

    const item = document.createElement('div');
    item.className = 'accordion-item';
    const headerTags = [];
    headerTags.push(`<span class="tag">${regionName}</span>`);
    headerTags.push(`<span class="tag ${hasSuccess ? 'success' : 'warning'}">${hasSuccess ? 'Imported' : 'Not Imported'}</span>`);
    headerTags.push(`<span class="tag ${exportFresh ? 'success' : 'warning'}">${exportFresh ? 'Exported' : 'Needs Export'}</span>`);
    if (missingRequired) headerTags.push(`<span class="tag danger">Missing Core</span>`);

    item.innerHTML = `
      <div class="accordion-header">
        <h4>${regionName}</h4>
        <div class="badges">${headerTags.join('')}</div>
      </div>
      <div class="accordion-body">
        <div class="card-sub" style="margin-bottom: 8px;">Dependency map (core → outputs)</div>
        <div class="badges" style="margin-bottom: 14px;">${depTags.join('')}</div>
        <div class="grid cols-2">
          <div>
            <div class="card-title" style="font-size:15px;">Core Inputs</div>
            ${(state.catalog.core_expected || []).map((core) => {
              const files = (region.core || []).filter((c) => c.kind === core.kind);
              if (!files.length) {
                return `
                  <div class="file-row">
                    <div class="file-name">${core.label}</div>
                    <div class="badges"><span class="tag danger">Missing</span></div>
                    <div>Expected patterns: ${core.patterns.join(', ')}</div>
                    <div class="file-actions"></div>
                  </div>
                `;
              }
              return files.map((file) => `
                <div class="file-row">
                  <div class="file-name">${file.file}</div>
                  <div class="badges">
                    <span class="tag success">Present</span>
                    <span class="tag">${core.label}</span>
                  </div>
                  <div>Core input</div>
                  <div class="file-actions">
                    <button class="btn btn-outline" data-preview-source="${file.file}"><span class="icon">⌕</span>View</button>
                  </div>
                </div>
              `).join('');
            }).join('')}
          </div>
          <div>
            <div class="card-title" style="font-size:15px;">Outputs</div>
            <div class="file-actions" style="justify-content:flex-start; margin: 6px 0 10px;">
              <button class="btn btn-outline" data-select-region="${regionName}"><span class="icon">✅</span>Select All</button>
            </div>
            ${(region.exports || []).map((file) => {
              const deps = depsForOutput(file);
              const missingDeps = deps.filter((dep) => !corePresent.has(dep));
              const exported = exportRows.find((r) => r.file === file.file);
              let statusText = 'Not generated';
              let statusTag = 'warning';
              if (missingDeps.length) {
                statusText = 'Needs core';
                statusTag = 'danger';
              } else if (exported) {
                statusText = exportFresh ? 'Exported' : 'Stale';
                statusTag = exportFresh ? 'success' : 'warning';
              }
              const key = `${regionName}::${file.file}`;
              const checked = state.selectedOutputs.has(key) ? 'checked' : '';
              return `
                <div class="file-row">
                  <div class="file-name">${file.file}</div>
                  <div class="badges">
                    <span class="tag ${file.export_type === 'regen' ? 'success' : ''}">${file.export_type}</span>
                    <span class="tag ${statusTag}">${statusText}</span>
                  </div>
                  <div>
                    ${file.category}
                    <div class="card-sub">Needs: ${deps.map((dep) => CORE_LABELS[dep] || dep).join(' + ')}</div>
                  </div>
                  <div class="file-actions">
                    <label class="checkbox"><input type="checkbox" data-select-file="${key}" ${checked} /></label>
                    <button class="btn btn-outline" data-preview-output="${file.file}"><span class="icon">⌕</span>View</button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>
    `;
    regionLibrary.appendChild(item);
  });

  regionLibrary.querySelectorAll('[data-preview-source]').forEach((btn) => {
    btn.addEventListener('click', async (event) => {
      const fileName = event.currentTarget.dataset.previewSource;
      const regionName = event.currentTarget.closest('.accordion-item').querySelector('h4').textContent;
      const preview = await AppUI.fetchJSON(`/api/imports/source_preview?region=${regionName}&file=${encodeURIComponent(fileName)}`);
      openPreviewDialog(preview, fileName);
    });
  });

  regionLibrary.querySelectorAll('[data-preview-output]').forEach((btn) => {
    btn.addEventListener('click', async (event) => {
      const fileName = event.currentTarget.dataset.previewOutput;
      const regionName = event.currentTarget.closest('.accordion-item').querySelector('h4').textContent;
      try {
        const preview = await AppUI.fetchJSON(`/api/reports/output_preview?region=${regionName}&file=${encodeURIComponent(fileName)}`);
        openPreviewDialog(preview, fileName);
      } catch (err) {
        const fallback = await AppUI.fetchJSON(`/api/imports/source_preview?region=${regionName}&file=${encodeURIComponent(fileName)}`);
        openPreviewDialog(fallback, fileName);
      }
    });
  });

  regionLibrary.querySelectorAll('[data-select-file]').forEach((box) => {
    box.addEventListener('change', (event) => {
      const key = event.target.dataset.selectFile;
      if (event.target.checked) {
        state.selectedOutputs.add(key);
      } else {
        state.selectedOutputs.delete(key);
      }
      updateExportSelection();
    });
  });

  regionLibrary.querySelectorAll('[data-select-region]').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      const regionName = event.currentTarget.dataset.selectRegion;
      const region = state.catalog.regions.find((r) => r.region === regionName);
      if (!region) return;
      (region.exports || []).forEach((file) => {
        state.selectedOutputs.add(`${regionName}::${file.file}`);
      });
      updateExportSelection();
      buildRegionLibrary();
    });
  });

  AppUI.initAccordions();
};

const updateExportSelection = () => {
  const selections = Array.from(state.selectedOutputs);
  if (!selections.length) {
    exportSelectionEl.className = 'empty';
    exportSelectionEl.textContent = 'No outputs selected yet.';
    return;
  }
  exportSelectionEl.className = '';
  exportSelectionEl.innerHTML = selections.map((key) => {
    const [region, file] = key.split('::');
    return `<div class="file-row"><div class="file-name">${file}</div><div>${region}</div><div></div></div>`;
  }).join('');
};

const renderImports = () => {
  const query = normalizeText(importsSearch ? importsSearch.value : '');
  const start = importsStart && importsStart.value ? new Date(importsStart.value).getTime() : null;
  const end = importsEnd && importsEnd.value ? new Date(importsEnd.value + 'T23:59:59').getTime() : null;
  const rows = state.imports.filter((r) => {
    const inRange = !start && !end ? true : inDateRange(r.requested_at, start, end);
    if (!query) return inRange;
    const haystack = [
      r.import_id,
      r.region,
      r.status,
      ...(r.file_names || []),
    ].map(normalizeText).join(' ');
    const matches = haystack.includes(query);
    return matches && inRange;
  });
  const tbody = importsTable.querySelector('tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.import_id}</td>
      <td>${r.region || '-'}</td>
      <td><span class="tag ${r.status === 'success' ? 'success' : r.status === 'failed' ? 'danger' : ''}">${r.status}</span></td>
      <td>${AppUI.formatRelative(r.requested_at)}</td>
      <td>${(r.file_names || []).join(', ')}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="5" class="empty">No imports found.</td>`;
    tbody.appendChild(tr);
  }
};

const loadImports = async () => {
  const data = await AppUI.fetchJSON('/api/imports?limit=200');
  state.imports = data.rows || [];
  renderImports();
};

const loadErrors = async () => {
  const query = errorSearch.value || '';
  const data = await AppUI.fetchJSON(`/api/imports/errors?limit=200&q=${encodeURIComponent(query)}`);
  state.errors = data.rows || [];
  const tbody = errorsTable.querySelector('tbody');
  tbody.innerHTML = '';
  state.errors.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.import_id}</td>
      <td>${r.region || '-'}</td>
      <td>${r.error_message || '-'}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!state.errors.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="3" class="empty">No errors found.</td>`;
    tbody.appendChild(tr);
  }
};

const loadOutputs = async () => {
  const runParam = outputsRun && outputsRun.value ? `?run=${encodeURIComponent(outputsRun.value)}` : '';
  const data = await AppUI.fetchJSON(`/api/reports/output_library${runParam}`);
  state.outputLibrary = data.rows || [];
  if (outputsRun) {
    outputsRun.innerHTML = '';
    const blank = document.createElement('option');
    blank.value = '';
    blank.textContent = 'Latest run';
    outputsRun.appendChild(blank);
    (data.runs || []).forEach((run) => {
      const opt = document.createElement('option');
      opt.value = run.id;
      opt.textContent = `${run.id.replace('export_', '')} · ${AppUI.formatRelative(run.updated_at)}`;
      outputsRun.appendChild(opt);
    });
    if (data.run) {
      outputsRun.value = data.run;
    }
  }
  renderOutputs();
};

const renderOutputs = () => {
  const query = normalizeText(outputsSearch ? outputsSearch.value : '');
  const statusFilter = outputsStatus ? outputsStatus.value : 'all';
  const rows = state.outputLibrary.filter((r) => {
    if (statusFilter !== 'all' && r.status !== statusFilter) return false;
    if (!query) return true;
    const haystack = `${r.region || ''} ${r.file || ''} ${r.status || ''} ${r.category || ''}`.toLowerCase();
    return haystack.includes(query);
  });
  const tbody = outputsTable.querySelector('tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.region}</td>
      <td>${r.file}</td>
      <td>${r.category || '-'}</td>
      <td>${r.status || '-'}</td>
      <td>${r.run_at ? AppUI.formatRelative(r.run_at) : '-'}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="5" class="empty">No outputs found.</td>`;
    tbody.appendChild(tr);
  }
};

const loadExportHistory = async () => {
  const data = await AppUI.fetchJSON('/api/reports/export_history?limit=25');
  state.exportHistory = data.rows || [];
  renderExports();
};

const renderExports = () => {
  const query = normalizeText(exportsSearch ? exportsSearch.value : '');
  const start = exportsStart && exportsStart.value ? new Date(exportsStart.value).getTime() : null;
  const end = exportsEnd && exportsEnd.value ? new Date(exportsEnd.value + 'T23:59:59').getTime() : null;
  const rows = state.exportHistory.filter((r) => {
    const inRange = !start && !end ? true : inDateRange(r.requested_at, start, end);
    if (!query) return inRange;
    const haystack = `${r.export_id || ''} ${r.status || ''} ${r.region || ''}`.toLowerCase();
    return haystack.includes(query) && inRange;
  });
  const tbody = exportsTable.querySelector('tbody');
  tbody.innerHTML = '';
  rows.forEach((r) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.export_id}</td>
      <td>${r.status}</td>
      <td>${r.region || '-'}</td>
      <td>${AppUI.formatRelative(r.requested_at)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows.length) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="4" class="empty">No exports found.</td>`;
    tbody.appendChild(tr);
  }
};

const renderWorkspaceResults = () => {
  if (!workspaceResults) return;
  if (!state.catalog) {
    workspaceResults.classList.add('hidden');
    return;
  }
  const query = normalizeText(workspaceSearch ? workspaceSearch.value : '').trim();
  if (!query) {
    workspaceResults.classList.add('hidden');
    workspaceResults.innerHTML = '';
    return;
  }

  const coreLabelMap = buildCoreLabelMap();
  const outputMap = new Map();
  state.outputLibrary.forEach((row) => {
    outputMap.set(`${row.region}::${row.file}`, row);
  });

  const results = [];
  (state.catalog.regions || []).forEach((region) => {
    const regionName = region.region;
    (region.core || []).forEach((file) => {
      const haystack = `${regionName} ${file.file} ${coreLabelMap[file.kind] || ''}`.toLowerCase();
      if (haystack.includes(query)) {
        results.push({
          type: 'core',
          region: regionName,
          file: file.file,
          label: coreLabelMap[file.kind] || 'Core Input',
        });
      }
    });
    (region.exports || []).forEach((file) => {
      const haystack = `${regionName} ${file.file} ${file.category || ''}`.toLowerCase();
      if (haystack.includes(query)) {
        const key = `${regionName}::${file.file}`;
        results.push({
          type: outputMap.has(key) ? 'output' : 'template',
          region: regionName,
          file: file.file,
          category: file.category,
          exportType: file.export_type,
          output: outputMap.get(key),
        });
      }
    });
  });

  state.outputLibrary.forEach((row) => {
    const key = `${row.region}::${row.file}`;
    if (results.some((r) => `${r.region}::${r.file}` === key)) return;
    const haystack = `${row.region} ${row.file} ${row.category || ''}`.toLowerCase();
    if (haystack.includes(query)) {
      results.push({
        type: 'output',
        region: row.region,
        file: row.file,
        category: row.category,
        output: row,
      });
    }
  });

  workspaceResults.classList.remove('hidden');
  const filter = state.workspaceFilter || 'all';
  const filtered = results.filter((result) => {
    if (filter === 'all') return true;
    if (filter === 'core') return result.type === 'core';
    if (filter === 'template') return result.type === 'template';
    if (filter === 'output') return result.type === 'output';
    return true;
  });

  workspaceResults.innerHTML = `
    <div class="card-header">
      <div>
        <div class="card-title">Search Results</div>
        <div class="card-sub">${filtered.length} matches for “${query}”</div>
      </div>
      <div class="filter-chips">
        <button class="chip ${filter === 'all' ? 'active' : ''}" data-workspace-filter="all">All</button>
        <button class="chip ${filter === 'core' ? 'active' : ''}" data-workspace-filter="core">Core Inputs</button>
        <button class="chip ${filter === 'template' ? 'active' : ''}" data-workspace-filter="template">Output Templates</button>
        <button class="chip ${filter === 'output' ? 'active' : ''}" data-workspace-filter="output">Generated Outputs</button>
      </div>
    </div>
    <div>
      ${filtered.length ? filtered.map((result) => {
        if (result.type === 'core') {
          return `
            <div class="file-row">
              <div class="file-name">${highlightMatch(result.file, query)}</div>
              <div class="badges">
                <span class="tag">${result.region}</span>
                <span class="tag success">Core Input</span>
                <span class="tag">${highlightMatch(result.label, query)}</span>
              </div>
              <div>Source file</div>
              <div class="file-actions">
                <button class="btn btn-outline" data-result-view data-type="core" data-region="${result.region}" data-file="${result.file}"><span class="icon">⌕</span>View</button>
              </div>
            </div>
          `;
        }
        if (result.type === 'template') {
          const key = `${result.region}::${result.file}`;
          const selected = state.selectedOutputs.has(key) ? '✅ Selected' : '✅ Select';
          return `
            <div class="file-row">
              <div class="file-name">${highlightMatch(result.file, query)}</div>
              <div class="badges">
                <span class="tag">${result.region}</span>
                <span class="tag">Output Template</span>
                <span class="tag ${result.exportType === 'regen' ? 'success' : ''}">${result.exportType}</span>
              </div>
              <div>${highlightMatch(result.category || 'Output', query)}</div>
              <div class="file-actions">
                <button class="btn btn-outline" data-result-select data-key="${key}">${selected}</button>
              </div>
            </div>
          `;
        }
        const out = result.output || {};
        return `
          <div class="file-row">
            <div class="file-name">${highlightMatch(result.file, query)}</div>
            <div class="badges">
              <span class="tag">${result.region}</span>
              <span class="tag success">Generated Output</span>
              <span class="tag">${highlightMatch(result.category || '-', query)}</span>
            </div>
            <div>${out.status || 'generated'}</div>
            <div class="file-actions">
              <button class="btn btn-outline" data-result-view data-type="output" data-region="${result.region}" data-file="${result.file}" data-run="${out.run || ''}"><span class="icon">⌕</span>View</button>
            </div>
          </div>
        `;
      }).join('') : '<div class="empty">No matches in this filter.</div>'}
    </div>
  `;

  workspaceResults.querySelectorAll('[data-workspace-filter]').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.workspaceFilter = btn.dataset.workspaceFilter || 'all';
      renderWorkspaceResults();
    });
  });

  workspaceResults.querySelectorAll('[data-result-view]').forEach((btn) => {
    btn.addEventListener('click', async (event) => {
      const type = event.currentTarget.dataset.type;
      const region = event.currentTarget.dataset.region;
      const file = event.currentTarget.dataset.file;
      const run = event.currentTarget.dataset.run;
      if (type === 'core') {
        const preview = await AppUI.fetchJSON(`/api/imports/source_preview?region=${region}&file=${encodeURIComponent(file)}`);
        openPreviewDialog(preview, file);
        return;
      }
      try {
        const params = new URLSearchParams({ region, file });
        if (run) params.set('run', run);
        const preview = await AppUI.fetchJSON(`/api/reports/output_preview?${params.toString()}`);
        openPreviewDialog(preview, file);
      } catch (err) {
        alert('Output preview not available yet.');
      }
    });
  });

  workspaceResults.querySelectorAll('[data-result-select]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.key;
      if (!key) return;
      if (state.selectedOutputs.has(key)) {
        state.selectedOutputs.delete(key);
      } else {
        state.selectedOutputs.add(key);
      }
      updateExportSelection();
      buildRegionLibrary();
      renderWorkspaceResults();
    });
  });
};

const loadCatalog = async () => {
  state.catalog = await AppUI.fetchJSON('/api/imports/catalog');
};

const loadRegions = async () => {
  const data = await AppUI.fetchJSON('/api/regions');
  state.regions = data.regions || [];
  state.regions.forEach((r) => {
    const opt = document.createElement('option');
    opt.value = r;
    opt.textContent = r;
    importRegion.appendChild(opt);
  });
};

const refreshLibrary = async () => {
  await Promise.all([loadCatalog(), loadImports(), loadErrors(), loadOutputs(), loadExportHistory(), loadManifest()]);
  buildGuide();
  buildRegionLibrary();
  renderWorkspaceResults();
  updateExportSelection();
};

runImportBtn.addEventListener('click', async () => {
  if (!state.fileList.length) {
    alert('Select files to import.');
    return;
  }
  const formData = new FormData();
  state.fileList.forEach((file) => formData.append('files', file));
  if (importRegion.value) {
    formData.append('region', importRegion.value);
  }
  await AppUI.fetchJSON('/api/imports', { method: 'POST', body: formData });
  await refreshLibrary();
});

refreshBtn.addEventListener('click', refreshLibrary);
importFiles.addEventListener('change', refreshDetected);
importRegion.addEventListener('change', refreshDetected);
regionFilter.addEventListener('input', buildRegionLibrary);
fileFilter.addEventListener('input', buildRegionLibrary);
statusFilter.addEventListener('change', buildRegionLibrary);
errorSearch.addEventListener('input', loadErrors);
if (importsSearch) importsSearch.addEventListener('input', renderImports);
if (importsStart) importsStart.addEventListener('change', renderImports);
if (importsEnd) importsEnd.addEventListener('change', renderImports);
if (exportsSearch) exportsSearch.addEventListener('input', renderExports);
if (exportsStart) exportsStart.addEventListener('change', renderExports);
if (exportsEnd) exportsEnd.addEventListener('change', renderExports);
if (outputsSearch) outputsSearch.addEventListener('input', renderOutputs);
if (outputsStatus) outputsStatus.addEventListener('change', renderOutputs);
if (outputsRun) outputsRun.addEventListener('change', loadOutputs);
if (workspaceSearch) workspaceSearch.addEventListener('input', renderWorkspaceResults);
manifestRegion.addEventListener('change', renderManifest);
downloadManifestBtn.addEventListener('click', async () => {
  if (!state.manifest) return;
  const payload = JSON.stringify(state.manifest, null, 2);
  const blob = new Blob([payload], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'dependency_manifest.json';
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});

clearSelectionBtn.addEventListener('click', () => {
  state.selectedOutputs.clear();
  updateExportSelection();
  buildRegionLibrary();
});

generateSelectedBtn.addEventListener('click', async () => {
  if (!state.selectedOutputs.size) {
    alert('Select at least one output file.');
    return;
  }
  const grouped = {};
  state.selectedOutputs.forEach((key) => {
    const [region, file] = key.split('::');
    grouped[region] = grouped[region] || [];
    grouped[region].push(file);
  });
  const selections = Object.entries(grouped).map(([region, files]) => ({ region, files }));
  const res = await fetch('/api/reports/export_excel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selections }),
  });
  if (!res.ok) {
    const text = await res.text();
    alert(text || 'Export failed');
    return;
  }
  const blob = await res.blob();
  const disposition = res.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
  const filename = match ? match[1] : 'export.zip';
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  await refreshLibrary();
});

loadRegions().then(refreshLibrary);
