# Generated by Django 2.2.15 on 2020-09-02 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_matnum_verbose_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentdetails',
            name='ownwork_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
