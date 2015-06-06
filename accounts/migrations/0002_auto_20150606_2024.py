# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='new_email',
            field=models.EmailField(default='', help_text="The user's temporary email address waiting to be validated", max_length=75, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='activation_key',
            field=models.CharField(help_text="SHA1 key used to verify the user's email", max_length=40),
            preserve_default=True,
        ),
    ]
