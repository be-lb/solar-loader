SELECT 
    __conv_geom_operator__(st_force2d({ground.geometry})) 
FROM 
    {ground.table}
WHERE 
    {ground.capakey} = %s;
