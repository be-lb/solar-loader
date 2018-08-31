

-- CREATE TABLE "solar"."results" (
--     id serial,
--     capakey varchar(18),
--     roof_id integer,
--     area decimal,
--     tilt decimal,
--     azimut decimal,
--     irradiance decimal
-- );

-- ALTER TABLE "solar"."results" ADD PRIMARY KEY (id);




INSERT INTO {results.table} 
    (capakey, roof_id, area, tilt, azimut, irradiance)
    VALUES (%s, %s, %s, %s, %s, %s);
