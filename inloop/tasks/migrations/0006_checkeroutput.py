# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_auto_20160122_1502'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckerOutput',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=30)),
                ('output', models.TextField()),
                ('result', models.ForeignKey(to='tasks.CheckerResult')),
            ],
        ),
    ]
