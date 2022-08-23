#!/bin/bash

# set -e


function sql_exec {
    sql_file=$1
    echo "sql_exec ${sql_file}"
    psql  -f "sql/${sql_file}.sql"
}

function s2p_append {
    echo "s2p_append $1 $2"
    shapefile=$1
    table=$2
    shp2pgsql -s 31370 -a -g geom -D -N skip ${shapefile} solar.${table} | psql  -v ON_ERROR_STOP=1  --quiet
}
function s2p_create {
    echo "s2p_create $1 $2"
    shapefile=$1
    table=$2
    shp2pgsql -s 31370 -g geom -D -N skip ${shapefile} solar.${table} | psql  -v ON_ERROR_STOP=1  --quiet
}


function process_urbis {
    echo "[process_urbis] $1"
    zip_file=$1
    bn=$(basename "${zip_file}" _SHP.zip)
    tmpdir=$(mktemp -d)
    unzip -d ${tmpdir} ${zip_file}

    if test -f ${tmpdir}/shp/${bn}_Bu_Roof.shp 
    then 
        (s2p_append  ${tmpdir}/shp/${bn}_Bu_Roof.shp    roof) || echo "Failed on ${bn}_Bu_Roof.shp"
    else 
        echo "${tmpdir}/shp/${bn}_Bu_Roof.shp does not expanded"
    fi
    if test -f ${tmpdir}/shp/${bn}_Bu_Solid.shp 
    then 
        (s2p_append  ${tmpdir}/shp/${bn}_Bu_Solid.shp   solid) || echo "Failed on ${bn}_Bu_Solid.shp"
    else 
        echo "${tmpdir}/shp/${bn}_Bu_Solid.shp does not expanded"
    fi

    echo "Removing ${tmpdir}"
    rm -rf ${tmpdir}
    echo "${tmpdir} removed"
}

# sql_exec prepare-tables

TMPDIR_3D=$(mktemp -d)
unzip -d ${TMPDIR_3D} UrbAdm3D_SHP.zip

# import
for zip_file in  ${TMPDIR_3D}/shp/*.zip
    do
        process_urbis "${zip_file}"
    done

s2p_create cadastre.shp cadastre

# finalize
sql_exec add-roof-centroids

# Clean the solid table
sql_exec repair_solid
