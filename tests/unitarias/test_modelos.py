"""Pruebas de los modelos Producto, ItemVenta, DetalleVenta y Venta."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from inventario.errores import ValidacionError
from inventario.modelos.producto import Producto
from inventario.modelos.venta import DetalleVenta, ItemVenta, Venta, validar_items_venta


def producto(**cambios):
    datos = {
        "nombre": "Concentrado gallina ponedora",
        "precio": "11.50",
        "cantidad": "500",
        "categoria_id": 1,
        "unidad_medida_id": 1,
    }
    datos.update(cambios)
    return Producto(**datos)


# ---------- Producto ----------


def test_producto_valido_normaliza_sus_datos():
    p = producto(nombre="  Catosal   100 ml ", precio="950", cantidad="2,5")

    assert p.nombre == "Catosal 100 ml"
    assert p.precio == Decimal("950")
    assert p.cantidad == Decimal("2.5")
    assert p.id is None


@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"nombre": ""}, "El nombre es obligatorio"),
        ({"precio": "0"}, "El precio debe ser mayor que 0"),
        ({"cantidad": "-1"}, "mayor o igual a 0"),
        ({"categoria_id": 0}, "identificador de categoría no es válido"),
        ({"unidad_medida_id": None}, "identificador de unidad de medida no es válido"),
        ({"id": -3}, "identificador de producto no es válido"),
    ],
)
def test_producto_no_se_puede_crear_con_datos_invalidos(cambio, mensaje):
    with pytest.raises(ValidacionError, match=mensaje):
        producto(**cambio)


@pytest.mark.parametrize("cantidad, agotado", [("0", True), ("0.000", True), ("0.001", False)])
def test_producto_agotado_cuando_la_cantidad_es_cero(cantidad, agotado):
    assert producto(cantidad=cantidad).esta_agotado is agotado


def test_producto_es_inmutable():
    p = producto()

    with pytest.raises(FrozenInstanceError):
        p.precio = Decimal("1")


def test_cambiar_un_producto_crea_uno_nuevo_y_lo_valida():
    p = producto()

    actualizado = replace(p, precio="12.00")

    assert actualizado.precio == Decimal("12.00")
    assert p.precio == Decimal("11.50")
    with pytest.raises(ValidacionError):
        replace(p, precio="-5")


# ---------- ItemVenta ----------


def test_item_venta_acepta_cantidad_por_peso():
    item = ItemVenta(producto_id=1, cantidad="2,5")

    assert item.cantidad == Decimal("2.5")


def test_item_venta_no_acepta_cantidad_cero():
    with pytest.raises(ValidacionError, match="mayor que 0"):
        ItemVenta(producto_id=1, cantidad="0")


def test_items_de_venta_sin_repetidos():
    items = [ItemVenta(1, "1"), ItemVenta(2, "3")]

    assert validar_items_venta(items) == items
    with pytest.raises(ValidacionError, match="repetidos"):
        validar_items_venta([ItemVenta(1, "1"), ItemVenta(1, "2")])
    with pytest.raises(ValidacionError, match="al menos un producto"):
        validar_items_venta([])


# ---------- DetalleVenta y Venta ----------


def test_subtotal_redondea_a_centavos_como_la_base_de_datos():
    # 0.125 qq x L 950 = 118.75 exactos; 0.333 lb x L 11.50 = 3.8295 -> 3.83
    assert DetalleVenta(1, "0.125", "950").subtotal == Decimal("118.75")
    assert DetalleVenta(2, "0.333", "11.50").subtotal == Decimal("3.83")


def test_total_de_venta_suma_los_subtotales():
    # Mismo caso que la verificación SQL de la Etapa 2: 1 x 950 + 2 x 360 = 1670
    venta = Venta(detalles=[DetalleVenta(1, "1", "950"), DetalleVenta(2, "2", "360")])

    assert venta.total == Decimal("1670.00")
    assert isinstance(venta.detalles, tuple)


def test_venta_registrada_valida_su_id():
    assert Venta(detalles=[DetalleVenta(1, "1", "10")], id=7).id == 7
    with pytest.raises(ValidacionError, match="identificador de venta"):
        Venta(detalles=[DetalleVenta(1, "1", "10")], id=0)


def test_venta_sin_detalles_es_invalida():
    with pytest.raises(ValidacionError, match="al menos un producto"):
        Venta(detalles=[])


def test_venta_no_repite_productos():
    with pytest.raises(ValidacionError, match="repetidos"):
        Venta(detalles=[DetalleVenta(1, "1", "10"), DetalleVenta(1, "2", "10")])
