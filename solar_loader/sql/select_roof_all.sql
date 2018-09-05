SELECT
    r.id, st_astext(r.{roof.geometry})
FROM
    {roof.table} r LIMIT 124;
