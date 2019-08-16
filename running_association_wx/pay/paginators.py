from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class ShowAllAddressesPagination(CursorPagination):
    """
        某用户所有地址的分页器
    """
    page_size = 10
    ordering = ('-is_default','name')

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'addresses': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class MonthRaceMembersPagination(CursorPagination):
    """
        某月赛参与成员的分页器
    """
    page_size = 10
    ordering = '-pay_time'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'activities': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)