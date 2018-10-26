WITH polyhedrals (hour, geom) AS
    (VALUES %s )
SELECT
    solid.gid, st_astext(solid.{solid.geometry}), poly.hour
FROM
    {solid.table} solid
    INNER JOIN polyhedrals poly 
        ON ST_3DIntersects(poly.geom, solid.{solid.geometry});

