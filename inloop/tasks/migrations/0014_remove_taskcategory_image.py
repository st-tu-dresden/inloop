# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_checkeroutput_name_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskcategory',
            name='image',
        ),
    ]
