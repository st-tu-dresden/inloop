# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='name',
            field=models.CharField(max_length=100, default='', help_text='Internal task name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='task',
            name='title',
            field=models.CharField(max_length=100, help_text='Task title'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taskcategory',
            name='image',
            field=models.ImageField(upload_to='images/category_thumbs/', null=True),
            preserve_default=True,
        ),
    ]
