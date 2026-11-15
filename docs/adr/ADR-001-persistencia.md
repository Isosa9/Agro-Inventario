# ADR-001: Usar PostgreSQL gestionado en Supabase con la venta como transacción atómica en la base de datos

- **Estado:** Aceptada
- **Fecha:** 2026-11-13
- **Etapa:** 2 (diseño de la base de datos)

## Contexto

La agrocomercial necesita controlar existencias y registrar ventas de productos que se venden
por unidad y por peso (por ejemplo, 2.5 lb de concentrado). Condiciones del negocio y del proyecto:

- **Nunca vender lo que no hay.** Si dos ventas del mismo producto ocurren casi al mismo tiempo,
  o si una venta de varios productos falla a la mitad, el inventario no puede quedar negativo ni a medias.
- **Cantidades decimales exactas.** Con `float`, `0.1 + 0.2` no da `0.3`; en inventario eso genera
  existencias "fantasma" y totales mal calculados.
- **Sin personal técnico.** Nadie en el negocio puede administrar un servidor de base de datos,
  aplicar parches ni hacer respaldos a mano.
- **Acceso desde varios dispositivos.** La dueña usa el celular en la tienda y otra persona
  puede usar una computadora: los datos deben estar centralizados en internet.
- **Requisito tecnológico del proyecto:** Supabase (PostgreSQL) y despliegue en Vercel, donde
  las funciones son *serverless* y no tienen disco permanente.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| SQLite embebido en la aplicación | Vercel no conserva archivos entre ejecuciones: los datos se perderían. Tampoco permite acceso concurrente desde varios dispositivos. |
| PostgreSQL en un servidor propio (VPS) | Requiere administrar el servidor, la seguridad y los respaldos; no hay quién lo haga en el negocio. |
| Validar el stock y descontar desde Python con varias consultas | Entre "consultar existencia" y "descontar" otra venta puede colarse (condición de carrera); un fallo intermedio deja la venta a medias. |

## Decisión

**Usar PostgreSQL gestionado en Supabase con la venta como transacción atómica en la base de datos.**

1. Los datos viven en PostgreSQL gestionado por Supabase (5 tablas: `unidad_medida`, `categoria`,
   `producto`, `venta`, `detalle_venta`).
2. Precios y cantidades usan `NUMERIC(12,2)` y `NUMERIC(12,3)`, no `float`.
3. Las reglas críticas se refuerzan con restricciones `CHECK` (precio > 0, cantidad >= 0) como última barrera,
   además de las validaciones en Python.
4. Toda venta se registra con la función `registrar_venta(jsonb)`, que en **una sola transacción**
   bloquea cada producto con `SELECT ... FOR UPDATE`, verifica existencias, descuenta el inventario
   y guarda la venta con sus detalles. Si un producto no alcanza, no se guarda nada.
   Los productos se bloquean en orden de `id` para evitar bloqueos cruzados.
5. La función devuelve códigos de error propios (`AG001`–`AG005`) que Python traduce a mensajes claros.
6. RLS activado sin políticas públicas: solo el servidor, con la clave secreta, accede a los datos.

## Consecuencias

### Positivas

- **Imposible vender sin existencias**, aun con ventas simultáneas: lo garantiza PostgreSQL, no la suerte.
- Cantidades y dinero exactos.
- Sin servidor que mantener: Supabase se encarga de actualizaciones y disponibilidad.
- Los datos están en un solo lugar, accesibles desde cualquier dispositivo con internet.
- La misma plataforma provee la autenticación (ver [ADR-002](ADR-002-autenticacion.md)).

### Negativas (lo que se sacrificó)

- **Dependencia de un proveedor externo.** Si Supabase falla, el sistema no funciona; migrar a otro
  proveedor exige trasladar datos y la función SQL. Se mitiga porque es PostgreSQL estándar: el esquema
  y la función funcionan en cualquier PostgreSQL.
- **Requiere internet.** Sin conexión no se pueden registrar ventas; la PWA solo muestra una página
  de "sin conexión".
- **Parte de la lógica de negocio está en SQL**, no en Python. La función `registrar_venta` no se prueba
  con pytest unitario sino con `supabase/verificacion_etapa2.sql` y pruebas de integración, y requiere
  saber PL/pgSQL para modificarla.
- **Límites del plan gratuito:** el proyecto se pausa tras una semana sin actividad y no incluye respaldos
  automáticos. Para uso comercial continuo conviene el plan de pago.

### Seguimiento

- Agregar pruebas de integración de `registrar_venta` desde Python en la Etapa 8 (ventas).
- Revisar el plan de Supabase antes de que el negocio dependa del sistema a diario.
