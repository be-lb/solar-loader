SELECT 
    r.gid, __conv_geom_operator__(r.{roof.geometry}), st_area(r.{roof.geometry})
FROM
    {roof.table} r
WHERE  gid = %s;