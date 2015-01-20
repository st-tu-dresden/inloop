# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='mat_num',
            field=models.IntegerField(help_text=b'Matriculation Number', max_length=7, null=True),
            preserve_default=True,
        ),
    ]
