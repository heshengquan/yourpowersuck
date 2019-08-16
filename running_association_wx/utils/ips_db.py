# coding:utf-8
import redis

# r = redis.Redis(host='127.0.0.1', port=6379)  # host后的IP是需要连接的ip，本地是127.0.0.1或者localhost
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, password='Wangdapao0916')
r = redis.Redis(connection_pool=pool)  # 建立连接池避免每次连接释放消耗


# 主ip池
def add_ip(ip):
    r.lpush('Iplist', ip)


# ip数量
def len_ip():
    return r.llen('Iplist')


# 取出ip
def get_ip(num):
    i = r.lrange('Iplist', 0, num)
    return i


# 删除不可用ip
def rem_ip(ipprot):
    i = r.lrem('Iplist', 0, ipprot)
    return i


