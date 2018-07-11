SELECT 
    capakey 
FROM 
    {ground.table}
WHERE 
    -- FIXME keeping the force2d here to remain TEMPORARILY compatible with ground3d
    st_intersects(st_force2d({ground.geometry}), ST_SetSRID(st_point(%s, %s), 31370)); 
