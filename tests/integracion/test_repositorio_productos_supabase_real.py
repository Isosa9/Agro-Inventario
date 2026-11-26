"""Adaptadores de Supabase contra la base real. Solo LEEN: no modifican el inventario."""

import pytest

from inventario.adaptadores.repositorio_catalogos import RepositorioCatalogosSupabase
from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase

pytestmark = pytest.mark.integracion


def test_contar_todos_coincide_con_productos_cargados(cliente):
    assert RepositorioProductosSupabase(cliente).contar_todos() > 0


def test_agotados_no_supera_el_total(cliente):
    repositorio = RepositorioProductosSupabase(cliente)

    assert 0 <= repositorio.contar_agotados() <= repositorio.contar_todos()


def test_todos_los_productos_reales_cumplen_las_reglas_del_dominio(cliente):
    # Cada fila se convierte en un Producto: si un dato real violara una regla, fallaría aquí
    repositorio = RepositorioProductosSupabase(cliente)

    productos = repositorio.listar_todos()

    assert len(productos) == repositorio.contar_todos()


def test_buscar_por_id_devuelve_el_mismo_producto(cliente):
    repositorio = RepositorioProductosSupabase(cliente)
    primero = repositorio.listar_todos()[0]

    assert repositorio.buscar_por_id(primero.id) == primero


def test_catalogos_reales(cliente):
    catalogos = RepositorioCatalogosSupabase(cliente)

    assert catalogos.listar_categorias()
    assert any(u.abreviatura == "und" for u in catalogos.listar_unidades())
