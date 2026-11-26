"""Portal privado: solo se muestra con sesión válida.

Adaptador de entrada: recibe la petición HTTP, llama al caso de uso y muestra el resultado.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase
from inventario.casos_de_uso.resumen_inventario import obtener_resumen_inventario
from inventario.db.cliente import obtener_cliente
from inventario.dominio.puertos import RepositorioProductos
from inventario.web.plantillas import templates
from inventario.web.sesion import correo_requerido

router = APIRouter()


def repositorio_productos(
    _: Annotated[str, Depends(correo_requerido)],
) -> RepositorioProductos:
    """Aquí se elige el adaptador real. Sin sesión, ni siquiera se conecta a la base de datos."""
    return RepositorioProductosSupabase(obtener_cliente())


@router.get("/portal", response_class=HTMLResponse)
def portal(
    request: Request,
    correo: Annotated[str, Depends(correo_requerido)],
    productos: Annotated[RepositorioProductos, Depends(repositorio_productos)],
):
    resumen = obtener_resumen_inventario(productos)
    respuesta = templates.TemplateResponse(
        request,
        "portal.html",
        {
            "correo": correo,
            "total_productos": resumen.total_productos,
            "productos_agotados": resumen.productos_agotados,
        },
    )
    respuesta.headers["Cache-Control"] = "no-store"  # datos privados: no guardar en caché
    return respuesta
