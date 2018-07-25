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

from json import loads
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseBadRequest
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, GeometryCollection
from django.views.decorators.cache import cache_page

from .store import Data
from .tmy import TMY
from .compute import get_results
from .radiation_cache import mk_cache
from .lingua import make_feature, make_feature_collection, rows_with_geom

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)
sample_rate = settings.SOLAR_SAMPLE_RATE


def capakey_in(capakey):
    return capakey.replace('-', '/')


def capakey_out(capakey):
    return capakey.replace('/', '-')


@cache_page(60 * 60)
def handle_request(request, capakey):
    """
    Compute the raditiaions for the parcel with capakey as cadastral number
    """
    results = get_results(data_store, tmy, sample_rate, capakey_in(capakey))
    return JsonResponse(results)


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
        return HttpResponse(geom.json, content_type='application/json')
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
    db = data_store
    rows = rows_with_geom(db, 'select_solid_intersect',
                          (capakey_in(capakey), ), 0)
    features = [make_feature(loads(row[0].json)) for row in rows]
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


def make_radition_cache(request):
    mk_cache()

    return JsonResponse({'ok': 'ok'})
