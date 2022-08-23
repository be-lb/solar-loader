CREATE INDEX roof_geom_idx
ON solar.roof
USING gist(geom);

CREATE INDEX roof_pos_idx
ON solar.roof
USING gist(pos);

CREATE INDEX solid_geom_idx
ON solar.solid
USING gist(geom);

CREATE INDEX cadastre_geom_idx
ON solar.cadastre
USING gist(geom);

CREATE INDEX typology_geom_idx
ON solar.typology
USING gist(geom);
