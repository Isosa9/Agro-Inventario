"""Punto de entrada para Vercel.

Vercel busca una variable `app` en este archivo. La aplicación real vive en
src/inventario/web/app.py; aquí solo se agrega `src` a la ruta de importación
por si el entorno de despliegue no instala el paquete.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from inventario.web.app import app  # noqa: E402

__all__ = ["app"]
