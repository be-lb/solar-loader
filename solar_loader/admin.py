from django.contrib import admin

from .models import SolarSim, AdjustDescription


class SolarSimAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'current',
    )
    list_editable = ('current',)
    fieldsets = (
        ('Version', {
            'fields': (
                'name',
                'current',
            ),
        }),
        ('PV installation', {
            'fields': (
                'max_power',
                'max_solar_irradiance',
                'max_solar_productivity',
                'medium_solar_productivity',
                'flat_roof_tilt',
                'low_productivity_limit',
                'pv_yield_poly',
                'pv_yield_mono',
                'pv_yield_mono_high',
                'pv_cost_poly',
                'pv_cost_mono',
                'pv_cost_mono_high',
                'lost_space_rate',
                'obstacle_default_rate',
                'obstacle_area_chimneySmoke',
                'obstacle_area_velux',
                'obstacle_area_dormerWindow',
                'obstacle_area_flatRoofWindow',
                'obstacle_area_terraceInUse',
                'obstacle_area_lift',
                'obstacle_area_existingSolarPannel',
            ),
        }),
        ('User', {
            'classes': ('collapse',),
            'fields': (
                'energy_sobriety_factor',
                'electric_water_heater_factor',
                'electric_water_heater_min_consumption',
                'electric_heating_factor',
                'self_production',
            ),
        }),
        ('Environmental', {
            'classes': ('collapse',),
            'fields': (
                'co2_emissions_by_kwh',
                'energetic_cost_factor_belgium',
                'energetic_cost_factor_europe',
                'energetic_cost_factor_china',
                'breakdown_cost_factor'
            ),
        }),
        ('Financial', {
            'classes': ('collapse',),
            'fields': (
                'meter_cost',
                'onduleur_cost_factor',
                'onduleur_replacement_rate',
                'redevance_cost',
                'pvheater_cost',
                'battery_cost',
                'inflation_rate',
                'elec_buying_price',
                'elec_selling_price',
                'elec_index',
                'discount_rate',
                'cv_price',
                'cv_rate_classes',
                'cv_time',
                'cv_end_of_compensation_year',
                'production_yearly_loss_index',
                'maintenance_cost_factor'
            ),
        }),
        ('Thermic solar', {
            'classes': ('collapse',),
            'fields': (
                'thermic_installation_cost',
                'thermic_maintenance_cost',
                'max_liter_per_day',
                'min_thermic_area',
                'hot_water_producer_yield_gas',
                'hot_water_producer_yield_fuel',
                'hot_water_producer_yield_electric',
                'hot_water_energy_cost_gas',
                'hot_water_energy_cost_fuel',
                'hot_water_energy_cost_electric',
                'hot_water_energy_cost_index_gas',
                'hot_water_energy_cost_index_fuel',
                'hot_water_energy_cost_index_electric',
                'co2_emissions_by_kwh_thermic_gas',
                'co2_emissions_by_kwh_thermic_fuel',
                'co2_emissions_by_kwh_thermic_electric',
                'thermic_production',
            ),
        }),
    )


class AdjustAdmin(admin.ModelAdmin):
    list_display = ('widget_key', 'description')


admin.site.register(SolarSim, SolarSimAdmin)
admin.site.register(AdjustDescription, AdjustAdmin)
