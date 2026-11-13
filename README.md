# AgroInventario

Sistema de inventario y ventas para una agrocomercial.
Python + Supabase (PostgreSQL) + pytest.

Arquitectura y decisiones: [docs/arquitectura.md](docs/arquitectura.md)

## Instalación (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env   # luego completa SUPABASE_URL y SUPABASE_KEY
```

## Base de datos

En Supabase > SQL Editor ejecuta `supabase/instalacion_completa.sql`
y luego `supabase/verificacion_etapa2.sql`.

## Pruebas

```powershell
pytest                       # todas
pytest -m "not integracion"  # solo unitarias (sin internet)
pytest -m integracion        # solo contra Supabase
```

## Estructura

```
src/inventario/    código de la aplicación
tests/unitarias/   pruebas aisladas con mocks
tests/integracion/ pruebas contra Supabase real
supabase/          scripts SQL
docs/              documentación
```
