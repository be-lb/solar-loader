FROM python:3.7-slim as base

WORKDIR /app

# COPY requirements.txt requirements.txt 

RUN apt-get update && apt-get install -y git-core libpq-dev libgdal-dev libgeos-dev libproj-dev binutils libxslt-dev

RUN git clone https://gitlab.com/atelier-cartographique/carto-station.git \
    && git clone https://github.com/be-lb/solar-loader.git \
    && git clone https://gitlab.com/atelier-cartographique/postgis-loader.git

RUN  pip install -r /app/carto-station/sdi/requirements.txt \
    && pip install /app/postgis-loader \
    && pip install /app/solar-loader 


FROM python:3.7-slim 

RUN apt update && apt install -y libpq-dev libgdal-dev libgeos-dev libproj-dev libxslt-dev

COPY --from=base /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
COPY --from=base /app /app

COPY Bruxelles_centre-hour.csv    /solar-data/Bruxelles_centre-hour.csv
COPY compute_settings.py /app/carto-station/sdi/ 

WORKDIR /app/carto-station/sdi

ENV DJANGO_SETTINGS_MODULE=compute_settings

ENTRYPOINT ["/usr/local/bin/python", "/app/carto-station/sdi/manage.py"]
# CMD  ["python", "manage.py"] 


