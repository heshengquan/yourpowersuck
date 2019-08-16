import datetime
import xlrd, os
import requests
import xlwt
from django.contrib import admin
from utils.access_token import get_access_token
# Register your models here.
from django.http import StreamingHttpResponse

from utils.admin_site import admin_site
from .models import Goods, GoodsImage, Order, Address, DeliveryRecord, GoodsAidRecord, ExpressPrice, CountSteps


class GoodsAdmin(admin.ModelAdmin):
    readonly_fields = ('id', )
    fields = ('id', 'name', 'price', 'ever_price', 'description', 'amount_sold',
              'amount_remain', 'does_exist', 'express_fee', 'aid')


class GoodsImageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('goods_id','image_ordering',)
    fields = ('id','goods_id','image', 'image_ordering','does_exist')


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ('id','create_time')
    list_display = ('id', 'goods_id', 'member_id','order_status','pay_time')
    fieldsets = (
        ('订单信息', {
            'fields': ('id', 'goods_id', 'member_id','express_fee','total_fee','create_time',
                       'out_trade_no','transaction_id','pay_time','prepay_id','order_status',)
        }),
        ('快递相关', {
            'fields': ('address_id','address_name','address_phone','address_detail',
                       'express_type','express_num')
        }),
    )
    list_filter = ('goods_id', 'order_status','pay_time', 'create_time',)
    actions = ("saveexecl",)
    ordering = ('-create_time',)
    search_fields = ('out_trade_no','address_name','address_phone')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def saveexecl(self,request,queryset):
        Begin = xlwt.Workbook()
        sheet = Begin.add_sheet("order")
        sheet.write(0, 0, '订单号')
        sheet.write(0, 1, '总价')
        sheet.write(0, 2, '姓名')
        sheet.write(0, 3, '电话')
        sheet.write(0, 4, '详细地址')
        cols = 1
        for order in queryset:
            # you need write colms
            sheet.write(cols,0,order.out_trade_no)
            sheet.write(cols,1,order.total_fee)
            sheet.write(cols,2,order.address_name)
            sheet.write(cols,3,order.address_phone)
            sheet.write(cols,4,order.address_detail)
            cols += 1
        # 根据当前系统时间来生成文件名，精确到分钟。
        date = datetime.datetime.now()
        filename = date.strftime("%Y%m%d%H%M")
        filename = 'order' + filename + '.xls'
        Begin.save("%s" %(filename))
        def file_iterator(filename,chuck_size=512):
            with open(filename,"rb") as f:
                while True:
                    c = f.read(chuck_size)
                    if c:
                        yield c
                    else:
                        break
        response = StreamingHttpResponse(file_iterator(filename))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(filename)
        return response
    saveexecl.short_description = "导出Excel"            # 按钮显示名字


class AddressAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('name', 'phone',)
    fields = ('id', 'member_id', 'name', 'phone','province_name', 'city_name',
              'county_name', 'detail_info', 'post_num','is_default','does_exist')
    search_fields = ('id', 'phone', 'name')
    list_filter = ('is_default', 'does_exist',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class DeliveryRecordAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'create_time')
    list_display = ('id', 'create_time', 'failure', 'is_update')
    fields = ('id', 'create_time', 'filename', 'is_update', 'amount', 'remark')
    list_filter = ('create_time', 'is_update', )
    actions = ("readexecl",)
    ordering = ('-create_time',)

    def readexecl(self, request, queryset):
        # 每次只允许更新一个文件
        if queryset.count() != 1:
            return False
        delivery_record = queryset[0]
        filename = 'media/{}'.format(delivery_record.filename)
        sheet_index=0
        table_header_row=0
        # 打开excel文件读取数据
        data = xlrd.open_workbook(filename)
        table = data.sheet_by_index(sheet_index)
        nrows = table.nrows
        nclos = table.ncols
        # 获取表头行的信息，为一个字典
        header_row_data = table.row_values(table_header_row)
        # 将每行的信息放入一个字典，再将字典放入一个列表中
        record_list = []
        for rownum in range(1, nrows):
            rowdata = table.row_values(rownum)
            # 如果rowdata有值，
            if rowdata:
                dict = {}
                for j in [0, 1, 2, 3, 4, 5]:
                    # 将excel中的数据分别设置成键值对的形式，放入字典，如‘标题’：‘name’；
                    dict[header_row_data[j]] = rowdata[j]
                record_list.append(dict)

        access_token = get_access_token()
        amount = 0
        failure = 0
        remark = ''
        for record in record_list:
            try:
                out_trade_no = record['订单号']
                order = Order.objects.get(out_trade_no=out_trade_no, order_status='has_paid')
                if order.address_id.phone != record['电话']:
                    failure += 1
                    remark += record['订单号'] + '订单信息匹配有误       '
                    continue
                order.order_status = 'has_posted'
                order.express_type = record['快递公司']
                order.express_num = str(record['运单号'])
                order.save()
                data = {
                    "touser": order.member_id.openid,
                    "template_id": '6-5tFGpGD9zV3_aAMgL6P9g5-LRnwNO4lrjnH474Z3c',
                    "page": 'pages/me/main',
                    "form_id": order.prepay_id,
                    "data": {
                        'keyword1': {
                            'value': order.goods_id.name,
                        },
                        'keyword2': {
                            'value': '您的商品已发货，正向您飞速赶来，请注意查收哦！',
                        },
                        'keyword3': {
                            'value': order.express_num,
                        },
                        'keyword4': {
                            'value': order.express_type,
                        }
                    },
                }
                push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                    access_token)
                requests.post(push_url, json=data, timeout=3)
                amount += 1
            except:
                failure += 1
                remark += record['订单号'] + '保存订单信息或发送消息通知失败       '
        delivery_record.is_update = True
        delivery_record.amount = amount
        delivery_record.failure = failure
        delivery_record.remark = remark
        delivery_record.save()
        return 'ok'

    readexecl.short_description = "更新Excel到数据库(每次一个文件）"  # 按钮显示名字


class GoodsAidRecordAdmin(admin.ModelAdmin):
    readonly_fields = ('datetime',)
    list_display = ('goods', 'launch_member', 'aid_member','datetime')
    fields = ('goods', 'launch_member', 'aid_member' )
    list_filter = ('goods',)
    search_fields = ('launch_member__name', 'aid_member__name')



class ExpressPriceAdmin(admin.ModelAdmin):
    list_display = ('province', 'price',)
    fields = ('province', 'price',)


class CountStepsAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('member', 'order', 'today_steps', 'total_steps')
    fields = ('id', 'member', 'order', 'today_steps', 'total_steps', 'last_count')
    search_fields = ('member__name', 'order__goods_id__name')
    list_filter = ('order__goods_id',)
    ordering = ('total_steps',)


admin_site.register(Goods, GoodsAdmin)
admin_site.register(GoodsImage, GoodsImageAdmin)
admin_site.register(Order, OrderAdmin)
# admin_site.register(Address, AddressAdmin)
admin_site.register(DeliveryRecord, DeliveryRecordAdmin)
# admin_site.register(GoodsAidRecord, GoodsAidRecordAdmin)
admin_site.register(ExpressPrice, ExpressPriceAdmin)
admin_site.register(CountSteps, CountStepsAdmin)