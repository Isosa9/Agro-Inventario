"""Casos de uso de productos con el repositorio en memoria (sin Supabase)."""

from decimal import Decimal

import pytest

from inventario.adaptadores.repositorio_productos_memoria import RepositorioProductosEnMemoria
from inventario.casos_de_uso import productos as casos
from inventario.dominio.producto import Producto
from inventario.errores import NombreDuplicadoError, ProductoNoEncontradoError


def producto(nombre, cantidad="5", precio="100"):
    return Producto(nombre, precio, cantidad, categoria_id=1, unidad_medida_id=1)


@pytest.fixture
def repositorio():
    return RepositorioProductosEnMemoria(
        [
            producto("Urea 46%", "15"),
            producto("Catosal 100 ml", "2"),
            producto("Oxitetraciclína L.A. 20 ml", "0"),
            producto("Amidan 500 ml", "0"),
        ]
    )


# ---------- Listar y buscar (RF-02, RF-04) ----------


def test_lista_ordenada_por_nombre(repositorio):
    nombres = [p.nombre for p in casos.listar_productos(repositorio)]

    assert nombres == [
        "Amidan 500 ml",
        "Catosal 100 ml",
        "Oxitetraciclína L.A. 20 ml",
        "Urea 46%",
    ]


@pytest.mark.parametrize("busqueda", ["oxitetraciclina", "OXITETRA", "  tetraciclína  ", "l.a."])
def test_busqueda_ignora_mayusculas_y_tildes(repositorio, busqueda):
    resultado = casos.listar_productos(repositorio, busqueda=busqueda)

    assert [p.nombre for p in resultado] == ["Oxitetraciclína L.A. 20 ml"]


def test_busqueda_sin_resultados(repositorio):
    assert casos.listar_productos(repositorio, busqueda="semilla") == []


def test_solo_agotados(repositorio):
    resultado = casos.listar_productos(repositorio, solo_agotados=True)

    assert [p.nombre for p in resultado] == ["Amidan 500 ml", "Oxitetraciclína L.A. 20 ml"]


def test_busqueda_y_agotados_combinados(repositorio):
    resultado = casos.listar_productos(repositorio, busqueda="amidan", solo_agotados=True)

    assert [p.nombre for p in resultado] == ["Amidan 500 ml"]


# ---------- Registrar (RF-01) ----------


def test_registrar_asigna_id_y_guarda(repositorio):
    nuevo = casos.registrar_producto(repositorio, producto("Concentrado de cerdo", "2.5"))

    assert nuevo.id is not None
    assert repositorio.buscar_por_id(nuevo.id).cantidad == Decimal("2.5")
    assert repositorio.contar_todos() == 5


def test_registrar_ignora_un_id_enviado(repositorio):
    # un formulario manipulado no puede sobrescribir otro producto
    con_id_ajeno = Producto("Febenzol 25 ml", "110", "2", categoria_id=1, unidad_medida_id=1, id=1)

    nuevo = casos.registrar_producto(repositorio, con_id_ajeno)

    assert nuevo.id != 1
    assert repositorio.buscar_por_id(1).nombre == "Urea 46%"


@pytest.mark.parametrize("nombre", ["Urea 46%", "urea 46%", "UREA   46%", "Catosal 100 mL"])
def test_registrar_rechaza_nombre_repetido_sin_importar_mayusculas(repositorio, nombre):
    with pytest.raises(NombreDuplicadoError, match="Ya existe un producto llamado"):
        casos.registrar_producto(repositorio, producto(nombre))

    assert repositorio.contar_todos() == 4


# ---------- Actualizar (RF-03) ----------


def test_actualizar_cambia_precio_y_cantidad(repositorio):
    original = casos.listar_productos(repositorio, busqueda="catosal")[0]

    actualizado = casos.actualizar_producto(
        repositorio, original.id, producto("Catosal 100 ml", cantidad="10", precio="975.50")
    )

    assert actualizado.id == original.id
    assert actualizado.precio == Decimal("975.50")
    assert repositorio.buscar_por_id(original.id).cantidad == Decimal("10")


def test_actualizar_puede_conservar_su_propio_nombre(repositorio):
    original = casos.listar_productos(repositorio, busqueda="urea")[0]

    casos.actualizar_producto(repositorio, original.id, producto("urea 46%", "20"))

    assert repositorio.buscar_por_id(original.id).nombre == "urea 46%"


def test_actualizar_rechaza_el_nombre_de_otro_producto(repositorio):
    original = casos.listar_productos(repositorio, busqueda="urea")[0]

    with pytest.raises(NombreDuplicadoError):
        casos.actualizar_producto(repositorio, original.id, producto("Catosal 100 ml"))


def test_actualizar_producto_inexistente(repositorio):
    with pytest.raises(ProductoNoEncontradoError):
        casos.actualizar_producto(repositorio, 999, producto("Nuevo"))


def test_obtener_producto_inexistente(repositorio):
    with pytest.raises(ProductoNoEncontradoError, match="999"):
        casos.obtener_producto(repositorio, 999)


def test_normalizar_texto():
    assert casos.normalizar_texto("  Oxitetraciclína   L.A. ") == "oxitetraciclina l.a."
