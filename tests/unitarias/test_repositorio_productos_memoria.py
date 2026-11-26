"""Pruebas del adaptador en memoria y de que ambos adaptadores cumplen el puerto."""

import pytest

from inventario.adaptadores.repositorio_productos_memoria import RepositorioProductosEnMemoria
from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase
from inventario.dominio.producto import Producto
from inventario.dominio.puertos import RepositorioProductos


def producto(nombre, cantidad):
    return Producto(nombre, "100", cantidad, categoria_id=1, unidad_medida_id=1)


def test_repositorio_vacio():
    repositorio = RepositorioProductosEnMemoria()

    assert repositorio.contar_todos() == 0
    assert repositorio.contar_agotados() == 0


def test_cuenta_productos_y_agotados():
    repositorio = RepositorioProductosEnMemoria(
        [producto("Catosal 100 ml", "2"), producto("Lima triangular", "0"), producto("Urea", "0")]
    )

    assert repositorio.contar_todos() == 3
    assert repositorio.contar_agotados() == 2


def test_no_comparte_la_lista_original():
    productos = [producto("Catosal 100 ml", "2")]
    repositorio = RepositorioProductosEnMemoria(productos)

    productos.append(producto("Urea", "0"))

    assert repositorio.contar_todos() == 1


METODOS_DEL_PUERTO = [nombre for nombre in vars(RepositorioProductos) if not nombre.startswith("_")]


@pytest.mark.parametrize("adaptador", [RepositorioProductosEnMemoria, RepositorioProductosSupabase])
@pytest.mark.parametrize("metodo", METODOS_DEL_PUERTO)
def test_cada_adaptador_implementa_el_puerto(adaptador, metodo):
    assert callable(getattr(adaptador, metodo, None))
