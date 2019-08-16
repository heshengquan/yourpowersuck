from rest_framework import serializers

from appointment.models import Activity
from association.models import Branch
from .models import MemberProfile


class MemberShowingSerializer(serializers.Serializer):
    """
        成员公开信息序列化器
    """
    name = serializers.CharField(max_length=32, required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    branch_location_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()
    is_master = serializers.SerializerMethodField()
    is_deputy = serializers.SerializerMethodField()
    number_of_activities = serializers.SerializerMethodField()
    activities_rank_in_branch = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    def get_branch_location_name(self, member):
        branch = member.member_of
        if branch:
            return branch.location.location_name
        return ''

    def get_branch_name(self, member):
        branch = member.member_of
        if branch:
            return branch.name
        else:
            return ''

    def get_branch_id(self, member):
        branch = member.member_of
        if branch:
            return branch.id
        else:
            return ''

    def get_is_master(self, member):
        return True if member.master_of else False

    def get_is_deputy(self, member):
        return True if member.deputy_of else False

    def get_number_of_activities(self, member):
        self.context['number_of_activities'] = member.existing_participation_records.count()
        return self.context['number_of_activities']

    def get_activities_rank_in_branch(self, member):
        branch = member.member_of
        if not branch:
            return None
        else:
            number_of_activities = self.context['number_of_activities']
            i = 1
            for each_member in branch.members.all():
                if each_member.existing_participation_records.count() > number_of_activities:
                    i += 1
            return i

    def get_is_owner(self, member):
        current_member = self.context.get('member')
        return member == current_member

    def create(self, validated_data):
        raise AssertionError('不允许调用create')

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.avatar_url = validated_data.get('avatar_url', instance.avatar_url)
        instance.save(update_fields=('name', 'avatar_url'))
        return instance

    def validate_name(self, name):
        # 验证name是否合法
        for i in name:
            if i in ('/', '<', '>'):
                # 非法字符
                raise serializers.ValidationError('包含非法字符')
        return name

    def validate_avatar_url(self, avatar_url):
        # 验证avatar_url是否合法
        if avatar_url.startswith('https://wx.qlogo.cn/mmopen/') or avatar_url.startswith('http://wx.qlogo.cn/mmopen/'):
            return avatar_url
        elif avatar_url == '':
            # 该用户无头像链接
            return avatar_url
        else:
            # 不符合微信头像格式
            raise serializers.ValidationError('不符合微信头像格式')


class MemberProfileSerializer(serializers.ModelSerializer):
    """
        成员私有信息序列化器
    """

    # 显式地写出这些是为了allow_blank。因为这些字段是从微信里面获取的，有可能为空值
    gender = serializers.CharField(max_length=1, required=False, allow_blank=True)
    city = serializers.CharField(max_length=32, required=False, allow_blank=True)
    province = serializers.CharField(max_length=16, required=False, allow_blank=True)
    country = serializers.CharField(max_length=16, required=False, allow_blank=True)
    language = serializers.CharField(max_length=8, required=False, allow_blank=True)

    # todo:第二个版本要完善,并且确定哪些是只读

    class Meta:
        model = MemberProfile
        fields = ('gender', 'city', 'province', 'country', 'language')


class MemberActivitiesSerializer(serializers.ModelSerializer):
    """
        成员参与过的活动列表序列化器
    """

    class Meta:
        model = Activity
        fields = ('id', 'name', 'begin', 'end', 'place', 'status', 'thumb_image')


class MemberActivitiesExtraInfoSerializer(serializers.Serializer):
    """
        成员参与过的活动列表的额外信息序列化器
    """
    name = serializers.SerializerMethodField()
    branch_location_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()

    def get_name(self, member):
        return member.name

    def get_branch_location_name(self, member):
        branch = member.member_of
        if branch:
            return branch.location.location_name
        return ''

    def get_branch_name(self, member):
        branch = member.member_of
        if branch:
            return branch.name
        else:
            return ''

    def get_branch_id(self, member):
        branch = member.member_of
        if branch:
            return branch.id
        else:
            return ''


def get_image_path(instance, filename=None):
    # 确定图片文件存储路径,并且以'id.jpg'命名
    filename = instance.id + '.jpg'
    # 这是一个相对路径，是在MEDIA_ROOT下面的一个路径
    return 'association/img/{0}'.format(filename)

class MemberStartBranchSerializer(serializers.Serializer):
    """
        新建分舵序列化器
    """
    name = serializers.CharField(max_length=16)
    announcement = serializers.CharField(max_length=200, required=False, allow_blank=True)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    location_name = serializers.CharField(max_length=16)
    address = serializers.CharField(max_length=64)
    image = serializers.ImageField(use_url=get_image_path, required=False)

    def create(self, validated_data):
        validated_data['member'] = self.context['member']
        validated_data['fund'] = 0
        return Branch.objects.create(**validated_data)

    def update(self, instance, validated_data):
        raise AssertionError('不允许调用update')


class NearbyActivitesSerializer(serializers.ModelSerializer):
    """
        附近分舵正在进行的活动的列表序列化器
    """
    distance = serializers.SerializerMethodField()
    number_of_activity = serializers.SerializerMethodField()

    def get_distance(self,activity):
        return activity.distance.mi

    def get_number_of_activity(self,activity):
        return activity.participation_records.filter(does_exist=True).count()

    class Meta:
        model = Activity
        fields = ('id', 'name', 'begin', 'end', 'place','distance','number_of_activity', 'thumb_image')
