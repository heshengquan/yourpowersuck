from django.contrib import admin

from utils.admin_site import admin_site
from utils.admin_filter import MemberIsRunnerFilter, MemberInBranchFilter
from .models import Member, MemberProfile, CityCode


class MemberProfileInline(admin.StackedInline):
    model = MemberProfile
    can_delete = False
    max_num = 1
    min_num = 1


class MemberAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'last_login',)
    fieldsets = (
        ('与分舵的关系', {
            'fields': ('master_of', 'deputy_of', 'member_of',)
        }),
        ('基本信息', {
            'fields': ('id', 'last_login', 'name', 'avatar_url', 'mobile', 'wx_number')
        }),
    )
    list_display = ('name', 'mobile', 'member_of',)
    list_display_links = ('name',)
    list_filter = (MemberIsRunnerFilter, MemberInBranchFilter, 'member_profile__gender',)
    search_fields = ('name', 'member_of__name',)
    inlines = [MemberProfileInline, ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CityCodeAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('city_id', 'province', 'city', )
    list_display_links = ('city_id',)
    list_filter = ('province',)
    search_fields = ('city', 'city_id',)


admin_site.register(Member, MemberAdmin)
admin_site.register(CityCode, CityCodeAdmin)