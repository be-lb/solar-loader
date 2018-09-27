from django.apps import AppConfig


class SolarConfig(AppConfig):
    name = 'solar_loader'
    label = 'solar'
    verbose_name = 'Solar'
    geodata = True

    def ready(self):
        from .signals import solarsim
        return super().ready()