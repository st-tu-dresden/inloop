# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_tasksolutionfile_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskcategory',
            name='image',
            field=models.FileField(default='images/category_thumbs/default.jpg', upload_to=b'images/category_thumbs/'),
            preserve_default=False,
        ),
    ]
