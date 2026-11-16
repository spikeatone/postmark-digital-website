// Offline cache for the hand-over demo. Bump VERSION whenever a file changes.
const VERSION = "ypj-demo-1";
const FILES = [
  "./", "index.html", "manifest.webmanifest", "qr.svg", "icon-180.png", "icon-512.png",
  "fonts/Merriweather.ttf", "fonts/NunitoSans.ttf",
  "img/blue-mountains-trail.jpg",
  "img/kingston-music-yard.jpg",
  "img/terrace-restaurant.jpg",
  "img/blue-mountains-sunrise-hike.jpg",
  "img/cliff-jump.jpg",
  "img/coffee-veranda-rain.jpg",
  "img/corn-soup-stall.jpg",
  "img/craft-market.jpg",
  "img/devon-house.jpg",
  "img/firefly-view.jpg",
  "img/frenchmans-cove.jpg",
  "img/hammock.jpg",
  "img/jerk-pit.jpg",
  "img/negril-sunset.jpg",
  "img/port-antonio-rain.jpg",
  "img/port-antonio-sunrise.jpg",
  "img/reach-falls.jpg",
  "img/rio-grande-raft.jpg",
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
