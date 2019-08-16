from django.db import models

from utils.global_tools import uuid_str


# 马拉松赛事
class Marathon(models.Model):
    SEX_CHOICES = (
        (0, '女'),
        (1, '男'),
    )
    AGE_GROUP = (
        (0, '未知'),
        (1, '29以下'),
        (2, '30-34'),
        (3, '35-39'),
        (4, '40-44'),
        (5, '45-49'),
        (6, '50-54'),
        (7, '55-59'),
        (8, '60-64'),
        (9, '65以上'),
    )
    date = models.DateField(verbose_name='比赛时间')
    name = models.CharField(max_length=64, verbose_name='比赛名称')
    project = models.CharField(max_length=8, verbose_name='项目')
    chip_time = models.TimeField(verbose_name='净计时', default=None, blank=True, null=True)
    clock_gun_time = models.TimeField(verbose_name='枪声成绩', default=None, blank=True, null=True)
    is_pb = models.BooleanField(default=False, verbose_name='是否个人最佳')
    sex = models.IntegerField(choices=SEX_CHOICES, verbose_name='性别', default=1)
    city = models.CharField(verbose_name='城市', null=True, blank=True, default=None, max_length=15)
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='marathons',
                               related_query_name='marathon', verbose_name='成员')
    age = models.IntegerField(verbose_name='年龄组', choices=AGE_GROUP, default=1)
    age_pb = models.BooleanField(verbose_name='年龄组PB', default=False)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '马拉松赛事'
        verbose_name_plural = '马拉松赛事'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['member']),
        ]


# 马拉松查询记录
class MarathonQueryRecord(models.Model):
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    pickled_cookie = models.BinaryField(verbose_name='pickled cookie',blank=True,null=True)
    captcha_img = models.ImageField(upload_to='captcha', null=True, default=None,
                                    verbose_name='验证码图片')
    query_time = models.DateTimeField(auto_now_add=True, verbose_name='查询时间')
    success = models.BooleanField(default=False, verbose_name='是否成功')

    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='marathon_query_records',
                               related_query_name='marathon_query_record', verbose_name='成员')

    def __str__(self):
        return self.member.name + ' 的查询记录'

    class Meta:
        verbose_name = '马拉松查询记录'
        verbose_name_plural = '马拉松查询记录'
        indexes = [
            models.Index(fields=['query_time', 'success', 'member']),
        ]


# 马拉松成绩
class MarathonData(models.Model):
    SEX_CHOICES = (
        (1,'男'),
        (0,'女',)
    )
    real_name = models.CharField(verbose_name='选手姓名', max_length=10)
    id_num = models.CharField(verbose_name='身份证号', max_length=30)
    date = models.DateField(verbose_name='比赛时间')
    name = models.CharField(max_length=64, verbose_name='比赛名称')
    project = models.CharField(max_length=8, verbose_name='项目')
    chip_time = models.TimeField(verbose_name='净计时')
    clock_gun_time = models.TimeField(verbose_name='枪声成绩', default=None, blank=True, null=True)
    is_pb = models.BooleanField(default=False, verbose_name='是否个人最佳')
    sex = models.IntegerField(choices=SEX_CHOICES,verbose_name='性别', default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '马拉松成绩'
        verbose_name_plural = '马拉松成绩'
        indexes = [
            models.Index(fields=['id_num']),
        ]


