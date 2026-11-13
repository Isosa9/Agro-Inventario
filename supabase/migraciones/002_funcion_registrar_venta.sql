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
