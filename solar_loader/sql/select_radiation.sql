SELECT 
    irradiance 
FROM 
    "solar"."radiation_5"
WHERE 
    tilt = %s AND azimuth = %s;
