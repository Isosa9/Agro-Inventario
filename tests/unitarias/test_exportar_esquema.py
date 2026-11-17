"""Pruebas del exportador de esquema, con un cliente de Supabase simulado."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from inventario.herramientas import exportar_esquema

ESQUEMA = {
    "motor": "postgres",
    "tablas": [
        {
            "nombre": "producto",
            "filas": 58,
            "relaciones": [{"columna": "categoria_id", "referencia": "categoria.id"}],
        },
        {"nombre": "categoria", "filas": 10, "relaciones": []},
    ],
}


def test_construir_export_pone_generado_at_primero_en_utc():
    hora_honduras = datetime(2026, 11, 15, 10, 0, tzinfo=timezone(timedelta(hours=-6)))

    export = exportar_esquema.construir_export(ESQUEMA, hora_honduras)

    assert list(export)[0] == "generado_at"
    assert export["generado_at"] == "2026-11-15T16:00:00Z"
    assert export["motor"] == "postgres"


def test_resumen_cuenta_relaciones_y_tabla_mayor():
    texto = exportar_esquema.resumen(ESQUEMA)

    assert "Tablas: 2" in texto
    assert "Relaciones: 1" in texto
    assert "producto (58)" in texto


def test_main_escribe_el_archivo_json(tmp_path, monkeypatch):
    cliente = MagicMock()
    cliente.rpc.return_value.execute.return_value.data = ESQUEMA
    monkeypatch.setattr(exportar_esquema, "obtener_cliente", lambda: cliente)
    ruta = tmp_path / "docs" / "db-export.json"

    exportar_esquema.main(ruta)

    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    assert contenido["tablas"][0]["nombre"] == "producto"
    cliente.rpc.assert_called_once_with("exportar_esquema")
