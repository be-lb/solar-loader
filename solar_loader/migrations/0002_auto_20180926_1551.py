# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-26 15:51
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import solar_loader.models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='solarsim',
            name='annual_consumption_base',
            field=models.FloatField(default=600),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='breakdown_cost_factor',
            field=jsonfield.fields.JSONField(default=solar_loader.models.breakdown_cost_factor_default),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_electric',
            field=models.FloatField(default=0.456),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_fuel',
            field=models.FloatField(default=0.263),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='co2_emissions_by_kwh_thermic_gas',
            field=models.FloatField(default=0.201),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='cv_end_of_compensation_year',
            field=models.FloatField(default=2020),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='cv_rate_high_power',
            field=models.FloatField(default=2.4),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='cv_rate_low_power',
            field=models.FloatField(default=3),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='cv_rate_switch_power',
            field=models.FloatField(default=5),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='cv_time',
            field=models.FloatField(default=10),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='discount_rate',
            field=models.FloatField(default=0.04),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='elec_buying_price',
            field=models.FloatField(default=0.23),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='elec_index',
            field=models.FloatField(default=0.03),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='electric_heating_factor',
            field=models.FloatField(default=16500),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='electric_water_heater_factor',
            field=models.FloatField(default=2336),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='flat_roof_tilt',
            field=models.FloatField(default=5),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_electric',
            field=models.FloatField(default=0.267),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_fuel',
            field=models.FloatField(default=0.081),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_gas',
            field=models.FloatField(default=0.08),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_electric',
            field=models.FloatField(default=0.04),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_fuel',
            field=models.FloatField(default=0.099),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_energy_cost_index_gas',
            field=models.FloatField(default=0.054),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_producer_yield_electric',
            field=models.FloatField(default=0.95),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_producer_yield_fuel',
            field=models.FloatField(default=0.55),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='hot_water_producer_yield_gas',
            field=models.FloatField(default=0.7),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='inflation_rate',
            field=models.FloatField(default=0.02),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='low_productivity_limit',
            field=models.FloatField(default=800),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='maintenance_cost_factor',
            field=models.FloatField(default=0.0075),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='max_liter_per_day',
            field=models.FloatField(default=210),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='max_solar_productivity',
            field=models.FloatField(default=1300),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='meter_cost',
            field=models.FloatField(default=289),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='min_thermic_area',
            field=models.FloatField(default=5),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='onduleur_cost_factor',
            field=models.FloatField(default=250),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='onduleur_replacement_rate',
            field=models.FloatField(default=15),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='production_yearly_loss_index',
            field=models.FloatField(default=0.0005),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_cost_mono',
            field=models.FloatField(default=1415.0943396226414),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_cost_mono_high',
            field=models.FloatField(default=1509.433962264151),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_cost_poly',
            field=models.FloatField(default=1320.754716981132),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_yield_mono',
            field=models.FloatField(default=0.155),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_yield_mono_high',
            field=models.FloatField(default=0.22),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='pv_yield_poly',
            field=models.FloatField(default=0.13),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='redevance_cost',
            field=models.FloatField(default=65),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='self_production',
            field=jsonfield.fields.JSONField(default=solar_loader.models.self_production_default),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='thermic_installation_cost',
            field=models.FloatField(default=6000),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='thermic_maintenance_cost',
            field=models.FloatField(default=100),
        ),
        migrations.AddField(
            model_name='solarsim',
            name='washing_machine_factor',
            field=models.FloatField(default=600),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='co2_emissions_by_kwh',
            field=models.FloatField(default=0.456),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_belgium',
            field=models.FloatField(default=2500),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_china',
            field=models.FloatField(default=2750),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='energetic_cost_factor_europe',
            field=models.FloatField(default=2600),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='max_power',
            field=models.FloatField(default=12),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='thermic_production',
            field=jsonfield.fields.JSONField(default=solar_loader.models.thermic_production_default),
        ),
    ]
