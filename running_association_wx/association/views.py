import time

import datetime
import requests
from decimal import Decimal
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import IntegerField, Case, Value, When, Count, Sum
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from me.models import Member
from me.paginators import ActivitiesCursorPagination
from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.config import WEIXIN_NOTIFY_URL_FOUND
from utils.payment import get_bodyData, xml_to_dict, get_paysign, WithDraw
from utils.permissions import IsAuthorizedByMobile
from . import paginators
from . import serializers
from .models import Branch, BranchFundRecord


class BranchesView(ListAPIView):
    """
        分舵列表【用户，且未加入任何分舵】
        https://api.yourpowersuck.com/branches/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.BranchesSerializer
    pagination_class = paginators.BranchesCursorPagination

    def get_queryset(self):
        if self.request.user.member_of:
            # 已加入分舵者不允许访问
            raise exceptions.RequestFailed
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
        return Branch.objects.get_existing_all().annotate(
            distance=Distance('location__coordinates', user_coordinates, spheroid=True))


class BranchView(APIView):
    """
        某分舵的信息【用户】
        https://api.yourpowersuck.com/branches/:id/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        context = {'member': request.user}
        serializer = serializers.BranchSerializer(branch, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchMemberAvatarURLsView(APIView):
    """
        某分舵的所有成员头像url【用户】
        https://api.yourpowersuck.com/branches/:id/member-avatar-urls/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        members = branch.members.annotate(
            priority=Case(
                When(master_of=branch, then=Value(2)),  # 舵主优先级最高
                When(deputy_of=branch, then=Value(1)),  # 副舵主优先级次之
                default=Value(0),  # 普通成员最次
                output_field=IntegerField(),
            ),
        )
        member_avatar_urls = [member.avatar_url for member in members.all().order_by('-priority')]
        response = {
            'data': {
                'member_avatar_urls': member_avatar_urls
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchActivitiesView(ListAPIView):
    """
        某分舵的活动列表【用户】
        https://api.yourpowersuck.com/branches/:id/activities/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.BranchActivitiesSerializer
    pagination_class = ActivitiesCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=self.kwargs['id'])
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        return branch.existing_activities


class BranchMembersView(ListAPIView):
    """
        某分舵的成员列表【此分舵成员】
        https://api.yourpowersuck.com/branches/:id/members/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.BranchMembersSerializer
    pagination_class = paginators.MembersCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=self.kwargs['id'])
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        # if self.request.user.member_of != branch:
        #     # 当前用户不是此分舵成员,权限不足
        #     raise exceptions.PermissionDenied
        return branch.members.annotate(
            priority=Case(
                When(master_of=branch, then=Value(2)),  # 舵主优先级最高
                When(deputy_of=branch, then=Value(1)),  # 副舵主优先级次之
                default=Value(0),  # 普通成员最次
                output_field=IntegerField(),
            ),
        )


class BranchMembersExtraInfoView(APIView):
    """
        "某分舵的成员列表"的额外信息【此分舵成员】
        https://api.yourpowersuck.com/branches/:id/members/extra-info/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        # if request.user.member_of != branch:
        #     # 当前用户不是此分舵成员,权限不足
        #     raise exceptions.PermissionDenied
        context = {'member': request.user}
        serializer = serializers.BranchMembersExtraInfoSerializer(branch, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class JoinBranchView(APIView):
    """
        加入分舵【跑者，且没有加入任何分舵】
        https://api.yourpowersuck.com/branches/:id/join/
    """

    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def permission_denied(self, request, message=None):
        raise exceptions.NotARunner

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.member_of:
            # 当前用户已加入分舵则请求失败
            raise exceptions.RequestFailed
        request.user.member_of = branch
        request.user.save(update_fields=('member_of',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class QuitBranchView(APIView):
    """
        退出分舵【此分舵成员，且不为此分舵舵主】
        https://api.yourpowersuck.com/branches/:id/quit/
    """

    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.member_of != branch:
            # 当前用户不是此分舵成员,权限不足
            raise exceptions.PermissionDenied
        if request.user.master_of == branch:
            # 当前用户是此分舵舵主,请求失败
            raise exceptions.RequestFailed
        request.user.member_of = None
        if request.user.deputy_of:
            # 如果当前用户是此分舵的副舵主则把副舵主职位去除
            request.user.deputy_of = None
        request.user.save(update_fields=('member_of', 'deputy_of'))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchStartActivityView(APIView):
    """
        发起活动【此分舵舵主或副舵主】
        https://api.yourpowersuck.com/branches/:id/start-activity/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if not (request.user.master_of == branch or request.user.deputy_of == branch):
            # 当前用户不是此分舵舵主或副舵主,权限不足
            raise exceptions.PermissionDenied
        # if branch.existing_activities.exclude(status='has_completed').exists():
        #     # 当前分舵有未结束的活动,请求失败
        #     raise exceptions.RequestFailed
        # if request.user.existing_participation_records.exclude(activity__status='has_completed').exists():
        #     # 当前用户有未结束的活动,请求失败
        #     raise exceptions.RequestFailed
        rechargeable = request.data.get('rechargeable',False)
        if rechargeable:
            does_pass = False
            money = request.data.get('money',0.00)
            # 记录活动发起者的微信号
            wx_number = request.data['wx_number']
            request.user.wx_number = wx_number
            request.user.save(update_fields=('wx_number',))
        else:
            money = 0.00
            does_pass = True
        context = {'branch': branch, 'founder': request.user, 'rechargeable':rechargeable, 'does_pass':does_pass, 'money':money}
        serializer = serializers.BranchStartActivitySerializer(data=request.data, context=context)
        if not serializer.is_valid():
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'data': id,
            'code': 0,
            'error': '',
        }
        return Response(response)


class DeleteBranchView(APIView):
    """
        删除分舵【此分舵舵主，且此分舵没有未结束活动】
        https://api.yourpowersuck.com/branches/:id/delete/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是此分舵舵主,权限不足
            raise exceptions.PermissionDenied
        branch_existing_activities = branch.existing_activities
        if branch_existing_activities.exclude(status='has_completed').exists():
            # 当前分舵有未结束的活动,请求失败
            raise exceptions.RequestFailed
        # 当前分舵有未提取的分舵基金则请求失败
        # if branch.fund:
        #     raise exceptions.ArgumentError
        branch.members.remove_all_branch_relationship()
        for activity in branch_existing_activities:
            activity.existing_participation_records.delete_all()
        branch_existing_activities.delete_all()
        branch.location.does_exist = False
        branch.location.save(update_fields=('does_exist',))
        branch.does_exist = False
        branch.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchEditView(APIView):
    """
        修改某分舵的信息【此分舵舵主】
        https://api.yourpowersuck.com/branches/:id/edit/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是此分舵舵主,权限不足
            raise exceptions.PermissionDenied
        serializer = serializers.BranchSerializer(branch, data=request.data, partial=True)
        if not serializer.is_valid():
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchEditLocationView(APIView):
    """
        修改某分舵的定位【此分舵舵主】
        https://api.yourpowersuck.com/branches/:id/edit-location/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是此分舵舵主,权限不足
            raise exceptions.PermissionDenied
        serializer = serializers.BranchLocationSerializer(branch.location, data=request.data)
        if not serializer.is_valid():
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class SetOrUnsetDeputyView(APIView):
    """
        任命/解任副舵主【此分舵舵主，且被任命/解任的成员是此分舵的成员且不为舵主】
        https://api.yourpowersuck.com/branches/:id/:option/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id, option):
        if option == 'set-deputy':
            # 任命副舵主操作
            flag = True
        elif option == 'unset-deputy':
            # 解任副舵主操作
            flag = False
        else:
            # 请求失败
            raise exceptions.RequestFailed
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是此分舵舵主,权限不足
            raise exceptions.PermissionDenied
        try:
            # 尝试获取待任命/解任副舵主的成员
            member = Member.objects.get(id=request.data['member_id'])
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.RequestFailed
        if member.member_of != branch or member.master_of == branch:
            # 待任命/解任副舵主的成员非此分舵成员或为此分舵的舵主,请求失败
            raise exceptions.RequestFailed
        member.deputy_of = branch if flag else None
        member.save(update_fields=('deputy_of',))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchTransferAuthority(APIView):
    """
        转移舵主权限
        https://api.yourpowersuck.com/branches/:id/transfer-authority/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是舵主,权限不足
            raise exceptions.PermissionDenied
        try:
            # 尝试获取被转移舵主的成员
            member = Member.objects.get(id=request.data['member_id'])
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.RequestFailed
        if member.deputy_of != branch:
            # 被转移舵主的成员不是副舵主,权限不足
            raise exceptions.RequestFailed
        request.user.master_of = None
        member.deputy_of = None
        member.master_of = branch
        # 更新
        request.user.save(update_fields=('master_of',))
        member.save(update_fields=('master_of', 'deputy_of'))
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class BranchEditImageView(APIView):
    """
        修改某分舵的配图【分舵舵主】
        https://api.yourpowersuck.com/branches/:id/edit-image/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if request.user.master_of != branch:
            # 当前用户不是此分舵舵主,权限不足
            raise exceptions.PermissionDenied
        serializer = serializers.BranchImageSerializer(branch, data=request.data)
        if not serializer.is_valid():
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MemberDonateFund(APIView):
    """
        分舵成员捐献分舵基金【分舵成员】
        https://api.yourpowersuck.com/branches/:id/donate-fund/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        # 验证用户是否属于该分舵，若不属于则不能捐赠
        if request.user.member_of != branch:
            raise exceptions.RequestFailed

        # 获取要捐献的钱
        money = int(request.data['money'])
        if money < 1:
            raise exceptions.ArgumentError

        # 获取客户端ip
        client_ip = request.META['REMOTE_ADDR']

        # 获取小程序openid
        openid = request.user.openid

        # 请求微信的url
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'

        # 拿到封装好的xml数据
        body = '分舵基金-' + branch.name
        body_data, nonce_str, out_trade_no, = get_bodyData(body, WEIXIN_NOTIFY_URL_FOUND, openid, client_ip, money)
        # 获取时间戳
        timeStamp = str(int(time.time()))
        # 请求微信接口下单
        respone = requests.post(url, body_data.encode("utf-8"), headers={'Content-Type': 'application/xml'})
        # 回复数据为xml,将其转为字典
        content = xml_to_dict(respone.content)
        if content["return_code"] == 'SUCCESS':
            # 获取预支付交易会话标识
            prepay_id = content.get("prepay_id")
            try:
                # 保存捐赠信息
                fund_dic = {
                    'branch': branch,
                    'member': request.user,
                    'money': money/100,
                    'nonce_str': nonce_str,
                    'out_trade_no': out_trade_no,
                    'order_status': 'has_created',
                    'prepay_id': prepay_id
                }
                order = BranchFundRecord(**fund_dic)
                order.save()
            except:
                return Response('保存捐赠信息失败')

            # 获取随机字符串
            nonceStr = content.get("nonce_str")
            # 获取paySign签名，这个需要我们根据拿到的prepay_id和nonceStr进行计算签名
            paySign = get_paysign(prepay_id, timeStamp, nonceStr)
            # 封装返回给前端的数据
            data = {"prepay_id": prepay_id, "nonceStr": nonceStr, "paySign": paySign, "timeStamp": timeStamp}
            return Response(data)
        else:
            return Response(content['return_msg'])


class MasterWithDrawFund(APIView):
    """
        舵主提现分舵基金【分舵舵主】
        https://api.yourpowersuck.com/branches/:id/withdraw-fund/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=id)
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        # 如果不是舵主则不能提现
        if request.user.master_of != branch:
            raise exceptions.RequestFailed
        # 获取要提取的钱
        money = int(request.data['money'])
        if money < 100 or money > 500000:
            raise exceptions.ArgumentError
        if money > branch.fund*100:
            raise exceptions.ArgumentError
        # 保存提现信息
        fund_dic = {
            'branch': branch,
            'member': request.user,
            'money': -money / 100,
            'out_trade_no': '',
            'nonce_str': '',
            'order_status': 'has_created',
        }
        withdraw_fund = BranchFundRecord(**fund_dic)
        withdraw_fund.save()
        open_id = request.user.openid
        xmlmsg = WithDraw(open_id, str(money), '分舵基金提现')
        if xmlmsg['xml']['return_code'] == 'SUCCESS' and xmlmsg['xml']['result_code'] == 'SUCCESS':
            branch.fund = branch.fund - Decimal(money)/100
            branch.save()
            # 保存提现信息
            withdraw_fund.out_trade_no = xmlmsg['xml']['partner_trade_no']
            withdraw_fund.transaction_id = xmlmsg['xml']['payment_no']
            withdraw_fund.nonce_str = xmlmsg['xml']['nonce_str']
            withdraw_fund.order_status = 'has_paid'
            withdraw_fund.pay_time = datetime.datetime.now()
            withdraw_fund.save()
        else:
            raise exceptions.PermissionDenied
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class ShowBranchFundDetail(ListAPIView):
    """
        某分舵的分舵基金明细【此分舵成员】
        https://api.yourpowersuck.com/branches/:id/fund-detail/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.BranchFundDeatailSerializer
    pagination_class = paginators.BranchFundDeatailCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=self.kwargs['id'])
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if self.request.user.member_of != branch:
            # 当前用户不是此分舵成员,权限不足
            raise exceptions.PermissionDenied

        return BranchFundRecord.objects.filter(branch=branch, order_status='has_paid')


class ShowBranchFundRanking(ListAPIView):
    """
        某分舵的分舵基金贡献排行榜【此分舵成员】
        https://api.yourpowersuck.com/branches/:id/fund-ranking/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.BranchFundRankingSerializer
    pagination_class = paginators.BranchFundRankingCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的分舵
            branch = Branch.objects.get_existing_all().get(id=self.kwargs['id'])
        except Branch.DoesNotExist:
            # 分舵不存在
            raise exceptions.NoSuchResource
        if self.request.user.member_of != branch:
            # 当前用户不是此分舵成员,权限不足
            raise exceptions.PermissionDenied

        return BranchFundRecord.objects.filter(
            branch=branch, order_status='has_paid', member__member_of=branch, money__gt=0)\
            .values('member').annotate(total = Sum('money'))


# 删除已经没有舵主的分舵
def DeleteBranch():
    branches = Branch.objects.get_existing_all()
    for branch in branches:
        try:
            branch.master
        except:
            branch.does_exist = False
            branch.save()
            members = branch.members.all()
            for member in members:
                member.member_of = None
                member.save()

