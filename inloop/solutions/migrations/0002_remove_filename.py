# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-02 11:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solutions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='solutionfile',
            name='filename',
        ),
    ]