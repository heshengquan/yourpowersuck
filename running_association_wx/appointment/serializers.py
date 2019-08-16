from rest_framework import serializers

from .models import Activity,ActivityImages,ParticipationRecord


class ActivitySerializer(serializers.ModelSerializer):
    """
        活动信息序列化器
    """
    # image_name = serializers.SerializerMethodField()
    branch_location_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()
    founder_name = serializers.SerializerMethodField()
    is_master_or_deputy = serializers.SerializerMethodField()
    is_founder = serializers.SerializerMethodField()
    in_this_activity = serializers.SerializerMethodField()

    # in_other_ongoing_activity = serializers.SerializerMethodField()
    #
    # def get_image_name(self, activity):
    #     return activity.image_name

    def get_branch_location_name(self, activity):
        return activity.branch.location.location_name

    def get_branch_name(self, activity):
        return activity.branch.name

    def get_branch_id(self, activity):
        return activity.branch.id

    def get_founder_name(self, activity):
        return activity.founder.name

    def get_is_master_or_deputy(self, activity):
        current_member = self.context.get('member')
        branch = activity.branch
        return current_member.master_of == branch or current_member.deputy_of == branch

    def get_is_founder(self, activity):
        current_member = self.context.get('member')
        return activity.founder == current_member

    def get_in_this_activity(self, activity):
        current_member = self.context.get('member')
        return activity.existing_participation_records.filter(member=current_member).exists()

    # def get_in_other_ongoing_activity(self, activity):
    #     current_member = self.context.get('member')
    #     return current_member.existing_participation_records.exclude(
    #         activity=activity).exclude(activity__status='has_completed').exists()

    class Meta:
        model = Activity
        fields = (
            'name', 'image', 'branch_location_name', 'branch_name', 'branch_id', 'founder_name', 'begin', 'end',
            'place', 'info', 'status', 'is_master_or_deputy', 'is_founder', 'in_this_activity', 'rechargeable', 'money')
        read_only_fields = ('status',)


class ActivityMembersSerializer(serializers.Serializer):
    """
        活动的参与成员列表序列化器
    """
    # 注意我们传进来的是participation_record而不是member
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    sign_in_status = serializers.BooleanField()

    def get_id(self, participation_record):
        return participation_record.member.id

    def get_name(self, participation_record):
        return participation_record.member.name

    def get_avatar_url(self, participation_record):
        return participation_record.member.avatar_url


class ActivityMembersExtraInfoSerializer(serializers.Serializer):
    """
        活动的参与成员列表的额外信息序列化器
    """
    name = serializers.SerializerMethodField()
    branch_location_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()
    is_master_or_deputy = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_name(self, activity):
        return activity.name

    def get_branch_location_name(self, activity):
        return activity.branch.location.location_name

    def get_branch_name(self, activity):
        return activity.branch.name

    def get_is_master_or_deputy(self, activity):
        current_member = self.context.get('member')
        return current_member.master_of == activity.branch or current_member.deputy_of == activity.branch

    def get_status(self, activity):
        return activity.status


class ActivityImageSerializer(serializers.ModelSerializer):
    """
        活动配图序列化器
    """

    class Meta:
        model = Activity
        fields = ('image',)


class CompletedActivityImagesSerializer(serializers.ModelSerializer):
    """
        活动结束后上传的图片
    """
    uploader_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_uploader_name(self,context):
        return context.member.name

    def get_avatar_url(self,context):
        return context.member.avatar_url

    class Meta:
        model = ActivityImages
        fields = ('id','img', 'tiny_img','uploader_name','avatar_url')


class UploaderActivityImagesDataSerializer(serializers.ModelSerializer):
    """
        对每一张上传的图片需要返回的信息进行序列化
    """
    uploader_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    def get_uploader_name(self, context):
        return context.member.name

    def get_avatar_url(self, context):
        return context.member.avatar_url

    class Meta:
        model = ActivityImages
        fields = ('id','img','tiny_img','uploader_name','avatar_url')