import json
import os
import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import exceptions
from utils.authentications import MemberAuthentication
from utils.global_tools import uuid_str
from utils.throttles import WXAndMobileThrottle

import time
import datetime

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from utils import config


class GenerateQRCodeView(APIView):
    """
        生成分享二维码【用户】
        https://api.yourpowersuck.com/share/generate-QRcode/
    """
    authentication_classes = (MemberAuthentication,)
    throttle_classes = (WXAndMobileThrottle,)

    def throttled(self, request, wait):
        return exceptions.TooManyRequests

    def post(self, request):
        """
            发送微信生成小程序二维码B接口所需的参数以获取生成的二维码图片名称
        """
        try:
            # 尝试获取生成参数
            scene = request.data['scene']
            page = request.data['page']
            width = request.data.get('width', 430)
            auto_color = request.data.get('auto_color', False)
            line_color = request.data.get('line_color', {"r": 0, "g": 0, "b": 0})
            is_hyaline = request.data.get('is_hyaline', False)
        except:
            # 参数错误
            raise exceptions.ArgumentError
        access_token = get_access_token()
        QRcode_url = 'https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={}'.format(access_token)
        raw_data = {
            'scene': scene,
            'page': page,
            'width': width,
            'auto_color': auto_color,
            'line_color': line_color,
            'is_hyaline': is_hyaline,
        }
        data = json.dumps(raw_data)
        QRcode_request = requests.post(QRcode_url, data=data)
        img_name = uuid_str()
        img = os.path.join(settings.MEDIA_ROOT, 'share', img_name + '.png')
        with open(img, 'wb') as f:
            f.write(QRcode_request.content)
        response = {
            'data': {
                'image_name': img_name + '.png',
            },
            'code': 0,
            'error': '',
        }
        return Response(response)



# (此函数只在正式服务器上使用）此函数得到access_token。读取文件,若access_token已失效，则重新获取并写入文件
def get_access_token():

    def write_token():
        token_url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}".format(config.WEIXIN_APP_ID, config.WEIXIN_APP_SECRET)
        r = requests.get(token_url)
        access_token = r.json().get('access_token')
        expires_in = int(r.json().get('expires_in'))
        end_time = int(time.time()) + expires_in -300
        with open('access_token.txt','wt') as f:
            f.write(str(end_time))
            f.write('\n')
            f.write(access_token)
        return access_token

    f = open('access_token.txt','rt').readlines()
    if len(f) < 2:
        access_token = write_token()
        return access_token
    else:
        if int(time.time()) >= int(f[0]):
            access_token = write_token()
            return access_token
        else:
            return f[1]


# # （此函数只在测试服务器上使用）访问生产服务器，获取加密后的access_token,解密后返回
# def get_access_token2():
#     token_url = "https://api.yourpowersuck.com/wx/access-token/"
#     data = {'password':'Ien6Hvq9GXkXCkeiDJxryesGS7Tievcx'}
#     r = requests.post(token_url,data=data)
#     access_token_aes = r.json()
#     pc = PrpCrypt('JEwKENYmRMSEYbn87Do5qQNagVxGJshl')
#     access_token = pc.decrypt(access_token_aes)
#     return access_token


class PrpCrypt(object):

    def __init__(self, key):
        self.key = key.encode('utf-8')
        self.mode = AES.MODE_CBC

    # 加密函数，如果text不足16位就用空格补足为16位，
    # 如果大于16当时不是16的倍数，那就补足为16的倍数。
    def encrypt(self, text):
        text = text.encode('utf-8')
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        # 这里密钥key 长度必须为16（AES-128）,
        # 24（AES-192）,或者32 （AES-256）Bytes 长度
        # 目前AES-128 足够目前使用
        length = 32
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        elif count > length:
            add = (length - (count % length))
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        self.ciphertext = cryptor.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串
        return b2a_hex(self.ciphertext)

    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'0000000000000000')
        plain_text = cryptor.decrypt(a2b_hex(text))
        # return plain_text.rstrip('\0')
        return bytes.decode(plain_text).rstrip('\0')
