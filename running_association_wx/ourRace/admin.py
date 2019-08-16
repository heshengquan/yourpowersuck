from django.contrib import admin

from utils.admin_site import admin_site
from .models import Marathon, CompetitionEvent, MarathonInfo, CompetitionEventParticipationRecord, ParticipationInfo


class MarathonInLine(admin.StackedInline):
    fields = ("id", "name", "status", "sign_up_begin", "sign_up_end", "time", "place", "image")
    readonly_fields = ('id',)
    model = Marathon
    extra = 1


class MarathonInfoAdmin(admin.ModelAdmin):
    fields = (
        "name", "sponsor", "organizer", "method_of_competition", "method_of_join", "method_of_reward",
        "method_of_punishment", "insurance", "contact_way")
    readonly_fields = ('id',)
    list_display = ('name', 'sponsor')
    inlines = [MarathonInLine, ]


class MarathonAdmin(admin.ModelAdmin):
    fields = ("id", "name", "status", "sign_up_begin", "sign_up_end", "time", "place", "image", "info")
    readonly_fields = ('id',)
    list_display = ("name", "status", "time", "place")


class CompetitionEventAdmin(admin.ModelAdmin):
    fields = ("id", "marathon", "name", "length", "route", "price")
    readonly_fields = ('id',)
    list_display = ("marathon", "name", "length", "price")


class CompetitionEventParticipationRecordAdmin(admin.ModelAdmin):
    autocomplete_fields = ("member", )
    fields = (
        "member", "competition_event", "branch_id", "marathon_id", "pay_status", "prepay_id", "out_trade_no",
        "nonce_str")
    readonly_fields = ('id', "in_time")
    list_display = ("id", "marathon_id", "competition_event", "in_time", "pay_status")


class ParticipationInfoAdmin(admin.ModelAdmin):
    autocomplete_fields = ("member",)
    fields = (
        "id", "member", "name", "gender", "certificate_type", "certificate_num", "birthday", "national", "email",
        "mobile", "blood_type", "emergency_contact", "emergency_contact_mobile")
    readonly_fields = ('id', "member",)
    list_display = ("name", "gender", "certificate_type", "certificate_num", "mobile")


admin_site.register(MarathonInfo, MarathonInfoAdmin)
admin_site.register(Marathon, MarathonAdmin)
admin_site.register(CompetitionEvent, CompetitionEventAdmin)
admin_site.register(CompetitionEventParticipationRecord, CompetitionEventParticipationRecordAdmin)
admin_site.register(ParticipationInfo, ParticipationInfoAdmin)
