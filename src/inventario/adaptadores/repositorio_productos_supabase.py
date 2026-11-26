"""Adaptador de producción: implementa RepositorioProductos con Supabase.

Solo traduce entre filas de la base de datos y entidades del dominio:
sin reglas de negocio.
"""

from postgrest.exceptions import APIError
from supabase import Client

from inventario.dominio.producto import Producto
from inventario.errores import NombreDuplicadoError, ValidacionError

COLUMNAS = "id, nombre, precio, cantidad, categoria_id, unidad_medida_id"
VIOLACION_UNIQUE = "23505"
VIOLACION_LLAVE_FORANEA = "23503"


def fila_a_producto(fila: dict) -> Producto:
    # str(): PostgREST entrega NUMERIC como número JSON; el dominio lo convierte a Decimal exacto
    return Producto(
        id=fila["id"],
        nombre=fila["nombre"],
        precio=str(fila["precio"]),
        cantidad=str(fila["cantidad"]),
        categoria_id=fila["categoria_id"],
        unidad_medida_id=fila["unidad_medida_id"],
    )


def producto_a_fila(producto: Producto) -> dict:
    # Decimal como texto: viaja en JSON sin perder precisión
    return {
        "nombre": producto.nombre,
        "precio": str(producto.precio),
        "cantidad": str(producto.cantidad),
        "categoria_id": producto.categoria_id,
        "unidad_medida_id": producto.unidad_medida_id,
    }


class RepositorioProductosSupabase:
    TABLA = "producto"

    def __init__(self, cliente: Client):
        self._cliente = cliente

    def listar_todos(self) -> list[Producto]:
        respuesta = self._cliente.table(self.TABLA).select(COLUMNAS).order("nombre").execute()
        return [fila_a_producto(fila) for fila in respuesta.data]

    def buscar_por_id(self, producto_id: int) -> Producto | None:
        respuesta = (
            self._cliente.table(self.TABLA).select(COLUMNAS).eq("id", producto_id).execute()
        )
        return fila_a_producto(respuesta.data[0]) if respuesta.data else None

    def guardar(self, producto: Producto) -> Producto:
        tabla = self._cliente.table(self.TABLA)
        fila = producto_a_fila(producto)
        try:
            if producto.id is None:
                respuesta = tabla.insert(fila).execute()
            else:
                respuesta = tabla.update(fila).eq("id", producto.id).execute()
        except APIError as error:
            raise _traducir_error(error, producto) from error
        return fila_a_producto(respuesta.data[0])

    def contar_todos(self) -> int:
        respuesta = (
            self._cliente.table(self.TABLA).select("id", count="exact").limit(1).execute()
        )
        return respuesta.count or 0

    def contar_agotados(self) -> int:
        respuesta = (
            self._cliente.table(self.TABLA)
            .select("id", count="exact")
            .eq("cantidad", 0)
            .limit(1)
            .execute()
        )
        return respuesta.count or 0


def _traducir_error(error: APIError, producto: Producto) -> Exception:
    """Convierte errores de PostgreSQL en errores del negocio; lo demás se propaga igual."""
    if error.code == VIOLACION_UNIQUE:
        return NombreDuplicadoError(f'Ya existe un producto llamado "{producto.nombre}"')
    if error.code == VIOLACION_LLAVE_FORANEA:
        return ValidacionError("La categoría o la unidad de medida elegida no existe")
    return error
