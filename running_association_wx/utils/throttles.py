from rest_framework.throttling import SimpleRateThrottle


class WXAndMobileThrottle(SimpleRateThrottle):
    """
        微信/手机短信相关接口访问阀门
        限制某ip一分钟内访问次数上限为5次
    """
    rate = '5/min'
    scope = 'wx'

    # get_cache_key() must be overridden
    # 此处我们只要把AnonRateThrottle里面的判断登录逻辑去掉即为我们想要的
    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }


class MarathonQueryThrottle(SimpleRateThrottle):
    """
        马拉松成绩查询接口访问阀门
        限制某用户一天内访问次数上限为20次
    """
    rate = '20/day'
    scope = 'marathon'

    # get_cache_key() must be overridden
    # 此处我们只要把UserRateThrottle里面的用户判断逻辑去掉即为我们想要的
    def get_cache_key(self, request, view):
        if request.user:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
