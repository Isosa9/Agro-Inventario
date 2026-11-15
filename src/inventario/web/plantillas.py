"""Configuración única de las plantillas HTML (Jinja2), compartida por todas las rutas."""

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from inventario import CODIGO_VERIFICACION


def url_absoluta(request: Request, ruta: str) -> str:
    """URL completa (https://dominio/ruta), necesaria para Open Graph.

    Detrás del proxy de Vercel el esquema real llega en x-forwarded-proto.
    """
    esquema = request.headers.get("x-forwarded-proto", request.url.scheme)
    return f"{esquema}://{request.url.netloc}{ruta}"


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals.update(
    codigo_verificacion=CODIGO_VERIFICACION,
    url_absoluta=url_absoluta,
)
