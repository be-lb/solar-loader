FROM postgis/postgis:10-2.5 as base

RUN apt-get update && apt-get install -y postgis unzip

COPY files/sql/prepare-tables.sql /docker-entrypoint-initdb.d/

