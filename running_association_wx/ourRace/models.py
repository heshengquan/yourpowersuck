import os
from django.db import models

from utils.global_tools import uuid_str


def get_marathon_image_path(instance, filename):
    filename = instance.id + '.' + os.path.splitext(filename)[-1]
    return 'ourRace/marathon/img/' + filename


# 马拉松信息
class Marathon(models.Model):
    STATUS_CHOICES = (
        ('is_signing_up', '报名中'),
        ('complete_sign', '报名结束'),
        ('has_completed', '已结束'),
    )

    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    name = models.CharField(max_length=64, default='', verbose_name='赛事名称')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='is_signing_up', verbose_name='赛事状态')
    sign_up_begin = models.DateTimeField(verbose_name='报名开始时间')
    sign_up_end = models.DateTimeField(verbose_name='报名结束时间')
    time = models.DateTimeField(verbose_name='比赛开始时间')
    place = models.CharField(max_length=64, default='', verbose_name='赛事地点')
    image = models.ImageField(upload_to=get_marathon_image_path, null=True, default=None, verbose_name='赛事图片',
                              blank=True)
    info = models.ForeignKey('MarathonInfo', null=True, on_delete=models.SET_NULL, related_name='race',
                             verbose_name='赛事章程')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '赛事信息'
        verbose_name_plural = '赛事信息'
        indexes = [
            models.Index(fields=['id', 'name', 'status']),
        ]


# 竞赛项目
class CompetitionEvent(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    marathon = models.ForeignKey('Marathon', on_delete=models.CASCADE, related_name='competition_events',
                                 verbose_name='所从属马拉松赛事')
    name = models.CharField(max_length=64, default='', verbose_name='竞赛项目名称')
    length = models.CharField(max_length=32, default='', verbose_name='里程长度')
    route = models.TextField(default='', verbose_name='路线')
    price = models.DecimalField(verbose_name='报名费用', max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '竞赛项目'
        verbose_name_plural = '竞赛项目'
        indexes = [
            models.Index(fields=['id', 'marathon', 'name']),
        ]


# 赛事章程
class MarathonInfo(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    name = models.CharField(max_length=64, default='', verbose_name='章程名称')
    sponsor = models.TextField(default='', verbose_name='主办运营单位')
    organizer = models.TextField(default='', verbose_name='承办运营单位')
    method_of_competition = models.TextField(default='', verbose_name='竞赛办法')
    method_of_join = models.TextField(default='', verbose_name='参赛办法')
    method_of_reward = models.TextField(default='', verbose_name='奖励办法')
    method_of_punishment = models.TextField(default='', verbose_name='处罚办法')
    insurance = models.TextField(default='', verbose_name='保险')
    contact_way = models.TextField(default='', verbose_name='联系方式')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '赛事章程'
        verbose_name_plural = '赛事章程'
        indexes = [
            models.Index(fields=['id', 'name']),
        ]


# 参与记录
class CompetitionEventParticipationRecord(models.Model):
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='marathon_participation_records',
                               related_query_name='marathon_participation_record', verbose_name='成员')
    competition_event = models.ForeignKey('CompetitionEvent', on_delete=models.CASCADE,
                                          related_name='competition_event_participation_records',
                                          related_query_name='competition_event_participation_record',
                                          verbose_name='竞赛项目')
    branch_id = models.CharField(max_length=32, default='', verbose_name='团报分舵id')  # 如果为空说明是非团报
    marathon_id = models.CharField(max_length=32, default='', verbose_name='马拉松id')
    in_time = models.DateTimeField(auto_now_add=True, verbose_name='参与时间')
    pay_status = models.BooleanField(default=False, verbose_name="是否付款")
    prepay_id = models.CharField(max_length=50, default='', verbose_name='预支付交易会话标识')
    out_trade_no = models.CharField(max_length=40, default='', verbose_name='商户订单号')
    nonce_str = models.CharField(max_length=40, default='', verbose_name='随机字符串')

    def __str__(self):
        return self.member.name + '-' + self.competition_event.marathon.name

    class Meta:
        verbose_name = '马拉松赛事参与记录'
        verbose_name_plural = '马拉松赛事参与记录'
        indexes = [
            models.Index(fields=['member', 'competition_event', "out_trade_no"]),
        ]


# 报名信息
class ParticipationInfo(models.Model):
    GENDER_CHOICES = (
        ('1', '男'),
        ('2', '女'),
        ('0', '未知'),
    )

    CERTIFICATE_TYPE_CHOICES = (
        ("0", "身份证"),
        ("1", "护照"),
        ("2", "军人证"),
    )

    BLOOD_TYPE_CHOICES = (
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
        ('O', 'O'),
        ('N', '其他'),
    )
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, verbose_name='成员')
    name = models.CharField(max_length=32, default='', verbose_name='姓名')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='0', verbose_name='性别')
    certificate_type = models.CharField(max_length=10, choices=CERTIFICATE_TYPE_CHOICES, default='0',
                                        verbose_name='证件类型')
    certificate_num = models.CharField(max_length=32, default='', verbose_name='证件号')
    birthday = models.CharField(max_length=32, default='', verbose_name="生日")
    national = models.CharField(max_length=32, default='', verbose_name="民族")
    email = models.CharField(max_length=32, default='', verbose_name='邮箱')
    mobile = models.CharField(max_length=11, default='', verbose_name='手机号')
    blood_type = models.CharField(max_length=2, choices=BLOOD_TYPE_CHOICES, default='N', verbose_name='血型')
    emergency_contact = models.CharField(max_length=32, default='', verbose_name='紧急联系人')
    emergency_contact_mobile = models.CharField(max_length=11, default='', verbose_name='紧急联系人电话')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '报名信息'
        verbose_name_plural = '报名信息'
        indexes = [
            models.Index(fields=['id', 'member']),
        ]


def get_cloth_image_path(instance, filename):
    filename = instance.id + '.' + os.path.splitext(filename)[-1]
    return '/ourRace/number_cloth/image/ao_ye/' + filename


# 奥野号码布信息
class AoNumberClothInfo(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    # 基本信息
    number = models.CharField(max_length=8, default='', verbose_name='参赛号')
    group_name = models.CharField(max_length=8, default='', verbose_name='组别')
    name = models.CharField(max_length=32, default='', verbose_name='姓名')
    gender = models.CharField(max_length=1, default='', verbose_name='性别')
    certificate_type = models.CharField(max_length=16, default='身份证', verbose_name='证件类型')
    certificate_num = models.CharField(max_length=32, default='', verbose_name='证件号')
    mobile = models.CharField(max_length=11, default='', verbose_name='手机号')
    clothes_size = models.CharField(max_length=12, default='', verbose_name='服装尺寸')
    country = models.CharField(max_length=2, default='CHN', verbose_name='国籍')
    image = models.ImageField(upload_to=get_cloth_image_path, null=True, default=None, verbose_name='号码布图片',
                              blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '号码布信息'
        verbose_name_plural = '号码布信息'
        indexes = [
            models.Index(fields=['id']),
        ]
