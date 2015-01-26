# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import accounts.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150117_1901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='mat_num',
            field=models.IntegerField(help_text=b'Matriculation Number', max_length=7, null=True, validators=[accounts.validators.validate_mat_num]),
            preserve_default=True,
        ),
    ]
