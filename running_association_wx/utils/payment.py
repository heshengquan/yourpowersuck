import random
import datetime
from utils import config
import requests
import hashlib
import string
import xmltodict

import xml.etree.ElementTree as ET

def getNonceStr():
    """
        生成随机字符串
    """
    data = "123456789zxcvbnmasdfghjklqwertyuiopZXCVBNMASDFGHJKLQWERTYUIOP"
    nonce_str = ''.join(random.sample(data, 30))
    return nonce_str


def paysign(body, nonce_str,notify_url, openid, out_trade_no, spbill_create_ip, total_fee):
    """
        生成签名的函数
    """
    ret = {
        # 小程序ID
        "appid": config.WEIXIN_APP_ID,
        # 商品描述
        "body": body,
        # 商户号
        "mch_id": config.WEIXIN_MCH_ID,
        # 随机字符串
        "nonce_str": nonce_str,
        # 通知地址   异步接收微信支付结果通知的回调地址，通知url必须为外网可访问的url，不能携带参数。
        "notify_url": notify_url,
        # 用户标识
        "openid": openid,
        # 商户订单号   商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*且在同一个商户号下唯一。
        "out_trade_no": out_trade_no,
        # 终端IP   APP和网页支付提交用户端ip
        "spbill_create_ip": spbill_create_ip,
        # 订单总金额，单位为分
        "total_fee": total_fee,
        # 交易类型   小程序取值为JSAPI
        "trade_type": 'JSAPI'
    }

    # 处理函数，对参数按照key=value的格式，并按照参数名ASCII字典序排序
    stringA = '&'.join(["{0}={1}".format(k, ret.get(k)) for k in sorted(ret)])
    stringSignTemp = '{0}&key={1}'.format(stringA, config.WEIXIN_MCH_KEY)
    sign = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest()
    return sign.upper()


def getWxPayOrdrID():
    """
        生成商品订单号
    """
    date = datetime.datetime.now()
    # 根据当前系统时间来生成商品订单号。时间精确到微秒
    payOrdrID = date.strftime("%Y%m%d%H%M%S%f")
    return payOrdrID


def get_bodyData(body, notify_url, openid, client_ip, price):
    """
        获取全部参数信息，封装成xml
    """
    body = body  # 商品描述
    notify_url = notify_url # 支付成功的回调地址  可访问 不带参数
    nonce_str = getNonceStr()  # 随机字符串
    out_trade_no = getWxPayOrdrID()  # 商户订单号
    total_fee = str(price)  # 订单价格 单位是 分

    # 获取签名
    sign = paysign(body, nonce_str,notify_url, openid, out_trade_no, client_ip, total_fee)

    bodyData = '<xml>'
    bodyData += '<appid>' + config.WEIXIN_APP_ID + '</appid>'  # 小程序ID
    bodyData += '<body>' + body + '</body>'  # 商品描述
    bodyData += '<mch_id>' + config.WEIXIN_MCH_ID + '</mch_id>'  # 商户号
    bodyData += '<nonce_str>' + nonce_str + '</nonce_str>'  # 随机字符串
    bodyData += '<notify_url>' + notify_url + '</notify_url>'  # 支付成功的回调地址
    bodyData += '<openid>' + openid + '</openid>'  # 用户标识
    bodyData += '<out_trade_no>' + out_trade_no + '</out_trade_no>'  # 商户订单号
    bodyData += '<spbill_create_ip>' + client_ip + '</spbill_create_ip>'  # 客户端终端IP
    bodyData += '<total_fee>' + total_fee + '</total_fee>'  # 总金额 单位为分
    bodyData += '<trade_type>JSAPI</trade_type>'  # 交易类型 小程序取值如下：JSAPI
    bodyData += '<sign>' + sign + '</sign>'
    bodyData += '</xml>'
    with open('testcontent.txt', 'wt') as f:
        f.write('nonce_str:'+nonce_str+'\n')
        f.write('sign:'+sign+'\n')

    return bodyData,nonce_str,out_trade_no


def xml_to_dict(xml_data):
    """
        将xml数据转为字典
    """
    xml_dict = {}
    root = ET.fromstring(xml_data)
    for child in root:
        xml_dict[child.tag] = child.text
    return xml_dict


def dict_to_xml(dict_data):
    """
        将字典数据转为xml
    """
    xml = ["<xml>"]
    for k, v in dict_data.iteritems():
        xml.append("<{0}>{1}</{0}>".format(k, v))
    xml.append("</xml>")
    return "".join(xml)


# 获取返回给小程序的paySign
def get_paysign(prepay_id, timeStamp, nonceStr):
    pay_data = {
        'appId': config.WEIXIN_APP_ID,
        'nonceStr': nonceStr,
        'package': "prepay_id=" + prepay_id,
        'signType': 'MD5',
        'timeStamp': timeStamp
    }
    stringA = '&'.join(["{0}={1}".format(k, pay_data.get(k)) for k in sorted(pay_data)])
    stringSignTemp = '{0}&key={1}'.format(stringA, config.WEIXIN_MCH_KEY)
    sign = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest()
    return sign.upper()



# 以下是企业付款相关的函数
# 生成签名
def generate_sign(param):
    stringA = ''

    ks = sorted(param.keys())
    # 参数排序
    for k in ks:
        stringA += (k + '=' + param[k] + '&')
    # 拼接商户KEY
    stringSignTemp = stringA + "key=" + config.WEIXIN_MCH_KEY

    # md5加密
    hash_md5 = hashlib.md5(stringSignTemp.encode('utf8'))
    sign = hash_md5.hexdigest().upper()

    return sign


# 发送携带证书的xml请求
def send_cert_request(url, param):
    # dict 2 xml
    param = {'root': param}
    xml = xmltodict.unparse(param)

    response = requests.post(url, data=xml.encode('utf-8'),
                             headers={'Content-Type': 'text/xml'},
                             cert=(config.WEIXIN_MCH_CERT_FILE,config.WEIXIN_MCH_KEY_FILE))
    # xml 2 dict
    msg = response.text
    xmlmsg = xmltodict.parse(msg)

    return xmlmsg


# 企业付款
def WithDraw(openid, withdraw_value, description):
    url = "https://api.mch.weixin.qq.com/mmpaymkttransfers/promotion/transfers"
    out_trade_no = getWxPayOrdrID()
    param = {
        "mch_appid": config.WEIXIN_APP_ID,
        "mchid": config.WEIXIN_MCH_ID,  # 商户号
        "nonce_str": getNonceStr(),  # 随机字符串
        "partner_trade_no": out_trade_no,
        "openid": openid,  # 获取openid见obtain_openid_demo.py
        "check_name": "NO_CHECK",
        "amount": withdraw_value,  # 提现金额，单位为分
        "desc": description,  # 提现说明
        "spbill_create_ip": "47.105.166.254",  # 发起提现的ip
    }

    sign = generate_sign(param)
    param["sign"] = sign
    # 携带证书
    xmlmsg = send_cert_request(url, param)
    print(xmlmsg)
    return xmlmsg

if __name__ == '__main__':
    WithDraw('oyWo65MlzdcjGpcn4IoqPfMWbJb0','100', '企业付款测试')

