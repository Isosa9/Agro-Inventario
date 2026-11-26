"""Pruebas del login, el cierre de sesión y el portal privado (con mocks)."""

import pytest
from fastapi.testclient import TestClient

from inventario.errores import AutenticacionError
from inventario.web import autenticacion
from inventario.web.app import app
from inventario.web.autenticacion import Sesion, UsuarioSesion
from inventario.web.dependencias import repositorio_productos
from inventario.web.sesion import COOKIE_SESION

CORREO = "dueña@agro.com"
TOKEN_VALIDO = "token-valido"


class RepositorioFalso:
    """Espía del repositorio: no toca Supabase y registra si se consultó."""

    def __init__(self):
        self.consultado = False

    def contar_todos(self):
        self.consultado = True
        return 58

    def contar_agotados(self):
        return 3


@pytest.fixture
def repositorio():
    falso = RepositorioFalso()
    app.dependency_overrides[repositorio_productos] = lambda: falso
    yield falso
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    """Solo TOKEN_VALIDO es una sesión válida."""
    monkeypatch.setattr(
        autenticacion,
        "usuario_del_token",
        lambda token: UsuarioSesion(CORREO, "Dueña") if token == TOKEN_VALIDO else None,
    )


@pytest.fixture
def navegador():
    # https: la cookie de sesión es Secure y solo viaja por HTTPS
    return TestClient(app, base_url="https://testserver", follow_redirects=False)


# ---------- Página de login ----------

def test_login_muestra_formulario_con_contrasena(navegador):
    respuesta = navegador.get("/login")

    assert respuesta.status_code == 200
    assert '<form class="formulario" method="post" action="/login">' in respuesta.text
    assert 'type="password"' in respuesta.text


def test_login_con_sesion_activa_redirige_al_portal(navegador):
    navegador.cookies.set(COOKIE_SESION, TOKEN_VALIDO)

    respuesta = navegador.get("/login")

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/portal"


def test_login_correcto_crea_cookie_segura_y_redirige(navegador, monkeypatch):
    monkeypatch.setattr(
        autenticacion,
        "iniciar_sesion",
        lambda correo, contrasena: Sesion(TOKEN_VALIDO, CORREO, 3600),
    )

    respuesta = navegador.post("/login", data={"correo": CORREO, "contrasena": "secreta"})

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/portal"
    cookie = respuesta.headers["set-cookie"].lower()
    assert f"{COOKIE_SESION}={TOKEN_VALIDO}" in cookie
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=3600" in cookie


def test_login_incorrecto_muestra_error_sin_cookie(navegador, monkeypatch):
    def rechazar(correo, contrasena):
        raise AutenticacionError("Correo o contraseña incorrectos")

    monkeypatch.setattr(autenticacion, "iniciar_sesion", rechazar)

    respuesta = navegador.post("/login", data={"correo": CORREO, "contrasena": "mala"})

    assert respuesta.status_code == 401
    assert "Correo o contraseña incorrectos" in respuesta.text
    assert "set-cookie" not in respuesta.headers
    assert f'value="{CORREO}"' in respuesta.text  # no obliga a reescribir el correo


# ---------- Portal privado ----------

def test_portal_sin_sesion_redirige_y_no_muestra_datos(navegador, repositorio):
    respuesta = navegador.get("/portal")

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/login"
    assert "Productos registrados" not in respuesta.text
    assert repositorio.consultado is False  # ni siquiera consultó la base de datos


def test_portal_con_token_invalido_redirige(navegador, repositorio):
    navegador.cookies.set(COOKIE_SESION, "token-alterado")

    respuesta = navegador.get("/portal")

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/login"


def test_portal_con_sesion_muestra_resumen(navegador, repositorio):
    navegador.cookies.set(COOKIE_SESION, TOKEN_VALIDO)

    respuesta = navegador.get("/portal")

    assert respuesta.status_code == 200
    assert CORREO in respuesta.text
    assert "Hola, Dueña" in respuesta.text
    assert "Resumen</a>" not in respuesta.text  # sin menú duplicado
    assert ">58<" in respuesta.text
    assert ">3<" in respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    assert 'content="noindex, nofollow"' in respuesta.text


# ---------- Cierre de sesión ----------

def test_logout_borra_la_cookie_y_vuelve_al_inicio(navegador):
    navegador.cookies.set(COOKIE_SESION, TOKEN_VALIDO)

    respuesta = navegador.post("/logout")

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/"
    cookie = respuesta.headers["set-cookie"].lower()
    assert f"{COOKIE_SESION}=" in cookie
    assert "max-age=0" in cookie
