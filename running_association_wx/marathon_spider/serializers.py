from rest_framework import serializers

from .models import Marathon


class MarathonSerializer(serializers.ModelSerializer):
    """
        马拉松成绩序列化器
    """

    class Meta:
        model = Marathon
        fields = ('date', 'name', 'project', 'chip_time', 'clock_gun_time', 'is_pb')


class MarathonRankingSerializer(serializers.ModelSerializer):
    """
        马拉松排名序列化器
    """
    member_image = serializers.SerializerMethodField()
    member_id = serializers.SerializerMethodField()
    member_name = serializers.SerializerMethodField()

    def get_member_image(self,marathon):
        return marathon.member.avatar_url

    def get_member_id(self,marathon):
        return marathon.member.id

    def get_member_name(self,marathon):
        return marathon.member.member_profile.real_name


    class Meta:
        model = Marathon
        fields = ('member_image','member_id','chip_time','member_name', 'sex')