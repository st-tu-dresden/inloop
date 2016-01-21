# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_checkerresult_time_taken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tasksolution',
            name='is_correct',
        ),
    ]
