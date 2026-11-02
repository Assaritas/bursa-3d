// Bursa 3D – Service Worker (çevrimdışı önbellek)
// Dosyaları güncellediğinizde VERSION'ı artırın; misafirlerin cihazları yeni sürümü indirir.
const VERSION = 'bursa3d-v1';

const PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/style.css',
  './js/main.js',
  './js/config.js',
  './js/geo.js',
  './js/terrain.js',
  './js/layers.js',
  './js/ui.js',
  './data/data.js',
  './vendor/three.module.min.js',
  './vendor/controls/OrbitControls.js',
  './vendor/lines/LineSegments2.js',
  './vendor/lines/LineSegmentsGeometry.js',
  './vendor/lines/LineMaterial.js',
  './assets/height.png',
  './assets/map_2048.webp',
  // map_4096.webp yalnızca masaüstünde kullanılır; ilk açılışta çalışma anında önbelleğe girer
  './assets/icons/icon-192.png',
  './assets/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    await cache.addAll(PRECACHE);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k)));
    await self.clients.claim();
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach((c) => c.postMessage('cached'));
  })());
});

// Önce önbellek, yoksa ağ (ve sonucu önbelleğe ekle). Harici linkler (Vikipedi vb.) dokunulmaz.
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(VERSION);
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      if (req.mode === 'navigate') return cache.match('./index.html');
      throw err;
    }
  })());
});
