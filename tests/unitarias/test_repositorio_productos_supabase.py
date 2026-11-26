"""Pruebas unitarias de los adaptadores de Supabase con un cliente simulado."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from postgrest.exceptions import APIError

from inventario.adaptadores.repositorio_catalogos import RepositorioCatalogosSupabase
from inventario.adaptadores.repositorio_productos_supabase import (
    RepositorioProductosSupabase,
    fila_a_producto,
    producto_a_fila,
)
from inventario.dominio.producto import Producto
from inventario.errores import NombreDuplicadoError, ValidacionError

FILA = {
    "id": 7,
    "nombre": "Concentrado de cerdo",
    "precio": 12.0,  # PostgREST entrega NUMERIC como número JSON
    "cantidad": 2.5,
    "categoria_id": 1,
    "unidad_medida_id": 2,
}


def cliente_con_conteo(conteo):
    cliente = MagicMock()
    # MagicMock devuelve el mismo objeto en cada llamada encadenada (.select().eq()...)
    consulta = cliente.table.return_value.select.return_value
    consulta.limit.return_value.execute.return_value.count = conteo
    consulta.eq.return_value.limit.return_value.execute.return_value.count = conteo
    return cliente


# ---------- Conteos ----------


def test_contar_todos():
    cliente = cliente_con_conteo(58)

    assert RepositorioProductosSupabase(cliente).contar_todos() == 58
    cliente.table.assert_called_with("producto")


def test_contar_agotados_filtra_cantidad_cero():
    cliente = cliente_con_conteo(3)

    assert RepositorioProductosSupabase(cliente).contar_agotados() == 3
    cliente.table.return_value.select.return_value.eq.assert_called_with("cantidad", 0)


def test_conteo_nulo_se_interpreta_como_cero():
    assert RepositorioProductosSupabase(cliente_con_conteo(None)).contar_todos() == 0


# ---------- Traducción fila <-> Producto ----------


def test_fila_a_producto_usa_decimal_exacto():
    producto = fila_a_producto(FILA)

    assert producto.id == 7
    assert producto.precio == Decimal("12.0")
    assert producto.cantidad == Decimal("2.5")


def test_producto_a_fila_envia_decimales_como_texto():
    producto = Producto("Urea 46%", "880.00", "0.125", categoria_id=3, unidad_medida_id=2)

    assert producto_a_fila(producto) == {
        "nombre": "Urea 46%",
        "precio": "880.00",
        "cantidad": "0.125",
        "categoria_id": 3,
        "unidad_medida_id": 2,
    }


# ---------- Listar, buscar y guardar ----------


def test_listar_todos_convierte_cada_fila():
    cliente = MagicMock()
    cliente.table.return_value.select.return_value.order.return_value.execute.return_value.data = [
        FILA
    ]

    productos = RepositorioProductosSupabase(cliente).listar_todos()

    assert [p.nombre for p in productos] == ["Concentrado de cerdo"]


def test_buscar_por_id_inexistente_devuelve_none():
    cliente = MagicMock()
    cliente.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    assert RepositorioProductosSupabase(cliente).buscar_por_id(99) is None


def test_guardar_nuevo_hace_insert():
    cliente = MagicMock()
    cliente.table.return_value.insert.return_value.execute.return_value.data = [FILA]
    nuevo = Producto("Concentrado de cerdo", "12", "2.5", categoria_id=1, unidad_medida_id=2)

    guardado = RepositorioProductosSupabase(cliente).guardar(nuevo)

    assert guardado.id == 7
    cliente.table.return_value.insert.assert_called_once()


def test_guardar_existente_hace_update_por_id():
    cliente = MagicMock()
    actualizar = cliente.table.return_value.update.return_value
    actualizar.eq.return_value.execute.return_value.data = [FILA]
    existente = fila_a_producto(FILA)

    RepositorioProductosSupabase(cliente).guardar(existente)

    actualizar.eq.assert_called_once_with("id", 7)


@pytest.mark.parametrize(
    "codigo, error_esperado",
    [("23505", NombreDuplicadoError), ("23503", ValidacionError)],
)
def test_errores_de_postgres_se_traducen_al_negocio(codigo, error_esperado):
    cliente = MagicMock()
    cliente.table.return_value.insert.return_value.execute.side_effect = APIError(
        {"code": codigo, "message": "violación"}
    )
    nuevo = Producto("Urea", "880", "1", categoria_id=1, unidad_medida_id=1)

    with pytest.raises(error_esperado):
        RepositorioProductosSupabase(cliente).guardar(nuevo)


def test_otros_errores_de_postgres_se_propagan():
    cliente = MagicMock()
    cliente.table.return_value.insert.return_value.execute.side_effect = APIError(
        {"code": "42501", "message": "permiso denegado"}
    )
    nuevo = Producto("Urea", "880", "1", categoria_id=1, unidad_medida_id=1)

    with pytest.raises(APIError):
        RepositorioProductosSupabase(cliente).guardar(nuevo)


# ---------- Catálogos ----------


def test_catalogos_supabase_convierte_filas():
    cliente = MagicMock()
    ordenar = cliente.table.return_value.select.return_value.order.return_value
    ordenar.execute.return_value.data = [{"id": 2, "nombre": "Libra", "abreviatura": "lb"}]

    unidades = RepositorioCatalogosSupabase(cliente).listar_unidades()

    assert unidades[0].etiqueta == "Libra (lb)"
    cliente.table.assert_called_with("unidad_medida")


def test_catalogos_supabase_categorias():
    cliente = MagicMock()
    ordenar = cliente.table.return_value.select.return_value.order.return_value
    ordenar.execute.return_value.data = [{"id": 6, "nombre": "Antiparasitarios"}]

    categorias = RepositorioCatalogosSupabase(cliente).listar_categorias()

    assert categorias[0].etiqueta == "Antiparasitarios"
