import pickle

import requests
import re
# from . import global_tools
from bs4 import BeautifulSoup
# from . import exceptions
import pytesseract
from PIL import Image
import random
from utils import ips_db

ip_list = ips_db.get_ip(10)


def get_cookies():
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Host': 'www.runchina.org.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Referer': 'http://www.runchina.org.cn/portal.php?mod=score&ac=personal'
    }
    # get方式访问该网站，获取所有的cookie
    grade_url = 'http://www.runchina.org.cn/portal.php?mod=score&ac=personal'
    proxies = {
        'https': 'https://' + '106.52.93.102:80',
        'http': 'http://' + '106.52.93.102:80'
    }
    # print(proxies)
    # r = requests.get('http://123.207.56.226:8000',  proxies=proxies)
    ipprot = ''
    for ip in ip_list:
        proxies = {
            'https': 'https://' + ip.decode(),
            'http': 'http://' + ip.decode()
        }
        try:
            print(proxies)
            r = requests.get(grade_url, headers=HEADERS, proxies=proxies, timeout=3)
        except:
            ips_db.rem_ip(ip)
            continue
        if r.status_code == 200:
            ipprot = ip
            break
        else:
            print(ip, 'fail')
            ips_db.rem_ip(ip)
            continue
    print(r)
    cookie = ''
    token = ''

    for i in r.cookies:
        if i.name == 'SMHa_2132_token':
            token = i.value
        cookie += str(i.name) + '=' + str(i.value) + '; '
    return cookie, token, ipprot


def get_captcha():
    """
        获取验证码
    """
    cookie, token, ip = get_cookies()
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Host': 'www.runchina.org.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }
    captcha_url = 'http://www.runchina.org.cn/template/default/public/js/securimage/securimage_show.php?0.8141818750195127'
    proxies = {
        'https': 'https://' + ip.decode(),
        'http': 'http://' + ip.decode()
    }
    # r = requests.get('http://123.207.56.226:8000',  proxies=proxies)

    r = requests.get(captcha_url, headers=HEADERS, proxies=proxies)
    captcha_img = r.content
    return token, captcha_img, cookie


def parse_html(html_content):
    """
        从html中解析比赛记录
    """
    HEADERS = {
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Host': 'www.runchina.org.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0'
    }
    races = []
    soup = BeautifulSoup(html_content, 'lxml')
    errorCode = re.search(r'验证码不正确!!', html_content)  # 判断是否验证码出错
    # with open('html_content01.txt', 'w+') as f:
    #     f.write(html_content)
    if errorCode:  # 如果验证码出错则抛出MarathonVerificationCodeError
        raise exceptions.MarathonVerificationCodeError
    table = soup.table
    # print(table)
    table.thead.extract()  # 移除thead元素
    trs = table.find_all('tr')
    # print(trs)
    for tr in trs:
        race = {}
        tds = tr.find_all('td')
        race['date'] = tds[0].string.strip()  # 比赛时间
        race['name'] = tds[1].a.string.strip()  # 比赛名称
        race['project'] = tds[2].string.strip()  # 项目
        # 注意这里面有可能包含代表PB的span元素，不能直接取string
        race['is_pb'] = True if tds[3].span else False  # 是否PB
        if race['is_pb']:
            chip_time = tds[3].get_text()  # 净计时
        else:
            chip_time = tds[3].string.strip()  # 净计时
        race['chip_time'] = chip_time
        races.append(race)
    return races


def get_grade(id_num, real_name, captcha_code, token, cookie):
    """
        获取比赛成绩
    """
    grade_url = 'http://www.runchina.org.cn/portal.php?mod=score&ac=personal'
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Host': 'www.runchina.org.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Referer': 'http://www.runchina.org.cn/portal.php?mod=score&ac=personal',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'name': real_name,
        'idnum': id_num,
        'captcha_code': captcha_code,
        'token': token,
    }
    ip = ips_db.get_ip(0)[0]
    proxies = {
        'https': 'https://' + ip.decode(),
        'http': 'http://' + ip.decode()
    }
    r = requests.post(grade_url, data=data, headers=HEADERS, proxies=proxies)
    return parse_html(r.text)


if __name__ == '__main__':
    # 现场爬取进行测试
    # pickled_cookie, captcha_img = get_captcha()
    # with open('captcha.jpg', 'wb') as f:
    #     f.write(captcha_img)
    # id_num = input('证件号：')
    # real_name = input('真实姓名：')
    # captcha_code = input('验证码：')
    # races = get_grade(id_num, real_name, captcha_code, pickled_cookie)
    # print(races)

    # 对已有文件进行测试
    # with open('test.html', 'rb') as f:
    #     html = f.read().decode()
    #     races = parse_html(html)
    #     print(races)
    # token, cookie,ip = get_cookies()
    token, captcha_img, cookie = get_captcha()
    print(token, 'token')
    print('_______________________________')
    print(captcha_img)
    print('+++++++++++++++++++++++++++++++')
    print(cookie, 'cookie')
