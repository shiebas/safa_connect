from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import os


def manifest(request):
    """Serve the PWA manifest.json file"""
    manifest_data = {
        "name": "SAFA Connect Management System",
        "short_name": "SAFA Connect",
        "description": "Official South African Football Association management system for Members",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#006633",
        "theme_color": "#006633",
        "orientation": "portrait-primary",
        "scope": "/",
        "icons": [
            {
                "src": "/static/images/safa_logo_192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/images/safa_logo-512.png",
                "sizes": "512x512", 
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "categories": ["sports", "utilities", "productivity"],
        "screenshots": [
            {
                "src": "/static/images/screenshot-desktop.png",
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide",
                "label": "SAFA Connect Desktop View"
            },
            {
                "src": "/static/images/screenshot-mobile.png",
                "sizes": "360x640",
                "type": "image/png",
                "form_factor": "narrow",
                "label": "SAFA Connect Mobile View"
            }
        ],
        "shortcuts": [
            
            {
                "name": "SAFA Store",
                "short_name": "Store",
                "description": "Browse SAFA merchandise",
                "url": "/store/",
                "icons": [
                    {
                        "src": "/static/images/store-icon.png",
                        "sizes": "96x96"
                    }
                ]
            }
        ]
    }
    
    return JsonResponse(manifest_data)


def service_worker(request):
    """Serve the service worker JavaScript file"""
    # In production, this should be served as a static file
    # For development, we'll serve it dynamically
    
    sw_content = '''
// SAFA Connect Service Worker
const CACHE_NAME = 'safa-global-v1';
const OFFLINE_URL = '/pwa/offline/';

// Files to cache for offline use
const CACHE_FILES = [
    '/',
    '/static/css/bootstrap.min.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/images/safa_logo.png',
    OFFLINE_URL
];

// Install event - cache essential files
self.addEventListener('install', event => {
    console.log('[SW] Install event');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching files');
                return cache.addAll(CACHE_FILES);
            })
            .then(() => {
                console.log('[SW] Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activate event');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Claim clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip external requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version if available
                if (response) {
                    console.log('[SW] Serving from cache:', event.request.url);
                    return response;
                }
                
                // Otherwise fetch from network
                console.log('[SW] Fetching from network:', event.request.url);
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone the response (can only be consumed once)
                        const responseClone = response.clone();
                        
                        // Add to cache for future requests
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseClone);
                            });
                        
                        return response;
                    })
                    .catch(() => {
                        // If network fails, show offline page
                        console.log('[SW] Network failed, showing offline page');
                        return caches.match(OFFLINE_URL);
                    });
            })
    );
});

// Background sync for form submissions
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'sync-forms') {
        event.waitUntil(syncPendingForms());
    }
});

// Sync pending forms when connection is restored
async function syncPendingForms() {
    try {
        // Get pending forms from IndexedDB
        const pendingForms = await getPendingForms();
        
        for (const form of pendingForms) {
            try {
                const response = await fetch('/api/sync/forms/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': form.csrfToken
                    },
                    body: JSON.stringify(form.data)
                });
                
                if (response.ok) {
                    // Remove from pending queue
                    await removePendingForm(form.id);
                    console.log('[SW] Form synced successfully:', form.id);
                } else {
                    console.error('[SW] Form sync failed:', form.id, response.status);
                }
            } catch (error) {
                console.error('[SW] Form sync error:', form.id, error);
            }
        }
    } catch (error) {
        console.error('[SW] Background sync error:', error);
    }
}

// Helper functions for IndexedDB operations
async function getPendingForms() {
    // Implementation for getting pending forms from IndexedDB
    return [];
}

async function removePendingForm(formId) {
    // Implementation for removing synced form from IndexedDB
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('[SW] Push received');
    
    const options = {
        body: event.data ? event.data.text() : 'New update available',
        icon: '/static/images/safa-logo-192.png',
        badge: '/static/images/safa-badge.png',
        tag: 'safa-notification',
        renotify: true,
        actions: [
            {
                action: 'open',
                title: 'Open SAFA Connect'
            },
            {
                action: 'close',
                title: 'Close'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('SAFA Connect', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});
'''
    
    return HttpResponse(sw_content, content_type='application/javascript')


def offline(request):
    """Offline fallback page"""
    return render(request, 'pwa/offline.html')


@csrf_exempt
@require_http_methods(["POST"])
def track_install(request):
    """Track PWA installation events"""
    try:
        data = json.loads(request.body)
        
        from .models import PWAInstallation
        
        PWAInstallation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            platform=data.get('platform', 'Unknown'),
            browser=data.get('browser', 'Unknown'),
            device_type=data.get('device_type', 'DESKTOP'),
            install_source=data.get('install_source', 'MANUAL')
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def sync_status(request):
    """Get sync status for current user"""
    from .models import SyncRecord
    
    pending_syncs = SyncRecord.objects.filter(
        user=request.user,
        status__in=['PENDING', 'IN_PROGRESS', 'FAILED']
    ).count()
    
    last_sync = SyncRecord.objects.filter(
        user=request.user,
        status='SUCCESS'
    ).order_by('-synced_at').first()
    
    return JsonResponse({
        'pending_syncs': pending_syncs,
        'last_sync': last_sync.synced_at.isoformat() if last_sync else None,
        'is_online': True  # This would be determined by client-side navigator.onLine
    })


def pwa_info(request):
    """Provide PWA information and installation instructions"""
    context = {
        'is_installed': request.GET.get('standalone') == 'true',
        'is_mobile': 'Mobile' in request.META.get('HTTP_USER_AGENT', ''),
    }
    return render(request, 'pwa/info.html', context)
