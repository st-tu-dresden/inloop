# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_taskfile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=tinymce.models.HTMLField(help_text=b'Task description'),
        ),
    ]
