"""Configuración única de las plantillas HTML (Jinja2), compartida por todas las rutas."""

from decimal import Decimal
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


def formato_lempiras(valor: Decimal) -> str:
    """Decimal("1670") -> "L 1,670.00"."""
    return f"L {valor:,.2f}"


def formato_cantidad(valor: Decimal) -> str:
    """Sin ceros de más: Decimal("2.500") -> "2.5", Decimal("500.000") -> "500"."""
    return f"{valor.normalize():f}"


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals.update(
    codigo_verificacion=CODIGO_VERIFICACION,
    url_absoluta=url_absoluta,
)
templates.env.filters.update(lempiras=formato_lempiras, cantidad=formato_cantidad)
