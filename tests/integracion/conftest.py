"""Fixtures para pruebas de integración contra Supabase real."""

import pytest

from inventario.db.cliente import obtener_cliente
from inventario.errores import ConfiguracionError


@pytest.fixture(scope="session")
def cliente():
    """Cliente real de Supabase. Si no hay .env, se omiten las pruebas."""
    try:
        return obtener_cliente()
    except ConfiguracionError as error:
        pytest.skip(f"Sin configuración de Supabase: {error}")
