"""Única responsabilidad: comprobar si la base de datos responde."""

import logging

from inventario.db.cliente import obtener_cliente

logger = logging.getLogger(__name__)


def base_de_datos_disponible() -> bool:
    """Hace una consulta mínima a Supabase. Nunca lanza excepciones."""
    try:
        obtener_cliente().table("producto").select("id").limit(1).execute()
        return True
    except Exception:  # el healthcheck debe responder aunque falle cualquier cosa
        logger.exception("La base de datos no respondió al healthcheck")
        return False
