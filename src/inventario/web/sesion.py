"""Rutas de inicio y cierre de sesión, y la dependencia que exige sesión."""

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from inventario.errores import AutenticacionError
from inventario.web import autenticacion
from inventario.web.plantillas import templates

COOKIE_SESION = "sesion"

router = APIRouter()


class SesionRequerida(Exception):
    """Se lanza cuando una página privada se pide sin sesión válida."""


def correo_actual(request: Request) -> str | None:
    return autenticacion.correo_del_token(request.cookies.get(COOKIE_SESION))


def correo_requerido(request: Request) -> str:
    """Dependencia para páginas privadas: corta la petición si no hay sesión."""
    correo = correo_actual(request)
    if correo is None:
        raise SesionRequerida()
    return correo


@router.get("/login", response_class=HTMLResponse)
def formulario_login(request: Request):
    if correo_actual(request):
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
    respuesta.set_cookie(
        COOKIE_SESION,
        sesion.token,
        max_age=sesion.expira_en_segundos,
        httponly=True,   # JavaScript no puede leerla
        secure=True,     # solo viaja por HTTPS
        samesite="lax",  # no se envía en formularios de otros sitios
    )
    return respuesta


@router.post("/logout")
def cerrar_sesion():
    respuesta = RedirectResponse("/", status_code=303)
    respuesta.delete_cookie(COOKIE_SESION, httponly=True, secure=True, samesite="lax")
    return respuesta
