SELECT
  gml_id,
  st_astext({ solid.geometry }) --  gid, st_astext(ST_DelaunayTriangles({solid.geometry}))
FROM
  { solid.table }
WHERE
  ST_3DIntersects(% s, { solid.geometry })
ORDER BY
  ST_3DDistance(% s, { solid.geometry });