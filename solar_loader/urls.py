#
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

from django.conf.urls import url
from .handler import get_roofs, get_geom, get_3d,\
    get_spatial_ref_key, get_solar_sim, get_descriptions

urlpatterns = [
    url(r'^solar/constants/$', get_solar_sim, name='geodata.solar.constants'),
    url(r'^solar/widgets/$', get_descriptions, name='geodata.solar.widgets'),
    url(r'^solar/geom/for/(?P<capakey>.+)/$',
        get_geom,
        name='geodata.solar.get_geom'),
    url(r'^solar/3d/for/(?P<capakey>.+)/$',
        get_3d,
        name='geodata.solar.get_3d'),
    url(r'^solar/key/(?P<longitude>.+)/(?P<latitude>.+)$',
        get_spatial_ref_key,
        name='geodata.solar.get_key'),
    url(r'^solar/roofs/(?P<capakey>.+)/$',
        get_roofs,
        name='geodata.solar.roofs'),
]
