// Service worker de AgroInventario.
// - Archivos estáticos: se guardan en caché al instalar y se sirven con
//   stale-while-revalidate: respuesta inmediata desde la caché y, en paralelo,
//   se descarga la versión nueva para la próxima visita. Así un cambio de estilos
//   llega a los usuarios sin quedar congelado (con cache-first nunca se actualizaban).
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

  evento.respondWith(desdeCacheYActualizar(evento, request));
});

async function desdeCacheYActualizar(evento, request) {
  const cache = await caches.open(VERSION);
  const enCache = await cache.match(request);
  const desdeRed = fetch(request)
  .then(async (respuesta) => {
      if (respuesta.ok) await cache.put(request, respuesta.clone());
      return respuesta;
    })
    .catch(() => enCache);
  evento.waitUntil(desdeRed); // la actualización termina aunque ya se haya respondido
  return enCache || desdeRed;
}
