"""Puertos: los "enchufes" que define el negocio.

Un puerto dice QUÉ necesita el negocio, no CÓMO se hace. Los adaptadores
(Supabase, memoria) se enchufan implementando estos métodos.

Protocol: cualquier clase con estos métodos cumple el puerto, sin heredar de él.
Solo contiene los métodos que el sistema usa hoy (YAGNI); crecerá con la Etapa 7.
"""

from typing import Protocol


class RepositorioProductos(Protocol):
    def contar_todos(self) -> int:
        """Cantidad de productos registrados."""
        ...

    def contar_agotados(self) -> int:
        """Cantidad de productos con existencia 0."""
        ...
