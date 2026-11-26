"""Pruebas de las reglas de validación del negocio."""

from decimal import Decimal

import pytest

from inventario.dominio import reglas
from inventario.errores import ValidacionError

# ---------- Conversión a Decimal ----------


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("2.5", Decimal("2.5")),
        ("2,5", Decimal("2.5")),  # coma decimal, como se escribe en Honduras
        ("  11.50 ", Decimal("11.50")),
        (3, Decimal("3")),
        (0.1, Decimal("0.1")),  # el float no arrastra su error binario
        (Decimal("0.125"), Decimal("0.125")),
    ],
)
def test_a_decimal_convierte_formatos_validos(entrada, esperado):
    assert reglas.a_decimal(entrada, "La cantidad") == esperado


@pytest.mark.parametrize("entrada", ["", "abc", "1.2.3", None, True, "NaN", "Infinity", [1]])
def test_a_decimal_rechaza_lo_que_no_es_numero(entrada):
    with pytest.raises(ValidacionError, match="La cantidad debe ser un número"):
        reglas.a_decimal(entrada, "La cantidad")


def test_decimal_evita_el_error_de_redondeo_del_float():
    suma = reglas.a_decimal("0.1", "x") + reglas.a_decimal("0.2", "x")

    assert suma == Decimal("0.3")  # con float daría 0.30000000000000004


# ---------- Nombre ----------


def test_nombre_se_limpia_de_espacios_sobrantes():
    assert reglas.validar_nombre("  Catosal    100  ml ") == "Catosal 100 ml"


@pytest.mark.parametrize("nombre", ["", "    ", None, 123])
def test_nombre_es_obligatorio(nombre):
    with pytest.raises(ValidacionError, match="El nombre es obligatorio"):
        reglas.validar_nombre(nombre)


def test_nombre_tiene_largo_maximo():
    reglas.validar_nombre("x" * reglas.LARGO_MAXIMO_NOMBRE)  # en el límite: válido

    with pytest.raises(ValidacionError, match="máximo 120 caracteres"):
        reglas.validar_nombre("x" * (reglas.LARGO_MAXIMO_NOMBRE + 1))


# ---------- Precio ----------


@pytest.mark.parametrize("precio", ["0.01", "950", "11.50", "9999999999.99"])
def test_precio_valido(precio):
    assert reglas.validar_precio(precio) == Decimal(precio)


@pytest.mark.parametrize("precio", ["0", "0.00", "-1", "-0.01"])
def test_precio_debe_ser_mayor_que_cero(precio):
    with pytest.raises(ValidacionError, match="El precio debe ser mayor que 0"):
        reglas.validar_precio(precio)


def test_precio_admite_maximo_dos_decimales():
    with pytest.raises(ValidacionError, match="máximo 2 decimales"):
        reglas.validar_precio("11.505")


def test_precio_no_supera_el_limite_de_la_base_de_datos():
    with pytest.raises(ValidacionError, match="no puede ser mayor"):
        reglas.validar_precio("10000000000")


# ---------- Existencia (inventario) ----------


@pytest.mark.parametrize("cantidad", ["0", "0.001", "2.5", "500", "999999999.999"])
def test_existencia_valida_incluye_cero(cantidad):
    assert reglas.validar_existencia(cantidad) == Decimal(cantidad)


def test_existencia_nunca_es_negativa():
    with pytest.raises(ValidacionError, match="La cantidad debe ser mayor o igual a 0"):
        reglas.validar_existencia("-0.001")


def test_existencia_admite_maximo_tres_decimales():
    reglas.validar_existencia("0.125")  # 1/8 de quintal: válido

    with pytest.raises(ValidacionError, match="máximo 3 decimales"):
        reglas.validar_existencia("0.1255")


# ---------- Cantidad vendida ----------


def test_cantidad_vendida_admite_decimales_por_peso():
    assert reglas.validar_cantidad_venta("2,5") == Decimal("2.5")


@pytest.mark.parametrize("cantidad", ["0", "-1"])
def test_cantidad_vendida_debe_ser_mayor_que_cero(cantidad):
    with pytest.raises(ValidacionError, match="La cantidad vendida debe ser mayor que 0"):
        reglas.validar_cantidad_venta(cantidad)


# ---------- Identificadores y productos repetidos ----------


@pytest.mark.parametrize("valor", [0, -5, True, "3", 2.0, None])
def test_id_debe_ser_entero_positivo(valor):
    with pytest.raises(ValidacionError, match="El identificador de producto no es válido"):
        reglas.validar_id(valor, "producto")


def test_venta_sin_productos_es_invalida():
    with pytest.raises(ValidacionError, match="al menos un producto"):
        reglas.validar_sin_productos_repetidos([])


def test_venta_con_producto_repetido_es_invalida():
    with pytest.raises(ValidacionError, match="productos repetidos"):
        reglas.validar_sin_productos_repetidos([1, 2, 1])


def test_venta_con_productos_distintos_es_valida():
    reglas.validar_sin_productos_repetidos([1, 2, 3])
