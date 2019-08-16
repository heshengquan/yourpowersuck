from django.contrib.gis.geos import Point
from rest_framework import serializers

from appointment.models import Activity
from me.models import Member
from appointment.models import ActivityImages
from .models import Branch, BranchFundRecord


class BranchesSerializer(serializers.ModelSerializer):
    """
        分舵列表序列化器
    """
    location_name = serializers.SerializerMethodField()
    number_of_members = serializers.SerializerMethodField()
    number_of_activities = serializers.SerializerMethodField()
    influence = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()

    def get_location_name(self, branch):
        return branch.location.location_name

    def get_number_of_members(self, branch):
        return branch.members.count()

    def get_number_of_activities(self, branch):
        return branch.existing_activities.count()

    def get_influence(self, branch):
        return branch.influence

    def get_latitude(self, branch):
        return branch.location.coordinates.y

    def get_longitude(self, branch):
        return branch.location.coordinates.x

    def get_distance(self, branch):
        return branch.distance.km

    class Meta:
        model = Branch
        fields = ('id', 'location_name', 'name', 'number_of_members', 'number_of_activities', 'influence', 'latitude',
                  'longitude', 'distance')


class BranchSerializer(serializers.ModelSerializer):
    """
        分舵序列化器
    """
    location_name = serializers.SerializerMethodField()
    master_name = serializers.SerializerMethodField()
    master_id = serializers.SerializerMethodField()
    deputies_name = serializers.SerializerMethodField()
    number_of_members = serializers.SerializerMethodField()
    members_rank_in_country = serializers.SerializerMethodField()
    number_of_activities = serializers.SerializerMethodField()
    activities_rank_in_country = serializers.SerializerMethodField()
    influence = serializers.SerializerMethodField()
    influence_rank_in_country = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    in_this_branch = serializers.SerializerMethodField()
    in_other_branch = serializers.SerializerMethodField()
    is_master = serializers.SerializerMethodField()
    is_deputy = serializers.SerializerMethodField()
    branch_has_uncompleted_activity = serializers.SerializerMethodField()
    # image_name = serializers.SerializerMethodField()

    # member_has_uncompleted_activity = serializers.SerializerMethodField()

    def get_location_name(self, branch):
        return branch.location.location_name

    def get_master_name(self, branch):
        return branch.master.name

    def get_master_id(self, branch):
        return branch.master.id

    def get_deputies_name(self, branch):
        return [deputy.name for deputy in branch.deputies.all()]

    def get_number_of_members(self, branch):
        # self.context['number_of_members'] = branch.members.count()
        # return self.context['number_of_members']
        return branch.members.count()

    def get_members_rank_in_country(self, branch):
        # i = 1
        # number_of_members = self.context['number_of_members']
        # for each_branch in Branch.objects.get_existing_all():
        #     if each_branch.members.count() > number_of_members:
        #         i += 1
        i = Branch.objects.filter(members_number__gt=branch.members_number).count() + 1
        return i

    def get_number_of_activities(self, branch):
        # self.context['number_of_activities'] = branch.existing_activities.count()
        # return self.context['number_of_activities']
        return branch.existing_activities.count()

    def get_activities_rank_in_country(self, branch):
        # i = 1
        # number_of_activities = self.context['number_of_activities']
        # for each_branch in Branch.objects.get_existing_all():
        #     if each_branch.existing_activities.count() > number_of_activities:
        #         i += 1
        i = Branch.objects.filter(activities_number__gt=branch.activities_number).count() + 1
        return i

    def get_influence(self, branch):
        # self.context['influence'] = branch.influence
        # return self.context['influence']
        return branch.influence

    def get_influence_rank_in_country(self, branch):
        # i = 1
        # influence = self.context['influence']
        # for each_branch in Branch.objects.get_existing_all():
        #     if each_branch.influence > influence:
        #         i += 1
        i = Branch.objects.filter(influence_number__gt=branch.influence_number).count() + 1
        return i

    def get_latitude(self, branch):
        return branch.location.coordinates.y

    def get_longitude(self, branch):
        return branch.location.coordinates.x

    def get_in_this_branch(self, branch):
        current_member = self.context.get('member')
        return current_member.member_of == branch

    def get_in_other_branch(self, branch):
        current_member = self.context.get('member')
        if current_member.member_of:
            return current_member.member_of != branch
        else:
            return False

    def get_is_master(self, branch):
        current_member = self.context.get('member')
        return current_member.master_of == branch

    def get_is_deputy(self, branch):
        current_member = self.context.get('member')
        return current_member.deputy_of == branch

    def get_branch_has_uncompleted_activity(self, branch):
        return branch.existing_activities.exclude(status='has_completed').exists()

    # def get_member_has_uncompleted_activity(self, branch):
    #     current_member = self.context.get('member')
    #     return current_member.existing_participation_records.exclude(activity__status='has_completed').exists()

    # def get_image_name(self, branch):
    #     return branch.image_name

    class Meta:
        model = Branch
        fields = ('location_name', 'name', 'master_name', 'master_id', 'deputies_name', 'number_of_members',
                  'members_rank_in_country', 'number_of_activities', 'activities_rank_in_country', 'influence',
                  'influence_rank_in_country', 'latitude', 'longitude', 'announcement', 'in_this_branch',
                  'in_other_branch', 'is_master', 'is_deputy', 'branch_has_uncompleted_activity', 'image', 'fund')


class BranchActivitiesSerializer(serializers.ModelSerializer):
    """
        分舵的活动列表序列化器
    """
    number_of_members = serializers.SerializerMethodField()
    number_of_images = serializers.SerializerMethodField()

    def get_number_of_members(self, activity):
        return activity.existing_participation_records.count()

    def get_number_of_images(self,activity):
        return ActivityImages.objects.filter(activity=activity,does_exist=True).count()

    class Meta:
        model = Activity
        fields = ('id', 'name', 'begin', 'end', 'place', 'status', 'build_up_time', 'number_of_members', 'number_of_images', 'does_pass', 'thumb_image')


class BranchMembersSerializer(serializers.ModelSerializer):
    """
        分舵的成员列表序列化器
    """
    is_master = serializers.SerializerMethodField()
    is_deputy = serializers.SerializerMethodField()

    def get_is_master(self, member):
        return True if member.master_of else False

    def get_is_deputy(self, member):
        return True if member.deputy_of else False

    class Meta:
        model = Member
        fields = ('id', 'name', 'avatar_url', 'is_master', 'is_deputy')


class BranchMembersExtraInfoSerializer(serializers.Serializer):
    """
        分舵的成员列表的额外信息序列化器
    """
    location_name = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    is_master = serializers.SerializerMethodField()

    def get_location_name(self, branch):
        return branch.location.location_name

    def get_name(self, branch):
        return branch.name

    def get_is_master(self, branch):
        current_member = self.context.get('member')
        return current_member.master_of == branch


class BranchStartActivitySerializer(serializers.ModelSerializer):
    """
        发起活动序列化器
    """

    def create(self, validated_data):
        branch = self.context.get('branch')
        founder = self.context.get('founder')
        rechargeable = self.context.get('rechargeable')
        does_pass = self.context.get('does_pass')
        money = self.context.get('money')
        validated_data['branch'] = branch
        validated_data['founder'] = founder
        validated_data['rechargeable'] = rechargeable
        validated_data['does_pass'] = does_pass
        validated_data['money'] = money
        # return super().create(validated_data)
        return Activity.objects.create(**validated_data)

    def update(self, instance, validated_data):
        raise AssertionError('不允许调用update')

    class Meta:
        model = Activity
        fields = ('name', 'begin', 'end', 'place', 'info', 'image', 'rechargeable', 'money', 'does_pass')


class BranchLocationSerializer(serializers.Serializer):
    """
        分舵位置序列化器
    """
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    location_name = serializers.CharField(max_length=16)
    address = serializers.CharField(max_length=64)

    def create(self, validated_data):
        raise AssertionError('不允许调用create')

    def update(self, instance, validated_data):
        longitude = validated_data.pop('longitude')
        latitude = validated_data.pop('latitude')
        instance.coordinates = Point(longitude, latitude, srid=4326)
        instance.location_name = validated_data['location_name']
        instance.address = validated_data['address']
        instance.save(update_fields=('coordinates', 'location_name', 'address'))
        return instance


class BranchImageSerializer(serializers.ModelSerializer):
    """
        分舵配图序列化器
    """

    class Meta:
        model = Branch
        fields = ('image',)


class BranchFundDeatailSerializer(serializers.ModelSerializer):
    """
        分舵基金明细序列化器
    """
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_name(self, branch_fund_record):
        return branch_fund_record.member.name

    def get_avatar(self, branch_fund_record):
        return branch_fund_record.member.avatar_url

    class Meta:
        model = BranchFundRecord
        fields = ('name', 'avatar', 'money', 'pay_time')


class BranchFundRankingSerializer(serializers.Serializer):
    """
        分舵基金明细序列化器
    """
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    total_money = serializers.SerializerMethodField()

    def get_name(self, branch_fund_record):
        member_id = branch_fund_record['member']
        member = Member.objects.get(id=member_id)
        return member.name

    def get_avatar(self, branch_fund_record):
        member_id = branch_fund_record['member']
        member = Member.objects.get(id=member_id)
        return member.avatar_url

    def get_total_money(self, branch_fund_record):
        return '{:.2f}'.format(branch_fund_record['total'])


