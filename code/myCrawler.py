import json
import time
import requests
import csv
import datetime
from datetime import timedelta

# ============ csv文件的配置 ============
# 列名
columns = ['id', '食堂名称', '食堂人数', '食堂座位数', '记录时间']
# 文件名
csv_file_name = 'other/Number_of_diners.csv'
# ============ csv文件的配置 ============

# 吃饭的小时
time_to_eat = set([6, 7, 8, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21])

# 两次相邻读取间隔秒数
interval_seconds = 60

# 连续读取天数
duration_of_days = 14

# 打开csv文件，并写入表头
csv_file = open(csv_file_name, 'w', newline='')
my_writer = csv.writer(csv_file)
my_writer.writerow(columns)

# 自增id
running_id = 0

# 这个函数将进行一次数据的读取操作
def fetch_once():

    global running_id

    # 我们发现校内门户中的数据被放到了canvas元素中，这导致selenium将并不好爬取数据，因此我们从浏览器中获取了校内门户加载canvas元素时所发出的请求，直接使用这个url进行post以获取数据
    url = "https://portal.pku.edu.cn/portal2017/publicsearch/canteen/retrCarteenInfos.do"
    response = requests.post(url)

    # 把返回值做成json
    response_json = json.loads(response.text)

    # 所有数据共用的时间
    cur_time = response_json['time']

    # 对json的每一项，提取一行所需的每一项数据放到csv文件中
    for x in response_json['rows']:
        cur_id = running_id
        running_id += 1
        cur_name = x['name']
        cur_ip = x['ip']
        cur_seat = x['seat']
        my_writer.writerow([cur_id, cur_name, cur_ip, cur_seat, cur_time])

# 计算到吃饭时间需要的秒数
def cal_sleep_duration():
    
    # 当前时间
    now = datetime.datetime.now()

    # 计算下一次吃饭的时间
    def cal_next_mealtime():
        if now.hour < 6:
            # 下一个6点
            return datetime.datetime(now.year, now.month, now.day, 6, 0, 0, 0)
        elif now.hour < 10:
            # 下一个10点
            return datetime.datetime(now.year, now.month, now.day, 10, 0, 0, 0)
        elif now.hour < 16:
            # 下一个16点
            return datetime.datetime(now.year, now.month, now.day, 16, 0, 0, 0)
        else:
            # 下一个6点
            return datetime.datetime(now.year, now.month, now.day + 1, 6, 0, 0, 0)
    
    # 返回到下一次吃饭时间需要的秒数
    sec = (cal_next_mealtime() - now).total_seconds()
    print("Not mealtime. Gonna sleep for %d seconds" % sec)
    return sec

# 这个函数在从今日起14天内，每隔1min读一次数据
def work():
    # 起始日期和终结日期
    start_time = datetime.datetime.now()
    # end_time = start_time + timedelta(seconds=10)
    end_time = start_time + timedelta(days=duration_of_days)

    # 被记录过的时间，用来每小时输出数据
    visited_hour_set = set()

    # 在从今日起14天内运行
    while datetime.datetime.now() < end_time:
        now = datetime.datetime.now()
        cur_hour_str = now.strftime("%Y-%m-%d %H")
        # 新的一个小时，输出一条输出
        if cur_hour_str not in visited_hour_set:
            visited_hour_set.add(cur_hour_str)
            print("%s: Fetched %d pieces of data" % (cur_hour_str, running_id))
        # 查询当前小时是否是吃饭时间，若不是，则睡眠到开饭
        if now.hour not in time_to_eat:
            time.sleep(cal_sleep_duration())
            continue
        # 开饭时间，每隔1分钟统计一次数据
        fetch_once()
        time.sleep(interval_seconds)

work()
csv_file.close()