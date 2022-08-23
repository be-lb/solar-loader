RESULTS_HOST='postgis-solar-result'
RESULTS_NAME='solar'
RESULTS_PASSWORD='solar'
RESULTS_USER='solar'

SOLAR_HOST='postgis-solar-build'
SOLAR_NAME='solar'
SOLAR_USER='solar'
SOLAR_PASSWORD='solar'

docker run --rm -it \
    --network build-net \
    -e RESULTS_HOST=${RESULTS_HOST} \
    -e RESULTS_NAME=${RESULTS_NAME} \
    -e RESULTS_PASSWORD=${RESULTS_PASSWORD} \
    -e RESULTS_USER=${RESULTS_USER} \
    -e SOLAR_HOST=${SOLAR_HOST} \
    -e SOLAR_NAME=${SOLAR_NAME} \
    -e SOLAR_USER=${SOLAR_USER} \
    -e SOLAR_PASSWORD=${SOLAR_PASSWORD} \
    app-img $@


# run this script as if it was manage.py itself, e.g.: ./run-node.sh computeradiations --batch-size 32 test0