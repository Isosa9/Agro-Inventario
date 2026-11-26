"""Pruebas del adaptador en memoria y de que todos los adaptadores cumplen sus puertos."""

import pytest

from inventario.adaptadores.repositorio_catalogos import (
    RepositorioCatalogosEnMemoria,
    RepositorioCatalogosSupabase,
)
from inventario.adaptadores.repositorio_productos_memoria import RepositorioProductosEnMemoria
from inventario.adaptadores.repositorio_productos_supabase import RepositorioProductosSupabase
from inventario.dominio.producto import Producto
from inventario.dominio.puertos import RepositorioCatalogos, RepositorioProductos
from inventario.errores import NombreDuplicadoError


def producto(nombre, cantidad="1", **extra):
    return Producto(nombre, "100", cantidad, categoria_id=1, unidad_medida_id=1, **extra)


def test_repositorio_vacio():
    repositorio = RepositorioProductosEnMemoria()

    assert repositorio.listar_todos() == []
    assert repositorio.contar_todos() == 0
    assert repositorio.contar_agotados() == 0


def test_cuenta_productos_y_agotados():
    repositorio = RepositorioProductosEnMemoria(
        [producto("Catosal 100 ml", "2"), producto("Lima triangular", "0"), producto("Urea", "0")]
    )

    assert repositorio.contar_todos() == 3
    assert repositorio.contar_agotados() == 2


def test_guardar_asigna_ids_consecutivos():
    repositorio = RepositorioProductosEnMemoria()

    primero = repositorio.guardar(producto("Catosal"))
    segundo = repositorio.guardar(producto("Urea"))

    assert (primero.id, segundo.id) == (1, 2)
    assert repositorio.buscar_por_id(2) == segundo


def test_respeta_ids_existentes_y_no_los_reutiliza():
    repositorio = RepositorioProductosEnMemoria([producto("Catosal", id=1)])

    assert repositorio.guardar(producto("Urea")).id == 2


def test_guardar_con_id_actualiza():
    repositorio = RepositorioProductosEnMemoria([producto("Catosal", "2")])

    repositorio.guardar(producto("Catosal", "9", id=1))

    assert repositorio.contar_todos() == 1
    assert str(repositorio.buscar_por_id(1).cantidad) == "9"


def test_rechaza_nombre_identico_como_la_restriccion_unique():
    repositorio = RepositorioProductosEnMemoria([producto("Catosal")])

    with pytest.raises(NombreDuplicadoError):
        repositorio.guardar(producto("Catosal"))


def test_buscar_inexistente_devuelve_none():
    assert RepositorioProductosEnMemoria().buscar_por_id(7) is None


def test_no_comparte_la_lista_original():
    productos = [producto("Catosal 100 ml", "2")]
    repositorio = RepositorioProductosEnMemoria(productos)

    productos.append(producto("Urea", "0"))

    assert repositorio.contar_todos() == 1


def metodos_de(puerto):
    return [nombre for nombre in vars(puerto) if not nombre.startswith("_")]


@pytest.mark.parametrize(
    "puerto, adaptador",
    [
        (RepositorioProductos, RepositorioProductosEnMemoria),
        (RepositorioProductos, RepositorioProductosSupabase),
        (RepositorioCatalogos, RepositorioCatalogosEnMemoria),
        (RepositorioCatalogos, RepositorioCatalogosSupabase),
    ],
)
def test_cada_adaptador_implementa_su_puerto(puerto, adaptador):
    faltantes = [m for m in metodos_de(puerto) if not callable(getattr(adaptador, m, None))]

    assert faltantes == []
