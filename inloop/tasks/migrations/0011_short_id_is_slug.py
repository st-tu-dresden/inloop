# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_default_submission_date'),
    ]

    operations = [
        migrations.RenameField(
            model_name='taskcategory',
            old_name='short_id',
            new_name='slug',
        ),
    ]
