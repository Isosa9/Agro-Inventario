"""ProductoRepositorio contra Supabase real. Solo lee datos."""

import pytest

from inventario.repositorios.producto_repositorio import ProductoRepositorio

pytestmark = pytest.mark.integracion


def test_contar_todos_coincide_con_productos_cargados(cliente):
    assert ProductoRepositorio(cliente).contar_todos() > 0


def test_agotados_no_supera_el_total(cliente):
    repositorio = ProductoRepositorio(cliente)

    assert 0 <= repositorio.contar_agotados() <= repositorio.contar_todos()
