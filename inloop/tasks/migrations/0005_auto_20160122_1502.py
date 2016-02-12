# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_add_checkerresult'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tasksolution',
            name='is_correct',
        ),
        migrations.AddField(
            model_name='tasksolution',
            name='passed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
