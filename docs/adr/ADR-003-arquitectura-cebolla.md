# ADR-003: Organizar el código en anillos (dominio, casos de uso, adaptadores) con puertos

- **Estado:** Aceptada
- **Fecha:** 2026-11-25
- **Etapa:** después de la Etapa 6 (modelos y validadores), antes de la Etapa 7 (productos)

## Contexto

Las Etapas 7 a 9 agregarán la lógica principal: registrar y editar productos, vender y generar reportes.
Antes de escribirla se revisó el código con la **regla de la cebolla** (arquitectura hexagonal o de
puertos y adaptadores, de Alistair Cockburn): las dependencias deben apuntar siempre hacia el centro,
y el centro no debe saber que el borde existe.

Situación encontrada:

- `modelos/` y `validadores/` ya eran puros (solo Python estándar), pero vivían en carpetas que no
  mostraban que son el **centro**.
- El portal usaba directamente `ProductoRepositorio`, que depende del SDK de Supabase. No había un
  **puerto** que dijera qué necesita el negocio, así que la lógica quedaba atada a Supabase.
- Para probar lógica que usa datos había que simular el cliente de Supabase con mocks encadenados
  (`table().select().eq()...`), frágiles y difíciles de leer.
- Nada impedía que, por error, alguien importara Supabase o FastAPI dentro de las reglas del negocio.

## Decisión

**Organizar el código en anillos (dominio, casos de uso, adaptadores) con puertos.**

```
src/inventario/
├── dominio/        🎯 Producto, Venta, reglas.py y puertos.py (RepositorioProductos)
├── casos_de_uso/   ⚙️ obtener_resumen_inventario(repositorio) …
├── adaptadores/    🧱 RepositorioProductosSupabase, RepositorioProductosEnMemoria
├── web/            🧱 adaptador de entrada (FastAPI)
└── db/             🧱 conexión a Supabase
```

1. **Dominio:** `modelos/` y `validadores/` pasan a `dominio/`. Se agrega `puertos.py` con
   `RepositorioProductos`, un `Protocol` que declara solo los métodos que el sistema usa hoy.
2. **Casos de uso:** reciben el repositorio **por parámetro**, como `obtener_resumen_inventario(repositorio)`.
   No saben si los datos vienen de Supabase o de memoria.
3. **Adaptadores:** `RepositorioProductosSupabase` (producción) y `RepositorioProductosEnMemoria`
   (pruebas) implementan el mismo puerto.
4. **El portal llama al caso de uso**, no al repositorio. El adaptador real se elige en un solo lugar:
   la dependencia `repositorio_productos` de `web/portal.py`.
5. **Prueba de arquitectura** (`tests/unitarias/test_arquitectura.py`): lee los imports de cada archivo
   y falla si el dominio o los casos de uso importan algo de un anillo exterior. Corre en el CI en cada PR.

## Ejemplos del curso que NO se implementaron (y por qué)

| Ejemplo | Decisión | Razón |
|---|---|---|
| Mover `web/` y `db/` dentro de `adaptadores/` | No por ahora | Sus dependencias ya apuntan hacia adentro. Moverlos cambiaría muchos archivos y pruebas sin beneficio funcional (KISS). Están documentados como adaptadores. |
| Puerto para la autenticación | No | Hay una sola implementación (Supabase Auth) y las pruebas ya la reemplazan con mocks. Un puerto sin un segundo uso sería abstracción especulativa (YAGNI). |
| Puerto `RepositorioVentas` | En la Etapa 8 | Todavía no hay código que registre ventas desde Python. Se creará cuando exista el caso de uso que lo necesite. |
| Métodos `listar`, `guardar`, `buscar` en el puerto | En la Etapa 7 | El puerto crece con los casos de uso reales, no antes. |
| Contenedor de inyección de dependencias | No | `Depends` de FastAPI ya inyecta el adaptador; agregar una librería sería complejidad sin necesidad. |
| Separar entidades del dominio de un ORM | No aplica | El proyecto no usa ORM: Supabase devuelve diccionarios y el adaptador los traduce. |

## Consecuencias

### Positivas

- **Pruebas de casos de uso rápidas y legibles:** con `RepositorioProductosEnMemoria` no hacen falta
  internet, Supabase ni mocks encadenados.
- **El negocio no depende de Supabase:** cambiar de proveedor implicaría escribir un adaptador nuevo,
  sin tocar el dominio ni los casos de uso.
- **La regla de la cebolla se verifica sola:** si alguien rompe la dirección de las dependencias, el CI falla.
- La estructura de carpetas **muestra la arquitectura** a quien abre el proyecto.

### Negativas (lo que se sacrificó)

- **Más archivos y más indirección:** para entender el portal hay que seguir web → caso de uso →
  puerto → adaptador.
- **Hay que mantener dos adaptadores** en sincronía con el puerto; una prueba verifica que ambos tengan
  los métodos del puerto.
- **El repositorio en memoria no reproduce todo lo que hace la base de datos** (por ejemplo, la función
  atómica `registrar_venta`). Esas reglas se siguen probando con pruebas de integración contra Supabase.
