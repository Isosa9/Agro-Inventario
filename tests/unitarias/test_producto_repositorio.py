"""Pruebas unitarias de ProductoRepositorio con un cliente de Supabase simulado."""

from unittest.mock import MagicMock

from inventario.repositorios.producto_repositorio import ProductoRepositorio


def cliente_con_conteo(conteo):
    cliente = MagicMock()
    # MagicMock devuelve el mismo objeto en cada llamada encadenada (.select().eq()...)
    consulta = cliente.table.return_value.select.return_value
    consulta.limit.return_value.execute.return_value.count = conteo
    consulta.eq.return_value.limit.return_value.execute.return_value.count = conteo
    return cliente


def test_contar_todos():
    cliente = cliente_con_conteo(58)

    assert ProductoRepositorio(cliente).contar_todos() == 58
    cliente.table.assert_called_with("producto")


def test_contar_agotados_filtra_cantidad_cero():
    cliente = cliente_con_conteo(3)

    assert ProductoRepositorio(cliente).contar_agotados() == 3
    cliente.table.return_value.select.return_value.eq.assert_called_with("cantidad", 0)


def test_conteo_nulo_se_interpreta_como_cero():
    assert ProductoRepositorio(cliente_con_conteo(None)).contar_todos() == 0
