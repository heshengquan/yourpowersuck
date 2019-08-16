from django.db import models

from utils.global_tools import uuid_str


def get_image_path(instance, filename=None):
    # 确定图片文件存储路径,并且以'id.jpg'命名
    filename = instance.id + '.jpg'
    # 这是一个相对路径，是在MEDIA_ROOT下面的一个路径
    return 'running/race/img/{0}'.format(filename)


# 赛事
class Race(models.Model):
    STATUS_CHOICES = (
        ('has_completed', '已结束'),
        ('is_signing_up', '报名中'),
        ('does_not_open', '未开启'),
    )

    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)

    name = models.CharField(max_length=64, default='', verbose_name='赛事名称')
    sign_up_date = models.DateField(verbose_name='报名日期', null=True, blank=True)
    deadline_date = models.DateField(verbose_name='截止日期', null=True, blank=True)
    start_date = models.DateField(verbose_name='赛事开始日期', null=True, blank=True)
    image = models.ImageField(upload_to=get_image_path, null=True, default=None, verbose_name='赛事配图')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='does_not_open', verbose_name='赛事状态')
    detail = models.TextField(default='', verbose_name='赛事详情')
    followers = models.ManyToManyField('me.Member', related_name='followed_races', related_query_name='followed_race',
                                       editable=False, verbose_name='关注者')

    @property
    def image_name(self):
        # 配图文件名
        if self.image:
            return self.id
        else:
            return 'default'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '赛事'
        verbose_name_plural = '赛事'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['id', 'status', ]),
        ]
