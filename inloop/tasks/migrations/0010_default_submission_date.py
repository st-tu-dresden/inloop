# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_deadline_blankable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasksolution',
            name='submission_date',
            field=models.DateTimeField(help_text='When was the solution submitted?', auto_now_add=True),
        ),
    ]
