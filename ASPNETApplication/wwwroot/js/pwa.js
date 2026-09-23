// StockPilot PWA shell: service worker registration, offline banner,
// install prompt, submit guard and low-stock notification checks.
// Runs on every page, so every DOM lookup below is null-safe.
(function () {
  'use strict';

  var swRegistration = null;
  var deferredInstallPrompt = null;

  var INSTALL_SELECTOR = '#installBtn, [data-role="install-btn"]';
  var ENABLE_ALERTS_SELECTOR = '#enableAlertsBtn, [data-role="enable-alerts-btn"]';

  function qsa(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function setOfflineBanner(offline, message) {
    var banner = byId('offlineBanner');
    if (!banner) return;
    if (offline) {
      banner.textContent = message || "You're offline. Showing saved data where available.";
      banner.hidden = false;
    } else {
      banner.hidden = true;
    }
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return Promise.resolve(null);

    return navigator.serviceWorker.register('/sw.js')
      .then(function () { return navigator.serviceWorker.ready; })
      .then(function (reg) {
        swRegistration = reg;
        return reg;
      })
      .catch(function (err) {
        console.warn('[pwa] service worker registration failed', err);
        return null;
      });
  }

  function initOfflineBanner() {
    setOfflineBanner(!navigator.onLine);
    window.addEventListener('online', function () { setOfflineBanner(false); });
    window.addEventListener('offline', function () { setOfflineBanner(true); });
  }

  function initInstallPrompt() {
    var buttons = qsa(INSTALL_SELECTOR);
    if (buttons.length === 0) return;

    window.addEventListener('beforeinstallprompt', function (event) {
      event.preventDefault();
      deferredInstallPrompt = event;
      buttons.forEach(function (btn) { btn.hidden = false; });
    });

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (!deferredInstallPrompt) return;
        deferredInstallPrompt.prompt();
        deferredInstallPrompt.userChoice.finally(function () {
          deferredInstallPrompt = null;
          buttons.forEach(function (b) { b.hidden = true; });
        });
      });
    });

    window.addEventListener('appinstalled', function () {
      buttons.forEach(function (btn) { btn.hidden = true; });
      deferredInstallPrompt = null;
    });
  }

  function initSubmitGuard() {
    document.addEventListener('submit', function (event) {
      var form = event.target;
      if (!form || form.tagName !== 'FORM') return;
      var method = (form.getAttribute('method') || 'get').toLowerCase();
      if (method !== 'post') return;
      if (navigator.onLine) return;

      event.preventDefault();
      setOfflineBanner(true, "You're offline. This action needs a connection - try again once you're back online.");
    }, true);
  }

  function lowStockSignature(items) {
    return items
      .map(function (item) { return item.productId + ':' + item.quantityAvailable; })
      .sort()
      .join(',');
  }

  function checkLowStock(force) {
    if (!document.body || document.body.dataset.auth !== '1') return;
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return;
    if (!swRegistration) return;

    fetch('/api/stock/low', { headers: { Accept: 'application/json' } })
      .then(function (res) {
        if (!res.ok) throw new Error('bad response');
        return res.json();
      })
      .then(function (data) {
        var items = (data && data.items) || [];
        if (items.length === 0) return;

        var sig = lowStockSignature(items);
        var lastSig = null;
        try {
          lastSig = localStorage.getItem('ims:lowSig');
        } catch (err) {
          // localStorage unavailable - treat every check as changed.
        }

        if (force || sig !== lastSig) {
          swRegistration.showNotification('Low stock alert', {
            body: items.length + ' product(s) need reordering.',
            icon: '/icons/icon-192.png',
            tag: 'ims-low-stock',
            renotify: true,
            data: { url: '/Pwa/LowStock' }
          });
        }

        try {
          localStorage.setItem('ims:lowSig', sig);
        } catch (err) {
          // ignore
        }
      })
      .catch(function () {
        // Offline or session expired - skip silently.
      });
  }

  function registerPeriodicSync() {
    if (!swRegistration || !('periodicSync' in swRegistration)) return;
    swRegistration.periodicSync
      .register('ims-low-stock', { minInterval: 12 * 60 * 60 * 1000 })
      .catch(function () {
        // Best effort - permission may be denied or unsupported.
      });
  }

  function enableAlerts() {
    if (typeof Notification === 'undefined') return;
    Notification.requestPermission().then(function (permission) {
      if (permission === 'granted') {
        checkLowStock(true);
        registerPeriodicSync();
      }
    });
  }

  function initEnableAlerts() {
    qsa(ENABLE_ALERTS_SELECTOR).forEach(function (btn) {
      btn.addEventListener('click', enableAlerts);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var swReady = registerServiceWorker();

    initOfflineBanner();
    initInstallPrompt();
    initSubmitGuard();
    initEnableAlerts();

    if (document.body && document.body.dataset.auth === '1') {
      swReady.then(function () { checkLowStock(false); });
      setInterval(function () { checkLowStock(false); }, 15 * 60 * 1000);
    }
  });

  window.IMS = window.IMS || {};
  window.IMS.checkLowStock = checkLowStock;
  window.IMS.enableAlerts = enableAlerts;
})();
