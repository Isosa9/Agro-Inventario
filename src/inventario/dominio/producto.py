"""Modelo Producto: lo que vende la agrocomercial y su existencia actual."""

from dataclasses import dataclass
from decimal import Decimal

from inventario.dominio.reglas import (
    validar_existencia,
    validar_id,
    validar_nombre,
    validar_precio,
)


@dataclass(frozen=True)
class Producto:
    """Un producto válido por construcción: no se puede crear con datos inválidos.

    frozen=True: una vez creado no se modifica; un cambio produce un Producto nuevo.
    """

    nombre: str
    precio: Decimal
    cantidad: Decimal
    categoria_id: int
    unidad_medida_id: int
    id: int | None = None

    def __post_init__(self) -> None:
        # object.__setattr__ porque la clase es inmutable (frozen)
        object.__setattr__(self, "nombre", validar_nombre(self.nombre))
        object.__setattr__(self, "precio", validar_precio(self.precio))
        object.__setattr__(self, "cantidad", validar_existencia(self.cantidad))
        object.__setattr__(self, "categoria_id", validar_id(self.categoria_id, "categoría"))
        object.__setattr__(
            self, "unidad_medida_id", validar_id(self.unidad_medida_id, "unidad de medida")
        )
        if self.id is not None:
            object.__setattr__(self, "id", validar_id(self.id, "producto"))

    @property
    def esta_agotado(self) -> bool:
        """RF-04: un producto está agotado cuando su existencia es 0."""
        return self.cantidad == 0
