SELECT 
    __conv_geom_operator__(solid.{solid.geometry}), solid.id
FROM 
    {solid.table} AS solid
    INNER JOIN {ground.table} AS gnd 
        ON ST_3DIntersects(solid.{solid.geometry}, gnd.{ground.geometry})
WHERE 
    gnd.{ground.capakey} = %s;
