from rest_framework import serializers

from .models import Marathon, CompetitionEvent, MarathonInfo, ParticipationInfo, AoNumberClothInfo


class MarathonSerializer(serializers.ModelSerializer):
    """
        马拉松赛事序列化器
    """

    marathon_info_id = serializers.SerializerMethodField()

    def get_marathon_info_id(self, marathon):
        return marathon.info.id

    class Meta:
        model = Marathon
        fields = ("id", "name", "status", "sign_up_begin", "sign_up_end", "time", "place", "marathon_info_id")


class CompetitionEventsSerializer(serializers.ModelSerializer):
    """
        竞赛项目列表序列化器
    """

    num = serializers.SerializerMethodField()

    def get_num(self, competition_event):
        return competition_event.competition_event_participation_records.filter(pay_status=True).count() + 253

    class Meta:
        model = CompetitionEvent
        fields = ("num", "id", "name", "price")


class CompetitionEventSerializer(serializers.ModelSerializer):
    """
        竞赛项目序列化器
    """

    class Meta:
        model = CompetitionEvent
        fields = ("name", "length", "route", "price")


class MarathonInfoSerializer(serializers.ModelSerializer):
    """
        赛事章程序列化器
    """

    class Meta:
        model = MarathonInfo
        fields = (
            "name", "sponsor", "organizer", "organizer", "method_of_competition", "method_of_join", "method_of_reward",
            "method_of_punishment", "insurance", "contact_way")


class ParticipationInfoSerializer(serializers.ModelSerializer):
    """
        报名信息序列化器
    """

    national = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def create(self, validated_data):
        validated_data['member'] = self.context['member']
        return ParticipationInfo.objects.create(**validated_data)

    class Meta:
        model = ParticipationInfo
        fields = (
            "name", "gender", "certificate_type", "certificate_num", "birthday", "national", "email", "mobile",
            "blood_type", "emergency_contact", "emergency_contact_mobile"
        )


class NumberClothInfoSerializer(serializers.ModelSerializer):
    """
        号码布信息序列化器
    """

    class Meta:
        model = AoNumberClothInfo
        fields = (
            "number", "group_name", "name", "gender", "certificate_type", "certificate_num",
            "mobile", "clothes_size", "country")
