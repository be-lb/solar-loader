
DROP TABLE IF EXISTS {results.table};

CREATE TABLE  {results.table}(
    id serial,
    roof_id         character varying(50) not null,
    irradiance      decimal DEFAULT 0.0,
    area            decimal DEFAULT 0.0,
    compute_status  integer DEFAULT 0,
    compute_node    character varying(32),
    compute_start   timestamp with time zone,
    compute_end     timestamp with time zone
);

INSERT INTO {results.table}(roof_id) SELECT id FROM {roof.table};
CREATE INDEX ON {results.table} (roof_id);
