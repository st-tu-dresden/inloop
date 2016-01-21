# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_remove_checkerresult_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkerresult',
            name='time_taken',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
    ]
