
DROP TABLE IF EXISTS "solar"."radiation_5";
DROP INDEX IF EXISTS "solar_radiation_5_id_index";

CREATE TABLE "solar"."radiation_5" (
    id varchar(10), -- month day hour tilt azimut 
    tilt decimal,
    azimuth decimal,
    gk decimal,
    dk decimal
);

CREATE INDEX  "solar_radiation_5_id_index" ON "solar"."radiation_5" ("id");

