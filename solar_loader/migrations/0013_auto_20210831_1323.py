# Generated by Django 3.2.5 on 2021-08-31 13:23

from django.db import migrations, models
import solar_loader.models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0012_solarsim_20190612_0907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solarsim',
            name='breakdown_cost_factor',
            field=models.JSONField(default=solar_loader.models.breakdown_cost_factor_default, help_text='Breakdown of the energetic cost for a photovoltaic         installation, by origin of the technology.'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='cv_rate_classes',
            field=models.TextField(default=solar_loader.models.cv_rate_classes_default_table, help_text='<p>Classes of Certificat verts rate by installed power in kWc.         The first column is the lower limit (kWc), the 2nd column the upper limit (kWc) and         the 3rd the value of the cv_rate (ratio). You can add as many lines as needed.         Each certificat vert rate (3rd column) value is applied for the range of         installed power between its respective (1st column) and (2nd column)         values. The larger (the last) second column value must be large enough to         apply in any situation (e.g., 9999999999 kWc).<p>         <p><b>Example:</b></p><p>0;5;2.4<br>5;9999999999;1.8</p> \n         <p>means: cv_rate = 2.4 for installations between 0 and 5 kWc and cv_rate = 1.8 for         installations above 5 kWc.</p>'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='self_production',
            field=models.JSONField(default=solar_loader.models.self_production_default, help_text='Table of self production rates, for different         user energetic profiles and self-production ratio'),
        ),
        migrations.AlterField(
            model_name='solarsim',
            name='thermic_production',
            field=models.JSONField(default=solar_loader.models.thermic_production_default),
        ),
    ]
