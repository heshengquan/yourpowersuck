from rest_framework.status import HTTP_200_OK
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
        自定义错误处理函数
    """
    response = exception_handler(exc, context)  # 获取本来应该返回的exception的response
    if response is not None:
        response.status_code = HTTP_200_OK  # 不管什么情况下都返回200,为了防止阿里云的阉割与运营商劫持
        response.data['code'] = response.data['detail'].code  # 加上code，代表错误代码
        response.data['error'] = response.data['detail']  # 把默认的detail换成我们定义的api的error
        del response.data['detail']  # 删掉默认的detail
    return response
