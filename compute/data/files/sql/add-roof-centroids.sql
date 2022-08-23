SELECT
    AddGeometryColumn('solar', 'roof', 'pos', '31370', 'POINT', 2);

UPDATE
    solar.roof
SET
    pos = ST_PointOnSurface(ST_MakeValid(ST_Force2D(geom)));

--SELECT AddGeometryColumn('solar','ground','flat_geom','31370','MULTIPOLYGON',2);
--UPDATE solar.ground SET flat_geom = ST_CollectionExtract(ST_MakeValid(ST_Force2D(geom)), 3)	;