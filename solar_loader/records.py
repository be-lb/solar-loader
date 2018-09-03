from collections import namedtuple

Triangle = namedtuple('Triangle', ['a', 'b', 'c'])
Grid = namedtuple('Grid', ['triangle', 'points', 'rot', 'rot_inv'])
PointIn = namedtuple('RichPoint', ['coords', 'inside'])
SunPosition = namedtuple(
    'SunPosition',
    ['coords', 'azimuth', 'elevation', 'is_daylight', 't', 'sza', 'saa'])

RdisoKey = namedtuple('RdisoKey', ['azimuth', 'tilt'])
RdisoValue = namedtuple('RdisoValue', ['rdiso_flat', 'rdiso'])

GisTriangle = namedtuple('GisTriangle',
                         ['geom', 'azimuth', 'tilt', 'center', 'area'])
