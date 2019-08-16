from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class MarathonsCursorPagination(CursorPagination):
    """
        马拉松成绩分页器
    """
    page_size = 4
    ordering = '-date'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'marathons': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class MarathonsRankingCursorPagination(CursorPagination):
    """
        用户马拉松排名分页器
    """
    page_size = 10
    ordering = 'chip_time'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'ranking': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)