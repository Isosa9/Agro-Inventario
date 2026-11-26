"""Adaptador en memoria: implementa RepositorioProductos con un diccionario de Python.

Sirve para probar casos de uso sin internet ni Supabase, en milisegundos.
Usa las entidades reales del dominio, así que los datos de prueba también
cumplen todas las reglas del negocio. Imita a la base de datos en lo esencial:
asigna ids y rechaza nombres exactamente iguales (como la restricción UNIQUE).
"""

from collections.abc import Iterable
from dataclasses import replace
from itertools import count

from inventario.dominio.producto import Producto
from inventario.errores import NombreDuplicadoError


class RepositorioProductosEnMemoria:
    def __init__(self, productos: Iterable[Producto] = ()):
        self._productos: dict[int, Producto] = {}
        self._siguiente_id = count(1)
        for producto in productos:
            self.guardar(producto)

    def listar_todos(self) -> list[Producto]:
        return list(self._productos.values())

    def buscar_por_id(self, producto_id: int) -> Producto | None:
        return self._productos.get(producto_id)

    def guardar(self, producto: Producto) -> Producto:
        if any(
            p.nombre == producto.nombre and p.id != producto.id for p in self._productos.values()
        ):
            raise NombreDuplicadoError(f'Ya existe un producto llamado "{producto.nombre}"')
        if producto.id is None:
            producto = replace(producto, id=self._nuevo_id())
        self._productos[producto.id] = producto
        return producto

    def contar_todos(self) -> int:
        return len(self._productos)

    def contar_agotados(self) -> int:
        return sum(1 for producto in self._productos.values() if producto.esta_agotado)

    def _nuevo_id(self) -> int:
        nuevo = next(self._siguiente_id)
        while nuevo in self._productos:
            nuevo = next(self._siguiente_id)
        return nuevo
