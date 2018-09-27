from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models import SolarSim


@receiver(post_save, sender=SolarSim)
def on_solar_sim_save(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if (instance is not None) and instance.current:
        for sim in SolarSim.objects.filter(current=True):
            if sim.id != instance.id:
                sim.current = False
                sim.save()
