SELECT
    gid, st_astext({solid.geometry})
FROM 
    {solid.table}
WHERE 
    ST_3DDWithin(%s, {solid.geometry}, %s);
