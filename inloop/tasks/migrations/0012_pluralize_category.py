# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_short_id_is_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taskcategory',
            options={'verbose_name_plural': 'Task categories'},
        ),
    ]
