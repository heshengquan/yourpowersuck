# Generated by Django 2.0.2 on 2018-11-07 11:38

import association.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('association', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='image',
            field=models.ImageField(default=None, null=True, upload_to=association.models.get_image_path, verbose_name='分舵配图'),
        ),
    ]
