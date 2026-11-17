"""Pruebas de la aplicación web con TestClient (sin servidor ni internet)."""

import pytest
from fastapi.testclient import TestClient

from inventario import CODIGO_VERIFICACION
from inventario.web import salud
from inventario.web.app import app


@pytest.fixture
def cliente_http():
    return TestClient(app)


@pytest.fixture
def pagina_inicio(cliente_http):
    return cliente_http.get("/")


# ---------- Página de inicio: SEO, accesibilidad y PWA ----------

def test_inicio_responde_200_con_html(pagina_inicio):
    assert pagina_inicio.status_code == 200
    assert pagina_inicio.headers["content-type"].startswith("text/html")


@pytest.mark.parametrize(
    "fragmento",
    [
        '<html lang="es">',
        "<title>AgroInventario",
        'name="viewport"',
        'name="description"',
        'property="og:title"',
        'property="og:description"',
        'property="og:image" content="http',
        'rel="icon"',
        'rel="apple-touch-icon"',
        'rel="manifest"',
        'src="/js/app.js"',
    ],
)
def test_inicio_incluye_etiqueta(pagina_inicio, fragmento):
    assert fragmento in pagina_inicio.text


def test_meta_description_tiene_al_menos_40_caracteres(pagina_inicio):
    marcador = 'name="description" content="'
    inicio = pagina_inicio.text.index(marcador) + len(marcador)
    descripcion = pagina_inicio.text[inicio:pagina_inicio.text.index('"', inicio)]
    assert len(descripcion) >= 40


def test_inicio_publica_codigo_de_verificacion(pagina_inicio):
    assert CODIGO_VERIFICACION in pagina_inicio.text


def test_og_image_usa_https_detras_del_proxy(cliente_http):
    respuesta = cliente_http.get("/", headers={"x-forwarded-proto": "https"})
    assert 'property="og:image" content="https://' in respuesta.text


# ---------- Healthcheck ----------

def test_healthcheck_ok_cuando_la_base_responde(cliente_http, monkeypatch):
    monkeypatch.setattr(salud, "base_de_datos_disponible", lambda: True)

    respuesta = cliente_http.get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/json"
    assert respuesta.json()["estado"] == "ok"
    assert respuesta.json()["base_de_datos"] == "ok"


def test_healthcheck_503_cuando_la_base_falla(cliente_http, monkeypatch):
    monkeypatch.setattr(salud, "base_de_datos_disponible", lambda: False)

    respuesta = cliente_http.get("/api/health")

    assert respuesta.status_code == 503
    assert respuesta.json()["estado"] == "degradado"


def test_base_de_datos_disponible_devuelve_false_si_hay_error(monkeypatch):
    def cliente_que_falla():
        raise RuntimeError("sin conexión")

    monkeypatch.setattr(salud, "obtener_cliente", cliente_que_falla)

    assert salud.base_de_datos_disponible() is False


# ---------- Errores 404 ----------

def test_pagina_inexistente_devuelve_404_html(cliente_http):
    respuesta = cliente_http.get("/esta-pagina-no-existe")

    assert respuesta.status_code == 404
    assert "No encontramos esa página" in respuesta.text


def test_api_inexistente_devuelve_404_json(cliente_http):
    respuesta = cliente_http.get("/api/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"error": "Recurso no encontrado"}


def test_en_local_se_sirven_los_archivos_de_public(cliente_http):
    respuesta = cliente_http.get("/css/estilos.css")

    assert respuesta.status_code == 200
    assert "@media" in respuesta.text


# ---------- Errores inesperados (500) ----------

@pytest.fixture
def navegador_tolerante():
    # raise_server_exceptions=False: ver la respuesta que recibe el usuario, no la excepción
    return TestClient(app, raise_server_exceptions=False)


def test_error_inesperado_muestra_pagina_500_y_lo_registra(
    navegador_tolerante, monkeypatch, caplog
):
    def falla():
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(salud, "base_de_datos_disponible", falla)

    with caplog.at_level("ERROR"):
        respuesta = navegador_tolerante.get("/api/health")

    assert respuesta.status_code == 500
    assert respuesta.json() == {"error": "Error interno del servidor"}
    assert "fallo simulado" not in respuesta.text  # no se filtran detalles internos
    assert "Error inesperado en GET /api/health" in caplog.text


def test_error_inesperado_en_pagina_html_muestra_plantilla(navegador_tolerante, monkeypatch):
    from inventario.web import plantillas

    original = plantillas.templates.TemplateResponse

    def plantilla_que_falla(request, nombre, *args, **kwargs):
        if nombre == "inicio.html":
            raise RuntimeError("fallo simulado")
        return original(request, nombre, *args, **kwargs)

    monkeypatch.setattr(plantillas.templates, "TemplateResponse", plantilla_que_falla)

    respuesta = navegador_tolerante.get("/")

    assert respuesta.status_code == 500
    assert "Algo salió mal" in respuesta.text
