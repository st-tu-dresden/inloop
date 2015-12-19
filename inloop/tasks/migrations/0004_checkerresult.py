# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import inloop.tasks.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0003_make_deadline_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckerResult',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('result', models.FileField(upload_to=inloop.tasks.models.get_upload_path)),
                ('passed', models.BooleanField(default=False)),
                ('solution', models.ForeignKey(to='tasks.TaskSolution')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
