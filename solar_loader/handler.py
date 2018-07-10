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

from django.http import JsonResponse
from django.conf import settings

from .store import Data
from .tmy import TMY
from .compute import get_results

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)
sample_rate = settings.SOLAR_SAMPLE_RATE


def handle_request(request, capakey):
    """
    Compute the raditiaions for the parcel with capakey as cadastral number
    """
    results = get_results(data_store, tmy, sample_rate, capakey)
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
                'error': True,
                'message': 'No SOLAR_SIMULATOR_SETTINGS entry in the \
Django settings'},
            status=500)


def get_geom(request, capakey):
    """
    Get the geometry of the parcel with capakey as cadastral number
    """
    db = data_store

    rows = db.rows('select_ground', (capakey, ))
    row_list = list(rows)

    if len(row_list) == 1:
        row = row_list[0]
        return JsonResponse({'geom': row[0]})
    else:
        return JsonResponse(
            {
                'error': True,
                'message': 'No entry found for {}'.format(capakey)
            },
            status=500)
