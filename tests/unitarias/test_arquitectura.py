"""Prueba de arquitectura: verifica la regla de la cebolla en cada ejecución del CI.

Las dependencias apuntan siempre hacia adentro:
    web / adaptadores  ->  casos_de_uso  ->  dominio
El dominio no conoce a nadie; los casos de uso solo conocen el dominio.
Lee los imports de cada archivo con el módulo ast de Python (sin ejecutar el código).
"""

import ast
import sys
from pathlib import Path

import pytest

PAQUETE = Path(__file__).resolve().parents[2] / "src" / "inventario"

# Lo que cada anillo puede importar, además de la librería estándar de Python
PERMITIDOS = {
    "dominio": ("inventario.dominio", "inventario.errores"),
    "casos_de_uso": ("inventario.casos_de_uso", "inventario.dominio", "inventario.errores"),
}


def imports_de(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module)
    return modulos


def es_libreria_estandar(modulo: str) -> bool:
    return modulo.split(".")[0] in sys.stdlib_module_names


def archivos_de(anillo: str) -> list[Path]:
    return sorted((PAQUETE / anillo).glob("*.py"))


CASOS = [
    pytest.param(anillo, archivo, id=f"{anillo}/{archivo.name}")
    for anillo in PERMITIDOS
    for archivo in archivos_de(anillo)
]


@pytest.mark.parametrize("anillo, archivo", CASOS)
def test_anillo_solo_importa_hacia_adentro(anillo, archivo):
    prohibidos = sorted(
        modulo
        for modulo in imports_de(archivo)
        if not es_libreria_estandar(modulo) and not modulo.startswith(PERMITIDOS[anillo])
    )

    assert not prohibidos, f"{anillo}/{archivo.name} importa hacia afuera: {prohibidos}"


def test_errores_del_negocio_no_dependen_de_nada_externo():
    # El dominio importa inventario.errores, así que ese módulo también debe ser puro
    externos = [m for m in imports_de(PAQUETE / "errores.py") if not es_libreria_estandar(m)]

    assert externos == []


def test_la_prueba_detecta_una_violacion(tmp_path):
    # Control: si alguien importara Supabase en el dominio, la regla lo atraparía
    archivo = tmp_path / "entidad_mal_hecha.py"
    archivo.write_text("from supabase import create_client\nimport decimal\n", encoding="utf-8")

    externos = [m for m in imports_de(archivo) if not es_libreria_estandar(m)]

    assert externos == ["supabase"]


def test_hay_archivos_en_cada_anillo():
    for anillo in PERMITIDOS:
        assert archivos_de(anillo), f"No se encontraron archivos en {anillo}/"
