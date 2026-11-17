"""Única responsabilidad: crear conexiones a Supabase."""

from functools import lru_cache

from supabase import Client, create_client

from inventario.config import cargar_configuracion


def crear_cliente() -> Client:
    """Crea un cliente nuevo de Supabase con la configuración del .env."""
    config = cargar_configuracion()
    return create_client(config.supabase_url, config.supabase_key)


@lru_cache(maxsize=1)
def obtener_cliente() -> Client:
    """Cliente compartido para consultar datos. Se crea la primera vez y se reutiliza."""
    return crear_cliente()
