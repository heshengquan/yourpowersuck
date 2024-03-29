# Generated by Django 2.0.2 on 2018-12-11 15:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('me', '0002_auto_20181211_1510'),
        ('pay', '0005_auto_20181203_1218'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoodsAidRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True, verbose_name='助攻时间')),
                ('aid_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aid_member', to='me.Member', verbose_name='助攻人')),
            ],
            options={
                'verbose_name': '助攻纪录',
                'verbose_name_plural': '助攻纪录',
            },
        ),
        migrations.AddField(
            model_name='goods',
            name='aid',
            field=models.IntegerField(default=0, verbose_name='助攻次数'),
        ),
        migrations.AddField(
            model_name='ordergoods',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=8, verbose_name='单价'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='goodsaidrecord',
            name='goods',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goods_aid', to='pay.Goods', verbose_name='助攻商品'),
        ),
        migrations.AddField(
            model_name='goodsaidrecord',
            name='launch_member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='launch_member', to='me.Member', verbose_name='助攻发起人'),
        ),
    ]
