#  Copyright (C) 2017 Atelier Cartographique <contact@atelier-cartographique.be>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 3 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from collections import namedtuple
from functools import reduce
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.conf import settings
from psycopg2.extensions import AsIs
from markdown import markdown

from .store import Data
from .tmy import TMY
from .lingua import make_feature_collection, rows_with_geom, shape_to_feature
from .roof import Roof
from .compute import get_roof_area, get_roof_tilt, get_roof_azimuth
from .models import SolarSim, AdjustDescription

import logging
logger = logging.getLogger(__name__)

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)
sample_rate = settings.SOLAR_SAMPLE_RATE


def capakey_in(capakey):
    return capakey.replace('-', '/')


def capakey_out(capakey):
    return capakey.replace('/', '-')


ID = 0
GEOM = 1
AREA = 2
IRRADIANCE = 3


def make_roof_props_from_row(solar_sim, row):
    area = float(row[AREA])
    r = float(row[IRRADIANCE])
    geom = row[GEOM]
    return {
        'area':
        area,
        'tilt':
        get_roof_tilt(geom),
        'azimuth':
        get_roof_azimuth(geom),
        'irradiance':
        r / 1000.0,
        'productivity': (r / 1000.0) * solar_sim.max_solar_productivity /
        solar_sim.max_solar_irradiance,
    }


def get_roofs(request, capakey):
    """
    Get roofs (id, geomtry, area and irradiance) as a geojson FeatureCollection
    for a given capakey.
    """
    solar_sim = get_object_or_404(SolarSim, current=True)
    db = data_store
    roof_rows = list(
        rows_with_geom(db, 'select_roof_within', (capakey_in(capakey), ), 1))

    features = [
        shape_to_feature(roof[GEOM], roof[ID],
                         make_roof_props_from_row(solar_sim, roof))
        for roof in roof_rows
    ]

    collection = make_feature_collection(features)
    return JsonResponse(collection)


def get_settings(request):
    """
    Get the settings for the solar-simulator defined in the Django
    settings file (in the variable SOLAR_SIMULATOR_SETTINGS)
    """
    if hasattr(settings, 'SOLAR_SIMULATOR_SETTINGS'):
        return JsonResponse(settings.SOLAR_SIMULATOR_SETTINGS)
    else:
        return JsonResponse(
            {
                'error':
                'No SOLAR_SIMULATOR_SETTINGS entry in the \
Django settings'
            },
            status=500)


def get_geom(request, capakey):
    """
    Get the geometry of the parcel with capakey as cadastral number
    """
    db = data_store

    rows = rows_with_geom(db, 'select_ground', (capakey_in(capakey), ), 0)
    row_list = list(rows)

    if len(row_list) == 1:
        geom = row_list[0][0]
        return JsonResponse(
            make_feature_collection([shape_to_feature(geom, capakey)]),
            status=200)
    else:
        return JsonResponse(
            {
                'error': 'No entry found for {}'.format(capakey_out(capakey))
            },
            status=404)


def get_3d(request, capakey):
    """
    Get the 3D-geojson that is associated to a parcel with capakey as
    cadastral number
    """
    roofs = []
    for row in rows_with_geom(data_store, 'select_roof_within',
                              (capakey_in(capakey), ), 4):
        roofs.append(row[4])

    solids = []
    for roof_centroid in roofs:
        x, y = roof_centroid.coords[0]
        axis = 'ST_GeomFromText(\'LINESTRING Z ({x} {y} 0, {x} {y} 1000)\', 31370)'.format(
            x=x, y=y)
        start_point = 'ST_GeomFromText(\'POINT Z({x} {y} 0)\', 31370)'.format(
            x=x, y=y)

        # print(axis)

        for row in rows_with_geom(data_store, 'select_intersect',
                                  (AsIs(axis), AsIs(start_point)), 1):
            solids.append(row[1])

    if len(solids) == 0:
        return JsonResponse(make_feature_collection([]))

    minx, miny, maxx, maxy = reduce(lambda acc, b: (
        min(acc[0], b[0]),
        min(acc[1], b[1]),
        max(acc[2], b[2]),
        max(acc[3], b[3]), ), map(lambda s: s.bounds, solids))

    sz = max(maxx - minx, maxy - miny)

    features = [
        shape_to_feature(s, idx, dict(is_exact=True))
        for idx, s in enumerate(solids)
    ]

    # box = 'Box3D(ST_GeomFromText(\'LINESTRING Z ({x0} {y0} 0,{x1} {y1} 1000)\', 31370))'.format(
    #     x0=minx - sz, y0=miny - sz, x1=maxx + sz, y1=maxy + sz)

    center = 'ST_GeomFromText(\'POINT Z ({x} {y} 50)\', 31370)'.format(
        x=minx + (maxx - minx), y=miny + (maxy - miny))

    # for row in rows_with_geom(data_store, 'select_intersect', (AsIs(box), ),
    #                           1):
    for row in rows_with_geom(data_store, 'select_within', (
            AsIs(center),
            sz * 1.6,
    ), 1):
        features.append(shape_to_feature(row[1], row[0], dict(is_exact=False)))


    collection = make_feature_collection(features)
    return JsonResponse(collection)


def get_spatial_ref_key(request, longitude, latitude):
    """
    Get the capakey for given coordinates
    """
    try:
        lon = float(longitude)
        lat = float(latitude)
    except ValueError:
        raise HttpResponseBadRequest('care to give valid lon/lat?')

    db = data_store
    rows = db.rows('select_ground_intersect', {}, (
        lon,
        lat,
    ))
    row_list = list(rows)

    capakey = None
    if len(row_list) == 1:
        capakey = row_list[0][0]
    else:
        raise Http404('coordinate didnt match a spatial reference')

    return JsonResponse(dict(capakey=capakey_out(capakey)))


def get_solar_sim(request):
    solar_sim = get_object_or_404(SolarSim, current=True)
    return JsonResponse(solar_sim.as_dict())


def get_descriptions(request):
    data = dict()
    for desc in AdjustDescription.objects.all():
        transformed = dict()
        for k, v in desc.description.to_dict().items():
            transformed[k] = markdown(v)

        data[desc.widget_key] = transformed

    return JsonResponse(data)