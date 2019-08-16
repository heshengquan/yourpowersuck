from django.contrib.gis.db import models as geo_models
from django.db import models

from utils.global_tools import uuid_str
from .managers import BranchManager


def get_image_path(instance, filename=None):
    # 确定图片文件存储路径,并且以'id.jpg'命名
    filename = instance.id + '.jpg'
    # 这是一个相对路径，是在MEDIA_ROOT下面的一个路径
    return 'association/img/{0}'.format(filename)

# 分舵
class Branch(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    name = models.CharField(max_length=16, default='', verbose_name='分舵名称')
    announcement = models.TextField(default='', verbose_name='分舵公告')
    image = models.ImageField(upload_to=get_image_path, null=True, default=None, verbose_name='分舵配图')
    members_number = models.IntegerField(default=0 ,verbose_name='分舵人数')
    activities_number = models.IntegerField(default=0, verbose_name='活动数量')
    influence_number = models.IntegerField(default=0, verbose_name='影响力')
    fund = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='分舵基金', default=0)

    # 是否官方
    # todo:第二个版本记得到api和视图和admin里面加上这个
    official = models.BooleanField(default=False, verbose_name='是否官方')

    # 是否存在
    does_exist = models.BooleanField(default=True, verbose_name='是否存在')

    objects = BranchManager()

    def save(self,update_fields = None):
        # 重写分舵保存人数，活动数，影响力的方法
        super(Branch, self).save()
        self.members_number = self.members.count()
        self.activities_number = self.existing_activities.count()
        self.influence_number = self.influence
        super(Branch, self).save()

    @property
    def existing_activities(self):
        # 当前分舵的所有活动
        return self.activities.get_existing_all()

    @property
    def influence(self):
        # 当前分舵的影响力(此分舵活动参与的总人数*50% + 此分舵人数*50%然后取整)
        return int(sum(activity.existing_participation_records.count() for activity in
                       self.existing_activities) + self.members.count())

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '分舵'
        verbose_name_plural = '分舵'
        indexes = [
            models.Index(fields=['id', 'does_exist']),
        ]

    @property
    def image_name(self):
        # 分舵配图文件名
        if self.image:
            return self.id
        else:
            return 'default'



# 分舵位置
class Location(models.Model):
    coordinates = geo_models.PointField(verbose_name="位置坐标", geography=True)
    location_name = models.CharField(max_length=16, default='', verbose_name='分舵位置名称')
    address = models.CharField(max_length=64, default='', verbose_name='分舵详细地址')

    # 是否存在
    does_exist = models.BooleanField(default=True, verbose_name='是否存在')

    branch = models.OneToOneField('Branch', primary_key=True, on_delete=models.CASCADE, related_name='location',
                                  related_query_name='location', verbose_name='分舵')

    def __str__(self):
        return self.location_name

    class Meta:
        verbose_name = '分舵位置'
        verbose_name_plural = '分舵位置'
        indexes = [
            models.Index(fields=['branch']),
        ]


# 分舵基金记录
class BranchFundRecord(models.Model):
    STATUS_CHOICES = (
        ('has_created', '已创建'),
        ('has_paid', '已付款'),
        ('has_posted', '已发货'),
    )
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, related_name='branch_fund', verbose_name='所属分舵')
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='member_branch_fund',
                               verbose_name='贡献成员')
    money = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='贡献额')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    out_trade_no = models.CharField(verbose_name='商户订单号', max_length=40, null=True, blank=True)
    transaction_id = models.CharField(verbose_name='微信交易单号', max_length=40, null=True, blank=True)
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='付款时间')
    order_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='has_created', verbose_name='订单状态')
    nonce_str = models.CharField(max_length=40, verbose_name='随机字符串', null=True, blank=True)
    prepay_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.member.name

    class Meta:
        verbose_name = '分舵基金记录'
        verbose_name_plural = '分舵基金记录'
        indexes = [
            models.Index(fields=['branch']),
        ]