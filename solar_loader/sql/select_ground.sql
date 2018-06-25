SELECT st_asewkt(st_force2d({ground.geometry})) 
FROM {ground.table}
WHERE id = %s;
