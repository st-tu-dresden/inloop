# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models

import inloop.tasks.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(help_text='Task name', max_length=100)),
                ('description', models.TextField(help_text='Task description')),
                ('publication_date', models.DateTimeField(help_text='When should the task be published?')),
                ('deadline_date', models.DateTimeField(help_text='Date the task is due to')),
                ('slug', models.SlugField(help_text='URL name', unique=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('short_id', models.CharField(help_text='Short ID for URLs', unique=True, max_length=50)),
                ('name', models.CharField(help_text='Category Name', unique=True, max_length=50)),
                ('image', models.ImageField(upload_to='images/category_thumbs/')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskSolution',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('submission_date', models.DateTimeField(help_text='When was the solution submitted?')),
                ('is_correct', models.BooleanField(help_text='Did the checker accept the solution?', default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(to='tasks.Task')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskSolutionFile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('filename', models.CharField(max_length=50)),
                ('file', models.FileField(upload_to=inloop.tasks.models.get_upload_path)),
                ('solution', models.ForeignKey(to='tasks.TaskSolution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.ForeignKey(to='tasks.TaskCategory'),
            preserve_default=True,
        ),
    ]
