-- =====================================================================
-- 004_politicas_y_exportacion.sql
-- 1) Políticas RLS explícitas: deja por escrito el modelo de acceso.
-- 2) Función exportar_esquema(): lee el catálogo de PostgreSQL y devuelve
--    tablas, columnas, llaves, índices, relaciones, políticas y filas en JSON.
-- Seguro de ejecutar más de una vez.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Políticas RLS
--
-- Modelo de acceso (ver docs/adr/ADR-002-autenticacion.md):
--   - Solo el servidor (clave service_role, que omite RLS) lee y escribe.
--   - Los roles de cliente de Supabase (anon y authenticated) NO acceden
--     directamente a las tablas, aunque alguien obtenga la clave pública
--     o un token de usuario: toda operación pasa por la aplicación.
--
-- Con RLS activo y sin políticas el acceso ya estaba denegado. Estas políticas
-- RESTRICTIVE lo vuelven explícito y lo mantienen aunque en el futuro alguien
-- agregue por error una política permisiva para esos roles.
-- ---------------------------------------------------------------------
do $$
declare
    v_tabla text;
begin
    foreach v_tabla in array array['unidad_medida', 'categoria', 'producto', 'venta', 'detalle_venta']
    loop
        execute format('drop policy if exists %I on public.%I', 'denegar_clientes_' || v_tabla, v_tabla);
        execute format(
            'create policy %I on public.%I as restrictive for all to anon, authenticated using (false) with check (false)',
            'denegar_clientes_' || v_tabla, v_tabla
        );
    end loop;
end $$;

-- ---------------------------------------------------------------------
-- 2. Exportación del esquema real
-- ---------------------------------------------------------------------
create or replace function public.exportar_esquema()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
declare
    v_tabla   record;
    v_filas   bigint;
    v_tablas  jsonb := '[]'::jsonb;
begin
    for v_tabla in
        select c.oid, c.relname, c.relrowsecurity
          from pg_class c
          join pg_namespace n on n.oid = c.relnamespace
         where n.nspname = 'public' and c.relkind = 'r'
         order by c.relname
    loop
        execute format('select count(*) from public.%I', v_tabla.relname) into v_filas;

        v_tablas := v_tablas || jsonb_build_object(
            'nombre', v_tabla.relname,
            'filas', v_filas,
            'rls_activo', v_tabla.relrowsecurity,
            'columnas', (
                select jsonb_agg(jsonb_build_object(
                           'nombre', a.attname,
                           'tipo', format_type(a.atttypid, a.atttypmod),
                           'pk', coalesce(a.attnum = any(pk.conkey), false),
                           'nulo', not a.attnotnull
                       ) order by a.attnum)
                  from pg_attribute a
                  left join pg_constraint pk on pk.conrelid = v_tabla.oid and pk.contype = 'p'
                 where a.attrelid = v_tabla.oid and a.attnum > 0 and not a.attisdropped
            ),
            'indices', (
                select coalesce(jsonb_agg(i.indexname order by i.indexname), '[]'::jsonb)
                  from pg_indexes i
                 where i.schemaname = 'public' and i.tablename = v_tabla.relname
            ),
            'relaciones', (
                select coalesce(jsonb_agg(jsonb_build_object(
                           'columna', a.attname,
                           'referencia', rt.relname || '.' || ra.attname
                       ) order by a.attname), '[]'::jsonb)
                  from pg_constraint fk
                  join pg_attribute a  on a.attrelid = fk.conrelid  and a.attnum = fk.conkey[1]
                  join pg_class rt     on rt.oid = fk.confrelid
                  join pg_attribute ra on ra.attrelid = fk.confrelid and ra.attnum = fk.confkey[1]
                 where fk.conrelid = v_tabla.oid and fk.contype = 'f'
            ),
            'politicas_rls', (
                select coalesce(jsonb_agg(p.policyname order by p.policyname), '[]'::jsonb)
                  from pg_policies p
                 where p.schemaname = 'public' and p.tablename = v_tabla.relname
            )
        );
    end loop;

    return jsonb_build_object(
        'motor', 'postgres',
        'version_motor', current_setting('server_version'),
        'tablas', v_tablas
    );
end;
$$;

-- Solo el backend puede ejecutarla: revela la estructura de la base de datos
revoke execute on function public.exportar_esquema() from public;
revoke execute on function public.exportar_esquema() from anon, authenticated;
grant  execute on function public.exportar_esquema() to service_role;
