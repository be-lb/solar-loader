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

from json import loads, dump
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .store import Data
from .tmy import TMY
from .compute import get_results

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)
sample_rate = settings.SOLAR_SAMPLE_RATE


def handle_request(request, capakey):

    results = get_results(data_store, tmy, sample_rate, capakey)

    return JsonResponse(results)
