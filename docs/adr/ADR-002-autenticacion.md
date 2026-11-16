# ADR-002: Usar Supabase Auth con sesión en cookie HttpOnly validada en el servidor

- **Estado:** Aceptada
- **Fecha:** 2026-11-15
- **Etapa:** 5 (login y portal privado)

## Contexto

El portal muestra el inventario y, en las próximas etapas, permitirá cambiar precios y registrar ventas.
Solo la dueña y personas autorizadas deben acceder. Condiciones:

- **Sistema interno:** no debe existir registro público; las cuentas las crea quien administra.
- **Cada persona con su propia cuenta**, para poder quitar el acceso a alguien sin afectar a los demás.
- **Las contraseñas no se pueden guardar en texto plano** ni con un cifrado casero.
- **El portal no puede filtrar datos sin sesión:** no basta con ocultarlos con JavaScript; quien no
  inició sesión no debe recibirlos.
- La aplicación se renderiza en el servidor (FastAPI + Jinja2) y se publica en Vercel.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Sistema de usuarios propio (tabla + hash de contraseñas) | Reimplementa algo delicado: hashing, límites de intentos, recuperación de cuenta. Más código y más riesgo. |
| Token guardado en `localStorage` y enviado por JavaScript | Cualquier script inyectado (XSS) podría leerlo y robar la sesión; además el portal tendría que cargarse vacío y pedir los datos después. |
| Protección con contraseña de Vercel | Es una sola contraseña compartida, no distingue usuarios y no está disponible en el plan gratuito. |

## Decisión

**Usar Supabase Auth con sesión en cookie HttpOnly validada en el servidor.**

1. Las cuentas se crean en Supabase Auth (correo y contraseña). El registro público está **desactivado**
   (*Allow new users to sign up = off*): sin esto, cualquiera con la clave pública podría crearse una cuenta
   por la API de Supabase y entrar al portal.
2. `POST /login` envía las credenciales a Supabase Auth desde el servidor. Si son correctas, la respuesta
   guarda el token de acceso en la cookie `sesion` con `HttpOnly`, `Secure`, `SameSite=Lax` y la misma
   duración que el token (1 hora).
3. Cada petición a una página privada valida el token con Supabase en el servidor
   (dependencia `correo_requerido`). Si no es válido, responde `303` a `/login` **sin consultar la base de datos**:
   el repositorio del portal depende de la sesión.
4. Mensaje de error genérico ("Correo o contraseña incorrectos") para no revelar qué cuentas existen.
5. El portal responde con `Cache-Control: no-store` y `noindex`.
6. Auth usa un cliente de Supabase distinto del cliente de datos, para que iniciar sesión no cambie
   las credenciales con las que el servidor consulta la base de datos.

## Consecuencias

### Positivas

- Contraseñas cifradas y límites de intentos gestionados por Supabase, sin código propio.
- JavaScript no puede leer la cookie, lo que reduce el impacto de un posible XSS.
- Los datos privados nunca salen del servidor sin una sesión válida.
- Agregar o quitar personas es una acción en el panel de Supabase.
- Todo en el mismo proveedor que la base de datos (ver [ADR-001](ADR-001-persistencia.md)).

### Negativas (lo que se sacrificó)

- **La sesión vence a la hora** y hay que volver a ingresar: no se implementó la renovación con
  *refresh token* para mantener la solución simple.
- **Cada visita al portal hace una llamada a Supabase Auth** para validar el token (unos milisegundos más).
- **Sin recuperación de contraseña ni invitaciones por correo** por ahora: si alguien olvida su contraseña,
  quien administra la cambia desde el panel de Supabase.
- **Sin roles:** todas las cuentas tienen los mismos permisos.

### Seguimiento

- Si las sesiones cortas molestan en el uso diario, implementar renovación con *refresh token*.
- Si el negocio contrata empleados, evaluar roles (por ejemplo, vender sin poder cambiar precios).
