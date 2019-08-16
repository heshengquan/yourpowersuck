from django.contrib import admin

from utils.admin_site import admin_site
from .models import Race


class RaceAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    fields = ('id', 'name', 'sign_up_date', 'deadline_date', 'start_date', 'image', 'status', 'detail')

    def has_delete_permission(self, request, obj=None):
        return False


admin_site.register(Race, RaceAdmin)
