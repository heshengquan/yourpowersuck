from rest_framework.authentication import BaseAuthentication

from me.models import Member
from utils.exceptions import AuthenticationFailed
from utils.global_tools import md5


class MemberAuthentication(BaseAuthentication):
    """
        用户认证(除去微信登录,所有内容都必须通过认证)
        根据header的Authorization是否为有效token来判断是用户请求还是匿名请求
        对所有未通过认证的请求返回AuthenticationFailed
    """

    def authenticate(self, request):
        try:
            token = request.META['HTTP_AUTHORIZATION']
            raw_token, member_id = token.split('.')
            member = Member.objects.get(id=member_id)
            assert member.token_hash == md5(token + member.salt)
            # todo:以后版本可以设置一个半年强制认证的机制
            return member, token
        except:
            raise AuthenticationFailed
