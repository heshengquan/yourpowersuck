import datetime

from django.contrib.gis.geos import Point
from rest_framework import serializers

from .models import PollingActivity, PollingItem, PollingItemImages, PollingItemCity, MemberPollingRecord


class PollingActivitiesSerializer(serializers.ModelSerializer):
    """
        投票活动列表序列化器
    """
    image_name = serializers.SerializerMethodField()

    def get_image_name(self, polling_activity):
        return polling_activity.image_name

    class Meta:
        model = PollingActivity
        fields = ('id', 'name', 'image_name', 'status')


class PollingActivitySerializer(serializers.ModelSerializer):
    """
        投票活动序列化器
    """
    image_name = serializers.SerializerMethodField()

    def get_image_name(self, polling_activity):
        return polling_activity.image_name

    class Meta:
        model = PollingActivity
        fields = ('id', 'pub_date', 'name', 'info', 'image_name', 'status')


class PollingItemsSerializer(serializers.ModelSerializer):
    """
        投票条目列表序列化器
    """
    avatar = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    def get_avatar(self,polling_item):
        return polling_item.image_name

    def get_city(self, polling_item):
        return polling_item.city.name

    class Meta:
        model = PollingItem
        fields = ('id', 'name', 'votes', 'city', 'avatar',)


class PollingItemSerializer(serializers.ModelSerializer):
    """
        投票条目详情序列化器
    """

    nation_ranking = serializers.SerializerMethodField()
    city_ranking = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    is_self = serializers.SerializerMethodField()
    two_bar_codes = serializers.SerializerMethodField()
    city_id = serializers.SerializerMethodField()

    def get_nation_ranking(self, polling_item):
        return self.context['nation_ranking']

    def get_city_ranking(self,polling_item):
        return self.context['city_ranking']

    def get_city(self,polling_item):
        return polling_item.city.name

    def get_is_self(self,polling_item):
        return self.context['is_self']

    def get_two_bar_codes(self,polling_item):
        return self.context['two_bar_codes']

    def get_city_id(self,polling_item):
        return self.context['city_id']

    class Meta:
        model = PollingItem
        fields = ('id', 'name', 'votes','city', 'nation_ranking', 'city_ranking', 'is_self', 'two_bar_codes', 'city_id')


class PollingItemsCityRankingSerializer(serializers.ModelSerializer):
    """
        得票数的城市排行榜
    """
    polling_item = serializers.SerializerMethodField()

    def get_polling_item(self, city):
        polling_item = PollingItem.objects.filter(city=city, is_successful=True).order_by('-votes')
        if polling_item:
            polling_item_info = {
                'polling_item_id':polling_item[0].id,
                'polling_item_name':polling_item[0].name,
                'polling_item_avatar':polling_item[0].avatar.name
            }
            return polling_item_info
        return []

    class Meta:
        model = PollingItemCity
        fields = ('id', 'name', 'number','polling_item')



class NearbyPollingItemsSerializer(serializers.ModelSerializer):
    """
        附近的投票条目列表序列化器
    """

    distance = serializers.SerializerMethodField()
    image_name = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    def get_distance(self, polling_item):
        return polling_item.distance.km

    def get_image_name(self,polling_item):
        return polling_item.image_name

    def get_city(self, polling_item):
        return polling_item.city.name

    class Meta:
        model = PollingItem
        fields = ('id', 'name', 'votes','city', 'distance','image_name')


