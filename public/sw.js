// Service worker de AgroInventario.
// - Archivos estáticos: se guardan en caché al instalar (carga rápida y sin conexión).
// - Páginas: se piden a la red; si no hay conexión se muestra /offline.html.
// - La API (/api/) nunca se guarda en caché: los datos de inventario deben ser actuales.

const VERSION = "agroinventario-v1";
const ARCHIVOS_ESTATICOS = [
  "/offline.html",
  "/css/estilos.css",
  "/js/app.js",
  "/manifest.webmanifest",
  "/iconos/icono-192.png",
  "/iconos/icono-512.png",
  "/favicon.ico",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(VERSION).then((cache) => cache.addAll(ARCHIVOS_ESTATICOS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((claves) =>
      Promise.all(claves.filter((c) => c !== VERSION).map((c) => caches.delete(c)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const { request } = evento;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) {
    return; // el navegador lo maneja normalmente
  }

  if (request.mode === "navigate") {
    evento.respondWith(fetch(request).catch(() => caches.match("/offline.html")));
    return;
  }

  evento.respondWith(
    caches.match(request).then((enCache) => enCache || fetch(request))
  );
});
