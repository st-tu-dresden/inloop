# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20150606_2024'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(help_text="The key's deprecation time", blank=True, default=datetime.datetime(2015, 6, 14, 17, 27, 8, 858525)),
            preserve_default=True,
        ),
    ]
