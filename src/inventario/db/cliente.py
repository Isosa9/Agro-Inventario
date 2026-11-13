"""Única responsabilidad: crear la conexión a Supabase (una sola vez)."""

from functools import lru_cache

from supabase import Client, create_client

from inventario.config import cargar_configuracion


@lru_cache(maxsize=1)
def obtener_cliente() -> Client:
    """Devuelve el cliente de Supabase. Se crea la primera vez y se reutiliza."""
    config = cargar_configuracion()
    return create_client(config.supabase_url, config.supabase_key)
