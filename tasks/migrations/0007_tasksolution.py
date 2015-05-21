# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0006_auto_20150417_1855'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskSolution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_date', models.DateTimeField(help_text=b'When was the solution submitted?')),
                ('is_correct', models.BooleanField(default=False, help_text=b'Did the checker accept the solution?')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(to='tasks.Task')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
