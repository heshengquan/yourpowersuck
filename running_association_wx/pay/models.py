from django.db import models

# Create your models here.

from utils.global_tools import uuid_str


# 商品
class Goods(models.Model):
    # 唯一标识
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    name = models.CharField(max_length=32, null=False, verbose_name='商品名称')
    price = models.DecimalField(max_digits=8,decimal_places=2,verbose_name='商品单价')
    ever_price = models.DecimalField(max_digits=8,decimal_places=2,verbose_name='商品原价')
    description = models.TextField(verbose_name='商品描述', null=True, blank=True)
    amount_sold = models.IntegerField(verbose_name='已售')
    amount_remain = models.IntegerField(verbose_name='库存')
    express_fee = models.DecimalField(max_digits=8,decimal_places=2,verbose_name='快递费')
    does_exist = models.BooleanField(default=True, verbose_name='是否上架')
    aid = models.IntegerField(verbose_name='助攻次数', default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品'
        indexes = [
            models.Index(fields=['id']),
        ]



# 商品图片
class GoodsImage(models.Model):
    goods_id = models.ForeignKey('Goods',on_delete=models.CASCADE, related_name='goods_image', verbose_name='商品')
    image = models.ImageField(upload_to='payment/goods/img', null=True, default=None, verbose_name='商品配图')
    image_ordering = models.IntegerField(verbose_name='图片顺序')
    does_exist = models.BooleanField(default=True, verbose_name='是否使用')

    def __str__(self):
        return self.goods_id.name

    class Meta:
        verbose_name = '商品图片'
        verbose_name_plural = '商品图片'
        indexes = [
            models.Index(fields=['goods_id','image_ordering']),
        ]


# 订单
class Order(models.Model):
    STATUS_CHOICES = (
        ('has_created', '已创建'),
        ('has_paid', '已付款'),
        ('has_posted', '已发货'),
    )
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    goods_id = models.ForeignKey('Goods',on_delete=models.CASCADE, related_name='goods_name', verbose_name='商品名称')
    member_id = models.ForeignKey('me.Member',on_delete=models.CASCADE, related_name='member_id', verbose_name='用户id')
    express_fee = models.DecimalField(verbose_name='快递费',max_digits=8,decimal_places=2)
    total_fee = models.DecimalField(max_digits=8,decimal_places=2,verbose_name='商品总价')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    out_trade_no = models.CharField(verbose_name='商户订单号',max_length=40)
    transaction_id = models.CharField(verbose_name='微信交易单号',max_length=40,null=True,blank=True)
    pay_time = models.DateTimeField(null=True,blank=True,verbose_name='付款时间')
    order_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='has_created', verbose_name='订单状态')
    nonce_str = models.CharField(max_length=40,verbose_name='随机字符串')
    address_id = models.ForeignKey('Address',on_delete=models.CASCADE, related_name='orderaddr_addressid', verbose_name='地址id')
    express_type = models.CharField(max_length=10,verbose_name='快递公司',null=True,blank=True)
    express_num = models.CharField(max_length=30,verbose_name='快递单号',null=True,blank=True)
    prepay_id = models.CharField(max_length=50, blank=True, null=True)
    address_name = models.CharField(max_length=20,blank=True,null=True,default='',verbose_name='收货人')
    address_phone = models.CharField(max_length=20, blank=True, null=True, default='',verbose_name='联系方式')
    address_detail = models.CharField(max_length=60, blank=True, null=True, default='',verbose_name='具体地址')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = '订单'
        indexes = [
            models.Index(fields=['id','goods_id','member_id','total_fee','out_trade_no','nonce_str']),
        ]


# 订单商品表
class OrderGoods(models.Model):
    order_id = models.ForeignKey('Order',on_delete=models.CASCADE, related_name='order_id', verbose_name='订单')
    goods_id = models.ForeignKey('Goods',on_delete=models.CASCADE, related_name='goods_id', verbose_name='商品名称')
    amount = models.IntegerField(verbose_name='数量')
    price = models.DecimalField(verbose_name='单价',max_digits=8,decimal_places=2)

    def __str__(self):
        return self.order_id.id

    class Meta:
        verbose_name = '订单商品'
        verbose_name_plural = '订单商品'
        indexes = [
            models.Index(fields=['goods_id','order_id']),
        ]


#  收货地址
class Address(models.Model):
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    member_id = models.ForeignKey('me.Member',on_delete=models.CASCADE, related_name='member_address', verbose_name='用户id')
    name = models.CharField(max_length=20,verbose_name='收货人')
    phone = models.CharField(max_length=20,verbose_name='联系电话')
    province_name = models.CharField(max_length=10,verbose_name='省份')
    city_name = models.CharField(max_length=10,verbose_name='城市')
    county_name = models.CharField(max_length=10,verbose_name='行政区')
    detail_info = models.CharField(max_length=50,verbose_name='详细地址')
    post_num = models.CharField(max_length=10,verbose_name='邮编')
    is_default = models.BooleanField(default=True,verbose_name='是否默认使用')
    does_exist = models.BooleanField(default=True, verbose_name='是否存在')

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = '收货地址'
        verbose_name_plural = '收货地址'
        indexes = [
            models.Index(fields=['member_id']),
        ]

    @property
    def detail_address(self):
        detail_address = self.province_name + ' ' + self.city_name + ' ' + \
                         self.county_name + ' ' + self.detail_info
        return detail_address


def get_file_path(instance,filename):
    filename = 'file/DeliveryRecord/{}'.format(filename)
    return filename

class DeliveryRecord(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='序号')
    filename = models.FileField(upload_to=get_file_path, verbose_name='发货文件',blank=True, null=True)
    is_update = models.BooleanField(verbose_name='是否更新信息', default=False)
    create_time = models.DateTimeField(verbose_name='上传时间', auto_now_add=True)
    amount = models.IntegerField(verbose_name='此次更新数量', default=0)
    remark = models.TextField(verbose_name='备注', blank=True, null=True)
    failure = models.IntegerField(verbose_name='更新失败的数量', default=-1)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = '发货记录'
        verbose_name_plural = '发货记录'


# 助攻纪录
class GoodsAidRecord(models.Model):
    goods = models.ForeignKey('Goods',on_delete=models.CASCADE, related_name='goods_aid', verbose_name='助攻商品')
    launch_member = models.ForeignKey('me.Member',on_delete=models.CASCADE, related_name='launch_member', verbose_name='助攻发起人')
    aid_member = models.ForeignKey('me.Member',on_delete=models.CASCADE, related_name='aid_member', verbose_name='助攻人')
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='助攻时间')

    def __str__(self):
        return str(self.launch_member.id)

    class Meta:
        verbose_name = '助攻纪录'
        verbose_name_plural = '助攻纪录'


# 快递费
class ExpressPrice(models.Model):
    province = models.CharField(max_length=10, verbose_name='省份')
    price = models.IntegerField(verbose_name='首重')

    def __str__(self):
        return self.province

    class Meta:
        verbose_name = '快递费'
        verbose_name_plural = '快递费'
        indexes = [
            models.Index(fields=['province']),
        ]


# 月赛计步
class CountSteps(models.Model):
    id = models.CharField(max_length=32, primary_key=True, default=uuid_str, editable=False)
    member = models.ForeignKey('me.Member', on_delete=models.CASCADE, related_name='member_count_steps', verbose_name='用户')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_count_steps', verbose_name='订单')
    total_steps = models.IntegerField(verbose_name='当月总步数', default=0)
    today_steps = models.IntegerField(verbose_name='今日步数', default=0)
    last_count = models.IntegerField(verbose_name='最后一次同步的时间', default=0)

    def __str__(self):
        return self.member.name + ' ' + self.order.goods_id.name

    class Meta:
        verbose_name = '月赛计步'
        verbose_name_plural = '月赛计步'
        indexes = [
            models.Index(fields=['order']),
        ]