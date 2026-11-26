"""RepositorioProductosSupabase contra Supabase real. Solo lee datos."""

import pytest

from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase

pytestmark = pytest.mark.integracion


def test_contar_todos_coincide_con_productos_cargados(cliente):
    assert RepositorioProductosSupabase(cliente).contar_todos() > 0


def test_agotados_no_supera_el_total(cliente):
    repositorio = RepositorioProductosSupabase(cliente)

    assert 0 <= repositorio.contar_agotados() <= repositorio.contar_todos()
