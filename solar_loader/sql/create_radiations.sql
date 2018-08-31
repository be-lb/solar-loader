
DROP TABLE IF EXISTS "solar"."radiation_5";
DROP INDEX IF EXISTS "solar_radiation_5_tilt_index";
DROP INDEX IF EXISTS "solar_radiation_5_azimuth_index";

CREATE TABLE "solar"."radiation_5" (
    tilt decimal,
    azimuth decimal,
    irradiance decimal
);

CREATE INDEX  "solar_radiation_5_tilt_index" ON "solar"."radiation_5" ("tilt");
CREATE INDEX  "solar_radiation_5_azimuth_index" ON "solar"."radiation_5" ("azimuth");

