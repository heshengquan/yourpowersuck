import decimal

from rest_framework.pagination import CursorPagination, _reverse_ordering
from rest_framework.response import Response


class ActivitiesCursorPagination(CursorPagination):
    """
        活动分页器
    """
    page_size = 10
    ordering = '-build_up_time'

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


class MembersCursorPagination(CursorPagination):
    """
        成员分页器
    """
    page_size = 10
    ordering = ('-priority', 'last_login')

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


class BranchesCursorPagination(CursorPagination):
    """
        分舵分页器
    """
    page_size = 10
    ordering = 'distance'

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = queryset.order_by(*_reverse_ordering(self.ordering))
        else:
            queryset = queryset.order_by(*self.ordering)

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            value, unit = current_position.split()
            current_position = decimal.Decimal(value)
            order = self.ordering[0]
            is_reversed = order.startswith('-')
            order_attr = order.lstrip('-')

            # Test for: (cursor reversed) XOR (queryset reversed)
            if self.cursor.reverse != is_reversed:
                kwargs = {order_attr + '__lt': current_position}
            else:
                kwargs = {order_attr + '__gt': current_position}
            queryset = queryset.filter(**kwargs)

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset:offset + self.page_size + 1])
        self.page = list(results[:self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1], self.ordering)
        else:
            has_following_position = False
            following_position = None

        # If we have a reverse queryset, then the query ordering was in reverse
        # so we need to reverse the items again before returning them to the user.
        if reverse:
            self.page = list(reversed(self.page))

        if reverse:
            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'branches': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


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


class RacesCursorPagination(CursorPagination):
    """
        赛事分页器
    """
    page_size = 6
    ordering = '-start_date'

    def get_paginated_response(self, data):
        response = {
            'data': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'races': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)


class NearbyActivitesPagination(CursorPagination):
    """
        附近活动分页器
    """
    page_size = 5
    ordering = 'distance'

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = self.get_ordering(request, queryset, view)

        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = queryset.order_by(*_reverse_ordering(self.ordering))
        else:
            queryset = queryset.order_by(*self.ordering)

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            value, unit = current_position.split()
            current_position = decimal.Decimal(value)
            order = self.ordering[0]
            is_reversed = order.startswith('-')
            order_attr = order.lstrip('-')

            # Test for: (cursor reversed) XOR (queryset reversed)
            if self.cursor.reverse != is_reversed:
                kwargs = {order_attr + '__lt': current_position}
            else:
                kwargs = {order_attr + '__gt': current_position}
            queryset = queryset.filter(**kwargs)

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset:offset + self.page_size + 1])
        self.page = list(results[:self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1], self.ordering)
        else:
            has_following_position = False
            following_position = None

        # If we have a reverse queryset, then the query ordering was in reverse
        # so we need to reverse the items again before returning them to the user.
        if reverse:
            self.page = list(reversed(self.page))

        if reverse:
            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page

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


class MarathonsNationwideRankingCursorPagination(CursorPagination):
    """
        用户马拉松全国排名分页器
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


class ShowAllAddressPagination(CursorPagination):
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
                'address': data,
            },
            'code': 0,
            'error': '',
        }
        return Response(response)