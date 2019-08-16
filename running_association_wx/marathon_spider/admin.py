from django.contrib import admin

from utils.admin_site import admin_site
from .models import Marathon, MarathonQueryRecord, MarathonData


class MarathonAdmin(admin.ModelAdmin):
    fields = ('date', 'name', 'project', 'chip_time', 'clock_gun_time', 'is_pb', 'member', 'sex', 'city', 'age')
    list_display = ('name', 'member', 'sex', 'chip_time', 'project', 'is_pb', 'age', 'age_pb')
    list_filter = ('sex', 'project', 'is_pb', 'age', 'age_pb')
    ordering = ['member__name', 'age', 'chip_time']
    search_fields = ('member__member_profile__marathon_id_num', 'member__member_profile__real_name',)
         

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MarathonDataAdmin(admin.ModelAdmin):
    fields = ('real_name', 'id_num', 'name', 'project', 'chip_time', 'clock_gun_time', 'is_pb', 'sex')
    list_display = ('real_name', 'id_num', 'name', 'project', 'chip_time', 'is_pb', 'sex')
    list_filter = ('is_pb', 'sex')


# class MarathonQueryRecordAdmin(admin.ModelAdmin):
#     fields = ('member',)
#
#     def has_add_permission(self, request):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False


admin_site.register(Marathon, MarathonAdmin)
# admin_site.register(MarathonQueryRecord, MarathonQueryRecordAdmin)
admin_site.register(MarathonData, MarathonDataAdmin)
