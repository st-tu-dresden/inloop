# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userprofile_key_expires'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='key_expires',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2015, 6, 14, 17, 31, 4, 706136, tzinfo=utc), help_text="The key's deprecation time"),
            preserve_default=True,
        ),
    ]
