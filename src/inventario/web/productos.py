"""Páginas de productos del portal: lista, búsqueda, agotados, registrar y editar.

Adaptador de entrada: convierte lo que llega del formulario (siempre texto) en
entidades del dominio, llama a los casos de uso y muestra el resultado.
"""

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from inventario.casos_de_uso import productos as casos
from inventario.dominio.producto import Producto
from inventario.errores import ProductoNoEncontradoError, ValidacionError
from inventario.web.dependencias import Catalogos, CorreoSesion, Productos, pagina_privada

router = APIRouter(prefix="/portal/productos")

Campo = Annotated[str, Form()]


def _a_entero(texto: str, mensaje_si_falta: str) -> int:
    try:
        return int(texto)
    except ValueError:
        raise ValidacionError(mensaje_si_falta) from None


def _valores_formulario(
    nombre: str, precio: str, cantidad: str, categoria_id: str, unidad_medida_id: str
) -> dict:
    return {
        "nombre": nombre,
        "precio": precio,
        "cantidad": cantidad,
        "categoria_id": categoria_id,
        "unidad_medida_id": unidad_medida_id,
    }


def _producto_desde_formulario(
    nombre: str, precio: str, cantidad: str, categoria_id: str, unidad_medida_id: str
) -> Producto:
    """Las reglas las aplica el dominio al crear el Producto; aquí solo se adapta el texto."""
    return Producto(
        nombre=nombre,
        precio=precio,
        cantidad=cantidad,
        categoria_id=_a_entero(categoria_id, "Elige una categoría"),
        unidad_medida_id=_a_entero(unidad_medida_id, "Elige una unidad de medida"),
    )


def _formulario(
    request: Request,
    correo: str,
    catalogos: Catalogos,
    *,
    valores: dict,
    accion: str,
    titulo: str,
    error: str | None = None,
) -> HTMLResponse:
    return pagina_privada(
        request,
        "producto_formulario.html",
        {
            "correo": correo,
            "titulo": titulo,
            "accion": accion,
            "valores": valores,
            "error": error,
            "categorias": catalogos.listar_categorias(),
            "unidades": catalogos.listar_unidades(),
        },
        status_code=422 if error else 200,
    )


@router.get("", response_class=HTMLResponse)
def lista(
    request: Request,
    correo: CorreoSesion,
    productos: Productos,
    catalogos: Catalogos,
    q: str = "",
    agotados: bool = False,
    guardado: str = "",
):
    return pagina_privada(
        request,
        "productos_lista.html",
        {
            "correo": correo,
            "productos": casos.listar_productos(productos, busqueda=q, solo_agotados=agotados),
            "categorias": {c.id: c.nombre for c in catalogos.listar_categorias()},
            "unidades": {u.id: u.abreviatura for u in catalogos.listar_unidades()},
            "q": q,
            "agotados": agotados,
            "guardado": guardado,
        },
    )


@router.get("/nuevo", response_class=HTMLResponse)
def formulario_nuevo(request: Request, correo: CorreoSesion, catalogos: Catalogos):
    return _formulario(
        request,
        correo,
        catalogos,
        valores={},
        accion="/portal/productos/nuevo",
        titulo="Nuevo producto",
    )


@router.post("/nuevo", response_class=HTMLResponse)
def crear(
    request: Request,
    correo: CorreoSesion,
    productos: Productos,
    catalogos: Catalogos,
    nombre: Campo = "",
    precio: Campo = "",
    cantidad: Campo = "",
    categoria_id: Campo = "",
    unidad_medida_id: Campo = "",
):
    valores = _valores_formulario(nombre, precio, cantidad, categoria_id, unidad_medida_id)
    try:
        producto = casos.registrar_producto(productos, _producto_desde_formulario(**valores))
    except ValidacionError as error:
        return _formulario(
            request,
            correo,
            catalogos,
            valores=valores,
            accion="/portal/productos/nuevo",
            titulo="Nuevo producto",
            error=str(error),
        )
    return _volver_a_la_lista(producto)


@router.get("/{producto_id}/editar", response_class=HTMLResponse)
def formulario_editar(
    request: Request,
    producto_id: int,
    correo: CorreoSesion,
    productos: Productos,
    catalogos: Catalogos,
):
    producto = _obtener_o_404(productos, producto_id)
    return _formulario(
        request,
        correo,
        catalogos,
        valores=_valores_formulario(
            producto.nombre,
            f"{producto.precio:.2f}",
            f"{producto.cantidad.normalize():f}",
            str(producto.categoria_id),
            str(producto.unidad_medida_id),
        ),
        accion=f"/portal/productos/{producto_id}/editar",
        titulo=f"Editar {producto.nombre}",
    )


@router.post("/{producto_id}/editar", response_class=HTMLResponse)
def actualizar(
    request: Request,
    producto_id: int,
    correo: CorreoSesion,
    productos: Productos,
    catalogos: Catalogos,
    nombre: Campo = "",
    precio: Campo = "",
    cantidad: Campo = "",
    categoria_id: Campo = "",
    unidad_medida_id: Campo = "",
):
    _obtener_o_404(productos, producto_id)
    valores = _valores_formulario(nombre, precio, cantidad, categoria_id, unidad_medida_id)
    try:
        producto = casos.actualizar_producto(
            productos, producto_id, _producto_desde_formulario(**valores)
        )
    except ValidacionError as error:
        return _formulario(
            request,
            correo,
            catalogos,
            valores=valores,
            accion=f"/portal/productos/{producto_id}/editar",
            titulo="Editar producto",
            error=str(error),
        )
    return _volver_a_la_lista(producto)


def _volver_a_la_lista(producto: Producto) -> RedirectResponse:
    # urlencode: los nombres llevan espacios y símbolos ("Urea 46%")
    return RedirectResponse(
        f"/portal/productos?{urlencode({'guardado': producto.nombre})}", status_code=303
    )


def _obtener_o_404(productos: Productos, producto_id: int) -> Producto:
    try:
        return casos.obtener_producto(productos, producto_id)
    except ProductoNoEncontradoError:
        raise HTTPException(status_code=404) from None
