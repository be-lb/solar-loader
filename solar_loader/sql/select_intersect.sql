SELECT
    gid, st_astext({solid.geometry})
FROM
    {solid.table}
WHERE
    ST_3DIntersects(%s, {solid.geometry})
ORDER BY ST_3DDistance(%s, {solid.geometry});
