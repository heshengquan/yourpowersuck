# Generated by Django 2.0.2 on 2018-11-29 17:03

from django.db import migrations, models
import pay.models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0002_order_prepay_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeliveryRecord',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='序号')),
                ('filename', models.FileField(blank=True, null=True, upload_to=pay.models.get_file_path, verbose_name='发货文件')),
                ('is_update', models.BooleanField(default=False, verbose_name='是否更新信息')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='上传时间')),
                ('amount', models.IntegerField(default=0, verbose_name='此次更新数量')),
                ('remark', models.TextField(blank=True, null=True, verbose_name='备注')),
                ('failure', models.IntegerField(default=-1, verbose_name='更新失败的数量')),
            ],
            options={
                'verbose_name': '发货记录',
                'verbose_name_plural': '发货记录',
            },
        ),
    ]
