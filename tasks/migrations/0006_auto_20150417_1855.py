# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_auto_20150409_2106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='category',
            field=models.ForeignKey(to='tasks.TaskCategory'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taskcategory',
            name='name',
            field=models.CharField(help_text=b'Category Name', unique=True, max_length=50),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taskcategory',
            name='short_id',
            field=models.CharField(help_text=b'Short ID for URLs', unique=True, max_length=50),
            preserve_default=True,
        ),
    ]
