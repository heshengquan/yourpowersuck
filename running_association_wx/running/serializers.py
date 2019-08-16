from rest_framework import serializers

from .models import Race


class RacesSerializer(serializers.ModelSerializer):
    """
        赛事列表序列化器
    """
    has_followed = serializers.SerializerMethodField()
    image_name = serializers.SerializerMethodField()

    def get_has_followed(self, race):
        current_member = self.context.get('request').user
        return current_member in race.followers.all()

    def get_image_name(self, race):
        return race.image_name

    class Meta:
        model = Race
        fields = ('id', 'name', 'sign_up_date', 'deadline_date', 'start_date', 'status', 'has_followed', 'image_name')


class RaceSerializer(serializers.ModelSerializer):
    """
        赛事序列化器
    """
    has_followed = serializers.SerializerMethodField()
    image_name = serializers.SerializerMethodField()
    number_of_followers = serializers.SerializerMethodField()

    def get_has_followed(self, race):
        current_member = self.context.get('member')
        return current_member in race.followers.all()

    def get_image_name(self, race):
        return race.image_name

    def get_number_of_followers(self, race):
        return race.followers.count()

    class Meta:
        model = Race
        fields = (
            'name', 'sign_up_date', 'deadline_date', 'start_date', 'status', 'detail', 'has_followed', 'image_name',
            'number_of_followers')
