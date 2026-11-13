"""Verifica que la app se conecta a Supabase y ve el esquema creado en la Etapa 2.

Solo LEEN datos: no modifican tu inventario.
"""

import pytest

pytestmark = pytest.mark.integracion

TABLAS = ["unidad_medida", "categoria", "producto", "venta", "detalle_venta"]


@pytest.mark.parametrize("tabla", TABLAS)
def test_tabla_existe_y_es_accesible(cliente, tabla):
    respuesta = cliente.table(tabla).select("id", count="exact").limit(1).execute()

    assert respuesta.count is not None


def test_hay_productos_cargados(cliente):
    respuesta = cliente.table("producto").select("id", count="exact").execute()

    assert respuesta.count > 0


def test_productos_traen_nombre_precio_y_cantidad(cliente):
    respuesta = (
        cliente.table("producto").select("nombre, precio, cantidad").limit(1).execute()
    )
    producto = respuesta.data[0]

    assert producto["nombre"]
    assert float(producto["precio"]) > 0
    assert float(producto["cantidad"]) >= 0
