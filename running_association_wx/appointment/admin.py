from django.contrib import admin

from utils.admin_site import admin_site
from .models import Activity, ParticipationRecord, RechargeableActivity


class ParticipationRecordInline(admin.StackedInline):
    model = ParticipationRecord
    fields = ('member', 'sign_in_status',)
    can_delete = False
    fk_name = 'activity'
    classes = ['collapse', ]


class ActivityAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'build_up_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'begin', 'end', 'place', 'info', 'status', 'build_up_time', 'image', 'rechargeable', 'money', 'does_pass')
        }),
        ('从属关系', {
            'fields': ('branch', 'founder',)
        }),
    )
    list_display = ('name', 'place', 'status', 'branch', 'rechargeable', 'does_pass',)
    list_display_links = ('branch',)
    list_filter = ('status', 'rechargeable', 'does_pass')
    search_fields = ('name', 'branch__name',)
    inlines = [ParticipationRecordInline, ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(does_exist=True)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RechargeableActivityAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'create_time', 'pay_time', )
    list_display = ('member', 'activity', 'pay_time', 'status', )
    fields = ('member', 'activity', 'money', 'out_trade_no',
              'transaction_id','nonce_str', 'prepay_id', 'status',)
    list_filter = ('status',)
    list_display_links = ('member',)

class ParticipationRecordAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'in_time',)
    list_display = ('member', 'activity', 'does_exist', )
    list_display_links = ('member',)


admin_site.register(Activity, ActivityAdmin)
admin_site.register(RechargeableActivity, RechargeableActivityAdmin)
admin_site.register(ParticipationRecord, ParticipationRecordAdmin)
