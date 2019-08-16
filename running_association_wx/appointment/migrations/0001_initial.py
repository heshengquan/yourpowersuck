# Generated by Django 2.0.2 on 2018-05-23 13:10

import appointment.models
from django.db import migrations, models
import django.db.models.deletion
import utils.global_tools


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('association', '0001_initial'),
        ('me', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.CharField(default=utils.global_tools.uuid_str, editable=False, max_length=32, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=15, verbose_name='活动名称')),
                ('begin', models.DateTimeField(verbose_name='开始时间')),
                ('end', models.DateTimeField(verbose_name='结束时间')),
                ('place', models.CharField(default='', max_length=50, verbose_name='活动地点')),
                ('image', models.ImageField(default=None, null=True, upload_to=appointment.models.get_image_path, verbose_name='活动配图')),
                ('info', models.TextField(default='', verbose_name='活动须知')),
                ('status', models.CharField(choices=[('has_completed', '已结束'), ('is_signing_in', '签到中'), ('is_signing_up', '报名中')], default='is_signing_up', max_length=16, verbose_name='活动状态')),
                ('build_up_time', models.DateTimeField(auto_now_add=True, verbose_name='发起时间')),
                ('does_exist', models.BooleanField(default=True, verbose_name='是否存在')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', related_query_name='activity', to='association.Branch', verbose_name='主办分舵')),
                ('founder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities_founded', related_query_name='activity_founded', to='me.Member', verbose_name='发起者')),
            ],
            options={
                'verbose_name': '活动',
                'verbose_name_plural': '活动',
                'ordering': ['-build_up_time'],
                'get_latest_by': 'build_up_time',
            },
        ),
        migrations.CreateModel(
            name='ParticipationRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sign_in_status', models.BooleanField(default=False, verbose_name='签到状态')),
                ('in_time', models.DateTimeField(auto_now_add=True, verbose_name='参与时间')),
                ('does_exist', models.BooleanField(default=True, verbose_name='是否存在')),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participation_records', related_query_name='participation_record', to='appointment.Activity', verbose_name='活动')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participation_records', related_query_name='participation_record', to='me.Member', verbose_name='成员')),
            ],
            options={
                'verbose_name': '参与记录',
                'verbose_name_plural': '参与记录',
            },
        ),
        migrations.AddIndex(
            model_name='participationrecord',
            index=models.Index(fields=['member', 'activity', 'does_exist'], name='appointment_member__97ce35_idx'),
        ),
        migrations.AddIndex(
            model_name='activity',
            index=models.Index(fields=['id', 'status', 'build_up_time', 'branch', 'founder', 'does_exist'], name='appointment_id_c56081_idx'),
        ),
    ]