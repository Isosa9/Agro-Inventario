"""Elementos de catálogo: categorías y unidades de medida de los productos."""

from dataclasses import dataclass

from inventario.dominio.reglas import validar_id, validar_nombre


@dataclass(frozen=True)
class ElementoCatalogo:
    """Una opción de catálogo: la categoría "Antiparasitarios" o la unidad "Libra" (lb)."""

    id: int
    nombre: str
    abreviatura: str = ""  # solo las unidades de medida la usan

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", validar_id(self.id, "catálogo"))
        object.__setattr__(self, "nombre", validar_nombre(self.nombre))
        object.__setattr__(self, "abreviatura", self.abreviatura.strip())

    @property
    def etiqueta(self) -> str:
        """Texto para mostrar en un formulario: "Libra (lb)" o "Antiparasitarios"."""
        return f"{self.nombre} ({self.abreviatura})" if self.abreviatura else self.nombre
