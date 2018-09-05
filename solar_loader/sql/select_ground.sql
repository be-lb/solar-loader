SELECT
    st_astext(st_force2d({ground.geometry})) 
FROM
    {ground.table}
WHERE
    {ground.capakey} = %s;
