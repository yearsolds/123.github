const CACHE_NAME = 'feniks-v1';
const urlsToCache = [
  '/',
  '/login',
  '/chat',
  '/reprimands',
  '/lateness',
  '/flag_duty',
  '/schedule',
  '/profile',
  '/users',
  '/change_unit'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});