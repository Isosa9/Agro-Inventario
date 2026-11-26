"""Rutas de inicio y cierre de sesión, y la dependencia que exige sesión."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from inventario.errores import AutenticacionError
from inventario.web import autenticacion
from inventario.web.plantillas import templates

COOKIE_SESION = "sesion"

# Atributos de seguridad de la cookie de sesión, definidos una sola vez (DRY).
# Deben ser idénticos al crearla y al borrarla; si no, el navegador no la borra.
ATRIBUTOS_COOKIE_SESION = {
    "httponly": True,  # JavaScript no puede leerla
    "secure": True,  # solo viaja por HTTPS
    "samesite": "lax",  # no se envía en formularios de otros sitios
}

router = APIRouter()


def guardar_cookie_de_sesion(respuesta: Response, sesion: autenticacion.Sesion) -> None:
    """Guarda el token en la cookie de sesión, con la misma duración que el token."""
    respuesta.set_cookie(
        COOKIE_SESION,
        sesion.token,
        max_age=sesion.expira_en_segundos,
        **ATRIBUTOS_COOKIE_SESION,
    )


def borrar_cookie_de_sesion(respuesta: Response) -> None:
    respuesta.delete_cookie(COOKIE_SESION, **ATRIBUTOS_COOKIE_SESION)


class SesionRequerida(Exception):
    """Se lanza cuando una página privada se pide sin sesión válida."""


def usuario_actual(request: Request) -> autenticacion.UsuarioSesion | None:
    return autenticacion.usuario_del_token(request.cookies.get(COOKIE_SESION))


def usuario_requerido(request: Request) -> autenticacion.UsuarioSesion:
    """Dependencia para páginas privadas: corta la petición si no hay sesión."""
    usuario = usuario_actual(request)
    if usuario is None:
        raise SesionRequerida()
    return usuario


@router.get("/login", response_class=HTMLResponse)
def formulario_login(request: Request):
    if usuario_actual(request):
        return RedirectResponse("/portal", status_code=303)
    return templates.TemplateResponse(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
def procesar_login(
    request: Request,
    correo: Annotated[str, Form()] = "",
    contrasena: Annotated[str, Form()] = "",
):
    try:
        sesion = autenticacion.iniciar_sesion(correo, contrasena)
    except AutenticacionError as error:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": str(error), "correo": correo},
            status_code=401,
        )

    respuesta = RedirectResponse("/portal", status_code=303)
    guardar_cookie_de_sesion(respuesta, sesion)
    return respuesta


@router.post("/logout")
def cerrar_sesion():
    respuesta = RedirectResponse("/", status_code=303)
    borrar_cookie_de_sesion(respuesta)
    return respuesta
