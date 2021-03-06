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
from solar_loader.final import compute_batches


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-bs',
            '--batch-size',
            dest='batch_size',
            type=int,
            default=124,
            help='Size of a batch to process',
        )

        parser.add_argument(
            'node_name',
            help='Name of this process',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        node_name = options['node_name']
        compute_batches(node_name, batch_size)
