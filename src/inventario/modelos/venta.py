"""Modelos de venta: lo que se pide vender (ItemVenta) y lo que quedó registrado."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from inventario.validadores.reglas import (
    validar_cantidad_venta,
    validar_id,
    validar_precio,
    validar_sin_productos_repetidos,
)

CENTAVO = Decimal("0.01")


@dataclass(frozen=True)
class ItemVenta:
    """Un producto y la cantidad que se quiere vender (entrada del formulario de venta)."""

    producto_id: int
    cantidad: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "producto_id", validar_id(self.producto_id, "producto"))
        object.__setattr__(self, "cantidad", validar_cantidad_venta(self.cantidad))


@dataclass(frozen=True)
class DetalleVenta:
    """Un producto dentro de una venta ya registrada, con el precio del momento."""

    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "producto_id", validar_id(self.producto_id, "producto"))
        object.__setattr__(self, "cantidad", validar_cantidad_venta(self.cantidad))
        object.__setattr__(self, "precio_unitario", validar_precio(self.precio_unitario))

    @property
    def subtotal(self) -> Decimal:
        """Mismo cálculo que la columna generada en PostgreSQL: round(cantidad * precio, 2)."""
        return (self.cantidad * self.precio_unitario).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Venta:
    """Una venta registrada: fecha, detalles y total."""

    detalles: tuple[DetalleVenta, ...]
    id: int | None = None
    fecha: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "detalles", tuple(self.detalles))
        validar_sin_productos_repetidos([d.producto_id for d in self.detalles])
        if self.id is not None:
            object.__setattr__(self, "id", validar_id(self.id, "venta"))

    @property
    def total(self) -> Decimal:
        """Suma de subtotales; no se guarda aparte para no tener dos fuentes de verdad."""
        return sum((d.subtotal for d in self.detalles), Decimal("0.00"))


def validar_items_venta(items: list[ItemVenta]) -> list[ItemVenta]:
    """Una venta pedida: al menos un producto y ninguno repetido."""
    validar_sin_productos_repetidos([item.producto_id for item in items])
    return items
