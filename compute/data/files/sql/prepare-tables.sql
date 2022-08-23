-- generated with
-- for what in Ground Roof Solid Wall; do echo "-- solar.${what}" && shp2pgsql -s 31370 -p -g geom -I  bbb/shp/UrbAdm3D_142166_Bu_${what}.shp solar.${what} 2> /dev/null ; done
SET
    CLIENT_ENCODING TO UTF8;

SET
    STANDARD_CONFORMING_STRINGS TO ON;

CREATE SCHEMA "solar";

-- solar.Roof
BEGIN;

CREATE TABLE "solar"."roof" (
    gid serial,
    "id" varchar(50),
    "lod" int2,
    "parent_id" varchar(254)
);

ALTER TABLE
    "solar"."roof"
ADD
    PRIMARY KEY (gid);

SELECT
    AddGeometryColumn(
        'solar',
        'roof',
        'geom',
        '31370',
        'MULTIPOLYGON',
        4
    );

CREATE INDEX ON "solar"."roof" USING GIST ("geom");

COMMIT;

ANALYZE "solar"."roof";

-- solar.Solid
BEGIN;

CREATE TABLE "solar"."solid" (
    gid serial,
    "id" numeric,
    "lod" int2,
    "parent_id" varchar(254)
);

ALTER TABLE
    "solar"."solid"
ADD
    PRIMARY KEY (gid);

SELECT
    AddGeometryColumn(
        'solar',
        'solid',
        'geom',
        '31370',
        'MULTIPOLYGON',
        4
    );

CREATE INDEX ON "solar"."solid" USING GIST ("geom");

COMMIT;

ANALYZE "solar"."solid";

-- -- generated with 
-- --  shp2pgsql -s 31370 -p  -I cadastre/cadastre.shp solar.cadastre
-- BEGIN;
-- CREATE TABLE "solar"."cadastre" (
--     gid serial,
--     "__gid" numeric(10, 0),
--     "capakey" varchar(18),
--     "apnc_mapc" varchar(50),
--     "bruenvi_cr" date,
--     "bruenvi_mo" date,
--     "bruenvi_au" varchar(20)
-- );
-- ALTER TABLE
--     "solar"."cadastre"
-- ADD
--     PRIMARY KEY (gid);
-- SELECT
--     AddGeometryColumn(
--         'solar',
--         'cadastre',
--         'geom',
--         '31370',
--         'MULTIPOLYGON',
--         2
--     );
-- CREATE INDEX ON "solar"."cadastre" USING GIST ("geom");
-- COMMIT;
-- ANALYZE "solar"."cadastre";