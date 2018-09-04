SELECT 
    r.id, __conv_geom_operator__(r.{roof.geometry})
FROM
    {roof.table} r LIMIT 124;
