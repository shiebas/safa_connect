const CACHE_NAME = 'tournament-app-v1';
const urlsToCache = [
  '/tournaments/',
  '/static/tournament_verification/css/team-selection.css',
  '/static/tournament_verification/js/team-selection.js',
  '/static/bootstrap/css/bootstrap.min.css',
  '/static/bootstrap/js/bootstrap.bundle.min.js',
  '/static/fontawesome/css/all.min.css',
  '/static/fontawesome/js/all.min.js'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline form submissions
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Handle offline form submissions when back online
  return new Promise(function(resolve) {
    // Implementation for syncing offline data
    console.log('Background sync triggered');
    resolve();
  });
}

// Push notifications for tournament updates
self.addEventListener('push', function(event) {
  const options = {
    body: event.data ? event.data.text() : 'New tournament update available!',
    icon: '/static/tournament_verification/icons/icon-192x192.png',
    badge: '/static/tournament_verification/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Tournament',
        icon: '/static/tournament_verification/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/tournament_verification/icons/icon-96x96.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Tournament Update', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/tournaments/')
    );
  }
});


