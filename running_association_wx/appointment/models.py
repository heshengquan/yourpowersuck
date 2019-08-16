from PIL import Image
from django.db import models
import os

from utils.global_tools import uuid_str,MakeThumb,timeStampSecond
from .managers import ActivityManager, ParticipationRecordManager
from django.db.models.fields.files import ImageFieldFile


def get_image_path(instance, filename):
    filename = instance.id + '.' + os.path.splitext(filename)[-1]
    return 'appointment/activity/img/' + filename

# 活动
class Activity(models.Model):
    STATUS_CHOICES = (
        ('has_completed', '已结束'),
        ('is_signing_in', '签到中'),
        ('is_signing_up', '报名中'),
    )

    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    name = models.CharField(max_length=64, default='', verbose_name='活动名称')
    begin = models.DateTimeField(verbose_name='开始时间')
    end = models.DateTimeField(verbose_name='结束时间')
    place = models.CharField(max_length=64, default='', verbose_name='活动地点')
    image = models.ImageField(upload_to=get_image_path, null=True, default=None, verbose_name='活动配图',blank=True)
    thumb_image = models.ImageField(verbose_name='缩略图', upload_to=get_image_path, blank=True, null=True, default=None)
    info = models.TextField(default='', verbose_name='活动须知')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='is_signing_up', verbose_name='活动状态')
    build_up_time = models.DateTimeField(auto_now_add=True, verbose_name='发起时间')
    rechargeable = models.BooleanField(default=False,verbose_name='收费活动')
    money = models.DecimalField(verbose_name='收费金额',max_digits=6,decimal_places=2,default=0.00)
    does_pass = models.BooleanField(verbose_name='是否通过',default=True)

    # 从属关系
    branch = models.ForeignKey('association.Branch', on_delete=models.CASCADE, related_name='activities',
                               related_query_name='activity', verbose_name='主办分舵')
    founder = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='activities_founded',
                                related_query_name='activity_founded', verbose_name='发起者')

    # 是否存在
    does_exist = models.BooleanField(default=True, verbose_name='是否存在')

    objects = ActivityManager()

    def save(self,update_fields = None):
        # 重写图片保存方法
        super(Activity, self).save()
        if self.thumb_image or self.image:
            img_name = self.image.name
            thumb_preview = MakeThumb('media/' + img_name)#image对象
            thumb_path = img_name.split('.')[0] + '_160*90.' + img_name.split('.')[-1]
            thumb_full_path = 'media/' + thumb_path
            thumb_preview.save(thumb_full_path)#将图片保存到这个位置
            self.thumb_image = ImageFieldFile(self, self.thumb_image, thumb_path)
            super(Activity, self).save()

    @property
    def image_name(self):
        # 配图文件名
        if self.image:
            return self.id
        else:
            return 'default'

    @property
    def existing_participation_records(self):
        # 当前活动的所有参与用户记录
        return self.participation_records.get_existing_all()

    @property
    def has_not_completed(self):
        # 当前活动未结束
        return self.status != 'has_completed'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '活动'
        verbose_name_plural = '活动'
        get_latest_by = 'build_up_time'
        ordering = ['-build_up_time']
        indexes = [
            models.Index(fields=['id', 'status', 'build_up_time', 'branch', 'founder', 'does_exist']),
        ]


# 参与记录
class ParticipationRecord(models.Model):
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='participation_records',
                               related_query_name='participation_record', verbose_name='成员')
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='participation_records',
                                 related_query_name='participation_record', verbose_name='活动')
    sign_in_status = models.BooleanField(default=False, verbose_name='签到状态')
    in_time = models.DateTimeField(auto_now_add=True, verbose_name='参与时间')

    # 是否存在
    does_exist = models.BooleanField(default=True, verbose_name='是否存在')

    objects = ParticipationRecordManager()

    def __str__(self):
        return self.member.openid + '-' + self.activity.name + '-' + str(self.sign_in_status)

    class Meta:
        verbose_name = '参与记录'
        verbose_name_plural = '参与记录'
        indexes = [
            models.Index(fields=['member', 'activity', 'does_exist']),
        ]


# 收费活动的收费表
class RechargeableActivity(models.Model):
    STATUS_CHOICES = (
        ('has_created', '已创建'),
        ('has_paid', '已付款'),
    )
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='rechargeable_member', verbose_name='成员')
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='rechargeable_activity', verbose_name='活动')
    money = models.DecimalField(max_digits=6, decimal_places=2,verbose_name='支付金额')
    out_trade_no = models.CharField(verbose_name='商户订单号', max_length=40)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    transaction_id = models.CharField(verbose_name='微信交易单号', max_length=40, null=True, blank=True)
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='付款时间',default=None)
    nonce_str = models.CharField(max_length=40, verbose_name='随机字符串')
    prepay_id = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='has_created', verbose_name='订单状态')

    def __str__(self):
        return self.member.name + ' ' + self.activity.name

    class Meta:
        verbose_name = '收费活动记录'
        verbose_name_plural = '收费活动记录'
        indexes = [
            models.Index(fields=['member', 'activity',]),
        ]

def activity_img_name(instance,filename):
    filename = str(timeStampSecond()) + uuid_str() + os.path.splitext(filename)[-1]
    return os.path.join('appointment/activityImages/', filename)


# 活动图片
class ActivityImages(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    activity = models.ForeignKey('Activity',on_delete=models.CASCADE,related_name='acitivty_image',verbose_name='活动')
    member = models.ForeignKey('me.Member',on_delete=models.CASCADE,related_name='member_image',verbose_name='上传者')
    time = models.DateTimeField(verbose_name='上传时间',auto_now=True)
    img = models.ImageField(upload_to=activity_img_name,verbose_name='活动图片',null=True,default=None)
    tiny_img = models.ImageField(upload_to=activity_img_name,verbose_name='缩略图',null=True,default=None,blank=True)#活动图片得缩略图
    does_exist = models.BooleanField(default=True,verbose_name='是否存在')

    def save(self, *args, **kwargs):
        # 重写图片保存方法
        super(ActivityImages, self).save()
        base, ext = os.path.splitext(self.img.name)
        thumb_preview = MakeThumb(self.img.path,300)
        thumb_path = base + '_tiny' + ext
        #调用Image.save这个函数的时候需要使用绝对路径
        thumb_preview.save('/home/webapp/wechat/running_association_wx/media/'+thumb_path)
        self.tiny_img = ImageFieldFile(self, self.tiny_img, thumb_path)
        super(ActivityImages, self).save()