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
