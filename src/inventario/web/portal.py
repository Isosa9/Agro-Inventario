"""Portal privado: solo se muestra con sesión válida."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from inventario.db.cliente import obtener_cliente
from inventario.repositorios.producto_repositorio import ProductoRepositorio
from inventario.web.plantillas import templates
from inventario.web.sesion import correo_requerido

router = APIRouter()


def repositorio_productos(
    _: Annotated[str, Depends(correo_requerido)],
) -> ProductoRepositorio:
    """Depende de correo_requerido: sin sesión, ni siquiera se conecta a la base de datos."""
    return ProductoRepositorio(obtener_cliente())


@router.get("/portal", response_class=HTMLResponse)
def portal(
    request: Request,
    correo: Annotated[str, Depends(correo_requerido)],
    productos: Annotated[ProductoRepositorio, Depends(repositorio_productos)],
):
    respuesta = templates.TemplateResponse(
        request,
        "portal.html",
        {
            "correo": correo,
            "total_productos": productos.contar_todos(),
            "productos_agotados": productos.contar_agotados(),
        },
    )
    respuesta.headers["Cache-Control"] = "no-store"  # datos privados: no guardar en caché
    return respuesta
