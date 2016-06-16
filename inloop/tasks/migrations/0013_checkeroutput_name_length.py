# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0012_pluralize_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkeroutput',
            name='name',
            field=models.CharField(max_length=60),
        ),
    ]
