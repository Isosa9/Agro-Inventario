# AgroInventario

![Pruebas](https://github.com/Isosa9/Agro-Inventario/actions/workflows/pruebas.yml/badge.svg)

Sistema de inventario y ventas para una agrocomercial: productos veterinarios,
agroquímicos y concentrados que se venden por unidad o por peso (libras, quintales, litros).

**Código de verificación:** `LEARN-CAP-FE054BF4`

## Funcionalidades

**Inventario**
- Registrar productos con nombre, precio y cantidad disponible (admite decimales: 2.5 lb).
- Consultar productos y su existencia, actualizar sus datos e identificar productos agotados.

**Ventas**
- Registrar ventas de uno o varios productos.
- Descontar el inventario automáticamente y rechazar ventas sin existencias suficientes.
- Guardar fecha, productos, cantidades, precio unitario y total de cada venta.

**Reportes**
- Ventas por día, ingresos diarios y productos vendidos con sus cantidades.

## Tecnologías

| Herramienta | Uso |
|---|---|
| Python 3.11+ | Lenguaje principal |
| Supabase (PostgreSQL) | Base de datos |
| pytest | Pruebas unitarias y de integración |
| GitHub Actions | Integración continua (ejecuta las pruebas en cada push) |
| Git + GitHub Flow | Control de versiones con ramas y Pull Requests |

## Arquitectura

```
CLI → Servicios → (Validadores, Repositorios) → Cliente Supabase
```

- **Modelos:** representan los datos del dominio (`Producto`, `Venta`, `DetalleVenta`).
- **Validadores:** reglas de entrada (precio > 0, cantidad >= 0, venta no vacía).
- **Repositorios:** único lugar que lee y escribe en Supabase.
- **Servicios:** lógica de negocio; reciben los repositorios por parámetro para poder probarse con mocks.

La venta se registra con una **función atómica de PostgreSQL** (`registrar_venta`): valida existencias,
descuenta el inventario y guarda la venta en una sola transacción. Si un producto no alcanza, no se guarda nada.

Detalle completo en [docs/arquitectura.md](docs/arquitectura.md).

## Modelo de datos

```
unidad_medida 1──N producto N──1 categoria
                      │1
                      N
venta 1──────N detalle_venta
```

## Instalación (Windows / PowerShell)

```powershell
git clone https://github.com/Isosa9/Agro-Inventario.git
cd Agro-Inventario
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy env.example .env      # completar SUPABASE_URL y SUPABASE_KEY (clave secreta)
```

Base de datos: en Supabase > SQL Editor ejecutar `supabase/instalacion_completa.sql`
y luego `supabase/verificacion_etapa2.sql`.

## Pruebas

```powershell
pytest                       # todas
pytest -m "not integracion"  # solo unitarias (sin internet)
pytest -m integracion        # solo contra Supabase
```

Las pruebas de integración se omiten automáticamente si no existe el archivo `.env`.

## Estructura

```
src/inventario/        código de la aplicación
tests/unitarias/       pruebas aisladas con mocks
tests/integracion/     pruebas contra Supabase real
supabase/              scripts SQL (esquema, función de venta, datos)
docs/                  arquitectura y bitácora
.github/workflows/     integración continua
```

## Principios aplicados

SRP, DRY, KISS y YAGNI; validación en dos niveles (Python y restricciones de la base de datos);
secretos fuera del repositorio (`.env` en `.gitignore`).

## Avance

| Etapa | Estado |
|---|---|
| 1. Requisitos y arquitectura | ✅ |
| 2. Base de datos | ✅ |
| 3. Entorno, conexión y pruebas | ✅ |
| 4. Modelos y validadores | ⏳ |
| 5. Productos | ⏳ |
| 6. Ventas | ⏳ |
| 7. Reportes | ⏳ |
| 8. Interfaz de línea de comandos | ⏳ |
