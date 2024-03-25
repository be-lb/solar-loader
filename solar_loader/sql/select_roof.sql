SELECT
    --    r.id, st_astext(ST_DelaunayTriangles(r.{roof.geometry})), st_area(r.{roof.geometry})
    gml_id.id,
    st_astext(r.{roof.geometry}),
    st_area(r.{roof.geometry})
FROM
    {roof.table} r
WHERE
    gml_id = % s;