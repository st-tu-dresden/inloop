# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_taskcategory_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskcategory',
            name='image',
            field=models.ImageField(upload_to=b'images/category_thumbs/'),
            preserve_default=True,
        ),
    ]
