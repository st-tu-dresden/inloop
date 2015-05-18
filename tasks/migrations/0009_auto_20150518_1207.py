# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tasks.models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_tasksolution_file_paths'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskSolutionFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(storage=tasks.models.get_storage_system, upload_to=b'')),
                ('solution', models.ForeignKey(to='tasks.TaskSolution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='tasksolution',
            name='file_paths',
        ),
    ]
