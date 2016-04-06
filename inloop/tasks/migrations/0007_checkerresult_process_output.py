# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_checkeroutput'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkerresult',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2016, 4, 6, 12, 13, 37, 677963, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checkerresult',
            name='return_code',
            field=models.SmallIntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='checkerresult',
            name='stderr',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='checkerresult',
            name='result',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='checkerresult',
            name='time_taken',
            field=models.FloatField(default=0.0),
        ),
    ]
