"""Caso de uso: resumen del inventario que se muestra en el portal."""

from dataclasses import dataclass

from inventario.dominio.puertos import RepositorioProductos


@dataclass(frozen=True)
class ResumenInventario:
    total_productos: int
    productos_agotados: int

    @property
    def hay_agotados(self) -> bool:
        return self.productos_agotados > 0


def obtener_resumen_inventario(repositorio: RepositorioProductos) -> ResumenInventario:
    return ResumenInventario(
        total_productos=repositorio.contar_todos(),
        productos_agotados=repositorio.contar_agotados(),
    )
