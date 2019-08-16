import time
from bs4 import BeautifulSoup
import requests
from utils import ips_db

url = 'http://www.89ip.cn/index_{}.html'
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'www.89ip.cn',
    'Referer': 'http://www.89ip.cn/index_1.html',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
}


def get_ip_list():
    ip_list = []

    for page in range(1, 5):
        web_data = requests.get(url.format(str(page)), headers=headers)
        soup = BeautifulSoup(web_data.text, 'lxml')
        ips = soup.find_all('tr')

        for i in range(1, len(ips)):
            ip_info = ips[i]
            tds = ip_info.find_all('td')
            ip = tds[0].text.strip()
            port = tds[1].text.strip()
            ip_list.append(ip + ':' + port)
        time.sleep(5)
        print(ip_list)
    return ip_list


def inspect_ip(ip_list):
    check_url = 'http://123.207.56.226'
    for ipprot in ip_list:
        proxies = {
            'https': 'https://' + ipprot,
            'http': 'http://' + ipprot
        }
        try:
            request = requests.get(check_url, headers=headers, proxies=proxies, timeout=3)
        except:
            continue

        if request.status_code == 200:
            print(ipprot)
            ips_db.add_ip(ipprot)
            print('success')
            request.close()
        else:
            print('fail')
            continue


if __name__ == '__main__':
    ip_list = get_ip_list()
    inspect_ip(ip_list)
