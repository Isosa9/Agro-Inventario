"""Pruebas de autenticacion.py: Supabase Auth se reemplaza con mocks."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from supabase import AuthApiError

from inventario.errores import AutenticacionError
from inventario.web import autenticacion


@pytest.fixture
def cliente_auth(monkeypatch):
    cliente = MagicMock()
    monkeypatch.setattr(autenticacion, "_nuevo_cliente", lambda: cliente)
    return cliente.auth


def respuesta_login(correo="ana@agro.com", token="jwt", expira=3600):
    return SimpleNamespace(
        session=SimpleNamespace(access_token=token, expires_in=expira),
        user=SimpleNamespace(email=correo),
    )


def test_iniciar_sesion_correcto_devuelve_sesion(cliente_auth):
    cliente_auth.sign_in_with_password.return_value = respuesta_login()

    sesion = autenticacion.iniciar_sesion("  Ana@Agro.com ", "secreta")

    assert sesion.token == "jwt"
    assert sesion.correo == "ana@agro.com"
    assert sesion.expira_en_segundos == 3600
    cliente_auth.sign_in_with_password.assert_called_once_with(
        {"email": "ana@agro.com", "password": "secreta"}
    )


@pytest.mark.parametrize(
    "correo, contrasena", [("", "secreta"), ("ana@agro.com", ""), ("   ", "x")]
)
def test_iniciar_sesion_exige_correo_y_contrasena(cliente_auth, correo, contrasena):
    with pytest.raises(AutenticacionError, match="Escribe tu correo"):
        autenticacion.iniciar_sesion(correo, contrasena)

    cliente_auth.sign_in_with_password.assert_not_called()


def test_credenciales_invalidas_dan_mensaje_generico(cliente_auth):
    cliente_auth.sign_in_with_password.side_effect = AuthApiError(
        "Invalid login credentials", 400, None
    )

    with pytest.raises(AutenticacionError, match="Correo o contraseña incorrectos"):
        autenticacion.iniciar_sesion("ana@agro.com", "mala")


def test_fallo_de_conexion_da_mensaje_distinto(cliente_auth):
    cliente_auth.sign_in_with_password.side_effect = ConnectionError("sin internet")

    with pytest.raises(AutenticacionError, match="Intenta de nuevo"):
        autenticacion.iniciar_sesion("ana@agro.com", "secreta")


def test_correo_del_token_valido(cliente_auth):
    cliente_auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(email="ana@agro.com"))

    assert autenticacion.correo_del_token("jwt") == "ana@agro.com"


@pytest.mark.parametrize("token", [None, ""])
def test_correo_del_token_vacio_es_none_sin_consultar(cliente_auth, token):
    assert autenticacion.correo_del_token(token) is None
    cliente_auth.get_user.assert_not_called()


def test_correo_del_token_invalido_es_none(cliente_auth):
    cliente_auth.get_user.side_effect = AuthApiError("invalid JWT", 401, None)

    assert autenticacion.correo_del_token("alterado") is None


def test_correo_del_token_con_servicio_caido_es_none_y_queda_en_el_log(cliente_auth, caplog):
    cliente_auth.get_user.side_effect = ConnectionError("sin internet")

    with caplog.at_level("ERROR"):
        assert autenticacion.correo_del_token("jwt") is None

    assert "No se pudo validar el token" in caplog.text
