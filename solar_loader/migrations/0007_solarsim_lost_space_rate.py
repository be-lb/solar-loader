# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-22 08:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0006_solarsim_obstacle_area'),
    ]

    operations = [
        migrations.AddField(
            model_name='solarsim',
            name='lost_space_rate',
            field=models.FloatField(default=0.15, help_text='This a rate of roof area that is lost due to the         impossibility of exploiting every part of the roof area. The usable         roof area is computed as UsableArea = Area * (1 - lost_space_rate -         obstacleRate)'),
        ),
    ]
