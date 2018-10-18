#  Copyright (C) 2018 Atelier Cartographique <contact@atelier-cartographique.be>
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

from django.core.management.base import BaseCommand
from solar_loader.explain import analyze
from solar_loader.time import get_day


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument(
        #     '-bs',
        #     '--batch-size',
        #     dest='batch_size',
        #     type=int,
        #     default=124,
        #     help='Size of a batch to process',
        # )

        parser.add_argument(
            'roof_id',
            help='Roof plane ID',
        )
        parser.add_argument(
            'day',
            type=int,
            help='Day of the year',
        )

    def handle(self, *args, **options):
        roof_id = options['roof_id']
        day_n = options['day']
        day = list(get_day(day_n))
        analyze(roof_id, day)
