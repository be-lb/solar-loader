from django.db import models
from jsonfield import JSONField
from api.models import message_field


class SolarSim(models.Model):
    """
    A model to store and adjust solar-sim module constants
    """
    id = models.AutoField(primary_key=True)

    # we'll serve to maintain different configs and serve just one
    current = models.BooleanField(default=False)

    # to encode simple values
    max_power = models.FloatField()
    co2_emissions_by_kwh = models.FloatField()

    # to encode simple stucts
    energetic_cost_factor_belgium = models.FloatField()
    energetic_cost_factor_europe = models.FloatField()
    energetic_cost_factor_china = models.FloatField()

    # to encode complex structures
    thermic_production = JSONField()

    # etc.


class AdjustDescription(models.Model):
    """
    A model to store and adjust decriptions attached
    to adjust widgets
    """
    id = models.AutoField(primary_key=True)

    PV_OBSTACLES = 'pvobstacle'
    PV_TECH = 'pvtech'
    PV_NUM = 'pvnum'
    PV_CONSUMPTION = 'pvcons'
    PV_AUTONOMY = 'pvauto'
    PV_VAT = 'pvvat'
    PV_LOAN = 'pvloan'
    THERMAL_SYS = 'thsys'
    THERMAL_CONSUMPTION = 'thcons'
    THERMAL_GRANT = 'thgrant'
    THERMAL_VAT = 'thvat'
    THERMAL_LOAN = 'thloan'

    KEYS = (
        (PV_OBSTACLES, 'Obstacles'),
        (PV_TECH, 'Thechnology (photovoltaic)'),
        (PV_NUM, 'Number of Panels (photovoltaic)'),
        (PV_CONSUMPTION, 'Consumption (photovoltaic)'),
        (PV_AUTONOMY, 'Autonomy (photovoltaic)'),
        (PV_VAT, 'VAT (photovoltaic)'),
        (PV_LOAN, 'Loan (photovoltaic)'),
        (THERMAL_SYS, 'System (thermal)'),
        (THERMAL_CONSUMPTION, 'Consumption (thermal)'),
        (THERMAL_GRANT, 'Grant (thermal)'),
        (THERMAL_VAT, 'VAT (thermal)'),
        (THERMAL_LOAN, 'Loan (thermal)'),
    )

    widget_key = models.CharField(max_length=12, choices=KEYS)
    description = message_field('adjust_description')
