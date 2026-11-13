-- =====================================================================
-- verificacion_etapa2.sql
-- Pruebas manuales de la base de datos. Todo corre dentro de una
-- transacción y termina en ROLLBACK: no deja cambios en tus datos.
-- Ejecutar completo en Supabase > SQL Editor y revisar los NOTICE.
-- =====================================================================
begin;

do $$
declare
    v_id_catosal bigint := (select id from producto where nombre = 'Catosal 100 ml');
    v_id_vitasel bigint := (select id from producto where nombre = 'Vitasel 100 ml');
    v_id_becafor bigint := (select id from producto where nombre = 'Decafor 100 ml');
    v_venta      bigint;
    v_total      numeric;
    v_stock      numeric;
    v_detalles   int;
begin
    -- Prueba 1: venta válida con decimales descuenta inventario
    v_venta := registrar_venta(jsonb_build_array(
        jsonb_build_object('producto_id', v_id_catosal, 'cantidad', 1),
        jsonb_build_object('producto_id', v_id_vitasel,   'cantidad', 2)
    ));
    select total into v_total from venta where id = v_venta;
    select cantidad into v_stock from producto where id = v_id_catosal;
    select count(*) into v_detalles from detalle_venta where venta_id = v_venta;
    assert v_total = 1670.00, format('Total esperado 1670.00, obtenido %s', v_total);  -- 1*950 + 2*360
    assert v_stock = 1,      format('Stock esperado 1, obtenido %s', v_stock);
    assert v_detalles = 2,   'Debe haber 2 detalles';
    raise notice 'OK 1: venta válida (total %, stock Catosal %)', v_total, v_stock;

    -- Prueba 2: stock insuficiente -> error y NO descuenta nada (atomicidad)
    begin
        perform registrar_venta(jsonb_build_array(
            jsonb_build_object('producto_id', v_id_catosal, 'cantidad', 1),  -- sí alcanza
            jsonb_build_object('producto_id', v_id_becafor,    'cantidad', 5)   -- Decafor: solo hay 1
        ));
        raise exception 'FALLO 2: debía rechazar la venta';
    exception when sqlstate 'AG004' then
        select cantidad into v_stock from producto where id = v_id_catosal;
        assert v_stock = 1, format('Catosal no debía cambiar: %s', v_stock);
        raise notice 'OK 2: stock insuficiente rechazado y sin descuentos parciales';
    end;

    -- Prueba 3: venta vacía
    begin
        perform registrar_venta('[]'::jsonb);
        raise exception 'FALLO 3';
    exception when sqlstate 'AG001' then
        raise notice 'OK 3: venta vacía rechazada';
    end;

    -- Prueba 4: cantidad negativa
    begin
        perform registrar_venta(jsonb_build_array(
            jsonb_build_object('producto_id', v_id_catosal, 'cantidad', -1)));
        raise exception 'FALLO 4';
    exception when sqlstate 'AG002' then
        raise notice 'OK 4: cantidad negativa rechazada';
    end;

    -- Prueba 5: producto inexistente
    begin
        perform registrar_venta('[{"producto_id": 999999, "cantidad": 1}]'::jsonb);
        raise exception 'FALLO 5';
    exception when sqlstate 'AG003' then
        raise notice 'OK 5: producto inexistente rechazado';
    end;

    -- Prueba 6: producto repetido
    begin
        perform registrar_venta(jsonb_build_array(
            jsonb_build_object('producto_id', v_id_catosal, 'cantidad', 1),
            jsonb_build_object('producto_id', v_id_catosal, 'cantidad', 2)));
        raise exception 'FALLO 6';
    exception when sqlstate 'AG005' then
        raise notice 'OK 6: producto repetido rechazado';
    end;

    -- Prueba 7: la tabla no permite stock negativo ni actualizándolo directo
    begin
        update producto set cantidad = -1 where id = v_id_catosal;
        raise exception 'FALLO 7';
    exception when check_violation then
        raise notice 'OK 7: la base de datos impide cantidades negativas';
    end;

    raise notice '=== TODAS LAS PRUEBAS PASARON ===';
end $$;

rollback;
