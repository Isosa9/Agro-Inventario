"""Única responsabilidad: iniciar sesión y validar sesiones con Supabase Auth."""

import logging
from dataclasses import dataclass

from supabase import AuthApiError, Client

from inventario.db.cliente import crear_cliente
from inventario.errores import AutenticacionError

logger = logging.getLogger(__name__)

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos"


@dataclass(frozen=True)
class Sesion:
    token: str
    correo: str
    expira_en_segundos: int


def _nuevo_cliente() -> Client:
    """Cliente aparte para Auth.

    Iniciar sesión cambia el estado interno del cliente de Supabase. Si usáramos
    el cliente compartido, sus consultas dejarían de usar la clave del servidor.
    """
    return crear_cliente()


def iniciar_sesion(correo: str, contrasena: str) -> Sesion:
    correo = correo.strip().lower()
    if not correo or not contrasena:
        raise AutenticacionError("Escribe tu correo y tu contraseña")

    try:
        respuesta = _nuevo_cliente().auth.sign_in_with_password(
            {"email": correo, "password": contrasena}
        )
    except AuthApiError as error:
        raise AutenticacionError(MENSAJE_CREDENCIALES) from error
    except Exception as error:
        logger.exception("Supabase Auth no respondió")
        raise AutenticacionError("No se pudo iniciar sesión. Intenta de nuevo.") from error

    if respuesta.session is None or respuesta.user is None:
        raise AutenticacionError(MENSAJE_CREDENCIALES)

    return Sesion(
        token=respuesta.session.access_token,
        correo=respuesta.user.email or correo,
        expira_en_segundos=respuesta.session.expires_in or 3600,
    )


def correo_del_token(token: str | None) -> str | None:
    """Devuelve el correo del usuario si el token es válido; si no, None."""
    if not token:
        return None
    try:
        respuesta = _nuevo_cliente().auth.get_user(token)
    except AuthApiError:
        return None  # token vencido o alterado: es normal, no se registra
    except Exception:
        # servicio caído o error inesperado: se trata como sin sesión, pero queda en el log
        logger.exception("No se pudo validar el token con Supabase Auth")
        return None
    if respuesta is None or respuesta.user is None:
        return None
    return respuesta.user.email
