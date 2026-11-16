"""Exporta el esquema REAL de la base de datos a docs/db-export.json.

Uso (desde la raíz del proyecto, con el entorno virtual activo):
    python -m inventario.herramientas.exportar_esquema

Llama a la función SQL exportar_esquema() (migración 004), que lee el catálogo
de PostgreSQL: tablas, columnas, llaves, índices, relaciones, políticas y filas.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from inventario.db.cliente import obtener_cliente

RUTA_EXPORT = Path("docs/db-export.json")


def construir_export(esquema: dict, ahora: datetime) -> dict:
    """Agrega la fecha de generación al inicio, con el formato pedido."""
    return {
        "generado_at": ahora.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **esquema,
    }


def resumen(export: dict) -> str:
    tablas = export["tablas"]
    relaciones = sum(len(t["relaciones"]) for t in tablas)
    mayor = max(tablas, key=lambda t: t["filas"])
    return (
        f"Tablas: {len(tablas)} | Relaciones: {relaciones} | "
        f"Tabla con más filas: {mayor['nombre']} ({mayor['filas']})"
    )


def main(ruta: Path = RUTA_EXPORT) -> dict:
    esquema = obtener_cliente().rpc("exportar_esquema").execute().data
    export = construir_export(esquema, datetime.now(timezone.utc))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(export, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Esquema exportado a {ruta}")
    print(resumen(export))
    return export


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
