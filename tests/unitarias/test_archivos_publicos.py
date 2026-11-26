"""Verifica los archivos estáticos que Vercel publica desde public/."""

import json
from pathlib import Path

import pytest

from inventario import CODIGO_VERIFICACION

RAIZ = Path(__file__).resolve().parents[2]
PUBLIC = RAIZ / "public"


@pytest.fixture(scope="module")
def manifest():
    return json.loads((PUBLIC / "manifest.webmanifest").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "archivo",
    [
        "favicon.ico",
        "sw.js",
        "robots.txt",
        "offline.html",
        "og-image.png",
        "iconos/apple-touch-icon.png",
        "css/estilos.css",
        "js/app.js",
    ],
)
def test_archivo_publico_existe(archivo):
    assert (PUBLIC / archivo).is_file()


CAMPOS_MANIFEST = (
    "name", "short_name", "start_url", "display", "theme_color", "background_color", "icons",
)


def test_manifest_tiene_campos_requeridos(manifest):
    for campo in CAMPOS_MANIFEST:
        assert manifest[campo]


def test_manifest_incluye_iconos_192_y_512_que_existen(manifest):
    tamanos = {icono["sizes"] for icono in manifest["icons"]}
    assert {"192x192", "512x512"} <= tamanos
    for icono in manifest["icons"]:
        assert (PUBLIC / icono["src"].lstrip("/")).is_file()


def test_css_es_responsive():
    assert "@media" in (PUBLIC / "css/estilos.css").read_text(encoding="utf-8")


def test_verificacion_txt_contiene_el_codigo():
    assert CODIGO_VERIFICACION in (PUBLIC / "verificacion.txt").read_text(encoding="utf-8")


def test_vercel_json_define_headers_de_seguridad():
    config = json.loads((RAIZ / "vercel.json").read_text(encoding="utf-8"))
    headers = {
        h["key"]
        for regla in config["headers"]
        if regla["source"] == "/(.*)"
        for h in regla["headers"]
    }
    assert {
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Content-Security-Policy",
    } <= headers


def test_service_worker_actualiza_los_archivos_estaticos():
    # stale-while-revalidate guarda la versión nueva (con cache-first los estilos se congelaban)
    sw = (PUBLIC / "sw.js").read_text(encoding="utf-8")

    assert "cache.put(request" in sw
    assert 'const VERSION = "agroinventario-v1"' in sw
