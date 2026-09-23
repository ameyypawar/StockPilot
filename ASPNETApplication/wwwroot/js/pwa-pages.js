// StockPilot PWA page logic: fetch + render for Search, Stock and Low
// Stock pages. Renders with textContent/createElement only, never innerHTML.
(function () {
  'use strict';

  window.IMS = window.IMS || {};

  function fetchJson(url) {
    return fetch(url, { headers: { Accept: 'application/json' } }).then(function (res) {
      var fromCache = res.headers.get('X-IMS-Cache') === 'hit';
      if (!res.ok) {
        throw new Error('Request failed: ' + res.status);
      }
      return res.json().then(function (data) {
        return { data: data, fromCache: fromCache };
      });
    });
  }
  window.IMS.fetchJson = fetchJson;

  function el(tag, opts) {
    var node = document.createElement(tag);
    if (opts) {
      if (opts.className) node.className = opts.className;
      if (opts.text !== undefined) node.textContent = opts.text;
    }
    return node;
  }

  function clear(node) {
    if (!node) return;
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleString();
    } catch (err) {
      return iso;
    }
  }

  function renderDataStatus(container, generatedAt, fromCache) {
    if (!container) return;
    clear(container);
    container.appendChild(el('span', { text: 'Last updated ' + formatDate(generatedAt) }));
    if (fromCache) {
      container.appendChild(el('span', { className: 'badge bg-secondary ms-2', text: 'Offline – saved data' }));
    }
  }

  function renderEmpty(container, message) {
    if (!container) return;
    clear(container);
    container.appendChild(el('p', { className: 'text-muted', text: message || 'Open this page once while online to save data.' }));
  }

  function statusBadgeClass(status) {
    if (status === 'Out') return 'bg-danger';
    if (status === 'Low') return 'bg-warning text-dark';
    return 'bg-success';
  }

  function buildItemRow(opts) {
    var card = el('div', { className: 'card mb-2' + (opts.warn ? ' border-warning' : '') });
    var body = el('div', { className: 'card-body d-flex justify-content-between align-items-center flex-wrap gap-2' });

    var left = el('div');
    left.appendChild(el('div', { className: 'fw-semibold', text: opts.title }));
    left.appendChild(el('div', { className: 'text-muted small', text: opts.subtitle }));

    var right = el('div', { className: 'text-end' });
    right.appendChild(el('span', { className: 'badge rounded-pill text-bg-light me-2', text: opts.qtyText }));
    right.appendChild(el('span', { className: 'badge ' + statusBadgeClass(opts.status), text: opts.status }));

    body.appendChild(left);
    body.appendChild(right);
    card.appendChild(body);
    return card;
  }

  // ---------- Search page ----------
  function initSearchPage() {
    var input = byId('q');
    var status = byId('dataStatus');
    var results = byId('results');
    if (!results) return;

    var allProducts = [];

    function renderResults(list) {
      clear(results);
      if (list.length === 0) {
        renderEmpty(results, 'No matching products.');
        return;
      }
      list.forEach(function (p) {
        results.appendChild(buildItemRow({
          title: p.productName,
          subtitle: (p.categoryName || '—') + ' · ' + (p.supplierName || '—'),
          qtyText: p.quantityAvailable + ' ' + p.unit,
          status: p.status
        }));
      });
    }

    function applyFilter() {
      var term = ((input && input.value) || '').trim().toLowerCase();
      if (!term) {
        renderResults(allProducts);
        return;
      }
      var filtered = allProducts.filter(function (p) {
        return (p.productName && p.productName.toLowerCase().indexOf(term) !== -1) ||
          (p.categoryName && p.categoryName.toLowerCase().indexOf(term) !== -1) ||
          (p.supplierName && p.supplierName.toLowerCase().indexOf(term) !== -1);
      });
      renderResults(filtered);
    }

    if (input) {
      input.addEventListener('input', applyFilter);
    }

    fetchJson('/api/products')
      .then(function (res) {
        allProducts = (res.data && res.data.items) || [];
        renderDataStatus(status, res.data.generatedAt, res.fromCache);
        applyFilter();
      })
      .catch(function () {
        renderEmpty(results);
        clear(status);
      });
  }

  // ---------- Stock page ----------
  function initStockPage() {
    var summary = byId('summary');
    var status = byId('dataStatus');
    var results = byId('results');
    var filterBtns = document.querySelectorAll('[data-status-filter]');
    if (!results) return;

    var allStock = [];
    var currentFilter = 'all';

    function renderSummary(list) {
      if (!summary) return;
      clear(summary);
      var counts = { total: list.length, OK: 0, Low: 0, Out: 0 };
      list.forEach(function (s) {
        if (counts[s.status] !== undefined) counts[s.status] += 1;
      });

      var chips = [
        ['Total', counts.total, 'text-bg-light'],
        ['OK', counts.OK, 'bg-success'],
        ['Low', counts.Low, 'bg-warning text-dark'],
        ['Out', counts.Out, 'bg-danger']
      ];
      chips.forEach(function (entry) {
        summary.appendChild(el('span', { className: 'badge ' + entry[2] + ' me-2 mb-2', text: entry[0] + ': ' + entry[1] }));
      });
    }

    function renderResults(list) {
      clear(results);
      if (list.length === 0) {
        renderEmpty(results, 'No stock records match this filter.');
        return;
      }
      list.forEach(function (s) {
        results.appendChild(buildItemRow({
          title: s.productName,
          subtitle: s.categoryName || '—',
          qtyText: s.quantityAvailable + ' ' + s.unit,
          status: s.status
        }));
      });
    }

    function applyFilter() {
      var list = currentFilter === 'all'
        ? allStock
        : allStock.filter(function (s) { return s.status === currentFilter; });
      renderResults(list);
    }

    filterBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        currentFilter = btn.getAttribute('data-status-filter');
        filterBtns.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        applyFilter();
      });
    });

    fetchJson('/api/stock')
      .then(function (res) {
        allStock = (res.data && res.data.items) || [];
        renderDataStatus(status, res.data.generatedAt, res.fromCache);
        renderSummary(allStock);
        applyFilter();
      })
      .catch(function () {
        renderEmpty(results);
        clear(status);
      });
  }

  // ---------- Low stock page ----------
  function initLowStockPage() {
    var status = byId('dataStatus');
    var results = byId('results');
    var notifyBtn = byId('notifyNowBtn');
    if (!results) return;

    function renderResults(list) {
      clear(results);
      if (list.length === 0) {
        renderEmpty(results, 'Nothing is low on stock right now.');
        return;
      }
      list.forEach(function (s) {
        results.appendChild(buildItemRow({
          title: s.productName,
          subtitle: 'Reorder level ' + s.reorderLevel + ' · suggest ordering ' + s.suggestedOrderQty + ' ' + s.unit,
          qtyText: s.quantityAvailable + ' ' + s.unit,
          status: s.status,
          warn: true
        }));
      });
    }

    function load() {
      fetchJson('/api/stock/low')
        .then(function (res) {
          var list = (res.data && res.data.items) || [];
          renderDataStatus(status, res.data.generatedAt, res.fromCache);
          renderResults(list);
        })
        .catch(function () {
          renderEmpty(results);
          clear(status);
        });
    }

    if (notifyBtn) {
      notifyBtn.addEventListener('click', function () {
        if (window.IMS && typeof window.IMS.checkLowStock === 'function') {
          window.IMS.checkLowStock(true);
        }
      });
    }

    load();
  }

  function byId(id) {
    return document.getElementById(id);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.querySelector('[data-page]');
    if (!root) return;

    switch (root.dataset.page) {
      case 'search':
        initSearchPage();
        break;
      case 'stock':
        initStockPage();
        break;
      case 'low':
        initLowStockPage();
        break;
      default:
        break;
    }
  });
})();
