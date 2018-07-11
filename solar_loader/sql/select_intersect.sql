SELECT
    -- TODO: templatize gid
    gid, __conv_geom_operator__({solid.geometry})
FROM 
    {solid.table}
WHERE 
    ST_3DIntersects(%s, {solid.geometry});
