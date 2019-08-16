from django.apps import apps
from django.db import models


class ActivityQuerySet(models.QuerySet):
    def existing_all(self):
        return self.filter(does_exist=True, does_pass=True)

    def delete_all(self):
        return self.update(does_exist=False)


class ActivityManager(models.Manager):
    def get_queryset(self):
        return ActivityQuerySet(self.model)

    def get_existing_all(self):
        """
            获取所有存在的活动
        """
        return self.get_queryset().existing_all()

    def delete_all(self):
        """
            软删除所有的活动
        """
        return self.get_queryset().update(does_exist=False)

    def create(self, *args, **kwargs):
        Activity = apps.get_model(app_label='appointment', model_name='Activity')
        activity = Activity(*args, **kwargs)
        activity.save()
        ParticipationRecord = apps.get_model(app_label='appointment', model_name='ParticipationRecord')
        ParticipationRecord.objects.create(member=activity.founder, activity=activity)
        return activity


class ParticipationRecordQuerySet(models.QuerySet):
    def existing_all(self):
        return self.filter(does_exist=True)

    def delete_all(self):
        return self.update(does_exist=False)


class ParticipationRecordManager(models.Manager):
    def get_queryset(self):
        return ParticipationRecordQuerySet(self.model)

    def get_existing_all(self):
        """
            获取所有存在的参与记录
        """
        return self.get_queryset().existing_all()

    def delete_all(self):
        """
            软删除所有的参与记录
        """
        return self.get_queryset().update(does_exist=False)
