import datetime
import json
import urllib.parse
import urllib.request
import time

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from appointment.models import Activity
from utils import exceptions
from utils.WXBizDataCrypt import WXBizDataCrypt
from utils.YPsms import send_verification_code
from utils.access_token import get_access_token, PrpCrypt
from utils.authentications import MemberAuthentication
from utils.global_tools import uuid_str, md5, random_int_6, ten_minutes_from_now
from utils.permissions import IsAuthorizedByMobile, IsOwner
from utils.throttles import WXAndMobileThrottle
from . import serializers
from . import paginators
from .models import Member, CheckMobile, MemberFormId


class WXLoginView(APIView):
    """
        微信登录【所有】
        https://api.yourpowersuck.com/wx/login/
    """
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        try:
            # 尝试获取code参数
            code = request.data['code']
        except:
            raise exceptions.ArgumentError
        wx_login_url = 'https://api.weixin.qq.com/sns/jscode2session?'
        params = {
            'appid': settings.WX_APPID,
            'secret': settings.WX_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
        wx_login_request = urllib.request.Request(wx_login_url + urllib.parse.urlencode(params))
        try:
            # 尝试调用微信登录API获取openid和session_key
            wx_response = urllib.request.urlopen(wx_login_request, timeout=2)  # 设置超时时间为2s
            wx_response_str = wx_response.read().decode()
            wx_response_dict = json.loads(wx_response_str)
            openid = wx_response_dict['openid']
            session_key = wx_response_dict['session_key']
        except:
            # 微信API调用失败
            raise exceptions.RequestFailed
        new_raw_token = md5(openid + session_key)
        new_salt = uuid_str()
        try:
            # 尝试查找此openid对应用户是否为老用户
            member = Member.objects.get(openid=openid)
        except Member.DoesNotExist:
            # 新用户
            member_id = uuid_str()
            new_token = new_raw_token + '.' + member_id
            new_token_hash = md5(new_token + new_salt)
            Member.objects.create(id=member_id, openid=openid, wx_session_key=session_key,
                                  token_hash=new_token_hash, salt=new_salt)
            is_new = True
        else:
            # 老用户
            new_token = new_raw_token + '.' + member.id
            new_token_hash = md5(new_token + new_salt)
            member.wx_session_key = session_key
            member.token_hash = new_token_hash
            member.salt = new_salt
            member.last_login = datetime.datetime.now()
            member.save(update_fields=('wx_session_key', 'token_hash', 'salt', 'last_login'))
            is_new = False
        response = {
            'data': {
                'token': new_token,
                'is_new': is_new,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)

class WXAuthorizationUserInfoView(APIView):
    """
        微信授权（个人信息）【用户】
        https://api.yourpowersuck.com/wx/authorization/user-info/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        try:
            # 尝试获取encryptedData和iv
            encrypted_data = request.data['encryptedData']
            iv = request.data['iv']
        except:
            # 参数错误
            raise exceptions.ArgumentError
        try:
            # 尝试解密用户信息密文
            user_info = WXBizDataCrypt(settings.WX_APPID, request.user.wx_session_key).decrypt(encrypted_data, iv)
            user_showing_info = {'name': user_info.pop('nickName'), 'avatar_url': user_info.pop('avatarUrl')}
        except:
            # 解密失败
            raise exceptions.RequestFailed
        # 保存公开信息
        member_showing_serializer = serializers.MemberShowingSerializer(request.user, data=user_showing_info)
        if not member_showing_serializer.is_valid():
            raise exceptions.RequestFailed
        member_showing_serializer.save()
        # 保存私有信息
        member_profile_serializer = serializers.MemberProfileSerializer(request.user.member_profile, data=user_info,
                                                                        partial=True)
        if not member_profile_serializer.is_valid():
            raise exceptions.RequestFailed
        member_profile_serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class WXAuthorizationMobileView(APIView):
    """
        微信授权（手机号码）【用户】
        https://api.yourpowersuck.com/wx/authorization/mobile/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        try:
            # 尝试获取encryptedData和iv
            encrypted_data = request.data['encryptedData']
            iv = request.data['iv']
        except:
            # 参数错误
            raise exceptions.ArgumentError
        try:
            # 尝试解密用户手机号码
            mobile_info = WXBizDataCrypt(settings.WX_APPID, request.user.wx_session_key).decrypt(encrypted_data, iv)
            mobile = mobile_info['purePhoneNumber']
        except:
            # 解密失败
            raise exceptions.RequestFailed
        try:
            # 尝试判断手机号是否合法
            assert mobile != ''  # 手机号不能为空
            # 目前版本我们认为手机号为空就非法，其余情况不考虑
        except:
            # 手机号非法
            raise exceptions.InvalidPhoneNumber
        request.user.mobile = mobile
        request.user.save(update_fields=('mobile',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberShowingView(APIView):
    """
        某成员的公开信息【用户】
        https://api.yourpowersuck.com/members/:id/showing/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=id)
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource
        context = {'member': request.user}
        serializer = serializers.MemberShowingSerializer(member, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberProfileView(APIView):
    """
        某成员的私有信息【本人】
        https://api.yourpowersuck.com/members/:id/profile/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsOwner,)

    def permission_denied(self, request, message=None):
        raise exceptions.PermissionDenied

    def get(self, request, id):
        # todo:第二个版本添加个人中心详细内容
        serializer = serializers.MemberProfileSerializer(request.user)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberStickyActivityView(APIView):
    """
        某成员的置顶活动【用户】
        https://api.yourpowersuck.com/members/:id/sticky-activity/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=id)
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource
            # 判断当前用户是否存在未结束的活动
            # 注意values('id')是以字典返回
        try:
            member_ongoing_activity_id_list = list(Activity.objects.filter(does_pass=True,
                participation_record__in=list(member.existing_participation_records)).exclude(
                status='has_completed').values_list('id',flat=True))
        except:
            member_ongoing_activity_id_list = []
        try:
            branch = member.member_of
            branch_ongoing_activity_id_list = list(branch.existing_activities.filter(does_pass=True,
                                             status='is_signing_up').values_list('id', flat=True))
        except:
            branch_ongoing_activity_id_list = []
        joined_activity_list = set(member_ongoing_activity_id_list + branch_ongoing_activity_id_list)
        data = []
        for activity_id in joined_activity_list:
            activity = Activity.objects.get(id=activity_id)
            activity_dic = {
                'id': activity_id,
                'name': activity.name,
                'begin': str(activity.begin),
                'end': str(activity.end),
                'number_of_activity':activity.participation_records.filter(does_exist=True).count(),
                'thumb_image':str(activity.thumb_image) if activity.thumb_image else '',
            }
            data.append(activity_dic)
        response = {
            'data': data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberActivitiesView(ListAPIView):
    """
        某成员参与过的活动列表【用户】
        https://api.yourpowersuck.com/members/:id/activities/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.MemberActivitiesSerializer
    pagination_class = paginators.ActivitiesCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=self.kwargs['id'])
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource
        activities = Activity.objects.filter(participation_record__in=list(member.existing_participation_records))
        return activities


class MemberActivitiesExtraInfoView(APIView):
    """
        "某成员参与过的活动列表"的额外信息【用户】
        https://api.yourpowersuck.com/members/:id/activities/extra-info/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        serializer = serializers.MemberActivitiesExtraInfoSerializer(request.user)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberBranchIdView(APIView):
    """
        某成员加入的分舵id【本人】
        https://api.yourpowersuck.com/members/:id/branch-id/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsOwner,)

    def permission_denied(self, request, message=None):
        raise exceptions.PermissionDenied

    def get(self, request, id):
        branch = request.user.member_of
        if not branch:
            # 此成员未加入分舵
            raise exceptions.NoSuchResource
        response = {
            'data': {'branch_id': branch.id},
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberIsRunnerView(APIView):
    """
        某成员是否跑者【本人】
        https://api.yourpowersuck.com/members/:id/is-runner/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsOwner,)

    def get(self, request, id):
        # is_runner = request.user.mobile != ''
        # 这个版本默认所有人都是跑者
        is_runner = True
        response = {
            'data': {'is_runner': is_runner},
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberEditView(APIView):
    """
        修改名称【用户】
        https://api.yourpowersuck.com/members/edit-name/
        同步头像（从微信）【用户】
        https://api.yourpowersuck.com/members/edit-avatar/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request):
        serializer = serializers.MemberShowingSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            # 参数错误
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberEditMobileView(APIView):
    """
        更改手机号（手动）【用户】
        https://api.yourpowersuck.com/members/edit-mobile/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        mobile = request.data.get('mobile', '')
        if not mobile:
            # 参数错误
            raise exceptions.ArgumentError
        check_mobile, created = CheckMobile.objects.get_or_create(member=request.user)
        if not created:
            # 老用户
            if check_mobile.counter == 9:
                # 若之前已调用接口9次，设置limit_time为当前时间
                check_mobile.limit_time = datetime.datetime.now()
            elif check_mobile.counter == 10:
                # 若之前已调用接口10次，检查当日访问是否达到上限
                if check_mobile.reaches_the_limit:
                    # 访问达到上限
                    # raise exceptions.TooManyRequests
                    check_mobile.counter = 0
                else:
                    # 检查成功则刷新次数
                    check_mobile.counter = 0
        check_mobile.mobile = mobile
        check_mobile.verification_code = random_int_6()
        check_mobile.expire = ten_minutes_from_now()
        check_mobile.counter += 1
        check_mobile.save(update_fields=('mobile', 'verification_code', 'expire', 'counter', 'limit_time'))
        try:
            # 尝试调用云片短信API发短信验证码到手机
            send_verification_code(check_mobile.verification_code, check_mobile.mobile)
        except:
            # 云片API调用失败
            raise exceptions.RequestFailed
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberCheckMobileView(APIView):
    """
        核验手机号【用户】
        https://api.yourpowersuck.com/members/check-mobile/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        verification_code = request.data.get('verification_code', '')
        if not (verification_code.isdigit() and len(verification_code) == 6):
            # 参数错误
            raise exceptions.ArgumentError
        try:
            # 尝试查找当前用户的核验手机号记录
            check_mobile = CheckMobile.objects.get(member=request.user)
        except CheckMobile.DoesNotExist:
            # 核验记录不存在
            raise exceptions.RequestFailed
        if check_mobile.verification_code != int(verification_code):
            # 验证码与核验记录不匹配
            raise exceptions.RequestFailed
        if check_mobile.has_expired:
            # 验证码超时
            raise exceptions.RequestFailed
        request.user.mobile = check_mobile.mobile
        request.user.save(update_fields=('mobile',))
        # 删除之前的核验记录
        CheckMobile.objects.filter(member=request.user).delete()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberStartBranchView(APIView):
    """
        新建分舵【跑者，且没有加入任何分舵】
        https://api.yourpowersuck.com/members/start-branch/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def permission_denied(self, request, message=None):
        raise exceptions.NotARunner

    def post(self, request):
        if request.user.member_of:
            # 已加入分舵则不允许新建分舵
            raise exceptions.PermissionDenied
        context = {'member': request.user}
        serializer = serializers.MemberStartBranchSerializer(data=request.data, context=context)
        if not serializer.is_valid():
            # 参数错误
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class NearbyActivitiesView(ListAPIView):
    """
        按照距离显示分舵正在进行的活动 【用户】
        http://api.yourpowersuck.com/members/:id/nearby-activities
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.NearbyActivitesSerializer
    pagination_class = paginators.NearbyActivitesPagination

    def get_queryset(self):
        try:
            # 尝试获取latitude和longitude参数并转换成坐标
            latitude = float(self.request.query_params['latitude'])
            longitude = float(self.request.query_params['longitude'])
            assert 90.00 >= latitude >= -90.00
            assert 180.00 >= longitude >= -180.00
            user_coordinates = Point(longitude, latitude, srid=4326)
        except:
            # 参数错误
            raise exceptions.ArgumentError
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=self.kwargs['id'])
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource

        # 获取成员加入的分舵，最后结果应排除该分舵的活动
        branch = member.member_of
        # 获取成员加入的活动，最后结果应排除已经加入的活动
        activities_list = Activity.objects.filter(participation_record__in=list(member.existing_participation_records))

        return Activity.objects.filter(does_exist=True,does_pass=True).exclude(status='has_completed').exclude(
            branch=branch).exclude(id__in= activities_list).annotate(
            distance=Distance('branch__location__coordinates', user_coordinates, spheroid=True))


class GetFormIdView(APIView):
    """
        获取用户的formid
        http://api.yourpowersuck.com/members/get-form-id/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request):
        # 记录当前用户的formid(2个)
        formid1 = request.data['formid1']
        formid2 = request.data['formid2']
        timestamp = int(time.time()) + 3600 * 24 * 7 - 3600
        if formid1 != 'the formId is a mock one':
            form_id_dic1 = {
                'member': request.user,
                'formid': formid1,
                'timestamp': timestamp,
            }
            form_id1 = MemberFormId(**form_id_dic1)
            form_id1.save()
        if formid2 != 'the formId is a mock one':
            form_id_dic2 = {
                'member': request.user,
                'formid': formid2,
                'timestamp': timestamp,
            }
            form_id2 = MemberFormId(**form_id_dic2)
            form_id2.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class GetAccessTokenView(APIView):
    """
        获取当前小程序的access_token
        http://api.yourpowersuck.com/wx/access-token/
    """

    def post(self, request):
        # 记录当前用户的formid(2个)
        password = request.data['password']
        # post请求发送的密码
        if password != 'Ien6Hvq9GXkXCkeiDJxryesGS7Tievcx':
            raise exceptions.RequestFailed
        client_ip = request.META['REMOTE_ADDR']
        # if client_ip != "59.173.98.1":
        # 此为测试服务器的ip，只有测试服务器发送该请求可以返回数据
        if client_ip != "47.105.166.254":
            raise exceptions.RequestFailed
        access_token = get_access_token()
        # 密钥
        pc = PrpCrypt('JEwKENYmRMSEYbn87Do5qQNagVxGJshl')
        e = pc.encrypt(access_token)
        return Response(e)