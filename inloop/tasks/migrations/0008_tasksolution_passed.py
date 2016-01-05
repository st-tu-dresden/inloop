# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_remove_tasksolution_is_correct'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasksolution',
            name='passed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
