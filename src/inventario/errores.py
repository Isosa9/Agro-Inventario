"""Excepciones propias del sistema.

Todas heredan de InventarioError para que la interfaz pueda atraparlas
juntas sin ocultar errores inesperados de Python.
"""


class InventarioError(Exception):
    """Error base del sistema."""


class ConfiguracionError(InventarioError):
    """Falta o es inválida la configuración (archivo .env)."""


class AutenticacionError(InventarioError):
    """No se pudo iniciar sesión (credenciales inválidas o servicio no disponible)."""


class ValidacionError(InventarioError):
    """Un dato no cumple las reglas del negocio (precio, cantidad, nombre...)."""


class NombreDuplicadoError(ValidacionError):
    """Ya existe otro producto con ese nombre."""


class ProductoNoEncontradoError(InventarioError):
    """No existe un producto con ese identificador."""
