from django.db import models
from jsonfield import JSONField
from api.models import message_field


def thermic_production_default():
    """ return the default values as JSON """
    return {
       "60": {
          "90": 519,
          "112.5": 534,
          "135": 546,
          "157.5": 553,
          "180": 555,
          "202.5": 553,
          "225": 546,
          "247.5": 534,
          "270": 519,
       },
       "90": {
          "90": 742,
          "112.5": 767,
          "135": 787,
          "157.5": 800,
          "180": 804,
          "202.5": 800,
          "225": 787,
          "247.5": 767,
          "270": 742,
       },
       "120": {
          "90": 932,
          "112.5": 968,
          "135": 997,
          "157.5": 1015,
          "180": 1022,
          "202.5": 1015,
          "225": 997,
          "247.5": 968,
          "270": 932,
       },
       "150": {
          "90": 1097,
          "112.5": 1145,
          "135": 1183,
          "157.5": 1207,
          "180": 1215,
          "202.5": 1207,
          "225": 1183,
          "247.5": 1145,
          "270": 1097,
       },
       "180": {
          "90": 1262,
          "112.5": 1321,
          "135": 1368,
          "157.5": 1398,
          "180": 1408,
          "202.5": 1398,
          "225": 1368,
          "247.5": 1321,
          "270": 1262,
       },
       "210": {
          "90": 1364,
          "112.5": 1432,
          "135": 1487,
          "157.5": 1522,
          "180": 1534,
          "202.5": 1522,
          "225": 1487,
          "247.5": 1432,
          "270": 1364,
       }
    }

def breakdown_cost_factor_default():
    """ return the default values as JSON """
    return {
        'Belgium': {
            'panels': 0.85,
            'setup': 0.04,
            'inverter': 0.09,
            'transportBE': 0.02,
            'transportEU': 0,
            'transportBoat': 0
        },
        'Europe': {
            'panels': 0.81,
            'setup': 0.03,
            'inverter': 0.08,
            'transportBE': 0.02,
            'transportEU': 0.05,
            'transportBoat': 0
        },
        'China': {
            'panels': 0.77,
            'setup': 0.03,
            'inverter': 0.08,
            'transportBE': 0.02,
            'transportEU': 0.02,
            'transportBoat': 0.08
        }
    }


def self_production_default():
    """ return the default values as JSON """
    return {
        "default": {
            "0.6": 0.25,
            "1": 0.3,
            "1.4": 0.34,
            "1.8": 0.36,
            "2.2": 0.38,
            "2.6": 0.39,
            "3": 0.4,
        },
        "energySobriety": {
            "0.6": 0.28,
            "1": 0.32,
            "1.4": 0.35,
            "1.8": 0.37,
            "2.2": 0.38,
            "2.6": 0.39,
            "3": 0.4,
        },
        "chargeShift": {
            "0.6": 0.3,
            "1": 0.34,
            "1.4": 0.36,
            "1.8": 0.38,
            "2.2": 0.39,
            "2.6": 0.4,
            "3": 0.41,
        },
        "pvHeater": {
            "0.6": 0.43,
            "1": 0.49,
            "1.4": 0.54,
            "1.8": 0.55,
            "2.2": 0.57,
            "2.6": 0.58,
            "3": 0.6,
        },
        "battery": {
            "0.6": 0.48,
            "1": 0.54,
            "1.4": 0.59,
            "1.8": 0.62,
            "2.2": 0.64,
            "2.6": 0.66,
            "3": 0.69,
        }
    }


class SolarSim(models.Model):
    """
    A model to store and adjust solar-sim module constants
    """
    id = models.AutoField(primary_key=True)

    # we'll serve to maintain different configs and serve just one
    current = models.BooleanField(default=False)

    # Environmental
    co2_emissions_by_kwh = models.FloatField(default=0.456)
    energetic_cost_factor_belgium = models.FloatField(default=2500)
    energetic_cost_factor_europe = models.FloatField(default=2600)
    energetic_cost_factor_china = models.FloatField(default=2750)
    breakdown_cost_factor = JSONField(default=breakdown_cost_factor_default)

    # financial
    meter_cost = models.FloatField(default=289)
    onduleur_cost_factor = models.FloatField(default=250)
    onduleur_replacement_rate = models.FloatField(default=15)
    redevance_cost = models.FloatField(default=65)
    inflation_rate = models.FloatField(default=0.02)
    elec_buying_price = models.FloatField(default=0.23)
    elec_index = models.FloatField(default=0.03)
    discount_rate = models.FloatField(default=0.04)
    cv_rate_switch_power = models.FloatField(default=5)
    cv_rate_low_power = models.FloatField(default=3)
    cv_rate_high_power = models.FloatField(default=2.4)
    cv_time = models.FloatField(default=10)
    cv_end_of_compensation_year = models.FloatField(default=2020)
    production_yearly_loss_index = models.FloatField(default=0.0005)
    maintenance_cost_factor = models.FloatField(default=0.0075)

    # roof
    max_power = models.FloatField(default=12)
    max_solar_productivity = models.FloatField(default=1300)
    flat_roof_tilt = models.FloatField(default=5)
    low_productivity_limit = models.FloatField(default=800)
    pv_yield_poly = models.FloatField(default=0.13)
    pv_yield_mono = models.FloatField(default=0.155)
    pv_yield_mono_high = models.FloatField(default=0.22)
    pv_cost_poly = models.FloatField(default=1400/1.06)
    pv_cost_mono = models.FloatField(default=1500/1.06)
    pv_cost_mono_high = models.FloatField(default=1600/1.06)

    # user
    annual_consumption_base = models.FloatField(default=600)
    washing_machine_factor = models.FloatField(default=600)
    electric_water_heater_factor = models.FloatField(default=2336)
    electric_heating_factor = models.FloatField(default=16500)
    self_production = JSONField(default=self_production_default)

    # Thermic
    thermic_installation_cost = models.FloatField(default=6000)
    thermic_maintenance_cost = models.FloatField(default=100)
    max_liter_per_day = models.FloatField(default=210)
    min_thermic_area = models.FloatField(default=5)

    hot_water_producer_yield_gas = models.FloatField(default=0.70)
    hot_water_producer_yield_fuel = models.FloatField(default=0.55)
    hot_water_producer_yield_electric = models.FloatField(default=0.95)

    hot_water_energy_cost_gas = models.FloatField(default=0.080)
    hot_water_energy_cost_fuel = models.FloatField(default=0.081)
    hot_water_energy_cost_electric = models.FloatField(default=0.267)

    hot_water_energy_cost_index_gas = models.FloatField(default=0.054)
    hot_water_energy_cost_index_fuel = models.FloatField(default=0.099)
    hot_water_energy_cost_index_electric = models.FloatField(default=0.040)

    co2_emissions_by_kwh_thermic_gas = models.FloatField(default=0.201)
    co2_emissions_by_kwh_thermic_fuel = models.FloatField(default=0.263)
    co2_emissions_by_kwh_thermic_electric = models.FloatField(default=0.456)

    thermic_production = JSONField(default=thermic_production_default)


    def as_dict(self):
        return {
            'max_power':
            self.max_power,
            'co2_emissions_by_kwh':
            self.co2_emissions_by_kwh,
            'meter_cost':
            self.meter_cost,
            'onduleur_cost_factor':
            self.onduleur_cost_factor,
            'onduleur_replacement_rate':
            self.onduleur_replacement_rate,
            'redevance_cost':
            self.redevance_cost,
            'inflation_rate':
            self.inflation_rate,
            'elec_buying_price':
            self.elec_buying_price,
            'elec_index':
            self.elec_index,
            'discount_rate':
            self.discount_rate,
            'cv_rate_switch_power':
            self.cv_rate_switch_power,
            'cv_rate_low_power':
            self.cv_rate_low_power,
            'cv_rate_high_power':
            self.cv_rate_high_power,
            'cv_time':
            self.cv_time,
            'cv_end_of_compensation_year':
            self.cv_end_of_compensation_year,
            'production_yearly_loss_index':
            self.production_yearly_loss_index,
            'maintenance_cost_factor':
            self.maintenance_cost_factor,
            'max_solar_productivity':
            self.max_solar_productivity,
            'flat_roof_tilt':
            self.flat_roof_tilt,
            'low_productivity_limit':
            self.low_productivity_limit,
            'annual_consumption_base':
            self.annual_consumption_base,
            'washing_machine_factor':
            self.washing_machine_factor,
            'electric_water_heater_factor':
            self.electric_water_heater_factor,
            'electric_heating_factor':
            self.electric_heating_factor,
            'thermic_installation_cost':
            self.thermic_installation_cost,
            'thermic_maintenance_cost':
            self.thermic_maintenance_cost,
            'max_liter_per_day':
            self.max_liter_per_day,
            'min_thermic_area':
            self.min_thermic_area,
            'energetic_cost_factor':
            dict(
                Belgium=self.energetic_cost_factor_belgium,
                Europe=self.energetic_cost_factor_europe,
                China=self.energetic_cost_factor_china,
            ),
            'breakdown_cost_factor':
            self.breakdown_cost_factor,
            'pv_yield':
            dict(
                poly=self.pv_yield_poly,
                mono=self.pv_yield_mono,
                mono_high=self.pv_yield_mono_high,
            ),
            'pv_cost':
            dict(
                poly=self.pv_cost_poly,
                mono=self.pv_cost_mono,
                mono_high=self.pv_cost_mono_high,
            ),
            'self_production':
            self.self_production,
            'hot_water_producer_yield':
            dict(
                gas=self.hot_water_producer_yield_gas,
                fuel=self.hot_water_producer_yield_fuel,
                electric=self.hot_water_producer_yield_electric,
            ),
            'hot_water_energy_cost':
            dict(
                gas=self.hot_water_energy_cost_gas,
                fuel=self.hot_water_energy_cost_fuel,
                electric=self.hot_water_energy_cost_electric,
            ),
            'hot_water_energy_cost_index':
            dict(
                gas=self.hot_water_energy_cost_index_gas,
                fuel=self.hot_water_energy_cost_index_fuel,
                electric=self.hot_water_energy_cost_index_electric,
            ),
            'co2_emissions_by_kwh_thermic':
            dict(
                gas=self.co2_emissions_by_kwh_thermic_gas,
                fuel=self.co2_emissions_by_kwh_thermic_fuel,
                electric=self.co2_emissions_by_kwh_thermic_electric,
            ),
            'thermic_production':
            self.thermic_production,
        }


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
