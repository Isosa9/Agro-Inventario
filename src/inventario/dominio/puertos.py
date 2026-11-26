"""Puertos: los "enchufes" que define el negocio.

Un puerto dice QUÉ necesita el negocio, no CÓMO se hace. Los adaptadores
(Supabase, memoria) se enchufan implementando estos métodos.

Protocol: cualquier clase con estos métodos cumple el puerto, sin heredar de él.
Solo contiene los métodos que el sistema usa (YAGNI).
"""

from typing import Protocol

from inventario.dominio.catalogo import ElementoCatalogo
from inventario.dominio.producto import Producto


class RepositorioProductos(Protocol):
    def listar_todos(self) -> list[Producto]:
        """Todos los productos registrados."""
        ...

    def buscar_por_id(self, producto_id: int) -> Producto | None:
        """El producto con ese id, o None si no existe."""
        ...

    def guardar(self, producto: Producto) -> Producto:
        """Crea el producto (si no tiene id) o lo actualiza. Devuelve el producto guardado.

        Lanza NombreDuplicadoError si ya existe otro producto con el mismo nombre.
        """
        ...

    def contar_todos(self) -> int:
        """Cantidad de productos registrados."""
        ...

    def contar_agotados(self) -> int:
        """Cantidad de productos con existencia 0."""
        ...


class RepositorioCatalogos(Protocol):
    def listar_categorias(self) -> list[ElementoCatalogo]:
        ...

    def listar_unidades(self) -> list[ElementoCatalogo]:
        ...
