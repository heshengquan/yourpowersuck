# Generated by Django 2.0.2 on 2018-05-23 13:10

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import utils.global_tools


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.CharField(default=utils.global_tools.uuid_str, editable=False, max_length=32, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=16, verbose_name='分舵名称')),
                ('announcement', models.TextField(default='', verbose_name='分舵公告')),
                ('official', models.BooleanField(default=False, verbose_name='是否官方')),
                ('does_exist', models.BooleanField(default=True, verbose_name='是否存在')),
            ],
            options={
                'verbose_name': '分舵',
                'verbose_name_plural': '分舵',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('coordinates', django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326, verbose_name='位置坐标')),
                ('location_name', models.CharField(default='', max_length=16, verbose_name='分舵位置名称')),
                ('address', models.CharField(default='', max_length=64, verbose_name='分舵详细地址')),
                ('does_exist', models.BooleanField(default=True, verbose_name='是否存在')),
                ('branch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='location', related_query_name='location', serialize=False, to='association.Branch', verbose_name='分舵')),
            ],
            options={
                'verbose_name': '分舵位置',
                'verbose_name_plural': '分舵位置',
            },
        ),
        migrations.AddIndex(
            model_name='branch',
            index=models.Index(fields=['id', 'does_exist'], name='association_id_7443f6_idx'),
        ),
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['branch'], name='association_branch__d486dc_idx'),
        ),
    ]