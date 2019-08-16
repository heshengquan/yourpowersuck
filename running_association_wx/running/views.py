from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.paginators import RacesCursorPagination
from utils.permissions import IsAuthorizedByMobile
from . import serializers
from .models import Race


class RacesView(ListAPIView):
    """
        赛事列表【用户】
        https://api.yourpowersuck.com/races/
    """
    authentication_classes = (MemberAuthentication,)

    serializer_class = serializers.RacesSerializer
    pagination_class = RacesCursorPagination

    def get_queryset(self):
        races = Race.objects.all()
        return races


class RaceView(APIView):
    """
        某赛事的信息【用户】
        https://api.yourpowersuck.com/races/:id/
    """
    authentication_classes = (MemberAuthentication,)

    def get(self, request, id):
        try:
            # 尝试获取当前id对应的赛事
            race = Race.objects.get(id=id)
        except Race.DoesNotExist:
            # 赛事不存在
            raise exceptions.NoSuchResource
        context = {'member': request.user}
        serializer = serializers.RaceSerializer(race, context=context)
        response = {
            'data': serializer.data,
            'code': 0,
            'error': '',
        }
        return Response(response)


class FollowRaceView(APIView):
    """
        关注赛事【跑者】
        https://api.yourpowersuck.com/races/:id/follow/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的赛事
            race = Race.objects.get(id=id)
        except Race.DoesNotExist:
            # 赛事不存在
            raise exceptions.NoSuchResource
        race.followers.add(request.user)
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)


class UnfollowRaceView(APIView):
    """
        取消关注赛事【跑者，且已关注此赛事】
        https://api.yourpowersuck.com/races/:id/unfollow/
    """
    authentication_classes = (MemberAuthentication,)
    permission_classes = (IsAuthorizedByMobile,)

    def post(self, request, id):
        try:
            # 尝试获取当前id对应的赛事
            race = Race.objects.get(id=id)
        except Race.DoesNotExist:
            # 赛事不存在
            raise exceptions.NoSuchResource
        if not race.followers.filter(id=request.user.id).exists():
            # 如果当前用户没有关注此赛事则请求失败
            raise exceptions.RequestFailed
        race.followers.remove(request.user)
        response = {
            'code': 0,
            'error': '',
        }
        return Response(response)
