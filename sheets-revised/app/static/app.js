const AppUI = (() => {
  const qs = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fetchJSON = async (url, opts = {}) => {
    const res = await fetch(url, opts);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  };

  const formatNumber = (val) => {
    if (val === null || val === undefined || val === '') return '-';
    const n = Number(val);
    if (Number.isNaN(n)) return String(val);
    return n.toLocaleString();
  };

  const formatDate = (val) => {
    if (!val) return '-';
    const d = new Date(val);
    if (Number.isNaN(d.getTime())) return String(val);
    return d.toLocaleDateString();
  };

  const formatRelative = (val) => {
    if (!val) return '-';
    const d = new Date(val);
    if (Number.isNaN(d.getTime())) return String(val);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  const syncScroll = () => {
    qsa('[data-sync-scroll]').forEach((el) => {
      const key = `scroll:${el.dataset.syncScroll}`;
      const saved = Number(localStorage.getItem(key));
      if (!Number.isNaN(saved)) {
        el.scrollLeft = saved;
      }
      el.addEventListener('scroll', () => {
        localStorage.setItem(key, String(el.scrollLeft));
      });
    });
  };

  const initSectionTabs = () => {
    qsa('[data-section-tabs]').forEach((wrap) => {
      const buttons = qsa('button[data-section]', wrap);
      const container = wrap.parentElement || document;
      const panels = qsa('[data-section-panel]', container);
      const setActive = (target) => {
        buttons.forEach((btn) => btn.classList.toggle('active', btn.dataset.section === target));
        panels.forEach((panel) => panel.classList.toggle('hidden', panel.dataset.sectionPanel !== target));
      };
      buttons.forEach((btn) => {
        btn.addEventListener('click', () => setActive(btn.dataset.section));
      });
      const defaultTarget = wrap.dataset.defaultSection || (buttons[0] && buttons[0].dataset.section);
      if (defaultTarget) setActive(defaultTarget);
    });
  };

  const initAccordions = () => {
    qsa('[data-accordion]').forEach((acc) => {
      qsa('.accordion-header', acc).forEach((header) => {
        header.addEventListener('click', () => {
          header.parentElement.classList.toggle('open');
        });
      });
    });
  };

  const openDialog = (contentBuilder) => {
    const dialog = qs('#preview-dialog');
    if (!dialog) return;
    const body = qs('[data-dialog-body]', dialog);
    body.innerHTML = '';
    const fragment = contentBuilder();
    if (fragment) body.appendChild(fragment);
    dialog.classList.add('open');
  };

  const closeDialog = () => {
    const dialog = qs('#preview-dialog');
    if (!dialog) return;
    dialog.classList.remove('open');
  };

  const initDialog = () => {
    const dialog = qs('#preview-dialog');
    if (!dialog) return;
    qsa('[data-dialog-close]', dialog).forEach((btn) => {
      btn.addEventListener('click', closeDialog);
    });
  };

  return {
    qs,
    qsa,
    fetchJSON,
    formatNumber,
    formatDate,
    formatRelative,
    syncScroll,
    initSectionTabs,
    initAccordions,
    initDialog,
    openDialog,
    closeDialog,
  };
})();

window.addEventListener('DOMContentLoaded', () => {
  AppUI.syncScroll();
  AppUI.initSectionTabs();
  AppUI.initAccordions();
  AppUI.initDialog();

  const menuBtn = document.querySelector('[data-menu-toggle]');
  if (menuBtn) {
    menuBtn.addEventListener('click', () => {
      document.body.classList.toggle('sidebar-open');
    });
  }
  document.body.addEventListener('click', (event) => {
    if (!document.body.classList.contains('sidebar-open')) return;
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    if (sidebar.contains(event.target) || (menuBtn && menuBtn.contains(event.target))) return;
    document.body.classList.remove('sidebar-open');
  });
});
