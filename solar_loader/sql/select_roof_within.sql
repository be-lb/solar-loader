SELECT 
    r.gid, __conv_geom_operator__(r.{roof.geometry}), __conv_geom_operator__(r.{roof.centroid})
FROM
    {roof.table} r
    CROSS JOIN (
        SELECT st_force2d({ground.geometry}) as geom
        FROM {ground.table}
        WHERE {ground.capakey} = %s
        LIMIT 1
        ) g
WHERE  st_within(r.{roof.centroid}, g.geom);
