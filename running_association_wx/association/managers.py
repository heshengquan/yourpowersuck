from django.apps import apps
from django.contrib.gis.geos import Point
from django.db import models


class BranchQuerySet(models.QuerySet):
    def existing_all(self):
        return self.filter(does_exist=True)


class BranchManager(models.Manager):
    def get_queryset(self):
        return BranchQuerySet(self.model)

    def get_existing_all(self):
        """
            获取所有存在的分舵
        """
        return self.get_queryset().existing_all()

    def create(self, *args, **kwargs):
        member = kwargs.pop('member')
        latitude = kwargs.pop('latitude')
        longitude = kwargs.pop('longitude')
        location_name = kwargs.pop('location_name')
        address = kwargs.pop('address')
        Branch = apps.get_model(app_label='association', model_name='Branch')
        branch = Branch(*args, **kwargs)
        branch.save()
        Location = apps.get_model(app_label='association', model_name='Location')
        Location.objects.create(branch=branch, coordinates=Point(longitude, latitude, srid=4326), location_name=location_name,
                                address=address)
        member.master_of = branch
        member.member_of = branch
        member.save(update_fields=('master_of', 'member_of'))
        return branch
