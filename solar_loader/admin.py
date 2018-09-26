from django.contrib import admin

from .models import SolarSim, AdjustDescription


class SolarSimAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'current',
    )


class AdjustAdmin(admin.ModelAdmin):
    list_display = ('widget_key', 'description')


admin.site.register(SolarSim, SolarSimAdmin)
admin.site.register(AdjustDescription, AdjustAdmin)
