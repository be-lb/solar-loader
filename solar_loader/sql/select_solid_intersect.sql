SELECT st_asewkt(solid.{solid.geometry}), solid.id
FROM {solid.table} AS solid
INNER JOIN {ground.table} AS gnd ON ST_3DIntersects(solid.{ground.geometry}, gnd.{solid.geometry})
WHERE gnd.id = %s;
