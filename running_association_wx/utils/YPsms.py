import urllib.parse

from django.conf import settings
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.ypclient import YunpianClient


def send_verification_code(verification_code, mobile):
    """
        发送短信验证码
    """
    client = YunpianClient(apikey=settings.YP_APIKEY)
    tpl_value = urllib.parse.urlencode({'#code#': verification_code})
    param = {YC.MOBILE: mobile, YC.TPL_ID: settings.YP_TPL_ID, YC.TPL_VALUE: tpl_value}
    r = client.sms().tpl_single_send(param)
    assert r.code() == 0
