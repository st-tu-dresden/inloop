# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_tasksolution'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasksolution',
            name='file_paths',
            field=models.TextField(default='/media/foo.java'),
            preserve_default=False,
        ),
    ]
