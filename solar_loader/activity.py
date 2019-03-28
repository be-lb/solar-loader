from .handler import capakey_in, data_store, AREA
from .lingua import rows_with_geom


def get_roofs_area(capakey):
    """
    Get roofs area for a given capakey.
    """
    db = data_store
    area = 0
    for row in rows_with_geom(db, 'select_roof_within',
                              (capakey_in(capakey), ), 1):
        area += row[AREA]

    return float(area)


def update_activity(data):
    action = data.get('action')
    if action is not None and action == 'navigate':
        data['roof_area'] = get_roofs_area(capakey_in(data.get('parameter')))