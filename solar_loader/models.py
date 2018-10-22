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
    name = models.CharField(max_length=128, default='(none)')
    current = models.BooleanField(default=False)

    # Environmental
    co2_emissions_by_kwh = models.FloatField(
        default=0.456,
        help_text='CO2 emissions by kWh of electric energy, in kg/kWh'
    )
    energetic_cost_factor_belgium = models.FloatField(
        default=2500,
        help_text='Energetic cost for a photovoltaic installation, by origin \
        of the technology, in kWh/kWc'
    )
    energetic_cost_factor_europe = models.FloatField(
        default=2600,
        help_text='Energetic cost for a photovoltaic installation, by origin \
        of the technology, in kWh/kWc'
    )
    energetic_cost_factor_china = models.FloatField(
        default=2750,
        help_text='Energetic cost for a photovoltaic installation, by origin \
        of the technology, in kWh/kWc'
    )
    breakdown_cost_factor = JSONField(
        default=breakdown_cost_factor_default,
        help_text='Breakdown of the energetic cost for a photovoltaic \
        installation, by origin of the technology.'
    )

    # financial
    meter_cost = models.FloatField(
        default=289,
        help_text='Cost of the electric meter, in € (21% VAT included)'
    )
    onduleur_cost_factor = models.FloatField(
        default=250,
        help_text='Cost of the onduler, in € (21% VAT included)'
    )
    onduleur_replacement_rate = models.FloatField(
        default=15,
        help_text='Rate of onduler replacement, in years'
    )
    redevance_cost = models.FloatField(
        default=65,
        help_text='Cost of the redevance, in €'
    )
    pvheater_cost = models.FloatField(
        default=1700,
        help_text='Cost of a PV heater, in €'
    )
    battery_cost = models.FloatField(
        default=7000,
        help_text='Cost of a home battery, in €'
    )
    inflation_rate = models.FloatField(
        default=0.02,
        help_text='Yearly inflation rate, in %'
    )
    elec_buying_price = models.FloatField(
        default=0.23,
        help_text='Buying electricity price, in €/kWh'
    )
    elec_index = models.FloatField(
        default=0.03,
        help_text='Yearly electricity price index, in %'
    )
    discount_rate = models.FloatField(
        default=0.04,
        help_text='Discount rate, in %'
    )
    cv_rate_switch_power = models.FloatField(
        default=5,
        help_text='Installation power (in KWc) at which the Certificat Vert \
        rate change'
    )
    cv_rate_low_power = models.FloatField(
        default=2.4,
        help_text='Rate of Certificat Vert for low power installation, in \
        CV/MWh'
    )
    cv_rate_high_power = models.FloatField(
        default=1.8182,
        help_text='Rate of Certificat Vert for high power installation, in \
        CV/MWh'
    )
    cv_time = models.FloatField(
        default=10,
        help_text='Duration of the Certicat Verts, in years'
    )
    cv_end_of_compensation_year = models.FloatField(
        default=2020,
        help_text='Year of the end of the compensation'
    )
    production_yearly_loss_index = models.FloatField(
        default=0.0005,
        help_text='Yearly photovoltaic production loss'
    )
    maintenance_cost_factor = models.FloatField(
        default=0.0075,
        help_text='Rate of maintenance cost with respect to the total \
        photovoltaic installation price'
    )

    # roof
    max_power = models.FloatField(
        default=12,
        help_text='Maximum power of the photovoltaic installation, in kWc'
    )
    max_solar_productivity = models.FloatField(
        default=940,
        help_text='Maximal solar productivity for a roof in Bruxelles, in \
        kWh/m².an')
    medium_solar_productivity = models.FloatField(
        default=831.25,
        help_text='Medium solar productivity for a roof in Bruxelles, in \
        kWh/m².an')
    max_solar_irradiance = models.FloatField(
        default=1313,
        help_text='Maximal solar irradiance for a roof in Bruxelles, in \
        kWh/m².an')
    flat_roof_tilt = models.FloatField(
        default=5,
        help_text='Inclination (tilt) threshold for flat roof, in °. Roofs \
        with a tilt below this threshold are considered as flat.'
    )
    low_productivity_limit = models.FloatField(
        default=722.5,
        help_text='Low limit for roof productivity (kWh/kWc.m²). No \
        photovoltaic production is considered for roofs with a productivity \
        below this limit.'
    )
    pv_yield_poly = models.FloatField(
        default=0.13,
        help_text='Yield of the photovoltaic system, for polycristallin panels'
    )
    pv_yield_mono = models.FloatField(
        default=0.155,
        help_text='Yield of the photovoltaic system, for monocristallin panels'
    )
    pv_yield_mono_high = models.FloatField(
        default=0.22,
        help_text='Yield of the photovoltaic system, for monocristallin high \
        yield panels'
    )
    pv_cost_poly = models.FloatField(
        default=1400/1.06,
        help_text='Price of the photovoltaic panel, for polycristallin panels \
        in €/kWc'
    )
    pv_cost_mono = models.FloatField(
        default=1500/1.06,
        help_text='Price of the photovoltaic panel, for monocristallin panels \
        in €/kWc'
    )
    pv_cost_mono_high = models.FloatField(
        default=1600/1.06,
        help_text='Price of the photovoltaic panel, for high yield \
        monocristallin panels in €/kWc'
    )
    lost_space_rate = models.FloatField(
        default=0.15,
        help_text='This a rate of roof area that is lost due to the \
        impossibility of exploiting every part of the roof area. The usable \
        roof area is computed as UsableArea = Area * (1 - lost_space_rate - \
        obstacleRate)'
    )
    obstacle_default_rate = models.FloatField(
        default=0.177,
        help_text='Default obstacle rate for a building'
    )
    obstacle_area_chimneySmoke = models.FloatField(
        default=0.8719,
        help_text='Average obstacle area for a chimney, in m²'
    )
    obstacle_area_velux = models.FloatField(
        default=1.409,
        help_text='Average obstacle area for a velux, in m²'
    )
    obstacle_area_dormerWindow = models.FloatField(
        default=5.339,
        help_text='Average obstacle area for a dormer window, in m²'
    )
    obstacle_area_flatRoofWindow = models.FloatField(
        default=4.192,
        help_text='Average obstacle area for a flat roof window, in m²'
    )
    obstacle_area_terraceInUse = models.FloatField(
        default=26.09,
        help_text='Average obstacle area for a terrace, in m²'
    )
    obstacle_area_lift = models.FloatField(
        default=10.93,
        help_text='Average obstacle area for a lift on a flat roof, in m²'
    )
    obstacle_area_existingSolarPannel = models.FloatField(
        default=36.05,
        help_text='Average obstacle area for a existing solar panel \
        installation, in m²'
    )

    # user
    annual_consumption_base = models.FloatField(
        default=600,
        help_text='Base of the annual consumption, in kWh'
    )
    washing_machine_factor = models.FloatField(
        default=600,
        help_text='Annual consumption of a washmachine, in kWh'
    )
    electric_water_heater_factor = models.FloatField(
        default=2336,
        help_text='Annual consumption of a hot water heater, in kWh'
    )
    electric_heating_factor = models.FloatField(
        default=16500,
        help_text='Annual consumption of a heating system, in kWh'
    )
    self_production = JSONField(
        default=self_production_default,
        help_text='Table of self production rates, for different \
        user energetic profiles and self-production ratio'
    )

    # Thermic
    thermic_installation_cost = models.FloatField(
        default=6000,
        help_text='Average cost of a solar thermic installation, in € (VAT \
        excluded)'
    )
    thermic_maintenance_cost = models.FloatField(
        default=100,
        help_text='Average maintenance cost of a solar thermic installation, \
        in € (VAT excluded), applied to a given maintenance rate (3 years)'
    )
    max_liter_per_day = models.FloatField(
        default=210,
        help_text='Maximum hot water consumption per day, in liter'
    )
    min_thermic_area = models.FloatField(
        default=5,
        help_text='Minimal area for a solar thermic installation, in m². Below \
        this limit, no solar thermic installation is possible'
    )

    hot_water_producer_yield_gas = models.FloatField(
        default=0.70,
        help_text='Yield of the hot water production system with gas'
    )
    hot_water_producer_yield_fuel = models.FloatField(
        default=0.55,
        help_text='Yield of the hot water production system with fuel'
    )
    hot_water_producer_yield_electric = models.FloatField(
        default=0.95,
        help_text='Yield of the hot water production system with electricity'
    )

    hot_water_energy_cost_gas = models.FloatField(
        default=0.080,
        help_text='Energy cost (for hot water production) for gas, in €/KWh'
    )
    hot_water_energy_cost_fuel = models.FloatField(
        default=0.081,
        help_text='Energy cost (for hot water production) for fuel, in €/KWh'
    )
    hot_water_energy_cost_electric = models.FloatField(
        default=0.267,
        help_text='Energy cost (for hot water production) for electricity, in \
        €/KWh'
    )

    hot_water_energy_cost_index_gas = models.FloatField(
        default=0.054,
        help_text='Energy cost index for gas'
    )
    hot_water_energy_cost_index_fuel = models.FloatField(
        default=0.099,
        help_text='Energy cost index for fuel'
    )
    hot_water_energy_cost_index_electric = models.FloatField(
        default=0.040,
        help_text='Energy cost index for electricity'
    )

    co2_emissions_by_kwh_thermic_gas = models.FloatField(
        default=0.201,
        help_text='CO2 emissions by kWh of gas, in kg/kWh'
    )
    co2_emissions_by_kwh_thermic_fuel = models.FloatField(
        default=0.263,
        help_text='CO2 emissions by kWh of fuel, in kg/kWh'
    )
    co2_emissions_by_kwh_thermic_electric = models.FloatField(
        default=0.456,
        help_text='CO2 emissions by kWh of electricity, in kg/kWh'
    )

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
            'pvheater_cost':
            self.pvheater_cost,
            'battery_cost':
            self.battery_cost,
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
            'medium_solar_productivity':self.medium_solar_productivity,
            'max_solar_irradiance':self.max_solar_irradiance,
            'lost_space_rate':
            self.lost_space_rate,
            'obstacle_default_rate':
            self.obstacle_default_rate,
            'obstacle': {
                'chimneySmoke': self.obstacle_area_chimneySmoke,
                'velux': self.obstacle_area_velux,
                'dormerWindow': self.obstacle_area_dormerWindow,
                'flatRoofWindow': self.obstacle_area_flatRoofWindow,
                'terraceInUse': self.obstacle_area_terraceInUse,
                'lift': self.obstacle_area_lift,
                'existingSolarPannel': self.obstacle_area_existingSolarPannel,
            },
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
