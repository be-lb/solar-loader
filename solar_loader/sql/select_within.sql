SELECT
    gid, __conv_geom_operator__({solid.geometry})
FROM 
    {solid.table}
WHERE 
    ST_3DDWithin(%s, {solid.geometry}, %s);
