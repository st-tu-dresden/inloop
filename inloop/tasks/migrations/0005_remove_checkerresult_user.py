# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_checkerresult'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checkerresult',
            name='user',
        ),
    ]
