import json
import random
from datetime import datetime, timedelta

import requests
from django.db.models import Max, Count, Q, Min
import time
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from me.models import Member, MemberFormId, CheckMobile
from pay.models import Address
from utils import exceptions
from utils.authentications import MemberAuthentication
from . import paginators
from utils.permissions import IsAuthorizedByMobile
from . import serializers
from .models import PollingActivity, PollingItem, PollingItemImages, MemberPollingRecord, PollingItemCity
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils.timezone import now, timedelta
from utils.access_token import get_access_token


class CreatePollingItemView(APIView):
    """
        创建新的投票条目,点击“我要报名”后创建,只创建新的报名条目,不更新信息【用户】
        https://api.yourpowersuck.com/polling-activities/:id/create-item/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=id)
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        # 若该活动已结束则不允许报名
        if polling_activity.status == 'has_completed':
            raise exceptions.RequestFailed
        # 如果该用户在该活动中已经报名成功则不允许再次报名
        if PollingItem.objects.filter(polling_activity=polling_activity, member=request.user, is_successful=True):
            raise exceptions.PermissionDenied
        # 若用户有默认的收货地址，则返回地址详情
        address = Address.objects.filter(member_id=request.user, is_default=True, does_exist=True)
        address_dic = {}
        if address:
            address_dic = {
                'name': address[0].name,
                'phone': address[0].phone,
                'province_name': address[0].province_name,
                'city_name': address[0].city_name,
                'county_name': address[0].county_name,
                'detail_info': address[0].detail_info,
                'post_num': address[0].post_num,
            }
        # 如果该用户曾点击过“我要报名”，判断用户是否上传过照片，若有则继续显示已上传的图片
        polling_item = PollingItem.objects.filter(polling_activity=polling_activity, member=request.user)
        if polling_item:
            polling_item_images_list = []
            avatar_image = ''
            for polling_item_image in PollingItemImages.objects.filter(polling_item=polling_item[0], does_exist=True):
                if polling_item_image.is_avatar == True:
                    avatar_image = {'image_url': str(polling_item_image.preview),
                                    'image_id': polling_item_image.id}
                else:
                    polling_item_images_list.append({'image_url': str(polling_item_image.preview),
                                                     'image_id': polling_item_image.id})
            response = {
                'data': {
                    'avatar_image': avatar_image,
                    'polling_item_images': polling_item_images_list,
                    'polling_item_id': polling_item[0].id,
                    'address': address_dic
                },
                'code': 0,
                'error': '',
            }
            return Response(response)
        # 若用户第一次点击“我要报名”，为该用户创建一个投票条目id
        polling_item_dic = {
            'polling_activity': polling_activity,
            'member': request.user,
        }
        polling_item = PollingItem(**polling_item_dic)
        polling_item.save()
        response = {
            'data': {
                'avatar_image': '',
                'polling_item_images': [],
                'polling_item_id': polling_item.id,
                'address': address_dic
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class JoinPollingItemView(APIView):
    """
        增加投票条目信息【已报名该活动的用户】
        https://api.yourpowersuck.com/polling-items/:id/join-item/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    # def throttled(self, request, wait):
    #     return exceptions.TooManyRequests

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 如果已报名成功则不允许修改信息
        if polling_item.is_successful == True:
            raise exceptions.ArgumentError
        # 如果未上传头像图则不允许保存
        if not PollingItemImages.objects.filter(polling_item=polling_item, does_exist=True, is_avatar=True):
            raise exceptions.PermissionDenied
        polling_item.city = ''
        polling_item.name = request.data['name']
        polling_item.phone = request.data['phone']
        polling_item.pub_date = datetime.now()
        polling_item.is_successful = True

        polling_item.save()
        # 为该选手推送模板消息
        access_token = get_access_token()
        time_now = int(time.time())
        # 获取其可用的formid
        formids = MemberFormId.objects.filter(is_available=True, timestamp__gt=time_now, member=polling_item.member)
        if formids:
            formid = formids[0]
            data = {
                "touser": polling_item.member.openid,
                "template_id": '5EShq2O4kDPDJSIX0du9LxaskidmA0iq09nB7w6dLf0',
                "page": 'pages/pollDetail/main?candidateId=' + id,
                "form_id": formid.formid,
                "data": {
                    'keyword1': {
                        'value': "遇见荆彩",
                    },
                    'keyword2': {
                        'value': request.data['name'],
                    },
                    'keyword3': {
                        'value': '您已报名成功，快去为自己拉票吧！',
                    }
                },
            }
            formid.is_available = False
            formid.save()
            push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                access_token)
            requests.post(push_url, json=data, timeout=3)
            formid.is_available = False
            formid.save()

        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class AddPollingItemView(APIView):
    """
        增加投票条目信息【已报名该活动的用户】
        https://api.yourpowersuck.com/polling-items/:id/add-item/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    # def throttled(self, request, wait):
    #     return exceptions.TooManyRequests

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 如果已报名成功则不允许修改信息
        if polling_item.is_successful == True:
            raise exceptions.ArgumentError
        # 如果未上传头像图则不允许保存
        if not PollingItemImages.objects.filter(polling_item=polling_item, does_exist=True, is_avatar=True):
            raise exceptions.PermissionDenied

        # 核验短信验证码
        verification_code = request.data.get('verification_code', '')
        if not (verification_code.isdigit() and len(verification_code) == 6):
            # 参数错误
            raise exceptions.RequestFailed
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
        # 把验证通过的手机号存入member表里
        request.user.mobile = check_mobile.mobile
        request.user.save(update_fields=('mobile',))
        # 删除之前的核验记录
        CheckMobile.objects.filter(member=request.user).delete()

        # 所有验证都通过，开始存数据
        city = request.data['cityName']
        if city == '省直辖县级行政区划':
            city = request.data['countyName']
        if city == '县':
            city = '重庆市'
        polling_item_city = PollingItemCity.objects.filter(name=city)
        if not polling_item_city:
            polling_item_city_dic = {
                'name': city,
                'polling_activity': polling_item.polling_activity,
            }
            polling_item_city = PollingItemCity(**polling_item_city_dic)
            polling_item_city.save()
        else:
            polling_item_city = polling_item_city[0]
        address = request.data['provinceName'] + ' ' + request.data['cityName'] + ' ' + \
                  request.data['countyName'] + ' ' + request.data['detailInfo']
        latitude = float(request.data['latitude'])
        longitude = float(request.data['longitude'])
        coordinates = Point(longitude, latitude, srid=4326)
        polling_item.name = request.data['name']
        polling_item.phone = request.data['phone']
        polling_item.city = polling_item_city
        polling_item.address = address
        polling_item.pub_date = datetime.now()
        polling_item.is_successful = True
        polling_item.coordinates = coordinates

        polling_item.save()
        polling_item_city.number += 1
        polling_item_city.save()
        # 为该选手推送模板消息
        access_token = get_access_token()
        time_now = int(time.time())
        # 获取其可用的formid
        formids = MemberFormId.objects.filter(is_available=True, timestamp__gt=time_now, member=polling_item.member)
        if formids:
            formid = formids[0]
            data = {
                "touser": polling_item.member.openid,
                "template_id": '5EShq2O4kDPDJSIX0du9LxaskidmA0iq09nB7w6dLf0',
                "page": 'pages/pollDetail/main?candidateId=' + id,
                "form_id": formid.formid,
                "data": {
                    'keyword1': {
                        'value': "第二届中国最美女跑者评选",
                    },
                    'keyword2': {
                        'value': request.data['name'],
                    },
                    'keyword3': {
                        'value': '您已报名成功，快来为自己拉票吧！\n添加约跑社客服微信，关注活动最新动态哦，微信号：yuepaosheyps',
                    }
                },
            }
            formid.is_available = False
            formid.save()
            push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                access_token)
            requests.post(push_url, json=data, timeout=3)
            formid.is_available = False
            formid.save()

        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class AddPollingItemImagesView(APIView):
    """
        新增投票条目图片【已报名该活动的用户】
        https://api.yourpowersuck.com/polling-items/:id/add-item-images/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 如果已报名成功则不允许添加图片
        if polling_item.is_successful == True:
            raise exceptions.RequestFailed
        # 如果上传的图片数量已达最大值则不允许添加图片
        img_amount = PollingItemImages.objects.filter(polling_item=polling_item, does_exist=True,
                                                      is_avatar=False).count()
        if img_amount >= polling_item.img_limits + 1:
            raise exceptions.RequestFailed
        # 判断是否为头像
        if request.data['is_avatar'] == '1':
            avatar_img = PollingItemImages.objects.filter(polling_item=polling_item, does_exist=True, is_avatar=True)
            if avatar_img:
                # 如果已经存在头像了则不允许再次添加头像
                raise exceptions.RequestFailed
            is_avatar = True
        else:
            is_avatar = False
        polling_item_image_dic = {
            'image': request.data['image'],
            'polling_item': polling_item,
            'is_avatar': is_avatar
        }
        polling_item_image = PollingItemImages(**polling_item_image_dic)
        polling_item_image.save()
        data = {
            'image_id': polling_item_image.id,
            'image_url': str(polling_item_image.preview)
        }
        response = {
            'data': data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class DeletePollingItemImagesView(APIView):
    """
        删除投票条目图片【已报名但未提交的该活动的用户】
        https://api.yourpowersuck.com/polling-items/:id/delete-item-images/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 如果已报名成功则不允许删除图片
        if polling_item.is_successful == True:
            raise exceptions.RequestFailed
        image_id = request.data['image_id']
        polling_item_image = PollingItemImages.objects.get(id=image_id)
        polling_item_image.does_exist = False
        polling_item_image.save()
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class PollingActivitiesView(ListAPIView):
    """
        投票活动列表【用户】
        https://api.yourpowersuck.com/polling-activities/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.PollingActivitiesSerializer
    pagination_class = paginators.PollingActivitiesCursorPagination

    def get_queryset(self):
        return PollingActivity.objects.all()


class PollingActivityView(APIView):
    """
        投票活动具体信息【跑者】
        https://api.yourpowersuck.com/polling-activities/:id/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=id)
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        serializer = serializers.PollingActivitySerializer(polling_activity)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class PollingItemView(APIView):
    """
        投票条目具体信息【跑者】
        https://api.yourpowersuck.com/polling-items/:id/detail
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id, is_successful=True)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 获取该投票条目当前的票数及城市
        votes = polling_item.votes
        city = polling_item.city
        is_self = True if polling_item.member == request.user else False
        two_bar_codes = polling_item.two_bar_codes if polling_item.two_bar_codes else ''
        # 获取该投票条目当前的全国排名
        nation_ranking = PollingItem.objects.filter(votes__gt=votes, is_successful=True).count() + 1
        # 获取该投票条目当前的全国排名
        city_ranking = PollingItem.objects.filter(votes__gt=votes, is_successful=True, city=city).count() + 1
        context = {
            'nation_ranking': nation_ranking,
            'city_ranking': city_ranking,
            'is_self': is_self,
            'two_bar_codes': two_bar_codes,
            'city_id': polling_item.city.id
        }
        serializer = serializers.PollingItemSerializer(polling_item, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class PollingItemImagesView(APIView):
    """
        投票条目的配图【跑者】
        https://api.yourpowersuck.com/polling-items/:id/detail-images
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id, is_successful=True)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource

        avatar_image = ''
        polling_item_images_list = []
        for polling_item_image in PollingItemImages.objects.filter(polling_item=polling_item, does_exist=True):
            if polling_item_image.is_avatar == True:
                avatar_image = str(polling_item_image.image)
            else:
                polling_item_images_list.append(str(polling_item_image.image))
        response = {
            'data': {
                'avatar_image': avatar_image,
                'polling_item_images': polling_item_images_list,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class ParticipatePollView(APIView):
    """
        参与投票【跑者】
        https://api.yourpowersuck.com/polling-items/:id/participate-poll/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id, is_successful=True)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        # 获取当前投票条目对应的活动
        polling_activity = polling_item.polling_activity
        # 如果该活动已结束则不允许投票
        if polling_activity.status == 'has_completed':
            raise exceptions.RequestFailed
        # 如果用户没有头像或者名字，不允许投票
        if not request.user.avatar_url:
            raise exceptions.PermissionDenied
        # 判断当前用户在该活动中，今天投票是否超过可投票上限
        date_today = datetime.now().date()
        counter = MemberPollingRecord.objects.filter(member=request.user, polling_activity=polling_activity,
                                                     vote_date=date_today, ).count()
        if counter >= polling_activity.limit_per_day:
            response = {
                'message': '投票失败！今日投票次数已达上限，请明日再投',
                'code': 0,
                'error': '',
            }
            return Response(response)
        else:
            remain_times = polling_activity.limit_per_day - counter - 1
        # 判断当前用户今天在该活动中是否已经为该选手投票
        vote_polling_item = MemberPollingRecord.objects.filter(member=request.user, polling_activity=polling_activity,
                                                               vote_date=date_today, vote_item=polling_item)
        if vote_polling_item:
            response = {
                'message': '投票失败！今日已为该选手投票，请明日再投',
                'code': 0,
                'error': '',
            }
            return Response(response)
        member_polling_dic = {
            'member': request.user,
            'polling_activity': polling_activity,
            'vote_item': polling_item
        }
        member_polling = MemberPollingRecord(**member_polling_dic)
        member_polling.save()
        polling_item.votes = polling_item.votes + 1
        polling_item.save()
        message = '投票成功！今日还可投{}次'.format(remain_times)
        response = {
            'message': message,
            'code': 0,
            'error': '',
        }
        return Response(response)


class PollingItemsRankingView(ListAPIView):
    """
        某投票活动的全国投票数排行榜【用户】
        https://api.yourpowersuck.com/polling-activities/:id/ranking/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.PollingItemsSerializer
    pagination_class = paginators.PollingItemsRankingCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=self.kwargs['id'])
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        return PollingItem.objects.filter(polling_activity=polling_activity, is_successful=True)


class PollingItemsCityRankingView(ListAPIView):
    """
        某投票活动的城市参与情况排行榜【用户】
        https://api.yourpowersuck.com/polling-activities/:id/city-ranking/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.PollingItemsCityRankingSerializer
    pagination_class = paginators.PollingItemsCityRankingCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=self.kwargs['id'])
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        return PollingItemCity.objects.filter(polling_activity=polling_activity, number__gt=0)


class CityPollingItemsView(ListAPIView):
    """
        某活动投票数的城市排行榜【用户】
        https://api.yourpowersuck.com/polling-activities/:id/city-polling_items/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.PollingItemsSerializer
    pagination_class = paginators.PollingItemsRankingCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=self.kwargs['id'])
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        city_id = self.request.query_params['city_id']
        city = PollingItemCity.objects.get(id=city_id)
        return PollingItem.objects.filter(polling_activity=polling_activity,
                                          is_successful=True, city=city)


class NearbyPollingItemsView(ListAPIView):
    """
        按照距离显示附近参与某活动投票的选手【用户】
        http://api.yourpowersuck.com/polling-activities/:id/nearby-polling-items/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.NearbyPollingItemsSerializer
    pagination_class = paginators.NearbyPollingItemsCursorPagination

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
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=self.kwargs['id'])
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource

        return PollingItem.objects.filter(is_successful=True, polling_activity=polling_activity) \
            .annotate(distance=Distance('coordinates', user_coordinates, spheroid=True))


class LuckyDrawResultView(APIView):
    """
        每日锦鲤展示，只显示与报名者同一天参赛的所有人
        http://api.yourpowersuck.com/polling-activities/:id/lucky-draw-result/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=id)
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        # 判断是否为选手，或者刘韬，若不是则拒绝访问
        polling_item = PollingItem.objects.filter(member=request.user, is_successful=True,
                                                  polling_activity=polling_activity)
        if polling_item:
            polling_item = polling_item[0]
            month = polling_item.pub_date.date().strftime('%m')
            day = polling_item.pub_date.date().strftime('%d')
        else:
            if request.user.id != '6d63d6d7ae024e2aafe8dd3f96dbd2f8':
                raise exceptions.RequestFailed
            else:
                month = int(request.query_params['month'])
                day = int(request.query_params['day'])
        polling_item_list = PollingItem.objects.filter(is_successful=True, polling_activity=polling_activity,
                                                       pub_date__month=int(month), pub_date__day=int(day))
        others = []
        luckystar = {}
        for every_polling_item in polling_item_list:
            if every_polling_item.is_luckystar:
                luckystar = {
                    'name': every_polling_item.name,
                    'avatar_name': str(every_polling_item.avatar),
                }
            else:
                dic = {
                    'avatar_name': str(every_polling_item.avatar),
                }
                others.append(dic)
        response = {
            'data': {
                'luckystar': luckystar,
                'others': others,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class MyPollingStatusView(APIView):
    """
        获取自己的报名状态，若在该活动报名成功，返回投票条目的id
        http://api.yourpowersuck.com/polling-activities/:id/my-polling-status/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=id)
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        # 判断是否已报名成功
        polling_item = PollingItem.objects.filter(member=request.user, is_successful=True,
                                                  polling_activity=polling_activity)
        id = ''
        if polling_item:
            id = polling_item[0].id
        response = {
            'my_polling_id': id,
            'code': 0,
            'error': '',
        }
        return Response(response)


# 自动刷票
class AddVotesAutoView(APIView):
    """
        http://api.yourpowersuck.com/polling-item/:id/detail-info/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id, is_successful=True)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
        votes = int(request.data['votes'])
        second = int(request.data['second'])
        password = request.data['password']
        if password != '3u5BtcA85n618ooIE8cczbUcVbtRZH1M':
            raise exceptions.RequestFailed
        if request.user.id != '6d63d6d7ae024e2aafe8dd3f96dbd2f8':
            raise exceptions.PermissionDenied
        interval = second / votes
        for i in range(votes):
            polling_item.votes += 1
            polling_item.save()
            time.sleep(interval)
        response = {
            'code': 0,
            'error': ''
        }

        return Response(response)


class GetTwoBarCodesView(APIView):
    """
        获取自己的海报二维码
        http://api.yourpowersuck.com/polling-item/:id/two-bar-codes/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票条目
            polling_item = PollingItem.objects.get(id=id, is_successful=True)
        except PollingItem.DoesNotExist:
            raise exceptions.NoSuchResource
            # 尝试获取生成参数
        if polling_item.two_bar_codes:
            response = {
                'data': {
                    'two_bar_codes': str(polling_item.two_bar_codes)
                },
                'code': 0,
                'error': '',
            }
            return Response(response)
        access_token = get_access_token()
        QRcode_url = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={}'.format(access_token)
        raw_data = {
            'scene': id,
            'page': 'pages/pollDetail/main',
            'width': request.data.get('width', 430),
            'auto_color': request.data.get('auto_color', False),
            'line_color': request.data.get('line_color', {"r": 0, "g": 0, "b": 0}),
            'is_hyaline': request.data.get('is_hyaline', True),
        }
        data = json.dumps(raw_data)
        QRcode_request = requests.post(QRcode_url, data=data)
        img = 'media/polling/item/share/' + id + '.png'
        with open(img, 'wb') as f:
            f.write(QRcode_request.content)
        polling_item.two_bar_codes = str(img)
        polling_item.save()
        response = {
            'data': {
                'two_bar_codes': img
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class GetAllView(APIView):
    """
    获取报名选手总人数,总投票数
    https://api.yourpowersuck.com/polling-activities/:id/get_all/
    """

    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的投票活动
            polling_activity = PollingActivity.objects.get(id=id)
        except PollingActivity.DoesNotExist:
            raise exceptions.NoSuchResource
        # 统计报名成功的总人数和投票总数
        rows = PollingItem.objects.filter(polling_activity=polling_activity, is_successful=True).values('name', 'votes')
        person_count = 0
        vote_count = 0
        for row in rows:
            person_count += 1
            vote_count += row.get('votes', 0)

        response = {
            'data': {
                'person_count': person_count,
                'vote_count': vote_count
            },
            'code': 0,
            'error': '',
        }
        return Response(response)
