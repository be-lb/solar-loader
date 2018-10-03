UPDATE  {results.table}

SET 
    irradiance = %s,
    area = %s,
    compute_status = %s,
    compute_start = %s,
    compute_end = %s

WHERE roof_id = %s;
