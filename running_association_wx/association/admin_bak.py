from django.contrib import admin

from utils.admin_site import admin_site
from .models import Branch, Location


class LocationInline(admin.StackedInline):
    model = Location
    fields = ('coordinates', 'location_name', 'address',)
    can_delete = False
    max_num = 1
    min_num = 1


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


admin_site.register(Branch, BranchAdmin)
