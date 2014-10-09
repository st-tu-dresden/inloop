# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_task_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(help_text=b'Name of the file including the ending', max_length=30)),
                ('task', models.ForeignKey(related_name=b'task_files', to='tasks.Task')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
