SELECT
    -- TODO: templatize gid
    gid, st_astext({solid.geometry})
FROM
    {solid.table}
WHERE
    ST_3DIntersects(%s, {solid.geometry});
