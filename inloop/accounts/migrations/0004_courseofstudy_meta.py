# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_activation_key_allow_bank'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='courseofstudy',
            options={'verbose_name_plural': 'Courses of study'},
        ),
    ]
