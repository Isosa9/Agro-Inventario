"""Portal privado: resumen del inventario. Solo se muestra con sesión válida.

Adaptador de entrada: recibe la petición HTTP, llama al caso de uso y muestra el resultado.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from inventario.casos_de_uso.resumen_inventario import obtener_resumen_inventario
from inventario.web.dependencias import CorreoSesion, Productos, pagina_privada

router = APIRouter()


@router.get("/portal", response_class=HTMLResponse)
def portal(request: Request, correo: CorreoSesion, productos: Productos):
    resumen = obtener_resumen_inventario(productos)
    return pagina_privada(
        request,
        "portal.html",
        {
            "correo": correo,
            "total_productos": resumen.total_productos,
            "productos_agotados": resumen.productos_agotados,
        },
    )
