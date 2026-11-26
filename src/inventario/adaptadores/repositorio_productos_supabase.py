"""Acceso a la tabla producto. Solo lee y escribe datos: sin reglas de negocio."""

from supabase import Client


class ProductoRepositorio:
    TABLA = "producto"

    def __init__(self, cliente: Client):
        self._cliente = cliente

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
