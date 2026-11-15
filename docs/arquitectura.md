# Arquitectura - Sistema de Inventario Agrocomercial

## 1. Requisitos funcionales

| ID | Requisito |
|---|---|
| RF-01 | Registrar producto (nombre, precio, cantidad) |
| RF-02 | Listar productos con su cantidad disponible |
| RF-03 | Actualizar nombre, precio o cantidad de un producto |
| RF-04 | Listar productos agotados (cantidad = 0) |
| RF-05 | Registrar venta con uno o varios productos |
| RF-06 | Descontar automáticamente el inventario vendido |
| RF-07 | Rechazar la venta completa si no hay existencias suficientes |
| RF-08 | Guardar fecha, productos, cantidades, precio unitario y total |
| RF-09 | Consultar ventas de un día |
| RF-10 | Total de ingresos por día |
| RF-11 | Productos vendidos y cantidades en un período |

**Reglas:** nombre obligatorio y único; precio > 0; cantidad >= 0 (decimales permitidos);
venta con al menos un producto y cantidades > 0; secretos solo en `.env`.

**Fuera de alcance (YAGNI):** roles y permisos, proveedores, compras, facturación.

**Requisitos de publicación (agregados en la Etapa 4):** sitio en HTTPS (Vercel), PWA instalable,
diseño responsive, SEO y Open Graph, headers de seguridad, página 404, robots.txt, healthcheck JSON,
login real y portal privado que no muestre datos sin sesión.

## 2. Modelo de datos (Supabase / PostgreSQL)

```
unidad_medida 1──N producto N──1 categoria
                      │1
                      N
venta 1──────N detalle_venta
```

| Tabla | Propósito |
|---|---|
| `unidad_medida` | lb, qq, kg, L, und |
| `categoria` | Agrupa productos |
| `producto` | Nombre, precio, cantidad `NUMERIC(12,3)` |
| `venta` | Fecha y total |
| `detalle_venta` | Producto, cantidad, `precio_unitario` copiado, `subtotal` calculado |

Decisiones:
- `NUMERIC` en lugar de `float` para evitar errores de redondeo.
- `CHECK` en la base de datos como última barrera (precio > 0, cantidad >= 0).
- Totales diarios se calculan con consultas, no se almacenan (DRY).
- `registrar_venta(jsonb)`: función atómica con `FOR UPDATE`; todo o nada.
  Códigos: `AG001` venta vacía, `AG002` cantidad inválida, `AG003` producto no existe,
  `AG004` stock insuficiente, `AG005` producto repetido.
- RLS activo sin políticas públicas; el backend usa la clave secreta.

Scripts en `supabase/migraciones/` (ejecutar en orden) o `supabase/instalacion_completa.sql`.

## 3. Capas de la aplicación

```
Web (FastAPI) → Servicios → (Validadores, Repositorios) → Cliente Supabase
Modelos: compartidos por todas las capas
```

Despliegue: `app.py` (raíz) expone la app de FastAPI para Vercel; `public/` lo sirve el CDN de Vercel;
`vercel.json` define los headers de seguridad. La interfaz web reemplaza a la CLI planeada originalmente.

| Capa | Responsabilidad |
|---|---|
| `modelos/` | Representar datos del dominio |
| `validadores/` | Verificar datos de entrada |
| `repositorios/` | Leer/escribir en Supabase, sin lógica de negocio |
| `servicios/` | Reglas de negocio; reciben repositorios por parámetro (mockeables) |
| `web/app.py` | Arma la aplicación: rutas, healthcheck, errores |
| `web/sesion.py` | Login, logout y dependencia `correo_requerido` |
| `web/autenticacion.py` | Habla con Supabase Auth (iniciar sesión, validar token) |
| `web/portal.py` | Portal privado; su repositorio depende de la sesión |
| `web/plantillas.py` | Configuración única de Jinja2 |
| `db/cliente.py` | Crear la conexión una sola vez |
| `config.py` | Leer `.env` |
| `errores.py` | Excepciones propias |

### Seguridad de la sesión

- Supabase Auth guarda las contraseñas cifradas; no se implementa un sistema propio.
- Cookie `sesion`: `HttpOnly` (JavaScript no la lee), `Secure` (solo HTTPS), `SameSite=Lax`, dura lo mismo que el token (1 h).
- Cada visita a `/portal` valida el token con Supabase. La dependencia del repositorio requiere sesión,
  así que sin sesión no se consulta la base de datos.
- El portal responde con `Cache-Control: no-store` y `noindex`.
- Auth usa un cliente de Supabase aparte para no alterar el cliente compartido que usa la clave del servidor.

## 4. Pruebas

- `tests/unitarias/`: sin internet, con mocks. `pytest -m "not integracion"`
- `tests/integracion/`: contra Supabase real; se omiten si no hay `.env`.

## 5. Git

GitHub Flow: `main` estable + ramas `feature/*`, `fix/*`, `chore/*` integradas por Pull Request.
Commits con Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`).

## 6. Bitácora de avances

| Etapa | Estado | Resultado |
|---|---|---|
| 1. Requisitos y arquitectura | ✅ | Este documento |
| 2. Base de datos | ✅ | 5 tablas, función de venta atómica, 58 productos, 7 verificaciones SQL |
| 3. Entorno Python + Git | ✅ | Config, conexión, CI con GitHub Actions, 12 pruebas |
| 4. Sitio web en Vercel | ✅ | FastAPI, PWA, SEO, headers, 404, healthcheck; 18/20 en la plataforma |
| 5. Login y portal privado | ✅ | Supabase Auth, cookie HttpOnly/Secure, portal protegido en servidor; 60 pruebas unitarias |
| 6. Modelos y validadores | ⏳ | |
| 7. Productos | ⏳ | |
| 8. Ventas | ⏳ | |
| 9. Reportes | ⏳ | |
