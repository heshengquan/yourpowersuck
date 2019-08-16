import time
import requests
from appointment.models import Activity
from datetime import datetime, timedelta
from django.db.models import Count

from association.models import Branch
from me.models import MemberFormId
from poll.models import MemberPollingRecord, PollingItemCity, PollingItem
from utils.access_token import get_access_token


def CompleteActivityAuto():
    """
        活动结束后如果没有手动结束，则每天凌晨三点执行一次该函数，自动把活动状态变成‘已结束’
    """
    # 获取所有状态不是‘已完成’的活动
    activities_has_not_completed = Activity.objects.filter(does_exist=True).exclude(status='has_completed')
    # 活动结束时间与此时对比，若小于此刻，则将状态变成‘已完成’
    now = datetime.now()
    i = 0
    j = 0
    for activity in activities_has_not_completed:
        i += 1
        if activity.end <= now:
            activity.status = 'has_completed'
            activity.save(update_fields=('status',))
            j += 1
    print(i, 'activities in all,', j, 'activities complete')
# 为目前有formid的所有投过票的人发送投票提醒（每天九点）
def RemindPollingAuto():
    access_token = get_access_token()
    time_now = int(time.time())
    today = datetime.now().date()
    begin = today + timedelta(-7)
    end = today + timedelta(-1)
    # 筛选七天内投过票的所有人
    members = MemberPollingRecord.objects.filter(vote_date__range=(begin,end)).values('member').annotate(Count('id'))
    for member in members:
        id = member['member']
        # 获取其可用的formid
        formids = MemberFormId.objects.filter(is_available=True, timestamp__gt=time_now,member=id)
        if formids:
            formid = formids[0]
            data = {
                "touser": formid.member.openid,
                "template_id": 'M-zLsu0x08j9kAhbseMPC1UvUO0sXZaM9ocEqWUwKJo',
                "page": 'pages/pollList/main?pollId=95bfcff3bd6849c895d065550fbc07b8',
                "form_id": formid.formid,
                "data": {
                    'keyword1': {
                        'value': "第二届中国最美女跑者",
                    },
                    'keyword2': {
                        'value': '您今日的投票机会已更新，快来为喜欢的女跑者投上一票吧！',
                    },
                    'keyword3': {
                        'value': '您喜欢的选手就快被反超了，来看看她的排名吧！',
                    }
                },
            }
            formid.is_available = False
            formid.save()
            push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                access_token)
            requests.post(push_url, json=data, timeout=3)
            formid.is_available = False
            formid.save()


# 自动计算该城市有多少人报名成功（每30分钟执行一次）
def CountCityNumberAuto():
    for city in PollingItemCity.objects.filter(polling_activity='95bfcff3bd6849c895d065550fbc07b8'):
        city.number = PollingItem.objects.filter(polling_activity='95bfcff3bd6849c895d065550fbc07b8',
                                                 city=city, is_successful=True).count()
        city.save()


# 在前一天报名的人中抽出一位锦鲤，要求票数达到8票及以上，可指定id也可随机抽取
def LuckyDrawAuto():

    # 发送模板消息
    def SendMessage(msg,polling_items):
        access_token = get_access_token()
        time_now = int(time.time())
        today = datetime.now()
        year = today.strftime('%y')  #今天的年份
        month = today.strftime('%m')  # 今天的月份
        date = today.strftime('%d')  # 今天的日期

        for polling_item in polling_items:
            # 获取其可用的formid
            formids = MemberFormId.objects.filter(member=polling_item.member,
                                                  is_available=True, timestamp__gt=time_now)
            if formids:
                formid = formids[0]
                data = {
                    "touser": polling_item.member.openid,
                    "template_id": 'Ntuj-5GgDQZEVMEPp9eBmbqbANmO_s-M204zzjKzE2c',
                    "page": 'pages/luckyPerson/main',
                    "form_id": formid.formid,
                    "data": {
                        'keyword1': {
                            'value': msg,
                        },
                        'keyword2': {
                            'value': '抽奖啦！赶紧戳进来看看大奖名单',
                        },
                        'keyword3': {
                            'value': '武汉约跑社体育文化管理有限公司',
                        },
                        'keyword4': {
                            'value': '空顶帽+腰包+压缩腿套+髌骨带',
                        },
                        'keyword5': {
                            'value': '{}年{}月{}日'.format(year,month,date)
                        }
                    },
                }
                push_url = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={}'.format(
                    access_token)
                requests.post(push_url, json=data, timeout=3)
                formid.is_available = False
                formid.save()
            else:
                print(polling_item.id + '通知失败，没有可用的fromid\n')

    # 筛选昨天报名的,且票数超过8票的人
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    date = yesterday.strftime('%d') # 昨天的日期
    month = yesterday.strftime('%m') # 昨天的月份
    polling_items = PollingItem.objects.filter(pub_date__day=int(date),pub_date__month=int(month), votes__gte=8)

    msg1 = '您于昨日报名参加的“中国最美女跑者”活动已符合抽奖条件，祝您好运！'
    SendMessage(msg1,polling_items)
    # 昨天报名的人里面票数少于8票的，通知活动参与失败
    polling_items_lt8 = PollingItem.objects.filter(pub_date__day=int(date), pub_date__month=int(month), votes__lt=8)
    msg2 = '很遗憾，您于昨日报名参加的“中国最美女跑者”活动，由于没达到票数要求，未获得中奖资格'
    SendMessage(msg2,polling_items_lt8)


def SaveBranchAuto():
    # 每天凌晨四点重新计算分舵的人数，活动数目，影响力等
    branches = Branch.objects.get_existing_all()
    for branch in branches:
        branch.save()
