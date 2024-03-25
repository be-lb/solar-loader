SELECT
    r.gml_id,
    st_astext(r.{ roof.geometry })
FROM
    { roof.table } r
ORDER BY
    r.gml_id OFFSET % s