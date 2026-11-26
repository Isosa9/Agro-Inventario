"""Pruebas de casos de uso con el repositorio en memoria: sin Supabase ni mocks encadenados."""

from inventario.adaptadores.repositorio_productos_memoria import RepositorioProductosEnMemoria
from inventario.casos_de_uso.resumen_inventario import obtener_resumen_inventario
from inventario.dominio.producto import Producto


def producto(nombre, cantidad):
    return Producto(nombre, "100", cantidad, categoria_id=1, unidad_medida_id=1)


def test_resumen_cuenta_total_y_agotados():
    repositorio = RepositorioProductosEnMemoria(
        [producto("Catosal 100 ml", "2"), producto("Becafor 100 ml", "0.000")]
    )

    resumen = obtener_resumen_inventario(repositorio)

    assert resumen.total_productos == 2
    assert resumen.productos_agotados == 1
    assert resumen.hay_agotados is True


def test_resumen_sin_agotados():
    resumen = obtener_resumen_inventario(
        RepositorioProductosEnMemoria([producto("Concentrado de cerdo", "2.5")])
    )

    assert resumen.hay_agotados is False


def test_resumen_de_inventario_vacio():
    resumen = obtener_resumen_inventario(RepositorioProductosEnMemoria())

    assert (resumen.total_productos, resumen.productos_agotados) == (0, 0)
