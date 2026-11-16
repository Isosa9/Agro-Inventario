-- instalacion_completa.sql = 001 + 002 + 003 + 004 en un solo archivo (para pegar una sola vez)

-- =====================================================================
-- 001_esquema_inicial.sql
-- Sistema de inventario - Agrocomercial
-- Crea las 5 tablas del dominio y activa la seguridad a nivel de fila.
-- Ejecutar en: Supabase > SQL Editor (en orden: 001, 002, 003)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. unidad_medida: en qué se mide y vende cada producto (lb, qq, kg...)
-- ---------------------------------------------------------------------
create table public.unidad_medida (
    id           bigint generated always as identity primary key,
    nombre       text not null unique check (length(trim(nombre)) > 0),
    abreviatura  text not null unique check (length(trim(abreviatura)) > 0)
);

-- ---------------------------------------------------------------------
-- 2. categoria: agrupa productos (Concentrados, Semillas, ...)
-- ---------------------------------------------------------------------
create table public.categoria (
    id      bigint generated always as identity primary key,
    nombre  text not null unique check (length(trim(nombre)) > 0)
);

-- ---------------------------------------------------------------------
-- 3. producto: lo que se vende y su existencia actual
--    cantidad es NUMERIC(12,3): permite 2.5 lb o 0.125 qq
-- ---------------------------------------------------------------------
create table public.producto (
    id                bigint generated always as identity primary key,
    nombre            text not null unique check (length(trim(nombre)) > 0),
    precio            numeric(12,2) not null check (precio > 0),
    cantidad          numeric(12,3) not null default 0 check (cantidad >= 0),
    categoria_id      bigint not null references public.categoria(id) on delete restrict,
    unidad_medida_id  bigint not null references public.unidad_medida(id) on delete restrict,
    creado_en         timestamptz not null default now()
);

create index idx_producto_categoria on public.producto(categoria_id);
create index idx_producto_unidad    on public.producto(unidad_medida_id);

-- ---------------------------------------------------------------------
-- 4. venta: encabezado de cada venta
-- ---------------------------------------------------------------------
create table public.venta (
    id     bigint generated always as identity primary key,
    fecha  timestamptz not null default now(),
    total  numeric(12,2) not null default 0 check (total >= 0)
);

create index idx_venta_fecha on public.venta(fecha);

-- ---------------------------------------------------------------------
-- 5. detalle_venta: cada producto dentro de una venta
--    precio_unitario se COPIA del producto al vender (historial fiel)
--    subtotal lo calcula la base de datos (no se puede desincronizar)
-- ---------------------------------------------------------------------
create table public.detalle_venta (
    id               bigint generated always as identity primary key,
    venta_id         bigint not null references public.venta(id) on delete cascade,
    producto_id      bigint not null references public.producto(id) on delete restrict,
    cantidad         numeric(12,3) not null check (cantidad > 0),
    precio_unitario  numeric(12,2) not null check (precio_unitario > 0),
    subtotal         numeric(12,2) generated always as (round(cantidad * precio_unitario, 2)) stored,
    unique (venta_id, producto_id)
);

create index idx_detalle_producto on public.detalle_venta(producto_id);

-- ---------------------------------------------------------------------
-- Seguridad: RLS activado SIN políticas públicas.
-- La clave pública (anon) no puede leer ni escribir nada.
-- La app Python usa la clave service_role (guardada en .env, nunca en Git).
-- ---------------------------------------------------------------------
alter table public.unidad_medida enable row level security;
alter table public.categoria     enable row level security;
alter table public.producto      enable row level security;
alter table public.venta         enable row level security;
alter table public.detalle_venta enable row level security;

-- =====================================================================
-- 002_funcion_registrar_venta.sql
-- Registra una venta de forma ATÓMICA: valida stock, descuenta inventario
-- y guarda encabezado + detalles en una sola transacción.
-- Si cualquier producto falla, NO se guarda nada (todo o nada).
--
-- Uso:  select public.registrar_venta('[{"producto_id":1,"cantidad":2.5}]');
-- Devuelve: id de la venta creada.
--
-- Códigos de error propios (Python los traducirá a excepciones):
--   AG001  venta sin productos o con formato inválido
--   AG002  cantidad inválida (<= 0)
--   AG003  producto no existe
--   AG004  stock insuficiente
--   AG005  producto repetido en la misma venta
-- =====================================================================

create or replace function public.registrar_venta(p_items jsonb)
returns bigint
language plpgsql
set search_path = public
as $$
declare
    v_venta_id  bigint;
    v_item      record;
    v_producto  record;
begin
    if p_items is null
       or jsonb_typeof(p_items) <> 'array'
       or jsonb_array_length(p_items) = 0 then
        raise exception 'La venta debe incluir al menos un producto'
            using errcode = 'AG001';
    end if;

    if (select count(distinct (e->>'producto_id')) from jsonb_array_elements(p_items) e)
       <> jsonb_array_length(p_items) then
        raise exception 'Hay productos repetidos en la venta'
            using errcode = 'AG005';
    end if;

    insert into venta default values returning id into v_venta_id;

    -- Orden por producto_id: evita bloqueos cruzados entre ventas simultáneas
    for v_item in
        select (e->>'producto_id')::bigint  as producto_id,
               (e->>'cantidad')::numeric    as cantidad
        from jsonb_array_elements(p_items) e
        order by 1
    loop
        if v_item.cantidad is null or v_item.cantidad <= 0 then
            raise exception 'Cantidad inválida para el producto %', v_item.producto_id
                using errcode = 'AG002';
        end if;

        -- FOR UPDATE bloquea la fila: dos ventas no pueden vender el mismo stock
        select id, nombre, precio, cantidad
          into v_producto
          from producto
         where id = v_item.producto_id
           for update;

        if not found then
            raise exception 'El producto % no existe', v_item.producto_id
                using errcode = 'AG003';
        end if;

        if v_producto.cantidad < v_item.cantidad then
            raise exception 'Stock insuficiente para "%": disponible %, solicitado %',
                v_producto.nombre, v_producto.cantidad, v_item.cantidad
                using errcode = 'AG004';
        end if;

        update producto
           set cantidad = cantidad - v_item.cantidad
         where id = v_item.producto_id;

        insert into detalle_venta (venta_id, producto_id, cantidad, precio_unitario)
        values (v_venta_id, v_item.producto_id, v_item.cantidad, v_producto.precio);
    end loop;

    update venta
       set total = (select coalesce(sum(subtotal), 0)
                      from detalle_venta where venta_id = v_venta_id)
     where id = v_venta_id;

    return v_venta_id;
end;
$$;

-- Solo el backend (service_role) puede ejecutar la función
revoke execute on function public.registrar_venta(jsonb) from public;
revoke execute on function public.registrar_venta(jsonb) from anon, authenticated;
grant  execute on function public.registrar_venta(jsonb) to service_role;

-- =====================================================================
-- 003_datos_iniciales.sql
-- Catálogos base e inventario real (fuente: Inventario_Agrocomercial.xlsx).
-- Generado con gen_seed.py. Precios en Lempiras por unidad.
-- Productos: 58. Omitidos por no tener precio: Biofolamin.
--
-- Es seguro ejecutarlo más de una vez:
--   - unidades y categorías existentes no se duplican
--   - si un producto ya existe (mismo nombre) se actualizan sus datos
-- =====================================================================

insert into public.unidad_medida (nombre, abreviatura) values
    ('Libra', 'lb'), ('Quintal', 'qq'), ('Kilogramo', 'kg'), ('Litro', 'L'), ('Unidad', 'und')
on conflict do nothing;

insert into public.categoria (nombre) values
    ('Concentrados'), ('Semillas'), ('Fertilizantes'), ('Agroquímicos'), ('Herramientas'),
    ('Vitaminas y minerales'), ('Antibióticos'), ('Analgésicos y antiinflamatorios'),
    ('Antiparasitarios'), ('Otros medicamentos')
on conflict do nothing;

insert into public.producto (nombre, precio, cantidad, categoria_id, unidad_medida_id)
select p.nombre, p.precio, p.cantidad, c.id, u.id
from (values
    ('Catosal 100 ml',                 950.00,  2, 'Vitaminas y minerales',           'und'),
    ('Vitasel 50 ml',                  270.00,  3, 'Vitaminas y minerales',           'und'),
    ('Vitasel 100 ml',                 360.00,  2, 'Vitaminas y minerales',           'und'),
    ('Minerales 100 ml',               260.00,  2, 'Vitaminas y minerales',           'und'),
    ('Decafor 100 ml',                 320.00,  1, 'Vitaminas y minerales',           'und'),
    ('VitaDunkel 10 ml',                90.00,  2, 'Vitaminas y minerales',           'und'),
    ('Univit B12 50 ml',               190.00,  3, 'Vitaminas y minerales',           'und'),
    ('Max-Hierro 20% 20 ml',           130.00,  2, 'Vitaminas y minerales',           'und'),
    ('Max-Hierro 10% 10 ml',           100.00,  1, 'Vitaminas y minerales',           'und'),
    ('Caloi 50 ml',                    220.00,  2, 'Vitaminas y minerales',           'und'),
    ('Diurivet 10 ml',                 140.00,  3, 'Otros medicamentos',              'und'),
    ('Emicina 20 ml',                  140.00,  2, 'Antibióticos',                    'und'),
    ('Emicina 50 ml',                  260.00,  2, 'Antibióticos',                    'und'),
    ('Emicina L/A 20 ml',              350.00,  2, 'Antibióticos',                    'und'),
    ('Synedem 25 ml',                  280.00,  2, 'Otros medicamentos',              'und'),
    ('Furodex 10 ml',                  120.00,  3, 'Otros medicamentos',              'und'),
    ('Diclofenaco 50 ml',              300.00,  1, 'Analgésicos y antiinflamatorios', 'und'),
    ('Biodipirona 20 ml',              130.00,  3, 'Analgésicos y antiinflamatorios', 'und'),
    ('Biodipirona 100 ml',             250.00,  1, 'Analgésicos y antiinflamatorios', 'und'),
    ('Oxitetraciclina L/A 20 ml',      110.00,  2, 'Antibióticos',                    'und'),
    ('Oxitetraciclina L/A 50 ml',      200.00,  2, 'Antibióticos',                    'und'),
    ('Neodip 20 ml',                   100.00,  1, 'Analgésicos y antiinflamatorios', 'und'),
    ('Neodip 100 ml',                  225.00,  2, 'Analgésicos y antiinflamatorios', 'und'),
    ('Pentagol Reforzado 6,000,000',   270.00,  3, 'Antibióticos',                    'und'),
    ('Pentagol Reforzado 12,000,000',  380.00,  3, 'Antibióticos',                    'und'),
    ('Fibrocine 50 ml',                350.00,  2, 'Otros medicamentos',              'und'),
    ('Flogidem 10 ml',                 150.00,  3, 'Analgésicos y antiinflamatorios', 'und'),
    ('Ethiotil 125 ml',                300.00,  3, 'Antiparasitarios',                'und'),
    ('Torsavet 120 ml',                190.00,  3, 'Otros medicamentos',              'und'),
    ('Impacto Ourofino 100 ml',        340.00,  2, 'Antiparasitarios',                'und'),
    ('Paredón 20 ml',                  100.00,  1, 'Antiparasitarios',                'und'),
    ('Paredón 120 ml',                 250.00,  2, 'Antiparasitarios',                'und'),
    ('Fulminado 20 ml',                100.00,  2, 'Antiparasitarios',                'und'),
    ('Fulminado 100 ml',               250.00,  1, 'Antiparasitarios',                'und'),
    ('Ultrametrin 100 ml',             330.00,  2, 'Antiparasitarios',                'und'),
    ('Fortemil 500 ml',                345.00,  6, 'Otros medicamentos',              'und'),
    ('Amidan 500 ml',                  250.00,  1, 'Antiparasitarios',                'und'),
    ('Purguing 350 g',                 120.00,  3, 'Antiparasitarios',                'und'),
    ('Adecto 100 ml',                  295.00,  2, 'Otros medicamentos',              'und'),
    ('Pilocarpina 15 ml',              140.00,  2, 'Otros medicamentos',              'und'),
    ('Albendazol 100 ml',              230.00,  1, 'Antiparasitarios',                'und'),
    ('Ivermectina 100 ml',             270.00,  1, 'Antiparasitarios',                'und'),
    ('Febenzol 25 ml',                 110.00,  2, 'Antiparasitarios',                'und'),
    ('Iverhorse 6.42 g',               180.00,  1, 'Antiparasitarios',                'und'),
    ('Nicofol Plus',                   510.00,  3, 'Agroquímicos',                    'und'),
    ('Espuela Galón',                  600.00,  1, 'Agroquímicos',                    'und'),
    ('Espuela Litro',                  230.00,  3, 'Agroquímicos',                    'und'),
    ('Totem Litro',                    750.00,  2, 'Agroquímicos',                    'und'),
    ('Elimina Litro',                  745.00,  5, 'Agroquímicos',                    'und'),
    ('Paraquat Litro',                 150.00,  3, 'Agroquímicos',                    'und'),
    ('Paraquat Galón',                 680.00,  1, 'Agroquímicos',                    'und'),
    ('Root Out Litro',                 300.00,  3, 'Agroquímicos',                    'und'),
    ('Root Out Galón',                 590.00,  1, 'Agroquímicos',                    'und'),
    ('Roundup Litro',                  230.00,  2, 'Agroquímicos',                    'und'),
    ('Curagro',                        750.00,  2, 'Agroquímicos',                    'und'),
    ('Cipermetrina',                   760.00,  2, 'Agroquímicos',                    'und'),
    ('Dupla',                          280.00,  3, 'Agroquímicos',                    'und'),
    ('Mancuerna',                      350.00,  3, 'Agroquímicos',                    'und')
) as p(nombre, precio, cantidad, categoria, unidad)
join public.categoria     c on c.nombre      = p.categoria
join public.unidad_medida u on u.abreviatura = p.unidad
on conflict (nombre) do update
    set precio           = excluded.precio,
        cantidad         = excluded.cantidad,
        categoria_id     = excluded.categoria_id,
        unidad_medida_id = excluded.unidad_medida_id;

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
