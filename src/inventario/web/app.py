"""Aplicación web: rutas HTML, healthcheck JSON y manejo de errores 404."""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from inventario import CODIGO_VERIFICACION, __version__
from inventario.web import salud

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals.update(codigo_verificacion=CODIGO_VERIFICACION)

app = FastAPI(title="AgroInventario", version=__version__, docs_url=None, redoc_url=None)


def url_absoluta(request: Request, ruta: str) -> str:
    """URL completa (https://dominio/ruta), necesaria para Open Graph.

    Detrás del proxy de Vercel el esquema real llega en x-forwarded-proto.
    """
    esquema = request.headers.get("x-forwarded-proto", request.url.scheme)
    return f"{esquema}://{request.url.netloc}{ruta}"


templates.env.globals.update(url_absoluta=url_absoluta)


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


CARPETA_PUBLIC = Path(__file__).resolve().parents[3] / "public"

# En Vercel, la carpeta public/ la sirve su CDN (variable VERCEL presente).
# En tu computadora la sirve FastAPI, para poder ver la página completa con estilos.
if not os.getenv("VERCEL") and CARPETA_PUBLIC.is_dir():
    app.mount("/", StaticFiles(directory=CARPETA_PUBLIC), name="public")


@app.exception_handler(StarletteHTTPException)
def pagina_de_error(request: Request, error: StarletteHTTPException):
    if error.status_code == 404:
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "Recurso no encontrado"}, status_code=404)
        return templates.TemplateResponse(request, "404.html", status_code=404)
    return JSONResponse({"error": error.detail}, status_code=error.status_code)
