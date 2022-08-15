Pre-computing Irradiance Values 
===============================



Here is a short recipe to replicate computing of irradiance per roof values. The main steps are:
 - build database server images
 - build application image
 - run a compute node 



## Data


Urbis3D (v1), cadaste and TMY.


### Urbis3D

This dataset comes from [urbis-download](https://datastore.brussels/web/urbis-download), in its ESRI Shapefile format.


### Cadastre

This dataset is a one of dump of a `cadastre` table on `Paola` server. There's not much history about this dump, it should obviously being updated as well. To integrate withou change into the provided scripts, it must and follow the schema represented by the statements

```sql
CREATE TABLE "solar"."cadastre" (
    gid serial,
    "__gid" numeric(10,0),
    "capakey" varchar(18),
    "apnc_mapc" varchar(50),
    "bruenvi_cr" date,
    "bruenvi_mo" date,
    "bruenvi_au" varchar(20)
);
ALTER TABLE "solar"."cadastre" ADD PRIMARY KEY (gid);
SELECT AddGeometryColumn('solar','cadastre','geom','31370','MULTIPOLYGON',2);
CREATE INDEX ON "solar"."cadastre" USING GIST ("geom");
```

But note that we actually only use the `geom` and `capakey` fields.


### TMY

This file has been provided by *Meteotest* and is known on IBGE servers as `Bruxelles_centre-hour.csv` under `/opt/sdi`.


## Postgis


The first step consists of integrating these listed datasets into a docker image based on Postgis in order to support further computations. 