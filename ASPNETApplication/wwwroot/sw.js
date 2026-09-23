// StockPilot service worker.
'use strict';

var VERSION = 'v1';
var STATIC_CACHE = 'ims-static-' + VERSION;
var PAGES_CACHE = 'ims-pages-' + VERSION;
var DATA_CACHE = 'ims-data-' + VERSION;
var CURRENT_CACHES = [STATIC_CACHE, PAGES_CACHE, DATA_CACHE];

var PRECACHE_URLS = [
  '/offline.html',
  '/manifest.json',
  '/css/site.css',
  '/js/site.js',
  '/js/pwa.js',
  '/js/pwa-pages.js',
  '/lib/bootstrap/dist/css/bootstrap.min.css',
  '/lib/bootstrap/dist/js/bootstrap.bundle.min.js',
  '/lib/jquery/dist/jquery.min.js',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/icon-maskable-512.png',
  '/icons/apple-touch-icon.png'
];

function isCacheable(response) {
  return !!response && response.ok && !response.redirected && response.type === 'basic';
}

self.addEventListener('install', function (event) {
  event.waitUntil((function () {
    return caches.open(STATIC_CACHE).then(function (cache) {
      var tasks = PRECACHE_URLS.map(function (url) {
        return cache.add(url).catch(function (err) {
          console.warn('[sw] precache failed for', url, err);
        });
      });
      return Promise.all(tasks);
    }).then(function () {
      return self.skipWaiting();
    });
  })());
});

self.addEventListener('activate', function (event) {
  event.waitUntil((function () {
    return caches.keys().then(function (names) {
      return Promise.all(
        names
          .filter(function (name) { return CURRENT_CACHES.indexOf(name) === -1; })
          .map(function (name) { return caches.delete(name); })
      );
    }).then(function () {
      return self.clients.claim();
    });
  })());
});

function networkFirstApi(request) {
  return caches.open(DATA_CACHE).then(function (cache) {
    return fetch(request).then(function (res) {
      if (isCacheable(res)) {
        cache.put(request, res.clone());
      }
      return res;
    }).catch(function () {
      return cache.match(request).then(function (cached) {
        if (!cached) {
          throw new Error('No cached response for ' + request.url);
        }
        var headers = new Headers(cached.headers);
        headers.set('X-IMS-Cache', 'hit');
        return cached.blob().then(function (body) {
          return new Response(body, {
            status: cached.status,
            statusText: cached.statusText,
            headers: headers
          });
        });
      });
    });
  });
}

function networkFirstNavigation(request) {
  return caches.open(PAGES_CACHE).then(function (cache) {
    return fetch(request).then(function (res) {
      if (isCacheable(res)) {
        cache.put(request, res.clone());
      }
      return res;
    }).catch(function () {
      return cache.match(request).then(function (cached) {
        if (cached) return cached;
        return caches.match('/offline.html');
      });
    });
  });
}

function staleWhileRevalidate(request) {
  return caches.open(STATIC_CACHE).then(function (cache) {
    return cache.match(request, { ignoreSearch: true }).then(function (cached) {
      var networkPromise = fetch(request).then(function (res) {
        if (isCacheable(res)) {
          cache.put(request, res.clone());
        }
        return res;
      }).catch(function () {
        return undefined;
      });

      return cached || networkPromise;
    });
  });
}

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.indexOf('/api/') === 0) {
    event.respondWith(networkFirstApi(request));
    return;
  }

  if (request.mode === 'navigate') {
    if (url.pathname.indexOf('/Account/') === 0) return;
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  if (
    url.pathname.indexOf('/css/') === 0 ||
    url.pathname.indexOf('/js/') === 0 ||
    url.pathname.indexOf('/lib/') === 0 ||
    url.pathname.indexOf('/icons/') === 0 ||
    url.pathname === '/favicon.ico' ||
    url.pathname === '/manifest.json'
  ) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }
});

self.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'CLEAR_USER_DATA') {
    event.waitUntil(Promise.all([
      caches.delete(PAGES_CACHE),
      caches.delete(DATA_CACHE)
    ]));
  }
});

self.addEventListener('periodicsync', function (event) {
  if (event.tag !== 'ims-low-stock') return;

  event.waitUntil(
    fetch('/api/stock/low').then(function (res) {
      if (!res.ok) return;
      return res.json().then(function (data) {
        var count = (data && data.count) || (data && data.items ? data.items.length : 0);
        if (count > 0) {
          return self.registration.showNotification('Low stock alert', {
            body: count + ' product(s) need reordering.',
            icon: '/icons/icon-192.png',
            tag: 'ims-low-stock',
            renotify: true,
            data: { url: '/Pwa/LowStock' }
          });
        }
      });
    }).catch(function () {
      // Offline or session expired - nothing to notify about.
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var targetUrl = (event.notification.data && event.notification.data.url) || '/Pwa/LowStock';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (allClients) {
      for (var i = 0; i < allClients.length; i++) {
        var client = allClients[i];
        var clientPath = new URL(client.url).pathname;
        if (clientPath === targetUrl && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
