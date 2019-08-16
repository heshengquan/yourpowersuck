import datetime
import hashlib
import random
import uuid
import time
from PIL import Image

# 全局工具集

def uuid_str():
    """
        生成一个uuid字符串(32个十六进制字符)
    """
    return uuid.uuid4().hex


def md5(string: str):
    """
        计算string的md5
    """
    return hashlib.md5(string.encode('utf-8')).hexdigest()


def random_int_6():
    """
        随机生成一个6位的整数
    """
    return random.randint(100000, 999999)


def ten_minutes_from_now():
    """
        获取从当前起10分钟后的日期时间
    """
    return datetime.datetime.now() + datetime.timedelta(minutes=10)


def calc(operand1, operand2, operator):
    """
         计算算式，注意所有参数与返回值都是str
    """
    operand1 = int(operand1)
    operand2 = int(operand2)
    if operator == '+':
        return str(operand1 + operand2)
    elif operator == '-':
        return str(operand1 - operand2)
    elif operator == '*':
        return str(operand1 * operand2)
    elif operand1 == '/':
        return str(operand1 / operand2)
    else:
        raise Exception

# 压缩图片函数
def MakeThumb(path, size=128):  # 指定size，在这里表示图片的宽度
    img = Image.open(path)
    width, height = img.size

    if width > size:  # 如果宽度大于指定值，则进行尺寸压缩
        delta = width / size
        height = int(height / delta)
        img.thumbnail((width, height), Image.ANTIALIAS)
    return img

# 获取时间戳,秒级别
def timeStampSecond():
    return int(time.time())

# 获取时间戳,毫秒级别
def timeStampSecond():
    return int(round(time.time()*1000))