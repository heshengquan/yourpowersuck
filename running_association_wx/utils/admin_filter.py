from django.contrib import admin


class MemberIsRunnerFilter(admin.SimpleListFilter):
    """
        是否跑者过滤器
    """
    title = '是否跑者'
    parameter_name = 'is-runner'

    def lookups(self, request, model_admin):
        return (
            ('true', '是跑者'),
            ('false', '不是跑者'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.exclude(mobile='')
        if self.value() == 'false':
            return queryset.filter(mobile='')


class MemberInBranchFilter(admin.SimpleListFilter):
    """
        是否加入分舵过滤器
    """
    title = '是否加入分舵'
    parameter_name = 'in-branch'

    def lookups(self, request, model_admin):
        return (
            ('true', '加入了分舵'),
            ('false', '未加入分舵'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(member_of__isnull=False)
        if self.value() == 'false':
            return queryset.exclude(member_of__isnull=False)
