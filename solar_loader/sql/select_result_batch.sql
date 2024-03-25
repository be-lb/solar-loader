SELECT
    res.roof_id,
    st_astext(ro.{ roof.geometry })
FROM
    { results.table } res
    LEFT JOIN { roof.table } ro ON res.roof_id = ro.gml_id
WHERE
    res.compute_status = 0
ORDER BY
    res.id
LIMIT
    % s;