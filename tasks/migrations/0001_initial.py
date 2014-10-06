# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Task name', max_length=100)),
                ('description', models.TextField(help_text=b'Task description')),
                ('publication_date', models.DateTimeField(help_text=b'When should the task be published?')),
                ('deadline_date', models.DateTimeField(help_text=b'Date the task is due to')),
                ('author', models.CharField(help_text=b'Creator of task', max_length=100)),
                ('category', models.CharField(help_text=b'Category of task', max_length=1, choices=[(b'B', b'Basic Exercise'), (b'A', b'Advanced Exercise'), (b'L', b'Lesson Exercise'), (b'E', b'Exam Exercise')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
