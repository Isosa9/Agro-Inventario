"""Lectura de la configuración desde variables de entorno (.env)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from inventario.errores import ConfiguracionError

VARIABLES_REQUERIDAS = ("SUPABASE_URL", "SUPABASE_KEY")


@dataclass(frozen=True)
class Configuracion:
    supabase_url: str
    supabase_key: str


def cargar_configuracion() -> Configuracion:
    """Lee el .env y devuelve la configuración, o falla con un mensaje claro."""
    load_dotenv()
    valores = {nombre: os.getenv(nombre, "").strip() for nombre in VARIABLES_REQUERIDAS}

    faltantes = [nombre for nombre, valor in valores.items() if not valor]
    if faltantes:
        raise ConfiguracionError(
            f"Faltan variables en el archivo .env: {', '.join(faltantes)}"
        )

    if not valores["SUPABASE_URL"].startswith("https://"):
        raise ConfiguracionError("SUPABASE_URL debe comenzar con https://")

    return Configuracion(
        supabase_url=valores["SUPABASE_URL"],
        supabase_key=valores["SUPABASE_KEY"],
    )
