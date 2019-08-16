import time
import requests
from django.http import HttpResponse
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from me.models import Member
from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.config import WEIXIN_NOTIFY_URL_ORDER, WEIXIN_NOTIFY_URL_ACTIVITY
from utils.payment import get_bodyData, xml_to_dict, get_paysign
from utils.permissions import IsAuthorizedByMobile
from . import paginators
from . import serializers
from .models import Activity, ParticipationRecord, RechargeableActivity, ActivityImages

class ActivityView(APIView):
    """
        某活动的信息【用户】
        https://api.yourpowersuck.com/activities/:id/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        context = {'member': request.user}
        serializer = serializers.ActivitySerializer(activity, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class ActivityMemberAvatarURLsView(APIView):
    """
        某活动的所有成员头像url【用户】
        https://api.yourpowersuck.com/activities/:id/member-avatar-urls/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        member_avatar_urls = [participation_record.member.avatar_url for participation_record in
                              activity.existing_participation_records.order_by('in_time')]
        response = {
            'data': {
                'member_avatar_urls': member_avatar_urls
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class ActivityMembersView(ListAPIView):
    """
        某活动的参与成员列表【参与者】
        https://api.yourpowersuck.com/activities/:id/members/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.ActivityMembersSerializer
    pagination_class = paginators.ParticipationRecordsCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=self.kwargs['id'])
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        # if not activity.existing_participation_records.filter(member=self.request.user).exists():
        #     # 当前用户非此活动的参与者,权限不足
        #     raise exceptions.PermissionDeniedf
        # 注:此处我们返回participation_records而不是members,这是为了包含sign_in_status信息进去
        return activity.existing_participation_records


class ActivityMembersExtraInfoView(APIView):
    """
        "某活动的参与成员列表"的额外信息【参与者】
        https://api.yourpowersuck.com/activities/:id/members/extra-info/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        # if not activity.existing_participation_records.filter(member=request.user).exists():
        #     # 当前用户非此活动的参与者,权限不足
        #     raise exceptions.PermissionDenied
        context = {'member': request.user}
        serializer = serializers.ActivityMembersExtraInfoSerializer(activity, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class ActivityEditView(APIView):
    """
        修改某活动的信息【发起者，且活动状态为报名中】
        https://api.yourpowersuck.com/activities/:id/edit/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.founder != request.user:
            # 当前用户非此活动的发起者,权限不足
            raise exceptions.PermissionDenied
        if activity.status != 'is_signing_up':
            # 活动状态不为报名中则请求失败
            raise exceptions.RequestFailed
        serializer = serializers.ActivitySerializer(activity, data=request.data, partial=True)
        if not serializer.is_valid():
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class ActivityEditImageView(APIView):
    """
        修改某活动的配图【发起者，且活动状态为报名中】
        https://api.yourpowersuck.com/activities/:id/edit-image/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.founder != request.user:
            # 当前用户非此活动的发起者,权限不足
            raise exceptions.PermissionDenied
        if activity.status != 'is_signing_up':
            # 活动状态不为报名中则请求失败
            raise exceptions.RequestFailed
        # serializer = serializers.ActivityImageSerializer(activity, data=request.data)
        # if not serializer.is_valid():
        #     raise exceptions.ArgumentError
        # serializer.save()
        activity.image = request.data['image']
        activity.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class ActivityEditStatusView(APIView):
    """
        修改某活动的状态【发起者，且活动状态不为已结束】
        https://api.yourpowersuck.com/activities/:id/edit-status/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.founder != request.user:
            # 当前用户非此活动的发起者,权限不足
            raise exceptions.PermissionDenied
        if activity.has_not_completed:
            # 若活动没有结束
            if activity.status == 'is_signing_up':
                # 若为报名中,改为签到中
                activity.status = 'is_signing_in'
            else:
                # 否则为签到中,改为已结束
                activity.status = 'has_completed'
        else:
            # 活动已结束则不允许修改状态
            raise exceptions.RequestFailed
        activity.save(update_fields=('status',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class SignInOrSignOutView(APIView):
    """
        签到/签退【参与者，且为当前活动所属分舵的舵主或者副舵主，且被签到/签退的成员也是参与者，且活动状态为签到中】
        https://api.yourpowersuck.com/activities/:id/:option/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id, option):
        if option == 'sign-in':
            # 签到操作
            flag = True
        elif option == 'sign-out':
            # 签退操作
            flag = False
        else:
            # 请求失败
            raise exceptions.RequestFailed
        try:
            # 尝试获取当前id对应的活动和member_id对应的被签到成员
            activity = Activity.objects.get_existing_all().get(id=id)
            sign_in_member = Member.objects.get(id=request.data['member_id'])
        except:
            # 活动或被签到成员不存在
            raise exceptions.NoSuchResource
        if activity.status != 'is_signing_in':
            # 若活动状态不为签到中则请求失败
            raise exceptions.RequestFailed
        if not activity.existing_participation_records.filter(member=request.user).exists():
            # 当前用户非此活动的参与者,权限不足
            raise exceptions.PermissionDenied
        if not (request.user.master_of == activity.branch or request.user.deputy_of == activity.branch):
            # 当前用户不是此活动所属分舵的舵主或副舵主,权限不足
            raise exceptions.PermissionDenied
        try:
            # 尝试获取被签到成员的参与记录
            participation_record = activity.existing_participation_records.get(member=sign_in_member)
        except:
            # 被签到成员非此活动的参与者,请求失败
            raise exceptions.RequestFailed
        participation_record.sign_in_status = flag
        participation_record.save(update_fields=('sign_in_status',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class JoinActivityView(APIView):
    """
        加入活动【跑者，且没有未结束活动，且此活动为报名中】
        https://api.yourpowersuck.com/activities/:id/join/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def permission_denied(self, request, message=None):
        raise exceptions.NotARunner

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.status != 'is_signing_up':
            # 若活动状态不为报名中则请求失败
            raise exceptions.RequestFailed
        # if Activity.objects.filter(participation_record__in=list(request.user.existing_participation_records)).exclude(
        #         status='has_completed').exists():
        #     # 如果当前用户有未结束的活动则请求失败
        #     raise exceptions.RequestFailed
        # 如果该用户已经加入过该活动则请求失败
        if ParticipationRecord.objects.filter(member=request.user,activity=activity,does_exist=True):
            raise exceptions.PermissionDenied
        # 如果是收费活动，此处调用微信支付，支付成功后自动进入该活动
        if activity.rechargeable:
            price = int(activity.money*100)

            # 获取客户端ip
            client_ip = request.META['REMOTE_ADDR']

            # 获取小程序openid
            openid = request.user.openid

            # 请求微信的url
            url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'

            # 拿到封装好的xml数据
            body = activity.name
            body = "收费活动-" + body
            body_data, nonce_str, out_trade_no, = get_bodyData(body, WEIXIN_NOTIFY_URL_ACTIVITY, openid, client_ip, price)
            # 获取时间戳
            timeStamp = str(int(time.time()))
            # 请求微信接口下单
            respone = requests.post(url, body_data.encode("utf-8"), headers={'Content-Type': 'application/xml'})
            # 回复数据为xml,将其转为字典
            content = xml_to_dict(respone.content)
            if content["return_code"] == 'SUCCESS':
                try:
                    # 保存加入该活动的信息
                    rechargeable_dic = {
                        'member': request.user,
                        'activity': activity,
                        'money': price / 100,
                        'nonce_str': nonce_str,
                        'out_trade_no': out_trade_no,
                        'status': 'has_created',
                    }
                    rechargeable = RechargeableActivity(**rechargeable_dic)
                    rechargeable.save()
                except:
                    return Response('保存收费信息失败')

                # 获取预支付交易会话标识
                prepay_id = content.get("prepay_id")
                # prepay_id作为一个form——id需要被存起来，七天内发送消息模板时使用
                rechargeable.prepay_id = prepay_id
                rechargeable.save()
                # 获取随机字符串
                nonceStr = content.get("nonce_str")
                # 获取paySign签名，这个需要我们根据拿到的prepay_id和nonceStr进行计算签名
                paySign = get_paysign(prepay_id, timeStamp, nonceStr)
                # 封装返回给前端的数据
                data = {"prepay_id": prepay_id, "nonceStr": nonceStr, "paySign": paySign, "timeStamp": timeStamp}
                return Response(data)
            else:
                return Response(content['return_msg'])
        else:
            ParticipationRecord.objects.create(member=request.user, activity=activity)
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class QuitActivityView(APIView):
    """
        退出活动【参与者，且非发起者，且此活动为报名中】
        https://api.yourpowersuck.com/activities/:id/quit/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.status != 'is_signing_up':
            # 若活动状态不为报名中则请求失败
            raise exceptions.RequestFailed
        if activity.founder == request.user:
            # 若当前用户为此活动发起者则请求失败
            raise exceptions.RequestFailed
        try:
            # 尝试获取当前用户的参与记录
            participation_record = activity.existing_participation_records.get(member=request.user)
        except:
            # 当前用户非此活动的参与者,权限不足
            raise exceptions.PermissionDenied
        participation_record.does_exist = False
        participation_record.save(update_fields=('does_exist',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class DeleteActivityView(APIView):
    """
        删除活动【发起者，且此活动为报名中】
        https://api.yourpowersuck.com/activities/:id/delete/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的活动
            activity = Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.founder != request.user:
            # 当前用户非此活动的发起者,权限不足
            raise exceptions.PermissionDenied
        if activity.status != 'is_signing_up':
            # 若活动状态不为报名中则请求失败
            raise exceptions.RequestFailed
        if activity.rechargeable == True:
            # 收费活动不允许删除
            raise exceptions.ArgumentError
        activity.existing_participation_records.delete_all()
        activity.does_exist = False
        activity.save(update_fields=('does_exist',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)

class UploadActivityPicView(APIView):
    """
        上传活动图片
        https://api.yourpowersuck.com/activities/:id/upload-pic/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self,request,id):
        try:
            activity=Activity.objects.get_existing_all().get(id=id)
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        if activity.status != 'has_completed':
            #活动没有结束
            raise exceptions.ActivityNotCompleted
        try:
            record=ParticipationRecord.objects.get_existing_all().get(activity=id,member=request.user)
        except:
            raise exceptions.NotInActivity
        try:
            img = request.data['img']
            # member = request.user
        except:
            raise exceptions.ArgumentError
        result=ActivityImages.objects.create(activity=activity,member=request.user,img=img,does_exist=True)
        data = serializers.UploaderActivityImagesDataSerializer(result)
        response = {
            'data':data.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class GetActivityImages(ListAPIView):
    """
        获取上传的活动图片
        https://api.yourpowersuck.com/activities/:id/activityImages/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.CompletedActivityImagesSerializer
    pagination_class = paginators.CompletedActivityImagesCursorPagination

    def get_queryset(self):
        try:
            activity = Activity.objects.get_existing_all().get(id=self.kwargs['id'])
        except Activity.DoesNotExist:
            # 活动不存在
            raise exceptions.NoSuchResource
        # if activity.status != 'has_completed':
        #     # 活动没有结束
        #     raise exceptions.ActivityNotCompleted
        return ActivityImages.objects.filter(activity=activity,does_exist=True)


class DeleteActivityImageView(APIView):
    authentication_classes = (MemberAuthentication,)

    def post(self,request,id):
        try:
            activity = Activity.objects.get_existing_all().get(id=id)
            image = ActivityImages.objects.get(activity=activity,id=request.data['id'],does_exist=True)
        except:
            raise exceptions.NoSuchResource
        if activity.founder != request.user and image.member != request.user:
            # 当前用户非此活动的发起者,权限不足
            raise exceptions.PermissionDenied
        try:
            record=ParticipationRecord.objects.get_existing_all().get(activity=activity,member=request.user)
        except:
            raise exceptions.NotInActivity
        image.does_exist=False
        image.save()
        return Response({
            'code':0,
            'error':''
        })