# Generated by Django 2.0.2 on 2018-12-25 21:06

import appointment.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0003_auto_20181212_1715'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='thumb_image',
            field=models.ImageField(blank=True, default=None, null=True, upload_to=appointment.models.get_image_path, verbose_name='缩略图'),
        ),
    ]