import datetime

import os

import zlib
from django.contrib.gis.geos import Point
from django.db import models
from django.contrib.gis.db import models as geo_models
from django.db.models.fields.files import ImageFieldFile

from utils.global_tools import uuid_str

from PIL import Image


# 压缩图片函数
def MakeThumb(path, size=128):  # 指定size，在这里表示图片的宽度
    img = Image.open(path)
    width, height = img.size

    if width > size:  # 如果宽度大于指定值，则进行尺寸压缩
        delta = width / size
        height = int(height / delta)
        img.thumbnail((width, height), Image.ANTIALIAS)
    return img


def get_activity_image_path(instance, filename):
    filename = instance.id + '.' + filename.split('.')[-1]
    return 'polling/activity/' + filename

# 投票活动
class PollingActivity(models.Model):
    STATUS_CHOICES = (
        ('has_completed', '已结束'),
        ('is_polling', '投票中'),
    )
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    pub_date = models.DateTimeField(default=datetime.datetime.now, verbose_name='发布时间')
    name = models.CharField(max_length=64, default='', verbose_name='投票活动名称')
    info = models.TextField(default='', verbose_name='投票活动信息')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='is_polling', verbose_name='状态')
    image = models.ImageField(upload_to=get_activity_image_path, null=True, default=None,blank=True,
                              verbose_name='投票活动图片')
    # 考虑兼容"非人的投票项目"
    is_people = models.BooleanField(default=True, verbose_name='是否为人')
    limit_per_day = models.IntegerField(verbose_name='每天投票限制次数')

    @property
    def image_name(self):
        # 配图文件名
        if self.image:
            return str(self.image)
        else:
            return 'default'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '投票活动'
        verbose_name_plural = '投票活动'
        indexes = [
            models.Index(fields=['id', 'pub_date']),
        ]


def get_avatar_image_path(instance, filename):
    filename = instance.id + '.' + filename.split('.')[-1]
    return 'polling/item/avatar/' + filename

# 投票条目
class PollingItem(models.Model):
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)  # 用于标识图片名称
    name = models.CharField(max_length=32, default='', verbose_name='名称', blank=True, null=True)
    phone = models.CharField(max_length=20,verbose_name='电话号码', blank=True, null=True)
    city = models.ForeignKey('PollingItemCity', on_delete=models.CASCADE, related_name='city',
                             verbose_name='城市', blank=True, null=True)
    address = models.CharField(max_length=50, verbose_name='收奖地址', blank=True, null=True, default='')
    votes = models.IntegerField(verbose_name='票数',default=0, blank=True, null=True)
    img_limits = models.IntegerField(verbose_name='上传图片限制',default=6, blank=True, null=True)
    pub_date = models.DateTimeField(auto_now_add=False, verbose_name='报名时间', blank=True, null=True)
    is_successful = models.BooleanField(default=False,verbose_name='报名成功')
    is_luckystar = models.BooleanField(default=False, verbose_name='是否为锦鲤')
    polling_activity = models.ForeignKey('PollingActivity', on_delete=models.CASCADE,
                                         related_name='polling_activities', related_query_name='polling_activity',
                                         verbose_name='投票活动')
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='polling_memebers',
                               related_query_name='polling_member', null=True, blank=True, default=None,
                               verbose_name='发起者')
    coordinates = geo_models.PointField(verbose_name="位置坐标", geography=True, blank=True, null=True)
    avatar  = models.ImageField(verbose_name='头像', upload_to=get_avatar_image_path, blank=True, null=True, default=None)
    two_bar_codes = models.CharField(verbose_name='二维码',max_length=100, default=None, blank=True,null=True)

    def save(self):
        # 重写图片保存方法
        if not self.avatar:
            avatar_img = PollingItemImages.objects.filter(is_avatar=True, does_exist=True, polling_item=self)
            if avatar_img:
                img_name = avatar_img[0].image.name
                thumb_avatar = MakeThumb('media/' + img_name, size=64)
                thumb_path = 'polling/item/avatar/' + str(self.id) + '_64*height.' + img_name.split('.')[-1]
                thumb_full_path = 'media/' + thumb_path
                thumb_avatar.save(thumb_full_path)
                self.avatar = ImageFieldFile(self, self.avatar, thumb_path)
        super(PollingItem, self).save()

    @property
    def image_name(self):
        # 配图文件名
        for image in self.images.all():
            if image.is_avatar == True and image.does_exist == True:
                return str(image.thumb)
        return 'default'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '投票条目'
        verbose_name_plural = '投票条目'
        indexes = [
            models.Index(fields=['id', 'votes']),
        ]


def get_item_image_path(instance, filename):
    filename = instance.id + '.' + filename.split('.')[-1]
    return 'polling/item/img/' + filename

# 投票条目图片
class PollingItemImages(models.Model):
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    image = models.ImageField(upload_to=get_item_image_path, null=True, default=None,
                              verbose_name='原图')
    is_avatar = models.BooleanField(default=False, verbose_name='是否为头图')
    polling_item = models.ForeignKey('PollingItem', on_delete=models.CASCADE, related_name='images',
                                     related_query_name='image', null=True, blank=True, default=None,
                                     verbose_name='投票条目')
    does_exist = models.BooleanField(default=True,verbose_name='是否存在')
    thumb = models.ImageField(upload_to=get_item_image_path, null=True, default=None,
                              verbose_name='头像或二维码缩略图')
    preview = models.ImageField(verbose_name='预览图', upload_to=get_item_image_path, blank=True, null=True, default=None) #  预览图

    def save(self):
        # 重写图片保存方法
        super(PollingItemImages, self).save()
        if self.image:
            img_name = self.image.name
            if self.is_avatar == True:
                thumb_avatar = MakeThumb('media/' + img_name, size=300)
                thumb_path = 'polling/item/img/' + str(self.id) + '_300*height.' + img_name.split('.')[-1]
                thumb_full_path = 'media/' + thumb_path
                thumb_avatar.save(thumb_full_path)
                self.thumb = ImageFieldFile(self, self.thumb, thumb_path)
                super(PollingItemImages, self).save()
            thumb_preview = MakeThumb('media/' + img_name)
            thumb_path = 'polling/item/img/' + str(self.id) + '_128*height.' + img_name.split('.')[-1]
            thumb_full_path = 'media/' + thumb_path
            thumb_preview.save(thumb_full_path)
            self.preview = ImageFieldFile(self, self.preview, thumb_path)
            super(PollingItemImages, self).save()


    def __str__(self):
        return self.id

    class Meta:
        verbose_name = '投票图片'
        verbose_name_plural = '投票图片'
        indexes = [
            models.Index(fields=['id']),
        ]


# 成员投票记录
class MemberPollingRecord(models.Model):
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='polling_records',
                               related_query_name='polling_record', verbose_name='成员')
    polling_activity = models.ForeignKey('PollingActivity', on_delete=models.CASCADE, related_name='polling_records',
                                         related_query_name='polling_record', verbose_name='投票活动')

    vote_date = models.DateField(verbose_name='投票日期',auto_now_add=True)
    vote_item = models.ForeignKey('PollingItem', on_delete=models.CASCADE, related_name='vote_items',
                                     related_query_name='vote_item', null=True, blank=True,
                                     verbose_name='投票条目')
    vote_time = models.DateTimeField(verbose_name='投票时间', auto_now_add=True)

    def __str__(self):
        return self.member.name

    class Meta:
        verbose_name = '投票记录'
        verbose_name_plural = '投票记录'
        indexes = [
            models.Index(fields=['member', 'polling_activity', 'vote_date', 'vote_item']),
        ]


class PollingItemCity(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, verbose_name='城市')
    number = models.IntegerField(verbose_name='报名成功人数', default=0)
    polling_activity = models.ForeignKey('PollingActivity', on_delete=models.CASCADE,
                                         related_name='polling_activity_city', verbose_name='投票活动')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '投票城市'
        verbose_name_plural = '投票城市'
        indexes = [
            models.Index(fields=['id']),
        ]

