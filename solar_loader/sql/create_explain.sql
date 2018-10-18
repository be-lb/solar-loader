
-- DROP TABLE IF EXISTS solar.explain_res;
DROP TABLE IF EXISTS solar.explain_sh;
DROP TABLE IF EXISTS solar.polyhedrals;

TRUNCATE TABLE solar.explain_res;
-- CREATE TABLE  solar.explain_res (
--     id integer not null,
--     hour integer not null,
--     exposed  decimal not null
-- );
-- SELECT AddGeometryColumn('solar','explain_res','geom','31370','POLYGON', 3);

CREATE TABLE  solar.polyhedrals (
    hour integer not null
);
SELECT AddGeometryColumn('solar','polyhedrals','geom','31370','POLYHEDRALSURFACE', 3);


CREATE TABLE  solar.explain_sh (
    tid integer not null,
    shid  integer not null
);