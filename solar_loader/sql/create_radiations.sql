
DROP TABLE IF EXISTS "solar"."radiation_5";
DROP INDEX IF EXISTS "solar_radiation_5_tilt_index";
DROP INDEX IF EXISTS "solar_radiation_5_azimuth_index";
DROP INDEX IF EXISTS "solar_radiation_5_timestamp_index";

CREATE TABLE "solar"."radiation_5" (
    tilt decimal,
    azimuth decimal,
    ts timestamp with timezone,
    gk decimal,
    bk decimal
);

CREATE INDEX  "solar_radiation_5_tilt_index" ON "solar"."radiation_5" ("tilt");
CREATE INDEX  "solar_radiation_5_azimuth_index" ON "solar"."radiation_5" ("azimuth");
CREATE INDEX  "solar_radiation_5_timestamp_index" ON "solar"."radiation_5" ("ts");

