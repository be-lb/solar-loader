<<<<<<< HEAD
SELECT
    r.id, st_astext(r.{roof.geometry}), st_area(r.{roof.geometry}), res.{results.irradiance}
=======
SELECT 
    r.gid, __conv_geom_operator__(r.{roof.geometry}), __conv_geom_operator__(r.{roof.centroid})
>>>>>>> master
FROM
    {roof.table} r
    JOIN (
        SELECT st_force2d({ground.geometry}) as geom
        FROM {ground.table}
        WHERE {ground.capakey} = %s
        ) g
    ON st_within(r.{roof.centroid}, g.geom)
    JOIN {results.table} res ON res.{results.roof_id} = r.id
