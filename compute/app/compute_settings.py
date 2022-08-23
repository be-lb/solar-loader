from main.settings import *
from os import environ

# INSTALLED_APPS.append("postgis_loader")
INSTALLED_APPS.append("solar_loader")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

LAYERS_SCHEMAS = []
CLIENTS = []
CLIENTS_DEFAULT = ""
DEFAULT_GROUP = "sdi:geodata"
PUBLIC_GROUP = "sdi:public"


SOLAR_CONNECTION_RESULTS = "results"

SOLAR_TABLES = {
    "ground": {
        "table": "cadastre",
        "geometry": "geom",
        "capakey": "capakey",
    },
    "roof": {"table": "roof", "geometry": "geom", "centroid": "flat_pos"},
    "solid": {"table": "solid", "geometry": "geom"},
    "results": {
        "table": "results", 
        "irradiance": "irradiance",
        "roof_id": "roof_id",
    },
}


SOLAR_WKT_FROM_DB = True
SOLAR_TMY = "/solar-data/Bruxelles_centre-hour.csv"
SOLAR_SAMPLE_RATE = 14

RESULTS_HOST = environ.get('RESULTS_HOST')
RESULTS_NAME = environ.get('RESULTS_NAME')
RESULTS_PASSWORD = environ.get('RESULTS_PASSWORD')
RESULTS_USER = environ.get('RESULTS_USER')

DATABASES['results'] = {
    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    'HOST': RESULTS_HOST,
    'NAME': RESULTS_NAME,
    'PASSWORD': RESULTS_PASSWORD,
    'USER': RESULTS_USER,
}

SOLAR_HOST = environ.get('SOLAR_HOST').split(',')
SOLAR_NAME = environ.get('SOLAR_NAME')
SOLAR_PASSWORD = environ.get('SOLAR_PASSWORD')
SOLAR_USER = environ.get('SOLAR_USER')

SOLAR_CONNECTION = []

for i, host in enumerate(SOLAR_HOST):
    SOLAR_CONNECTION.append(f'solar{i}')
    DATABASES[f'solar{i}'] = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': host,
        'NAME': SOLAR_NAME,
        'PASSWORD': SOLAR_PASSWORD,
        'USER': SOLAR_USER,
        'OPTIONS': {
            'options': '-c search_path=solar,public',
        },
    }
