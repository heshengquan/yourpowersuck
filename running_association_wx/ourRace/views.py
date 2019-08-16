import time
import requests
from django.http import HttpResponse
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers
from .models import Marathon, MarathonInfo, CompetitionEventParticipationRecord, ParticipationInfo, AoNumberClothInfo
from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.config import WEIXIN_NOTIFY_URL_MARATHON_ORDER
from utils.payment import get_bodyData, xml_to_dict, get_paysign
from utils.access_token import get_access_token


# class MarathonsView(APIView):
#     """
#         赛事列表【用户】
#         https://api.yourpowersuck.com/our-races/
#     """
#
#     authentication_classes = (MemberAuthentication,)
#
#     def get(self, request):
#         timestamp = int(time.time())
#         try:
#             marathons = Marathon.objects.all()
#             res = []
#             for marathon in marathons:
#                 serializer = serializers.MarathonSerializer(marathon)
#                 data = serializer.data
#                 complete_sign = int(time.mktime(time.strptime(data['sign_up_end'], '%Y-%m-%d %H:%M')))
#                 has_completed = int(time.mktime(time.strptime(data['time'], '%Y-%m-%d %H:%M')))
#                 if timestamp > has_completed:
#                     data['status'] = 'has_completed'
#                 elif timestamp > complete_sign:
#                     data['status'] = 'complete_sign'
#                 else:
#                     data['status'] = 'is_signing_up'
#                 res.append(data)
#             return Response(res)
#         except Marathon.DoesNotExist:
#             # 不存在
#             raise exceptions.NoSuchResource


class MarathonsView(ListAPIView):
    """
        赛事列表【用户】
        https://api.yourpowersuck.com/our-races/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.MarathonSerializer

    def get_queryset(self):
        try:
            marathons = Marathon.objects.all()
            return marathons
        except Marathon.DoesNotExist:
            # 不存在
            raise exceptions.NoSuchResource


class MarathonView(APIView):
    """
        某赛事详细信息【用户】
        https://api.yourpowersuck.com/our-races/:id/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的赛事
            marathon = Marathon.objects.get(id=id)
        except Marathon.DoesNotExist:
            # 不存在
            raise exceptions.NoSuchResource
        serializer = serializers.MarathonSerializer(marathon)
        response = {
            'data': {
                'member_avatar_urls': serializer.data
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class CompetitionEventsView(ListAPIView):
    """
        某赛事的竞赛项目列表【用户】
        https://api.yourpowersuck.com/our-races/:id/competition-events/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.CompetitionEventsSerializer

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的赛事
            marathon = Marathon.objects.get(id=self.kwargs['id'])
        except Marathon.DoesNotExist:
            # 不存在
            raise exceptions.NoSuchResource
        return marathon.competition_events


class CompetitionEventView(APIView):
    """
        某赛事的某竞赛项目的详细信息【用户】
        https://api.yourpowersuck.com/our-races/:id/competition-events/:evid/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id, evid):
        try:
            # 尝试获取当前id对应的赛事
            marathon = Marathon.objects.get(id=id)
            # 尝试获取当前evid对应的竞赛项目
            competition_event = marathon.competition_events.get(id=evid)
        except:
            # 不存在
            raise exceptions.NoSuchResource
        serializer = serializers.CompetitionEventSerializer(competition_event)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MarathonInfoView(APIView):
    """
        赛事章程【用户】
        https://api.yourpowersuck.com/our-races/info/:infoid/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, infoid):
        try:
            marathon_info = MarathonInfo.objects.get(id=infoid)
        except:
            raise exceptions.NoSuchResource
        serializer = serializers.MarathonInfoSerializer(marathon_info)
        response = {
            "data": serializer.data,
            "code": 0,
            "error": ''
        }
        return Response(response)


class MarathonExtraInfoView(APIView):
    """
        赛事额外信息【用户】
        https://api.yourpowersuck.com/our-races/:id/extra/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的赛事
            marathon = Marathon.objects.get(id=id)
        except Marathon.DoesNotExist:
            # 不存在
            raise exceptions.NoSuchResource
        # 当前用户是否已报名当前赛事并已支付
        is_in = request.user.marathon_participation_records.filter(marathon_id=marathon.id, pay_status=True).exists()
        branch = request.user.member_of
        if not branch:
            # 如果没有加入分舵
            branch_name = ''
            current_branch_in_num = ''
        else:
            # 当前分舵团报人数
            branch_name = branch.name
            current_branch_in_num = CompetitionEventParticipationRecord.objects.filter(marathon_id=marathon.id,
                                                                                       branch_id=branch.id,
                                                                                       pay_status=True).count()
        response = {
            "data": {
                "is_in": is_in,
                "branch_name": branch_name,
                "current_branch_in_num": current_branch_in_num,
            },
            "code": 0,
            "error": ''
        }
        return Response(response)


class ParticipationInfoView(APIView):
    """
        查看/修改当前用户报名信息【用户】
        https://api.yourpowersuck.com/our-races/participation-info/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request):
        has_info = True
        try:
            # 查看此人是否有报名信息
            participation_info = ParticipationInfo.objects.get(member=request.user)
        except:
            # 无报名信息
            has_info = False
        try:
            # 尝试获取此人的地址
            address = request.user.member_address.get(does_exist=True, is_default=True).detail_address
        except:
            address = ''
        if has_info:
            serializer = serializers.ParticipationInfoSerializer(participation_info)
            data = serializer.data
        else:
            data = dict()
        data['address'] = address
        response = {
            'data': data,
            'code': 0,
            'error': '',
        }
        return Response(response)

    def post(self, request):
        update = True
        try:
            # 查看此人是否有报名信息
            participation_info = ParticipationInfo.objects.get(member=request.user)
        except:
            update = False
        if update:
            # 更新原有信息
            serializer = serializers.ParticipationInfoSerializer(participation_info, data=request.data, partial=True)
        else:
            # 创建新的信息
            serializer = serializers.ParticipationInfoSerializer(data=request.data, context={'member': request.user})
        if not serializer.is_valid():
            # 参数错误
            raise exceptions.ArgumentError
        serializer.save()
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class MarathonSignUpView(APIView):
    """
        当前用户报名【用户】
        https://api.yourpowersuck.com/our-races/:id/sign-up/:evid/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id, evid):
        try:
            # 尝试获取当前id对应的赛事
            marathon = Marathon.objects.get(id=id)
            # 尝试获取当前evid对应的竞赛项目
            competition_event = marathon.competition_events.get(id=evid)
        except:
            # 不存在
            raise exceptions.NoSuchResource
        branch = request.user.member_of
        if not branch:
            # 如果没有加入分舵
            branch_id = ''
        else:
            branch_id = branch.id
        if not CompetitionEventParticipationRecord.objects.filter(member=request.user,
                                                                  marathon_id=marathon.id).exists():
            # 未参加此马拉松
            record = CompetitionEventParticipationRecord.objects.create(member=request.user,
                                                                        competition_event=competition_event,
                                                                        branch_id=branch_id, marathon_id=marathon.id)
        else:
            # 已参加此马拉松
            if CompetitionEventParticipationRecord.objects.filter(member=request.user, marathon_id=marathon.id,
                                                                  pay_status=True).exists():
                # 存在已付款竞赛项目
                raise exceptions.PermissionDenied
            else:
                # 不存在已付款竞赛项目
                try:
                    # 参加此项目但未付款
                    record = CompetitionEventParticipationRecord.objects.get(member=request.user,
                                                                             competition_event=competition_event,
                                                                             pay_status=False)
                    # 针对已记录报名信息未付款的用户,更新其所在团报信息
                    record.branch_id = branch_id
                    record.save()
                except:
                    # 参加其余项目但未付款
                    record = CompetitionEventParticipationRecord.objects.create(member=request.user,
                                                                                competition_event=competition_event,
                                                                                branch_id=branch_id,
                                                                                marathon_id=marathon.id)
        try:
            # 尝试组装数据调用微信统一下单接口
            # 价格
            price = int(competition_event.price * 100)
            # 获取客户端ip
            client_ip = request.META['REMOTE_ADDR']
            # 获取小程序openid
            openid = request.user.openid
            # 请求微信的url
            url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
            # 拿到封装好的xml数据
            body = marathon.name + '-' + competition_event.name
            body_data, nonce_str, out_trade_no, = get_bodyData(body, WEIXIN_NOTIFY_URL_MARATHON_ORDER, openid,
                                                               client_ip, price)
            # 获取时间戳
            timeStamp = str(int(time.time()))
            # 请求微信接口下单
            respone = requests.post(url, body_data.encode("utf-8"), headers={'Content-Type': 'application/xml'})
            # 回复数据为xml,将其转为字典
            content = xml_to_dict(respone.content)
            if content["return_code"] == 'SUCCESS':
                try:
                    # 从微信的返回结果获取预支付交易会话标识
                    prepay_id = content.get("prepay_id")
                    # 保存信息
                    record.prepay_id = prepay_id
                    record.nonce_str = nonce_str
                    record.out_trade_no = out_trade_no
                    record.save()
                except:
                    raise exceptions.RequestFailed
                # 从微信的返回结果获取随机字符串
                nonceStr = content.get("nonce_str")
                # 计算paySign签名，这个需要我们根据从微信拿到的prepay_id和nonceStr进行计算签名
                paySign = get_paysign(prepay_id, timeStamp, nonceStr)
                # 封装返回给前端的数据
                data = {"prepay_id": prepay_id, "nonceStr": nonceStr, "paySign": paySign, "timeStamp": timeStamp}
                return Response(data)
            else:
                return Response(content['return_msg'])
        except:
            raise exceptions.RequestFailed


class MarathonOrderResultView(APIView):
    """
        马拉松报名支付成功通知函数接口
        https://api.yourpowersuck.com/payment/marathon-order-result/
    """

    def post(self, request):
        xmldata = request.body.decode('utf-8')
        return_data = xml_to_dict(xmldata)
        return_code = return_data['return_code']
        if return_code == 'FAIL':
            # 官方发出错误
            return HttpResponse("""<xml><return_code><![CDATA[FAIL]]></return_code>
                                    <return_msg><![CDATA[Signature_Error]]></return_msg></xml>""",
                                content_type='text/xml', status=200)
        elif return_code == 'SUCCESS':
            # 拿到这次支付的订单号
            out_trade_no = return_data['out_trade_no']
            record = CompetitionEventParticipationRecord.objects.get(out_trade_no=out_trade_no)
            if return_data['nonce_str'] != record.nonce_str:
                # 随机字符串不一致
                return HttpResponse("""<xml><return_code><![CDATA[FAIL]]></return_code>
                                       <return_msg><![CDATA[Signature_Error]]></return_msg></xml>""",
                                    content_type='text/xml', status=200)
            total_fee = int(record.competition_event.price * 100)
            if return_data['total_fee'] != str(total_fee):
                # 账单金额不一致
                return HttpResponse("""<xml><return_code><![CDATA[FAIL]]></return_code>
                                       <return_msg><![CDATA[Signature_Error]]></return_msg></xml>""",
                                    content_type='text/xml', status=200)
            # 修改该订单的相关记录
            record.pay_status = True
            record.save()
            print('支付完成')
            return HttpResponse(
                """<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>""",
                content_type='text/xml', status=200)


class MarathonOrderSuccessView(APIView):
    """
       前端查询支付完成后调用此接口,进行模板发送及支付状态未更新处理
       https://api.yourpowersuck.com/our-races/:prepay_id/order-success-result/
   """

    authentication_classes = (MemberAuthentication,)

    def get(self, request, prepay_id):
        response = {
            'data': {},
            'code': 0,
            'error': 'deal success'
        }
        try:
            # 获取个人信息
            participation_info = ParticipationInfo.objects.get(member=request.user)
        except:
            response['error'] += ' 个人信息查询失败 '

        try:
            # 获取参赛记录
            record = CompetitionEventParticipationRecord.objects.get(member=request.user, prepay_id=prepay_id,
                                                                     pay_status=True)
            # 获取对应比赛信息
            marathon_info = Marathon.objects.get(id=record.marathon_id)
            date = marathon_info.time.strftime("%Y-%m-%d %H:%M:%S")
            access_token = get_access_token()
            # 发送模板封装
            data = {
                "touser": record.member.openid,
                "template_id": 'vkRjdubdEt-75wg11ThxMpLbevGQZr2Ul6iTZVVWT5Y',
                "page": 'pages/me/main',
                "form_id": record.prepay_id,
                "data": {
                    'keyword1': {
                        'value': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))),
                    },
                    'keyword2': {
                        'value': date,
                    },
                    'keyword3': {
                        'value': participation_info.name,
                    },
                    'keyword4': {
                        'value': marathon_info.place,
                    }
                },
            }
            push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                access_token)
            requests.post(push_url, json=data, timeout=3)

        except:
            # 用户支付成功,由于微信回调出错导致付款状态未更新,进行下面更新
            record = CompetitionEventParticipationRecord.objects.get(member=request.user, prepay_id=prepay_id)
            record.pay_status = True
            record.save()
            marathon_info = Marathon.objects.get(id=record.marathon_id)
            date = marathon_info.time.strftime("%Y-%m-%d %H:%M:%S")
            access_token = get_access_token()
            data = {
                "touser": record.member.openid,
                "template_id": 'vkRjdubdEt-75wg11ThxMpLbevGQZr2Ul6iTZVVWT5Y',
                "page": 'pages/me/main',
                "form_id": record.prepay_id,
                "data": {
                    'keyword1': {
                        'value': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))),
                    },
                    'keyword2': {
                        'value': date,
                    },
                    'keyword3': {
                        'value': participation_info.name,
                    },
                    'keyword4': {
                        'value': marathon_info.place,
                    }
                },
            }
            push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                access_token)
            requests.post(push_url, json=data, timeout=3)
            response = {
                'data': {},
                'code': 0,
                'error': '付款状态更新成功'
            }

        return Response(response)


class AoNumberSearch(APIView):
    """
       奥野号码布信息查询
       https://api.yourpowersuck.com/our-races/ao-number-search/
   """

    # authentication_classes = (MemberAuthentication,)

    def get(self, request):
        name = request.GET.get('name')
        certificate_num = request.GET.get('certificate_num')
        certificate_type = request.GET.get('type')
        try:
            player = AoNumberClothInfo.objects.get(certificate_num=certificate_num, name=name)
        except:
            # 不存在
            raise exceptions.NoSuchResource
        serializer = serializers.NumberClothInfoSerializer(player)
        data = serializer.data
        # 查询证件类型为身份证
        if certificate_type == '0':
            data['image'] = '/ourRace/number_cloth/image/ao_ye/{}.jpg'.format(data['group_name'])
        # 查询证件类型为其他证件
        else:
            data['image'] = '/ourRace/number_cloth/image/ao_ye/{}.jpg'.format(data['number'])
        return Response({'data': data, 'code': 0})
