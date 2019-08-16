from django.contrib import admin

# Register your models here.
import xlwt
import datetime
from utils.admin_site import admin_site
from .models import PollingActivity, PollingItem, PollingItemImages, PollingItemCity
from django.contrib import admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.contrib.gis import admin as geoadmin
from django.http import StreamingHttpResponse

class PollingActivityAdmin(admin.ModelAdmin):
    readonly_fields = ('id', )
    fields = ('id','name','info','status','image','is_people','limit_per_day','pub_date')
    list_display = ('name','id', 'status')
    list_display_links = ('name',)
    list_filter = ('status','is_people')

admin_site.register(PollingActivity,PollingActivityAdmin)

class PollingItemAdmin(geoadmin.OSMGeoAdmin,admin.ModelAdmin):
    model = PollingItem
    readonly_fields = ('id', )
    fields = ('id','name','phone','city','address','votes','img_limits','is_luckystar',
              'pub_date','is_successful','member','polling_activity','coordinates', 'two_bar_codes','avatar')
    list_display = ('name','id', 'votes','is_successful','city','is_luckystar','pub_date')
    list_display_links = ('id',)
    list_filter = ('is_successful','polling_activity','pub_date','is_luckystar')
    list_editable = ('is_successful', 'is_luckystar')
    raw_id_fields = ['polling_activity','member','city']
    actions = ("saveexecl",)
    ordering = ('pub_date','-votes')
    search_fields = ('name', 'id', 'city__name', 'phone', 'member__id')

    def saveexecl(self,request,queryset):
        Begin = xlwt.Workbook()
        sheet = Begin.add_sheet("items")
        sheet.write(0, 0, '姓名')
        sheet.write(0, 1, '电话')
        sheet.write(0, 2, '城市')
        sheet.write(0, 3, '收奖地址')
        sheet.write(0, 4, '票数')
        cols = 1
        for polling_item in queryset:
            # you need write colms
            sheet.write(cols,0,polling_item.name)
            sheet.write(cols,1,polling_item.phone)
            sheet.write(cols,2,polling_item.city.name)
            sheet.write(cols,3,polling_item.address)
            sheet.write(cols,4,polling_item.votes)
            cols += 1
        # 根据当前系统时间来生成文件名，精确到分钟。
        date = datetime.datetime.now()
        filename = date.strftime("%Y%m%d%H%M")
        filename = 'items' + filename + '.xls'
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
    saveexecl.short_description = "导出Excel"


class PollingItemImagesAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    fields = ('id', 'image', 'is_avatar', 'polling_item','does_exist')
    list_display = ('id', 'is_avatar','does_exist', 'polling_item')
    list_filter = ('is_avatar', 'does_exist')
    list_display_links = ('id',)
    search_fields = ('polling_item__name',)
    raw_id_fields=['polling_item']


class PollingItemCityAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    fields = ('id', 'name', 'number', 'polling_activity',)
    list_display = ('id', 'name', 'number', 'polling_activity',)
    list_filter = ('polling_activity',)
    search_fields = ('name',)
    list_display_links = ('name',)
    ordering = ('number',)
    raw_id_fields = ['polling_activity']

admin_site.register(PollingItem,PollingItemAdmin)
admin_site.register(PollingItemImages,PollingItemImagesAdmin)
admin_site.register(PollingItemCity, PollingItemCityAdmin)