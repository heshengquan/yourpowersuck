# Generated by Django 2.0.2 on 2018-12-16 22:07

import datetime
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import poll.models
import utils.global_tools


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('me', '0002_auto_20181211_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberPollingRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote_date', models.DateField(auto_now_add=True, verbose_name='投票日期')),
            ],
            options={
                'verbose_name': '投票图片',
                'verbose_name_plural': '投票图片',
            },
        ),
        migrations.CreateModel(
            name='PollingActivity',
            fields=[
                ('id', models.CharField(default=utils.global_tools.uuid_str, editable=False, max_length=32, primary_key=True, serialize=False)),
                ('pub_date', models.DateTimeField(default=datetime.datetime.now, verbose_name='发布时间')),
                ('name', models.CharField(default='', max_length=64, verbose_name='投票活动名称')),
                ('info', models.TextField(default='', verbose_name='投票活动信息')),
                ('status', models.CharField(choices=[('has_completed', '已结束'), ('is_polling', '投票中')], default='is_polling', max_length=16, verbose_name='状态')),
                ('image', models.ImageField(blank=True, default=None, null=True, upload_to=poll.models.get_activity_image_path, verbose_name='投票活动图片')),
                ('is_people', models.BooleanField(default=True, verbose_name='是否为人')),
                ('limit_per_day', models.IntegerField(verbose_name='每天投票限制次数')),
            ],
            options={
                'verbose_name': '投票活动',
                'verbose_name_plural': '投票活动',
            },
        ),
        migrations.CreateModel(
            name='PollingItem',
            fields=[
                ('id', models.CharField(default=utils.global_tools.uuid_str, editable=False, max_length=32, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=32, null=True, verbose_name='名称')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='电话号码')),
                ('address', models.CharField(blank=True, default='', max_length=50, null=True, verbose_name='收奖地址')),
                ('votes', models.IntegerField(blank=True, default=0, null=True, verbose_name='票数')),
                ('img_limits', models.IntegerField(blank=True, default=6, null=True, verbose_name='上传图片限制')),
                ('pub_date', models.DateTimeField(blank=True, null=True, verbose_name='报名时间')),
                ('is_successful', models.BooleanField(default=False, verbose_name='报名成功')),
                ('is_luckystar', models.BooleanField(default=False, verbose_name='是否为锦鲤')),
                ('coordinates', django.contrib.gis.db.models.fields.PointField(blank=True, geography=True, null=True, srid=4326, verbose_name='位置坐标')),
                ('avatar', models.ImageField(blank=True, default=None, null=True, upload_to=poll.models.get_avatar_image_path, verbose_name='头像')),
                ('two_bar_codes', models.CharField(blank=True, default=None, max_length=100, null=True, verbose_name='二维码')),
            ],
            options={
                'verbose_name': '投票条目',
                'verbose_name_plural': '投票条目',
            },
        ),
        migrations.CreateModel(
            name='PollingItemCity',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20, verbose_name='城市')),
                ('number', models.IntegerField(default=0, verbose_name='报名成功人数')),
                ('polling_activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polling_activity_city', to='poll.PollingActivity', verbose_name='投票活动')),
            ],
            options={
                'verbose_name': '投票城市',
                'verbose_name_plural': '投票城市',
            },
        ),
        migrations.CreateModel(
            name='PollingItemImages',
            fields=[
                ('id', models.CharField(default=utils.global_tools.uuid_str, editable=False, max_length=32, primary_key=True, serialize=False)),
                ('image', models.ImageField(default=None, null=True, upload_to=poll.models.get_item_image_path, verbose_name='原图')),
                ('is_avatar', models.BooleanField(default=False, verbose_name='是否为头图')),
                ('does_exist', models.BooleanField(default=True, verbose_name='是否存在')),
                ('thumb', models.ImageField(default=None, null=True, upload_to=poll.models.get_item_image_path, verbose_name='头像或二维码缩略图')),
                ('preview', models.ImageField(blank=True, default=None, null=True, upload_to=poll.models.get_item_image_path, verbose_name='预览图')),
                ('polling_item', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', related_query_name='image', to='poll.PollingItem', verbose_name='投票条目')),
            ],
            options={
                'verbose_name': '投票图片',
                'verbose_name_plural': '投票图片',
            },
        ),
        migrations.AddField(
            model_name='pollingitem',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='city', to='poll.PollingItemCity', verbose_name='城市'),
        ),
        migrations.AddField(
            model_name='pollingitem',
            name='member',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polling_memebers', related_query_name='polling_member', to='me.Member', verbose_name='发起者'),
        ),
        migrations.AddField(
            model_name='pollingitem',
            name='polling_activity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polling_activities', related_query_name='polling_activity', to='poll.PollingActivity', verbose_name='投票活动'),
        ),
        migrations.AddIndex(
            model_name='pollingactivity',
            index=models.Index(fields=['id', 'pub_date'], name='poll_pollin_id_09bf2f_idx'),
        ),
        migrations.AddField(
            model_name='memberpollingrecord',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polling_records', related_query_name='polling_record', to='me.Member', verbose_name='成员'),
        ),
        migrations.AddField(
            model_name='memberpollingrecord',
            name='polling_activity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='polling_records', related_query_name='polling_record', to='poll.PollingActivity', verbose_name='投票活动'),
        ),
        migrations.AddField(
            model_name='memberpollingrecord',
            name='vote_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vote_items', related_query_name='vote_item', to='poll.PollingItem', verbose_name='投票条目'),
        ),
        migrations.AddIndex(
            model_name='pollingitemimages',
            index=models.Index(fields=['id'], name='poll_pollin_id_8f0a60_idx'),
        ),
        migrations.AddIndex(
            model_name='pollingitemcity',
            index=models.Index(fields=['id'], name='poll_pollin_id_d9edcb_idx'),
        ),
        migrations.AddIndex(
            model_name='pollingitem',
            index=models.Index(fields=['id', 'votes'], name='poll_pollin_id_c24456_idx'),
        ),
        migrations.AddIndex(
            model_name='memberpollingrecord',
            index=models.Index(fields=['id'], name='poll_member_id_90b764_idx'),
        ),
    ]