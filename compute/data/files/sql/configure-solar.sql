CREATE EXTENSION postgis;
CREATE SCHEMA solar;
SET postgis.backend = sfcgal;
ALTER DATABASE solar SET search_path = public,solar;
