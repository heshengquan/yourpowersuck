from marathon_spider.models import Marathon
from me.models import MemberProfile


def ModifyAllData():
    """
        marathon_spider_marathon表中某些人的成绩没有pb,
        通过优化爬虫程序使新插入的数据都有pb,对数据库中原有数据执行该函数，改变is_pb字段值
        也可使用sql语句直接操作数据库更为简便
    """
    for pro in ['10公里','半程','全程']:
        sql = "SELECT id,min(chip_time),member_id,is_pb from marathon_spider_marathon WHERE project='{}' GROUP BY member_id HAVING is_pb=0".format(pro)
        all_list = Marathon.objects.raw(sql)
        if all_list:
            for i in all_list:
                marathon = Marathon.objects.get(id=i.id)
                marathon.is_pb = True
                marathon.save()


def ModifyOneData(member,member_id):
    """
        爬虫操作一次数据库后执行该函数，分别检测这三个项目
        为用时最短的一次设置is_pb=True
    """
    for pro in ['10公里','半程','全程']:
        all_list = Marathon.objects.filter(member=member,project=pro).order_by('chip_time')
        if all_list:
            min_time = all_list[0]
            min_time.is_pb = True
            min_time.save(update_fields=('is_pb',))

    for pro in ['10公里', '半程', '全程']:
        sql = "SELECT id,min(chip_time),member_id from marathon_spider_marathon WHERE project='{}' AND member_id='{}' GROUP BY age HAVING age_pb=0".format(
            pro,member_id)
        all_list = Marathon.objects.raw(sql)
        if all_list:
            for i in all_list:
                marathon = Marathon.objects.get(id=i.id)
                marathon.age_pb = True
                marathon.save()
