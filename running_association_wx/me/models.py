import datetime

from django.db import models

from utils.global_tools import uuid_str, random_int_6, ten_minutes_from_now
from .managers import MemberManager


# 成员
class Member(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 认证所需字段
    openid = models.CharField(max_length=28, unique=True, verbose_name='微信openid')
    wx_session_key = models.CharField(max_length=128, verbose_name='微信session_key')
    token_hash = models.CharField(max_length=32, verbose_name='用户token的加盐哈希')
    salt = models.CharField(max_length=32, verbose_name='盐')
    last_login = models.DateTimeField(default=datetime.datetime.now, verbose_name='上一次调用微信认证的时间')

    # 舵主/副舵主/参与者的表示
    master_of = models.OneToOneField('association.Branch', on_delete=models.SET_NULL, related_name='master',
                                     related_query_name='master', null=True, blank=True, default=None,
                                     verbose_name='是舵主')
    deputy_of = models.ForeignKey('association.Branch', on_delete=models.SET_NULL, related_name='deputies',
                                  related_query_name='deputy', null=True, blank=True, default=None,
                                  verbose_name='是副舵主')
    member_of = models.ForeignKey('association.Branch', on_delete=models.SET_NULL, related_name='members',
                                  related_query_name='member', null=True, blank=True, default=None,
                                  verbose_name='是分舵参与者')

    name = models.CharField(max_length=32, default='', verbose_name='用户名称')  # 用户名称,若不修改则为拉取的微信昵称
    avatar_url = models.URLField(default='', verbose_name='用户头像URL')  # 头像url从微信中获取
    mobile = models.CharField(max_length=11, default='', verbose_name='手机号')  # 手机号需要调用验证逻辑才能储存
    wx_number = models.CharField(max_length=50, default=None, blank=True, null=True)

    objects = MemberManager()

    @property
    def existing_participation_records(self):
        # 当前用户的所有参与活动记录
        return self.participation_records.get_existing_all()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '成员'
        verbose_name_plural = '成员'
        ordering = ['-last_login']
        indexes = [
            models.Index(fields=['id', 'openid', 'last_login', 'master_of', 'deputy_of', 'member_of']),
        ]


# 成员私有信息
class MemberProfile(models.Model):
    # todo: 二期加详细字段,记得manager里面也要修改
    GENDER_CHOICES = (
        ('1', '男'),
        ('2', '女'),
        ('0', '未知'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='0', verbose_name='用户性别')
    city = models.CharField(max_length=32, default='', verbose_name='用户所在城市')
    province = models.CharField(max_length=16, default='', verbose_name='用户所在省份')
    country = models.CharField(max_length=16, default='', verbose_name='用户所在国家')
    language = models.CharField(max_length=8, default='zh_CN', verbose_name='用户语言')
    marathon_id_num = models.CharField(max_length=32, default='', verbose_name='马拉松证件号')
    real_name = models.CharField(max_length=8, default='', verbose_name='真实姓名')

    member = models.OneToOneField('Member', primary_key=True, on_delete=models.CASCADE, related_name='member_profile',
                                  related_query_name='member_profile', verbose_name='成员')
    marathon_city = models.ForeignKey('CityCode', on_delete=models.SET_NULL, related_name='city_codes',
                             related_query_name='city_code', null=True, blank=True, default=None,
                             verbose_name='所属城市')

    def __str__(self):
        return self.member.name

    class Meta:
        verbose_name = '成员信息'
        verbose_name_plural = '成员信息'
        indexes = [
            models.Index(fields=['member']),
        ]


# 核验手机号
class CheckMobile(models.Model):
    mobile = models.CharField(max_length=11, default='', verbose_name='手机号')
    verification_code = models.PositiveIntegerField(default=random_int_6, verbose_name='验证码')  # 随机生成六位数字
    expire = models.DateTimeField(default=ten_minutes_from_now, verbose_name='过期时间')  # 超过10min为过期
    counter = models.SmallIntegerField(default=0, verbose_name='调用次数')  # 每个用户有10次机会，用完之后要间隔24小时才可以刷新验证机会
    limit_time = models.DateTimeField(null=True, default=None, verbose_name='上一次达到验证上限的时间')

    member = models.OneToOneField('Member', primary_key=True, on_delete=models.CASCADE, related_name='check_mobile',
                                  related_query_name='check_mobile', verbose_name='成员')

    @property
    def has_expired(self):
        # 验证码过期
        return datetime.datetime.now() >= self.expire

    @property
    def reaches_the_limit(self):
        # 达到验证次数上限
        return datetime.datetime.now() - self.limit_time <= datetime.timedelta(days=1)

    def __str__(self):
        return self.member.name

    class Meta:
        verbose_name = '成员'
        verbose_name_plural = '成员'
        indexes = [
            models.Index(fields=['member']),
        ]


class MemberFormId(models.Model):
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='member_formid',
                               related_query_name='member_formids', null=True, blank=True, default=None,
                               verbose_name='成员')
    formid = models.CharField(max_length=50)
    timestamp = models.IntegerField(verbose_name='失效时间戳')
    is_available = models.BooleanField(default=True, verbose_name='是否可用')

    def __str__(self):
        return self.member.name

    class Meta:
        verbose_name = 'FormId'
        verbose_name_plural = 'FormId'
        indexes = [
            models.Index(fields=['member','timestamp','is_available'])
        ]


class CityCode(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='序号')
    province = models.CharField(max_length=20, verbose_name='省份名')
    city = models.CharField(max_length=20, verbose_name='城市名')
    city_id = models.CharField(max_length=10, verbose_name='城市编码')

    def __str__(self):
        return self.city

    class Meta:
        verbose_name = '城市编码'
        verbose_name_plural = '城市编码'
        indexes = [
            models.Index(fields=['id', 'city_id'])
        ]