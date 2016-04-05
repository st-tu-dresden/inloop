# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_activation_key_allow_bank'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='bonus_points',
            field=models.PositiveSmallIntegerField(default=0, help_text='Bonus points for solved exam tasks'),
        ),
    ]
