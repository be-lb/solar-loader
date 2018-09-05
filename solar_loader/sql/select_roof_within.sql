SELECT
    r.id, st_astext(r.{roof.geometry}), st_area(r.{roof.geometry}), res.{results.irradiance}
FROM
    {roof.table} r
    JOIN (
        SELECT st_force2d({ground.geometry}) as geom
        FROM {ground.table}
        WHERE {ground.capakey} = %s
        ) g
    ON st_within(r.{roof.centroid}, g.geom)
    JOIN {results.table} res ON res.{results.roof_id} = r.id
