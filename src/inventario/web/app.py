"""Aplicación web: arma las rutas, el healthcheck y el manejo de errores."""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from inventario import __version__
from inventario.web import portal, salud, sesion
from inventario.web.plantillas import templates

app = FastAPI(title="AgroInventario", version=__version__, docs_url=None, redoc_url=None)
app.include_router(sesion.router)
app.include_router(portal.router)


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse(request, "inicio.html")


@app.get("/api/health")
def healthcheck():
    disponible = salud.base_de_datos_disponible()
    return JSONResponse(
        status_code=200 if disponible else 503,
        content={
            "estado": "ok" if disponible else "degradado",
            "base_de_datos": "ok" if disponible else "sin conexión",
            "version": __version__,
            "hora_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )


@app.exception_handler(sesion.SesionRequerida)
def redirigir_a_login(request: Request, error: sesion.SesionRequerida):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(StarletteHTTPException)
def pagina_de_error(request: Request, error: StarletteHTTPException):
    if error.status_code == 404:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "Recurso no encontrado"}, status_code=404)
        return templates.TemplateResponse(request, "404.html", status_code=404)
    return JSONResponse({"error": error.detail}, status_code=error.status_code)


CARPETA_PUBLIC = Path(__file__).resolve().parents[3] / "public"

# En Vercel, la carpeta public/ la sirve su CDN (variable VERCEL presente).
# En tu computadora la sirve FastAPI, para poder ver la página completa con estilos.
# Debe ir al final: las rutas definidas arriba tienen prioridad.
if not os.getenv("VERCEL") and CARPETA_PUBLIC.is_dir():
    app.mount("/", StaticFiles(directory=CARPETA_PUBLIC), name="public")
