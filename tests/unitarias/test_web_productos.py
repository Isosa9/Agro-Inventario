"""Páginas de productos del portal, con adaptadores en memoria (sin Supabase)."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from inventario.adaptadores.repositorio_catalogos import RepositorioCatalogosEnMemoria
from inventario.adaptadores.repositorio_productos_memoria import RepositorioProductosEnMemoria
from inventario.dominio.catalogo import ElementoCatalogo
from inventario.dominio.producto import Producto
from inventario.web import autenticacion
from inventario.web.app import app
from inventario.web.autenticacion import UsuarioSesion
from inventario.web.dependencias import repositorio_catalogos, repositorio_productos
from inventario.web.plantillas import formato_cantidad, formato_lempiras
from inventario.web.sesion import COOKIE_SESION

TOKEN = "token-valido"


@pytest.fixture
def productos():
    return RepositorioProductosEnMemoria(
        [
            Producto("Catosal 100 ml", "950", "2", categoria_id=1, unidad_medida_id=5),
            Producto("Concentrado de cerdo", "12", "2.500", categoria_id=2, unidad_medida_id=1),
            Producto("Lima triangular", "65", "0", categoria_id=2, unidad_medida_id=5),
        ]
    )


@pytest.fixture
def navegador(productos, monkeypatch):
    catalogos = RepositorioCatalogosEnMemoria(
        categorias=[ElementoCatalogo(1, "Vitaminas y minerales"), ElementoCatalogo(2, "Otros")],
        unidades=[ElementoCatalogo(1, "Libra", "lb"), ElementoCatalogo(5, "Unidad", "und")],
    )
    app.dependency_overrides[repositorio_productos] = lambda: productos
    app.dependency_overrides[repositorio_catalogos] = lambda: catalogos
    monkeypatch.setattr(
        autenticacion,
        "usuario_del_token",
        lambda t: UsuarioSesion("duena@agro.com", "Duena") if t == TOKEN else None,
    )
    cliente = TestClient(app, base_url="https://testserver", follow_redirects=False)
    cliente.cookies.set(COOKIE_SESION, TOKEN)
    yield cliente
    app.dependency_overrides.clear()


def formulario(**cambios):
    datos = {
        "nombre": "Febenzol 25 ml",
        "precio": "110",
        "cantidad": "2,5",
        "categoria_id": "2",
        "unidad_medida_id": "1",
    }
    datos.update(cambios)
    return datos


# ---------- Seguridad ----------


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("get", "/portal/productos"),
        ("get", "/portal/productos/nuevo"),
        ("post", "/portal/productos/nuevo"),
        ("get", "/portal/productos/1/editar"),
        ("post", "/portal/productos/1/editar"),
    ],
)
def test_todas_las_paginas_exigen_sesion(navegador, productos, metodo, ruta):
    navegador.cookies.clear()

    respuesta = getattr(navegador, metodo)(ruta)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/login"
    assert productos.contar_todos() == 3  # nada se creó ni modificó


# ---------- Lista, búsqueda y agotados ----------


def test_lista_muestra_productos_con_formato(navegador):
    respuesta = navegador.get("/portal/productos")

    assert respuesta.status_code == 200
    assert "Catosal 100 ml" in respuesta.text
    assert "L 950.00" in respuesta.text
    assert '<td data-etiqueta="Existencia" class="numero">2.5</td>' in respuesta.text  # sin ceros
    assert "2.5 lb" not in respuesta.text  # la existencia se muestra sin unidad
    assert "Vitaminas y minerales" in respuesta.text
    assert "3 productos" in respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    assert 'href="/portal">← Volver al inicio' in respuesta.text


def test_lista_marca_agotados(navegador):
    respuesta = navegador.get("/portal/productos")

    assert respuesta.text.count('class="etiqueta-agotado"') == 1


def test_busqueda(navegador):
    respuesta = navegador.get("/portal/productos", params={"q": "CONCENTRADO"})

    assert "Concentrado de cerdo" in respuesta.text
    assert "Catosal" not in respuesta.text
    assert "1 producto<" in respuesta.text


def test_filtro_de_agotados(navegador):
    respuesta = navegador.get("/portal/productos", params={"agotados": "true"})

    assert "Productos agotados" in respuesta.text
    assert "Lima triangular" in respuesta.text
    assert "Catosal" not in respuesta.text


def test_busqueda_sin_resultados(navegador):
    respuesta = navegador.get("/portal/productos", params={"q": "semilla"})

    assert "No se encontraron productos" in respuesta.text


def test_busqueda_escapa_html(navegador):
    respuesta = navegador.get("/portal/productos", params={"q": "<script>alert(1)</script>"})

    assert "<script>alert(1)</script>" not in respuesta.text
    assert "&lt;script&gt;" in respuesta.text


# ---------- Registrar ----------


def test_formulario_nuevo_tiene_catalogos(navegador):
    respuesta = navegador.get("/portal/productos/nuevo")

    assert respuesta.status_code == 200
    assert "Libra (lb)" in respuesta.text
    assert 'name="precio"' in respuesta.text


def test_crear_producto_valido(navegador, productos):
    respuesta = navegador.post("/portal/productos/nuevo", data=formulario())

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/portal/productos?guardado=Febenzol+25+ml"
    nuevo = [p for p in productos.listar_todos() if p.nombre == "Febenzol 25 ml"][0]
    assert nuevo.cantidad == Decimal("2.5")  # aceptó la coma decimal


def test_lista_confirma_lo_guardado(navegador):
    respuesta = navegador.get("/portal/productos", params={"guardado": "Urea 46%"})

    assert "Se guardó «Urea 46%»" in respuesta.text


@pytest.mark.parametrize(
    "cambio, mensaje",
    [
        ({"precio": "-5"}, "El precio debe ser mayor que 0"),
        ({"precio": "abc"}, "El precio debe ser un número"),
        ({"nombre": "   "}, "El nombre es obligatorio"),
        ({"categoria_id": ""}, "Elige una categoría"),
        ({"unidad_medida_id": ""}, "Elige una unidad de medida"),
        ({"nombre": "catosal 100 ML"}, "Ya existe un producto llamado"),
    ],
)
def test_crear_con_error_conserva_lo_escrito(navegador, productos, cambio, mensaje):
    datos = formulario(**cambio)

    respuesta = navegador.post("/portal/productos/nuevo", data=datos)

    assert respuesta.status_code == 422
    assert mensaje in respuesta.text
    assert f'value="{datos["cantidad"]}"' in respuesta.text
    assert productos.contar_todos() == 3


# ---------- Editar ----------


def test_formulario_editar_viene_lleno(navegador):
    respuesta = navegador.get("/portal/productos/2/editar")

    assert respuesta.status_code == 200
    assert 'value="Concentrado de cerdo"' in respuesta.text
    assert 'value="12.00"' in respuesta.text
    assert 'value="2.5"' in respuesta.text
    assert '<option value="2" selected>' in respuesta.text


def test_editar_actualiza_el_producto(navegador, productos):
    datos = formulario(nombre="Catosal 100 ml", precio="975.50", cantidad="10")

    respuesta = navegador.post("/portal/productos/1/editar", data=datos)

    assert respuesta.status_code == 303
    assert productos.buscar_por_id(1).precio == Decimal("975.50")


def test_editar_con_error_no_guarda(navegador, productos):
    respuesta = navegador.post("/portal/productos/1/editar", data=formulario(cantidad="-1"))

    assert respuesta.status_code == 422
    assert productos.buscar_por_id(1).cantidad == Decimal("2")


def test_editar_producto_inexistente_da_404(navegador):
    assert navegador.get("/portal/productos/999/editar").status_code == 404
    assert navegador.post("/portal/productos/999/editar", data=formulario()).status_code == 404


# ---------- Formatos ----------


@pytest.mark.parametrize(
    "valor, texto", [("1670", "L 1,670.00"), ("11.5", "L 11.50"), ("0.01", "L 0.01")]
)
def test_formato_lempiras(valor, texto):
    assert formato_lempiras(Decimal(valor)) == texto


@pytest.mark.parametrize(
    "valor, texto", [("2.500", "2.5"), ("500.000", "500"), ("0.125", "0.125"), ("0", "0")]
)
def test_formato_cantidad(valor, texto):
    assert formato_cantidad(Decimal(valor)) == texto
