from .rad5 import rad_max
PRODUCTIVITY_MAX = 940

class Roof:
    def __init__(self, roof_id, wkt_geom, area, irradiance):
        self.id = roof_id
        self.wkt_geom = wkt_geom
        self.area = area
        self.irradiance = irradiance
        self.productivity = irradiance * PRODUCTIVITY_MAX / rad_max
