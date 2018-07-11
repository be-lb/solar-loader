SELECT
    rdiso_flat, rdiso
FROM
    solar.res_roof_rdiso
WHERE
    azimuth = %s
AND
    inclination = %s
