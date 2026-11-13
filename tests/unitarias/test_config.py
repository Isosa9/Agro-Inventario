"""Pruebas unitarias de config.py. No usan internet ni el .env real."""

import pytest

from inventario import config
from inventario.errores import ConfiguracionError

URL_VALIDA = "https://ejemplo.supabase.co"


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    """Aísla cada prueba: sin .env real y sin variables previas."""
    monkeypatch.setattr(config, "load_dotenv", lambda: None)  # mock: no leer .env
    for nombre in config.VARIABLES_REQUERIDAS:
        monkeypatch.delenv(nombre, raising=False)


def test_carga_configuracion_valida(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
    monkeypatch.setenv("SUPABASE_KEY", "clave-secreta")

    resultado = config.cargar_configuracion()

    assert resultado.supabase_url == URL_VALIDA
    assert resultado.supabase_key == "clave-secreta"


def test_elimina_espacios_alrededor_de_los_valores(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", f"  {URL_VALIDA}  ")
    monkeypatch.setenv("SUPABASE_KEY", "  clave  ")

    resultado = config.cargar_configuracion()

    assert resultado.supabase_url == URL_VALIDA
    assert resultado.supabase_key == "clave"


def test_falla_si_faltan_todas_las_variables():
    with pytest.raises(ConfiguracionError, match="SUPABASE_URL, SUPABASE_KEY"):
        config.cargar_configuracion()


def test_falla_si_la_clave_esta_vacia(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", URL_VALIDA)
    monkeypatch.setenv("SUPABASE_KEY", "   ")

    with pytest.raises(ConfiguracionError, match="SUPABASE_KEY"):
        config.cargar_configuracion()


def test_falla_si_la_url_no_es_https(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://ejemplo.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "clave")

    with pytest.raises(ConfiguracionError, match="https://"):
        config.cargar_configuracion()
