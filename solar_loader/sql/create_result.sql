
DROP TABLE IF EXISTS "solar"."result";

CREATE TABLE "solar"."result" (
    id serial,
    roof_id character varying(50),
    irradiance decimal
);

