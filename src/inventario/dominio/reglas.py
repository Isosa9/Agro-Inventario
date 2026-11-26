"""Reglas de validación del negocio.

Cada función revisa UN dato: si es válido lo devuelve normalizado (por ejemplo,
texto sin espacios sobrantes o número como Decimal); si no, lanza ValidacionError
con un mensaje claro en español.

Los límites coinciden con las columnas de la base de datos (migración 001):
  precio   NUMERIC(12,2) -> hasta 2 decimales
  cantidad NUMERIC(12,3) -> hasta 3 decimales (ventas por peso: 2.5 lb, 0.125 qq)
"""

from decimal import Decimal, InvalidOperation

from inventario.errores import ValidacionError

LARGO_MAXIMO_NOMBRE = 120
DECIMALES_PRECIO = 2
DECIMALES_CANTIDAD = 3
PRECIO_MAXIMO = Decimal("9999999999.99")
CANTIDAD_MAXIMA = Decimal("999999999.999")


def a_decimal(valor: object, campo: str) -> Decimal:
    """Convierte a Decimal exacto. Acepta '2,5' (coma decimal) además de '2.5'."""
    if isinstance(valor, bool) or valor is None:
        raise ValidacionError(f"{campo} debe ser un número")
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    elif isinstance(valor, float):
        valor = str(valor)  # evita el error binario del float (0.1 -> 0.1000000000000000055)
    try:
        numero = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidacionError(f"{campo} debe ser un número") from None
    if not numero.is_finite():
        raise ValidacionError(f"{campo} debe ser un número")
    return numero


def _validar_numero(
    valor: object,
    campo: str,
    *,
    decimales: int,
    maximo: Decimal,
    permitir_cero: bool,
) -> Decimal:
    """Regla común a precios y cantidades (DRY)."""
    numero = a_decimal(valor, campo)

    if numero < 0 or (numero == 0 and not permitir_cero):
        condicion = "mayor o igual a 0" if permitir_cero else "mayor que 0"
        raise ValidacionError(f"{campo} debe ser {condicion}")
    if numero > maximo:
        raise ValidacionError(f"{campo} no puede ser mayor que {maximo}")
    if -numero.as_tuple().exponent > decimales:
        raise ValidacionError(f"{campo} admite como máximo {decimales} decimales")
    return numero


def validar_nombre(nombre: object) -> str:
    """Nombre obligatorio, sin espacios repetidos y de largo razonable."""
    if not isinstance(nombre, str):
        raise ValidacionError("El nombre es obligatorio")
    limpio = " ".join(nombre.split())
    if not limpio:
        raise ValidacionError("El nombre es obligatorio")
    if len(limpio) > LARGO_MAXIMO_NOMBRE:
        raise ValidacionError(f"El nombre admite como máximo {LARGO_MAXIMO_NOMBRE} caracteres")
    return limpio


def validar_precio(precio: object) -> Decimal:
    return _validar_numero(
        precio, "El precio", decimales=DECIMALES_PRECIO, maximo=PRECIO_MAXIMO, permitir_cero=False
    )


def validar_existencia(cantidad: object) -> Decimal:
    """Cantidad en inventario: puede ser 0 (agotado), nunca negativa."""
    return _validar_numero(
        cantidad,
        "La cantidad",
        decimales=DECIMALES_CANTIDAD,
        maximo=CANTIDAD_MAXIMA,
        permitir_cero=True,
    )


def validar_cantidad_venta(cantidad: object) -> Decimal:
    """Cantidad vendida: siempre mayor que 0."""
    return _validar_numero(
        cantidad,
        "La cantidad vendida",
        decimales=DECIMALES_CANTIDAD,
        maximo=CANTIDAD_MAXIMA,
        permitir_cero=False,
    )


def validar_id(valor: object, entidad: str) -> int:
    """Identificador de la base de datos: entero positivo."""
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValidacionError(f"El identificador de {entidad} no es válido")
    return valor


def validar_sin_productos_repetidos(producto_ids: list[int]) -> None:
    """Una venta incluye cada producto una sola vez (la base de datos también lo exige)."""
    if not producto_ids:
        raise ValidacionError("La venta debe incluir al menos un producto")
    if len(set(producto_ids)) != len(producto_ids):
        raise ValidacionError("Hay productos repetidos en la venta")
