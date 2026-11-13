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
