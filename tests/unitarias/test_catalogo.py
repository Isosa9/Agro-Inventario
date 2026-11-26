"""Pruebas del elemento de catálogo del dominio."""

import pytest

from inventario.dominio.catalogo import ElementoCatalogo
from inventario.errores import ValidacionError


def test_unidad_muestra_su_abreviatura():
    assert ElementoCatalogo(1, "Libra", " lb ").etiqueta == "Libra (lb)"


def test_categoria_sin_abreviatura():
    assert ElementoCatalogo(6, "  Antiparasitarios ").etiqueta == "Antiparasitarios"


@pytest.mark.parametrize("identificador, nombre", [(0, "Libra"), (1, "  ")])
def test_catalogo_invalido(identificador, nombre):
    with pytest.raises(ValidacionError):
        ElementoCatalogo(identificador, nombre)
