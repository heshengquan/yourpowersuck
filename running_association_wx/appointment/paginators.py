from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class ParticipationRecordsCursorPagination(CursorPagination):
    """
        活动的参与记录分页器
    """
    page_size = 10
    ordering = 'in_time'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'members': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class CompletedActivityImagesCursorPagination(CursorPagination):
    """
        活动完成后上传的图片分页器
    """
    page_size = 9
    ordering = 'time'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'images': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)