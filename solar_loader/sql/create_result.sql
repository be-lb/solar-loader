
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

INSERT INTO 
    {results.table}(roof_id) 
SELECT id FROM {roof.table}
WHERE id in (
    'fme-gen-9b31a4b0-c5aa-46e8-b482-bb1e57c8cffb',
    'fme-gen-783ef191-0667-4b19-a99c-6d4fa7fa0d81',
    'fme-gen-fe8009e3-f1dc-4de9-96ee-a265da368439',
    'fme-gen-b9d8c909-b8e4-4a00-beac-347535dc1709',
    'fme-gen-6ed98043-ed30-47d1-b59f-4f75257ec946',
    'fme-gen-6fcfdd14-4fd0-4341-9eb2-ac2c36871084',
    'fme-gen-91e72cd9-bcb8-48f3-8be8-b768a34f4be1',
    'fme-gen-89180ac7-3248-4f77-8159-6653bdb29ca8',
    'fme-gen-1c965af2-daa5-4f25-bc5b-d00fa53df4a1',
    'fme-gen-31327686-3df8-4c5a-a2ea-6dc2bf8f6b81',
    'fme-gen-ba9e4a7c-bfee-4840-8512-e65d2a9b446e',
    'fme-gen-a704528d-301f-42c5-ab9c-5f236db5e399'
)
;

CREATE INDEX ON {results.table} (roof_id);
