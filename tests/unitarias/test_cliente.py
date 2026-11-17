"""Pruebas de db/cliente.py sin conectarse a Supabase."""

from inventario.config import Configuracion
from inventario.db import cliente


def test_crear_cliente_usa_la_configuracion(monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        cliente,
        "cargar_configuracion",
        lambda: Configuracion("https://ejemplo.supabase.co", "clave"),
    )
    monkeypatch.setattr(cliente, "create_client", lambda url, key: llamadas.append((url, key)))

    cliente.crear_cliente()

    assert llamadas == [("https://ejemplo.supabase.co", "clave")]


def test_obtener_cliente_reutiliza_la_misma_conexion(monkeypatch):
    cliente.obtener_cliente.cache_clear()
    monkeypatch.setattr(cliente, "crear_cliente", object)  # cada llamada crearía un objeto distinto

    try:
        assert cliente.obtener_cliente() is cliente.obtener_cliente()
    finally:
        cliente.obtener_cliente.cache_clear()
