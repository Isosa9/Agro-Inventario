"""Adaptadores de RepositorioCatalogos: categorías y unidades de medida."""

from collections.abc import Iterable

from supabase import Client

from inventario.dominio.catalogo import ElementoCatalogo


class RepositorioCatalogosSupabase:
    def __init__(self, cliente: Client):
        self._cliente = cliente

    def listar_categorias(self) -> list[ElementoCatalogo]:
        respuesta = self._cliente.table("categoria").select("id, nombre").order("nombre").execute()
        return [ElementoCatalogo(fila["id"], fila["nombre"]) for fila in respuesta.data]

    def listar_unidades(self) -> list[ElementoCatalogo]:
        respuesta = (
            self._cliente.table("unidad_medida")
            .select("id, nombre, abreviatura")
            .order("nombre")
            .execute()
        )
        return [
            ElementoCatalogo(fila["id"], fila["nombre"], fila["abreviatura"])
            for fila in respuesta.data
        ]


class RepositorioCatalogosEnMemoria:
    def __init__(
        self,
        categorias: Iterable[ElementoCatalogo] = (),
        unidades: Iterable[ElementoCatalogo] = (),
    ):
        self._categorias = list(categorias)
        self._unidades = list(unidades)

    def listar_categorias(self) -> list[ElementoCatalogo]:
        return list(self._categorias)

    def listar_unidades(self) -> list[ElementoCatalogo]:
        return list(self._unidades)
