"""Verifica que docs/db-export.json cumpla los requisitos del modelo de datos.

Si el archivo aún no se generó, las pruebas se omiten.
"""

import json
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[2] / "docs" / "db-export.json"

pytestmark = pytest.mark.skipif(
    not RUTA.exists(), reason="docs/db-export.json aún no se ha generado"
)


@pytest.fixture(scope="module")
def export():
    return json.loads(RUTA.read_text(encoding="utf-8"))


def test_tiene_campos_principales(export):
    assert export["generado_at"].endswith("Z")
    assert export["motor"] == "postgres"


def test_al_menos_5_tablas_todas_con_llave_primaria(export):
    assert len(export["tablas"]) >= 5
    for tabla in export["tablas"]:
        assert any(c["pk"] for c in tabla["columnas"]), f"{tabla['nombre']} no tiene llave primaria"


def test_al_menos_2_relaciones(export):
    assert sum(len(t["relaciones"]) for t in export["tablas"]) >= 2


def test_al_menos_1_indice(export):
    assert any(t["indices"] for t in export["tablas"])


def test_al_menos_3_tablas_con_datos(export):
    assert sum(1 for t in export["tablas"] if t["filas"] > 0) >= 3


def test_politicas_rls_en_al_menos_2_tablas(export):
    assert sum(1 for t in export["tablas"] if t["politicas_rls"]) >= 2
