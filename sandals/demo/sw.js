// Offline cache for the Sandals hand-over demo. Bump VERSION whenever a file changes.
const VERSION = "sandals-demo-16";
const FILES = [
  "./", "index.html", "manifest.webmanifest", "qr.svg", "icon-180.png", "icon-512.png",
  "img/blue-mountains-sunrise-hike.jpg",
  "img/cliff-jump.jpg",
  "img/coffee-veranda-rain.jpg",
  "img/corn-soup-stall.jpg",
  "img/cove-sunrise.jpg",
  "img/craft-market.jpg",
  "img/frenchmans-cove.jpg",
  "img/hammock.jpg",
  "img/jerk-pit.jpg",
  "img/kingston-music-yard.jpg",
  "img/negril-sunset.jpg",
  "img/port-antonio-sunrise.jpg",
  "img/reach-falls.jpg",
  "img/rio-grande-raft.jpg",
  "img/ship-sunset.jpg",
  "img/terrace-restaurant.jpg",
];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((hit) => hit || fetch(e.request))
  );
});
