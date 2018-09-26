

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

-- CREATE TABLE "solar"."result" (
--     id serial,
--     roof_id character varying(50),
--     irradiance decimal
-- );


INSERT INTO  {results.table} 
    ({results.roof_id}, {results.irradiance})
    VALUES (%s, %s);
