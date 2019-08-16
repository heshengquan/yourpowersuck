from django.apps import apps
from django.db import models


class MemberQuerySet(models.QuerySet):
    def masters(self):
        return self.filter(master_of__isnull=False)

    def deputies(self):
        return self.filter(deputy_of__isnull=False)

    def runners(self):
        return self.exclude(mobile='')

    def members_in_branch(self):
        return self.filter(member_of__isnull=False)


class MemberManager(models.Manager):
    def get_queryset(self):
        return MemberQuerySet(self.model)

    def get_masters(self):
        """
            获取所有舵主身份的成员
        """
        return self.get_queryset().masters()

    def get_deputies(self):
        """
            获取所有副舵主身份的成员
        """
        return self.get_queryset().deputies()

    def get_runners(self):
        """
            获取所有跑者(经过手机号核验的成员)
        """
        return self.get_queryset().runners()

    def get_members_in_branch(self):
        """
            获取所有加入了分舵的成员
        """
        return self.get_queryset().members_in_branch()

    def remove_all_branch_relationship(self):
        """
            移除所有的分舵关系(master_of,deputy_of,member_of这三个)
        """
        return self.get_queryset().update(master_of=None, deputy_of=None, member_of=None)

    def create(self, *args, **kwargs):
        Member = apps.get_model(app_label='me', model_name='Member')
        member = Member(*args, **kwargs)
        member.save()
        MemberProfile = apps.get_model(app_label='me', model_name='MemberProfile')
        MemberProfile.objects.create(member=member)
        return member
