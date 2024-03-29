# Generated by Django 2.0.2 on 2019-01-02 16:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('me', '0002_auto_20181211_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='CityCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='序号')),
                ('province', models.CharField(max_length=20, verbose_name='省份名')),
                ('city', models.CharField(max_length=20, verbose_name='城市名')),
                ('city_id', models.CharField(max_length=10, verbose_name='城市编码')),
            ],
            options={
                'verbose_name': '城市编码',
                'verbose_name_plural': '城市编码',
            },
        ),
        migrations.AddIndex(
            model_name='citycode',
            index=models.Index(fields=['id', 'city_id'], name='me_citycode_id_e85a27_idx'),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='marathon_city',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='city_codes', related_query_name='city_code', to='me.CityCode', verbose_name='所属城市'),
        ),
    ]
