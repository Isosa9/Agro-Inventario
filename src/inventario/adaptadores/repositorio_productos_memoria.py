"""Adaptador en memoria: implementa RepositorioProductos con una lista de Python.

Sirve para probar casos de uso sin internet ni Supabase, en milisegundos.
Usa las entidades reales del dominio, así que los datos de prueba también
cumplen todas las reglas del negocio.
"""

from collections.abc import Iterable

from inventario.dominio.producto import Producto


class RepositorioProductosEnMemoria:
    def __init__(self, productos: Iterable[Producto] = ()):
        self._productos = list(productos)

    def contar_todos(self) -> int:
        return len(self._productos)

    def contar_agotados(self) -> int:
        return sum(1 for producto in self._productos if producto.esta_agotado)
