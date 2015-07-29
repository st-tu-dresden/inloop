# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20150723_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='deadline_date',
            field=models.DateTimeField(help_text='Date the task is due to', null=True),
            preserve_default=True,
        ),
    ]
