"""Dependencias de FastAPI compartidas por las páginas privadas.

Aquí se eligen los adaptadores reales (Supabase). Las pruebas los reemplazan
con los adaptadores en memoria mediante app.dependency_overrides.
Todas dependen de correo_requerido: sin sesión, ni siquiera se conectan a la base de datos.
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse

from inventario.adaptadores.repositorio_catalogos import RepositorioCatalogosSupabase
from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase
from inventario.db.cliente import obtener_cliente
from inventario.dominio.puertos import RepositorioCatalogos, RepositorioProductos
from inventario.web.plantillas import templates
from inventario.web.sesion import correo_requerido

CorreoSesion = Annotated[str, Depends(correo_requerido)]


def repositorio_productos(_: CorreoSesion) -> RepositorioProductos:
    return RepositorioProductosSupabase(obtener_cliente())


def repositorio_catalogos(_: CorreoSesion) -> RepositorioCatalogos:
    return RepositorioCatalogosSupabase(obtener_cliente())


Productos = Annotated[RepositorioProductos, Depends(repositorio_productos)]
Catalogos = Annotated[RepositorioCatalogos, Depends(repositorio_catalogos)]


def pagina_privada(
    request: Request, plantilla: str, contexto: dict, status_code: int = 200
) -> HTMLResponse:
    """Respuesta de una página del portal: datos privados, nunca en caché."""
    respuesta = templates.TemplateResponse(request, plantilla, contexto, status_code=status_code)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta
