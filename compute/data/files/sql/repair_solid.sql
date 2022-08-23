-- set all the solids in solar.solid_all
-- then create a version with the solids whithout error in 3D in solar.solid
BEGIN;

ALTER TABLE
    solar.solid RENAME TO solid_all;

COMMIT;

BEGIN;

CREATE TABLE solar.solid AS (
    SELECT
        *
    FROM
        solar.solid_all
    WHERE
        ST_isvalidreason(geom) NOT LIKE 'I%'
);

CREATE INDEX ON "solar"."solid" USING GIST ("geom");

COMMIT;

BEGIN;

DROP TABLE solid_all;

COMMIT;