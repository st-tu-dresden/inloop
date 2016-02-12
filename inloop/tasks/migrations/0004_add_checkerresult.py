# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_make_deadline_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckerResult',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('result', models.TextField()),
                ('time_taken', models.FloatField()),
                ('passed', models.BooleanField(default=False)),
                ('solution', models.ForeignKey(to='tasks.TaskSolution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
