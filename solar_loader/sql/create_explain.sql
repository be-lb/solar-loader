
DROP TABLE IF EXISTS solar.explain_res CASCADE;
DROP TABLE IF EXISTS solar.explain_sh CASCADE;
DROP TABLE IF EXISTS solar.explain_s CASCADE;
DROP TABLE IF EXISTS solar.polyhedrals CASCADE;
DROP TABLE IF EXISTS solar.tesselated CASCADE;

CREATE TABLE  solar.explain_res (
    id integer not null,
    idx integer not null,
    hour integer not null,
    exposed  decimal not null
);
SELECT AddGeometryColumn('solar','explain_res','geom','31370','POLYGON', 3);

CREATE TABLE  solar.polyhedrals (
    hour integer not null,
    request text
);
SELECT AddGeometryColumn('solar','polyhedrals','geom','31370','POLYHEDRALSURFACE', 3);

CREATE TABLE  solar.explain_s (
    hour integer not null,
    stype text
);
SELECT AddGeometryColumn('solar','explain_s','geom','31370','POLYGON', 3);

CREATE TABLE solar.tesselated (
	id integer not null
);
SELECT AddGeometryColumn('solar','tesselated','geom','31370','POLYGON', 3);

CREATE TABLE  solar.explain_sh (
    tid integer not null,
    shid  integer not null
);

SET postgis.backend = geos;
