from rest_framework.permissions import BasePermission


class IsAuthorizedByMobile(BasePermission):
    """
        是否通过手机号授权(新建分舵/加入分舵/加入活动都需要此权限)
    """

    def has_permission(self, request, view):
        # return request.user.mobile != ''
        # 这个版本所有人都有权限
        return True

class IsOwner(BasePermission):
    """
        是否拥有者(访问私人信息需要此权限)
    """

    def has_permission(self, request, view):
        return view.kwargs.get('id') == request.user.id



