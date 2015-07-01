# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20150618_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(default=datetime.datetime(2015, 7, 2, 12, 28, 12, 921436, tzinfo=utc), blank=True, help_text="The key's deprecation time"),
            preserve_default=True,
        ),
    ]
