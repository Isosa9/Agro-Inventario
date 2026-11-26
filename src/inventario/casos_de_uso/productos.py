"""Casos de uso de productos: listar, buscar, registrar y actualizar (RF-01 a RF-04)."""

import unicodedata
from dataclasses import replace

from inventario.dominio.producto import Producto
from inventario.dominio.puertos import RepositorioProductos
from inventario.errores import NombreDuplicadoError, ProductoNoEncontradoError


def normalizar_texto(texto: str) -> str:
    """Para comparar sin importar mayúsculas ni tildes: "Oxitetraciclína" == "oxitetraciclina"."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())


def listar_productos(
    repositorio: RepositorioProductos, busqueda: str = "", solo_agotados: bool = False
) -> list[Producto]:
    """RF-02 y RF-04: productos ordenados por nombre, filtrados por texto o por agotados."""
    termino = normalizar_texto(busqueda)
    productos = [
        producto
        for producto in repositorio.listar_todos()
        if termino in normalizar_texto(producto.nombre)
        and (producto.esta_agotado or not solo_agotados)
    ]
    return sorted(productos, key=lambda producto: normalizar_texto(producto.nombre))


def obtener_producto(repositorio: RepositorioProductos, producto_id: int) -> Producto:
    producto = repositorio.buscar_por_id(producto_id)
    if producto is None:
        raise ProductoNoEncontradoError(f"No existe el producto {producto_id}")
    return producto


def registrar_producto(repositorio: RepositorioProductos, producto: Producto) -> Producto:
    """RF-01: registra un producto nuevo con nombre único."""
    _verificar_nombre_disponible(repositorio, producto.nombre)
    return repositorio.guardar(replace(producto, id=None))


def actualizar_producto(
    repositorio: RepositorioProductos, producto_id: int, cambios: Producto
) -> Producto:
    """RF-03: actualiza nombre, precio, cantidad, categoría o unidad de un producto existente."""
    obtener_producto(repositorio, producto_id)  # falla si no existe
    _verificar_nombre_disponible(repositorio, cambios.nombre, excluir_id=producto_id)
    return repositorio.guardar(replace(cambios, id=producto_id))


def _verificar_nombre_disponible(
    repositorio: RepositorioProductos, nombre: str, excluir_id: int | None = None
) -> None:
    """Regla del negocio: no puede haber dos productos con el mismo nombre.

    Compara sin mayúsculas ni tildes ("urea 46%" choca con "Urea 46%"), algo que la
    restricción UNIQUE de la base de datos no detecta. La UNIQUE sigue como última barrera.
    """
    buscado = normalizar_texto(nombre)
    for existente in repositorio.listar_todos():
        if existente.id != excluir_id and normalizar_texto(existente.nombre) == buscado:
            raise NombreDuplicadoError(f'Ya existe un producto llamado "{existente.nombre}"')
