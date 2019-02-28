# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-02-28 10:39
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields
import solar_loader.models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0010_auto_20181210_1328'),
    ]

    operations = [
        migrations.AddField(
            model_name='solarsim',
            name='cv_rate_classes',
            field=jsonfield.fields.JSONField(default=solar_loader.models.cv_rate_classes_default, help_text='Classes of Certificat verts rate by installed power in kWc.'),
        ),
    ]
