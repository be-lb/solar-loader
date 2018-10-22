UPDATE  {results.table}
SET
    compute_node = %s,
    compute_status = %s
WHERE roof_id = ANY( %s );
