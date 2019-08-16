from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group


class YourPowerSuckAdminSite(AdminSite):
    site_header = '约跑社后台管理系统'
    site_title = '约跑社后台管理系统'
    index_title = '站点管理'


admin_site = YourPowerSuckAdminSite(name='your-power-suck-admin')

