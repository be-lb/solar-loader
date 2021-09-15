# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-10 13:48
from __future__ import unicode_literals

from django.db import migrations, models
try:
    from jsonfield.fields import JSONField
except Exception:
    from django.db.models import JSONField
import solar_loader.models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0003_auto_20180927_0942'),
    ]

    operations = [
        migrations.AddField(
            model_name='solarsim',
            name='max_solar_irradiance',
            field=models.FloatField(default=1313, help_text='Maximal solar irradiance for a roof in Bruxelles, in         kWh/m².an'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='annual_consumption_base',
            field=models.FloatField(default=600, help_text='Base of the annual consumption, in kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='breakdown_cost_factor',
            field=JSONField(default=solar_loader.models.breakdown_cost_factor_default, help_text='Breakdown of the energetic cost for a photovoltaic         installation, by origin of the technology.'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_electric',
            field=models.FloatField(default=0.456, help_text='CO2 emissions by kWh of electricity, in kg/kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_fuel',
            field=models.FloatField(default=0.263, help_text='CO2 emissions by kWh of fuel, in kg/kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_gas',
            field=models.FloatField(default=0.201, help_text='CO2 emissions by kWh of gas, in kg/kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_end_of_compensation_year',
            field=models.FloatField(default=2020, help_text='Year of the end of the compensation'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_rate_high_power',
            field=models.FloatField(default=2.4, help_text='Rate of Certificat Vert for high power installation, in         CV/MWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_rate_low_power',
            field=models.FloatField(default=3, help_text='Rate of Certificat Vert for low power installation, in         CV/MWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_rate_switch_power',
            field=models.FloatField(default=5, help_text='Installation power (in KWc) at which the Certificat Vert         rate change'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_time',
            field=models.FloatField(default=10, help_text='Duration of the Certicat Verts, in years'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='discount_rate',
            field=models.FloatField(default=0.04, help_text='Discount rate, in %'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='elec_buying_price',
            field=models.FloatField(default=0.23, help_text='Buying electricity price, in €/kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='elec_index',
            field=models.FloatField(default=0.03, help_text='Yearly electricity price index, in %'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='electric_heating_factor',
            field=models.FloatField(default=16500, help_text='Annual consumption of a heating system, in kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='electric_water_heater_factor',
            field=models.FloatField(default=2336, help_text='Annual consumption of a hot water heater, in kWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_belgium',
            field=models.FloatField(default=2500, help_text='Energetic cost for a photovoltaic installation, by origin         of the technology, in kWh/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_china',
            field=models.FloatField(default=2750, help_text='Energetic cost for a photovoltaic installation, by origin         of the technology, in kWh/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_europe',
            field=models.FloatField(default=2600, help_text='Energetic cost for a photovoltaic installation, by origin         of the technology, in kWh/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='flat_roof_tilt',
            field=models.FloatField(default=5, help_text='Inclination (tilt) threshold for flat roof, in °. Roofs         with a tilt below this threshold are considered as flat.'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_electric',
            field=models.FloatField(default=0.267, help_text='Energy cost (for hot water production) for electricity, in         €/KWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_fuel',
            field=models.FloatField(default=0.081, help_text='Energy cost (for hot water production) for fuel, in €/KWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_gas',
            field=models.FloatField(default=0.08, help_text='Energy cost (for hot water production) for gas, in €/KWh'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_electric',
            field=models.FloatField(default=0.04, help_text='Energy cost index for electricity'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_fuel',
            field=models.FloatField(default=0.099, help_text='Energy cost index for fuel'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_gas',
            field=models.FloatField(default=0.054, help_text='Energy cost index for gas'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_producer_yield_electric',
            field=models.FloatField(default=0.95, help_text='Yield of the hot water production system with electricity'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_producer_yield_fuel',
            field=models.FloatField(default=0.55, help_text='Yield of the hot water production system with fuel'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='hot_water_producer_yield_gas',
            field=models.FloatField(default=0.7, help_text='Yield of the hot water production system with gas'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='inflation_rate',
            field=models.FloatField(default=0.02, help_text='Yearly inflation rate, in %'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='low_productivity_limit',
            field=models.FloatField(default=800, help_text='Low limit for roof productivity (kWh/kWc.m²). No         photovoltaic production is considered for roofs with a productivity         below this limit.'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='maintenance_cost_factor',
            field=models.FloatField(default=0.0075, help_text='Rate of maintenance cost with respect to the total         photovoltaic installation price'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='max_liter_per_day',
            field=models.FloatField(default=210, help_text='Maximum hot water consumption per day, in liter'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='max_power',
            field=models.FloatField(default=12, help_text='Maximum power of the photovoltaic installation, in kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='max_solar_productivity',
            field=models.FloatField(default=940, help_text='Maximal solar productivity for a roof in Bruxelles, in         kWh/m².an'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='meter_cost',
            field=models.FloatField(default=289, help_text='Cost of the electric meter, in € (21% VAT included)'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='min_thermic_area',
            field=models.FloatField(default=5, help_text='Minimal area for a solar thermic installation, in m². Below         this limit, no solar thermic installation is possible'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='onduleur_cost_factor',
            field=models.FloatField(default=250, help_text='Cost of the onduler, in € (21% VAT included)'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='onduleur_replacement_rate',
            field=models.FloatField(default=15, help_text='Rate of onduler replacement, in years'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='production_yearly_loss_index',
            field=models.FloatField(default=0.0005, help_text='Yearly photovoltaic production loss'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_cost_mono',
            field=models.FloatField(default=1415.0943396226414, help_text='Price of the photovoltaic panel, for monocristallin panels         in €/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_cost_mono_high',
            field=models.FloatField(default=1509.433962264151, help_text='Price of the photovoltaic panel, for high yield         monocristallin panels in €/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_cost_poly',
            field=models.FloatField(default=1320.754716981132, help_text='Price of the photovoltaic panel, for polycristallin panels         in €/kWc'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_yield_mono',
            field=models.FloatField(default=0.155, help_text='Yield of the photovoltaic system, for monocristallin panels'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_yield_mono_high',
            field=models.FloatField(default=0.22, help_text='Yield of the photovoltaic system, for monocristallin high         yield panels'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='pv_yield_poly',
            field=models.FloatField(default=0.13, help_text='Yield of the photovoltaic system, for polycristallin panels'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='redevance_cost',
            field=models.FloatField(default=65, help_text='Cost of the redevance, in €'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='self_production',
            field=JSONField(default=solar_loader.models.self_production_default, help_text='Table of self production rates, for different         user energetic profiles and self-production ratio'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='thermic_installation_cost',
            field=models.FloatField(default=6000, help_text='Average cost of a solar thermic installation, in € (VAT         excluded)'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='thermic_maintenance_cost',
            field=models.FloatField(default=100, help_text='Average maintenance cost of a solar thermic installation,         in € (VAT excluded), applied to a given maintenance rate (3 years)'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='washing_machine_factor',
            field=models.FloatField(default=600, help_text='Annual consumption of a washmachine, in kWh'),
        ),
    ]
