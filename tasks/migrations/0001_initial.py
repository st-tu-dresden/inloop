# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import tasks.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('short_id', models.CharField(help_text='Short ID for URLs', max_length=50, unique=True)),
                ('name', models.CharField(help_text='Category Name', max_length=50, unique=True)),
                ('image', models.ImageField(upload_to='images/category_thumbs/')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskSolution',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('submission_date', models.DateTimeField(help_text='When was the solution submitted?')),
                ('is_correct', models.BooleanField(default=False, help_text='Did the checker accept the solution?')),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=50)),
                ('file', models.FileField(upload_to=tasks.models.get_upload_path)),
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
