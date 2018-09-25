SELECT
    r.id, st_astext(r.{roof.geometry})
FROM
    {roof.table} r 
ORDER BY r.id    
LIMIT %s
