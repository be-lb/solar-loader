SELECT gid, geom
FROM {solid.table}
WHERE ST_3DIntersects(%s, {solid.geometry});