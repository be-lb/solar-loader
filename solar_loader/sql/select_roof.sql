SELECT
    r.id, st_astext(r.{roof.geometry}), st_area(r.{roof.geometry})
FROM
    {roof.table} r
WHERE  id = %s;
