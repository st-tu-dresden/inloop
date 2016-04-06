# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_checkerresult_process_output'),
    ]

    operations = [
        migrations.RenameField(
            model_name='checkerresult',
            old_name='result',
            new_name='stdout',
        ),
    ]
