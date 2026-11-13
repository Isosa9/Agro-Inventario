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
