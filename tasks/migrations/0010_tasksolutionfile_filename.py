# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_auto_20150518_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasksolutionfile',
            name='filename',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
