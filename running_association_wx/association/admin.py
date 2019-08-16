from django.contrib import admin
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.contrib.gis import admin as geoadmin

from utils.admin_site import admin_site
from .models import Branch, Location, BranchFundRecord


class LocationInline(geoadmin.OSMGeoAdmin, admin.StackedInline):
    model = Location
    fields = ('coordinates', 'location_name', 'address',)
    can_delete = False
    max_num = 1
    min_num = 1

    def __init__(self, parent_model, admin_site):
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)
        overrides = FORMFIELD_FOR_DBFIELD_DEFAULTS.copy()
        overrides.update(self.formfield_overrides)
        self.formfield_overrides = overrides
        if self.verbose_name is None:
            self.verbose_name = self.model._meta.verbose_name
        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.model._meta.verbose_name_plural


class BranchAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    fields = ('id', 'name', 'announcement',)
    search_fields = ('name',)
    inlines = [LocationInline, ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(does_exist=True)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BranchFundRecordAdmin(admin.ModelAdmin):
    readonly_fields = ('create_time', 'pay_time', )
    fields = ('branch', 'member', 'money', 'out_trade_no', 'transaction_id',
              'order_status', 'nonce_str', 'prepay_id')
    search_fields = ('branch__name', 'member__name')
    list_filter = ('order_status',)
    list_display = ('branch', 'member', 'money', 'order_status')



admin_site.register(Branch, BranchAdmin)
admin_site.register(BranchFundRecord, BranchFundRecordAdmin)
