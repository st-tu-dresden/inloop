# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_tasksolution_passed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkerresult',
            name='result',
            field=models.TextField(),
            preserve_default=True,
        ),
    ]
