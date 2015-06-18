# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20150607_1731'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='new_email',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(help_text="The key's deprecation time", blank=True, default=datetime.datetime(2015, 6, 25, 8, 20, 41, 144803, tzinfo=utc)),
            preserve_default=True,
        ),
    ]
