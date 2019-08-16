# Generated by Django 2.0.2 on 2018-12-14 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('association', '0002_branch_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='activities_number',
            field=models.IntegerField(default=0, verbose_name='活动数量'),
        ),
        migrations.AddField(
            model_name='branch',
            name='influence_number',
            field=models.IntegerField(default=0, verbose_name='影响力'),
        ),
        migrations.AddField(
            model_name='branch',
            name='members_number',
            field=models.IntegerField(default=0, verbose_name='分舵人数'),
        ),
    ]