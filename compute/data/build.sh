#!/bin/bash

# set -e

CUR_DIR=$(pwd)
# TMP_DIR=$(mktemp -d)

SOLAR_DATA=${CUR_DIR}/files

PG_DATA=${CUR_DIR}/pgdata
PG_NAME=solar
PG_USER=solar
PG_PASSWORD=solar
PG_HOST="postgis-solar-build"
BUILD_IMG="solar-build-image:current"

if test -e  ${PG_DATA} ; then 
echo ">> removing pgdata"
sudo rm -rf ${PG_DATA}
fi

echo ">> building base image"
docker build . -t ${BUILD_IMG}

echo ">> creating network"
docker network create build-net

echo ">> starting postgis"
POSTGIS_CONTAINER=$(\
    docker run -d  \
    --name ${PG_HOST} \
    --network build-net \
    -e POSTGRES_PASSWORD=${PG_PASSWORD} \
    -e POSTGRES_USER=${PG_USER} \
    -e POSTGRES_DB=${PG_NAME} \
    -e PGDATA=/pgdata  \
    -v ${PG_DATA}:/pgdata  \
    ${BUILD_IMG} 
)

echo ">> waiting for the postgis conatiner to setup itself"
for i in $(seq 6)
do
echo -n "${i}..."
sleep 1s
echo  -n -e "\033[1K\r"
done
echo ">> hoping it's ready"


echo ">> running deploy"
docker run --rm -it \
    --network build-net \
    -v ${SOLAR_DATA}:/solar-data \
    -e  PGPASSWORD=${PG_PASSWORD} \
    -e  PGUSER=${PG_USER} \
    -e  PGDATABASE=${PG_NAME} \
    -e  PGHOST=${PG_HOST} \
    ${BUILD_IMG} \
    sh -c 'cd /solar-data && ./deploy.sh && pg_dump -n solar -O -x | gzip > /solar-data/solar-data.sql.gz'


echo ">> clearing docker things"
docker container kill  ${POSTGIS_CONTAINER}
docker container rm -f ${POSTGIS_CONTAINER}
docker image rm -f ${BUILD_IMG}
docker network rm build-net

echo ">> Bye"


