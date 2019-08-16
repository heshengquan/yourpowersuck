import os
import pickle

import re

import datetime,time
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from me.models import Member, CityCode
from running.models import Race
from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.global_tools import uuid_str, calc
from utils.modify_database import ModifyOneData
from . import paginators
from utils.spider import get_captcha, get_grade
from utils.throttles import MarathonQueryThrottle
from . import serializers
from .models import Marathon, MarathonQueryRecord, MarathonData


class MarathonQueryView(APIView):
    """
        马拉松成绩查询【用户】
        https://api.yourpowersuck.com/marathons/query/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (MarathonQueryThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def get(self, request):
        """
            获取验证码和cookie
        """
        try:
            # 尝试爬取cookie与验证码图片
            token, captcha_img, cookie= get_captcha()
            assert isinstance(captcha_img, bytes)
            captcha_img = ContentFile(captcha_img)
            query_id = uuid_str()
        except:
            raise exceptions.RequestFailed
        # 新建查询记录并且保存图片
        record = MarathonQueryRecord.objects.create(id=query_id, member=request.user)
        record.captcha_img.save(name=record.id + '.jpg', content=captcha_img, save=True)
        # 读取当前用户原来存储的证件号和真实姓名
        member_profile = request.user.member_profile
        id_num = member_profile.marathon_id_num
        real_name = member_profile.real_name
        response = {
            'data': {
                'token':token,
                'cookie':cookie,
                'captcha_name': query_id,
                'id_num': id_num,
                'real_name': real_name,
                # 'hiddenName': hiddenName,
                # 'hiddenValue': hiddenValue
            },
            'code': 0,
            'error': '',
        }
        return Response(response)

    def post(self, request):
        """
            发送证件号和真实姓名以及验证码内容以获取马拉松成绩
        """
        try:
            # 尝试获取证件号和真实姓名以及两个操作数和运算符并计算结果
            id_num = request.data['id_num']
            real_name = request.data['real_name']
            answer = request.data['result']
            cookie = request.data['cookie']
            token = request.data['token']
            # hiddenName = request.data['hiddenName']
            # hiddenValue = request.data['hiddenValue']
        except:
            raise exceptions.ArgumentError
        member = request.user
        # try:
        # 尝试获取当前用户最近一次查询记录并爬取马拉松成绩
        record = MarathonQueryRecord.objects.filter(member=member).latest('query_time')
        races = get_grade(id_num=id_num, real_name=real_name, captcha_code=answer,
                          token=token,cookie=cookie)
        # except:
        #     raise exceptions.RequestFailed
        if len(races) == 0:
            # 如果没有马拉松成绩
            raise exceptions.NoMarathonGrade
        if Marathon.objects.filter(member=member, **races[0]).exists():
            # 如果爬取的第一条数据(最新的数据)已经存在于数据库中，说明成绩未更新
            raise exceptions.MarathonGradeDoesNotUpdate
        try:
            # 删除当前用户原有所有记录更新为最新爬取的结果
            Marathon.objects.filter(member=member).delete()
            # 获取该选手的性别
            sex = int(id_num[16]) % 2
            Marathon.objects.bulk_create((Marathon(member=member, sex=sex, **race) for race in races))
            # 为每一条记录计算当时的年龄,并计算出年龄组的pb
            for marathon in Marathon.objects.filter(member=member):
                if len(id_num) >= 18:
                    birthday = id_num[6:14]
                    race_date = marathon.date
                    marathon.age = CountAgeGroup(birthday, race_date)
                    marathon.save()
                else:
                    marathon.age = 0
                    marathon.save()
            # 删除马拉松数据表里该用户之前的所有记录
            MarathonData.objects.filter(id_num=id_num).delete()
            MarathonData.objects.bulk_create\
                ((MarathonData(real_name=real_name, id_num=id_num, sex=sex, **race) for race in races))
            # 计算每个年龄组的pb，并确保10公里，半程，全程三个项目一定有pb
            ModifyOneData(member,member.id)
            # 更新查询记录的内容
            record.success = True
            new_img_name = record.id + ' ' + str(answer) + '.jpg'
            record.captcha_img.name = '/captcha/' + new_img_name  # 更新ImageField的路径
            # 最后记得save一下
            record.save(update_fields=('success', 'captcha_img'))
            # 把当前用户失败的查询记录删除
            MarathonQueryRecord.objects.filter(member=member, success=False).delete()
            # 存储用户的证件号和真实姓名
            member_profile = member.member_profile
            member_profile.marathon_id_num = id_num
            member_profile.real_name = real_name
            member_profile.save(update_fields=('marathon_id_num', 'real_name'))
        except:
            raise exceptions.RequestFailed
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class MarathonsPersonalBestDisplayView(APIView):
    """
        某成员的马拉松PB成绩展示【用户】
        https://api.yourpowersuck.com/marathons/display/:id/personal-best/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=id)
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource
        try:
            # 尝试获取半程PB
            half_pb_chip_time = member.marathons.get(is_pb=True, project='半程').chip_time
        except Marathon.DoesNotExist:
            half_pb_chip_time = ''
        try:
            # 尝试获取全程PB
            full_pb_chip_time = member.marathons.get(is_pb=True, project='全程').chip_time
        except Marathon.DoesNotExist:
            full_pb_chip_time = ''
        response = {
            'data': {
                'half_pb_chip_time': half_pb_chip_time,
                'full_pb_chip_time': full_pb_chip_time,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class MarathonsDisplayView(ListAPIView):
    """
        某成员的马拉松成绩展示【用户】
        https://api.yourpowersuck.com/marathons/display/:id/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.MarathonSerializer
    pagination_class = paginators.MarathonsCursorPagination

    def get_queryset(self):
        try:
            # 尝试获取当前id对应的成员
            member = Member.objects.get(id=self.kwargs['id'])
        except Member.DoesNotExist:
            # 成员不存在
            raise exceptions.NoSuchResource
        return member.marathons


class MarathonRankingView(ListAPIView):
    """
        马拉松排行榜————根据不同参数获取不同的马拉松排行榜
        https://api.yourpowersuck.com/marathons/ranking
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.MarathonRankingSerializer
    pagination_class = paginators.MarathonsRankingCursorPagination

    def get_queryset(self):
        # 获取查询参数
        try:
            city = self.request.query_params['city']
            sex = self.request.query_params['sex']
            project = self.request.query_params['project']
            age = self.request.query_params['age']
        except:
            raise exceptions.ArgumentError
        if age != '':
            query_set = Marathon.objects.filter(age_pb=True,age=int(age))
        else:
            query_set = Marathon.objects.filter(is_pb=True)
        if city != '':
            if len(city) == 2:
                city_code = city + '0100'
                province = CityCode.objects.get(city_id=city_code).province
                query_set = query_set.filter(member__member_profile__marathon_city__province=province)
            else:
                city_code = city[0:4] + '00'
                query_set = query_set.filter(member__member_profile__marathon_city__city_id=city_code)
        if sex != '':
            query_set = query_set.filter(sex=int(sex))
        return query_set.filter(project=project)


class MyMarathonRankingView(APIView):
    """
        马拉松个人排名————根据不同参数获取不同的马拉松排名
        https://api.yourpowersuck.com/marathons/my-ranking/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self,request):
        # 获取查询参数
        try:
            member_id = request.data['member']
            project = request.data['project']
            age = request.data['age']
            city = request.data['city']
            sex = request.data['sex']
        except:
            raise exceptions.ArgumentError
        try:
            member = Member.objects.get(id=member_id)
        except:
            raise exceptions.NoSuchResource
        id_card = 1
        if not Marathon.objects.filter(member=member):
            raise exceptions.NoMarathonGrade
        if len(member.member_profile.marathon_id_num) <= 18:
            id_card = 0
        my_pb = Marathon.objects.filter(member=member, project=project, is_pb=True)
        if not my_pb:
            response = {
                'data': {
                    'chip_time': '',
                    'ranking':'',
                    'id_card': id_card,
                    'name': member.member_profile.real_name,
                    'avatar': member.avatar_url,
                },
                'code': 0,
                'error': ''
            }
            return Response(response)
        else:
            my_pb_chip_time = my_pb[0].chip_time
        if age != '':
            if id_card:
                my_age_pb = Marathon.objects.filter(member=member, age=int(age), age_pb=True, project=project)
                if my_age_pb:
                    my_pb_chip_time = my_age_pb[0].chip_time
                    query_set = Marathon.objects.filter(age_pb=True, age=int(age), project=project)
                else:
                    response = {
                        'data': {
                            'chip_time': '',
                            'ranking': '',
                            'id_card': id_card,
                            'name': member.member_profile.real_name,
                            'avatar': member.avatar_url,
                        },
                        'code': 0,
                        'error': ''
                    }
                    return Response(response)
            else:
                query_set = Marathon.objects.filter(is_pb=True, project=project)
        else:
            query_set = Marathon.objects.filter(is_pb=True, project=project)
        if city != '':
            if len(city) == 2:
                city_code = city + '0100'
                province = CityCode.objects.get(city_id=city_code).province
                query_set = query_set.filter(member__member_profile__marathon_city__province=province)
            else:
                city_code = city[0:4] + '00'
                query_set = query_set.filter(member__member_profile__marathon_city__city_id=city_code)
        if sex != '':
            query_set = query_set.filter(sex=int(sex))
        my_ranking = query_set.filter(chip_time__lt = my_pb_chip_time).count() + 1
        response = {
            'data': {
                'chip_time': my_pb_chip_time,
                'ranking': my_ranking,
                'id_card': id_card,
                'name': member.member_profile.real_name,
                'avatar': member.avatar_url,
                'id': member_id,
            },
            'code': 0,
            'error': ''
        }
        return Response(response)


class RecordMemberMarathonCity(APIView):
    """
        记录个人马拉松成绩属于哪个城市
        https://api.yourpowersuck.com/marathons/record-city/
    """
    authentication_classes = (MemberAuthentication,)

    def post(self,request):
        # 获取查询参数
        try:
            city_code = request.data['city']
        except:
            raise exceptions.ArgumentError
        city_code = city_code[0:4] + '00'
        try:
            city = CityCode.objects.get(city_id = city_code)
        except:
            raise exceptions.NoSuchResource
        member = request.user
        member.member_profile.marathon_city = city
        member.member_profile.save()
        response = {
            'code': 0,
            'error': ''
        }
        return Response(response)



# 初始化数据时执行
def RecordMarathon():
    for marathon_data in MarathonData.objects.all():
        if len(marathon_data.id_num) >= 18:
            sex_num = marathon_data.id_num[16]
            marathon_data.sex = int(sex_num) % 2
            marathon_data.save()
    for marathon in Marathon.objects.all():
        try:
            id_num = marathon.member.member_profile.marathon_id_num
            if len(id_num) >= 18:
                birthday = id_num[6:14]
                race_date = marathon.date
                marathon.age = CountAgeGroup(birthday, race_date)
                sex_num = id_num[16]
                marathon.sex = int(sex_num) % 2
                marathon.save()
            else:
                marathon.age = 0
                marathon.save()
        except:
            pass
    m = Marathon.objects.filter().values('member__id').annotate(Count('id'))
    for i in m:
        member_id = i['member__id']
        for pro in ['10公里', '半程', '全程']:
            sql = "SELECT id,min(chip_time),member_id,age_pb from marathon_spider_marathon WHERE project='{}' AND member_id='{}' GROUP BY age HAVING age_pb=0".format(pro, member_id)
            all_list = Marathon.objects.raw(sql)
            for j in all_list:
                marathon = Marathon.objects.get(id=j.id)
                marathon.age_pb = True
                marathon.save()

        member = Member.objects.get(id = member_id)
        id_num = member.member_profile.marathon_id_num
        if len(id_num) >= 18:
            city_code = id_num[0:4]
            city = CityCode.objects.filter(city_id__contains=city_code)
            if city:
                member.member_profile.marathon_city = city[0]
                member.member_profile.save()


# 计算某场比赛时的年龄组
def CountAgeGroup(birthday, race_date):
    birthday = datetime.datetime.strptime(birthday, '%Y%m%d')
    race_date = datetime.datetime.strptime(str(race_date),'%Y-%m-%d')
    birthday_stamp = time.mktime(time.strptime(birthday.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
    race_date_stamp = time.mktime(time.strptime(race_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
    interval = race_date_stamp - birthday_stamp
    if interval <= 915148800:
        return 1
    elif interval <= 1073001600:
        return 2
    elif interval <= 1230768000:
        return 3
    elif interval <= 1388534400:
        return 4
    elif interval <= 1546300800:
        return 5
    elif interval <= 1704067200:
        return 6
    elif interval <= 1861833600:
        return 7
    elif interval <= 2019686400:
        return 8
    else:
        return 9

