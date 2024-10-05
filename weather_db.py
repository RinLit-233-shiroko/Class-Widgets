import datetime
import sqlite3
import json

weather_status = json.load(open('config/data/xiaomi_weather_status.json'))
path = 'config/data/xiaomi_weather.db'
def search_by_name(search_term):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM citys WHERE name LIKE ?', ('%' + search_term + '%',))  # 模糊查询
    citys_results = cursor.fetchall()
    conn.close()
    result_list = []
    for city in citys_results:
        result_list.append(city[2])
    # 返回两个表的搜索结果
    return result_list


def search_code_by_name(search_term):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM citys WHERE name LIKE ?', ('%' + search_term + '%',))  # 模糊查询
    citys_results = cursor.fetchall()
    conn.close()
    result = citys_results[0][3]
    # 返回两个表的搜索结果
    return result


def search_by_num(search_term):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM citys WHERE city_num LIKE ?', ('%' + search_term + '%',))  # 模糊查询
    citys_results = cursor.fetchall()

    conn.close()

    result = citys_results[0][2]
    # 返回两个表的搜索结果
    return result


def get_weather_by_code(code):
    for weather in weather_status['weatherinfo']:
        if weather['code'] == code:
            return weather['wea']
    return '未知'


def get_weather_icon_by_code(code):
    current_time = datetime.datetime.now()
    if code in ('0', '1', '3'):
        if current_time.hour < 6 or current_time.hour >= 18:  # 如果是夜间
            return f'img/weather/{code}d.svg'
    return f'img/weather/{code}.svg'


def get_weather_stylesheet(code):  # 天气样式
    current_time = datetime.datetime.now()
    if code in ('0', '1', '3'):
        if 6 <= current_time.hour < 18:  # 如果是日间
            return 'spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(40, 60, 110, 255), stop:1 rgba(75, 175, 245, 255)'
    return 'spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(20, 60, 90, 255), stop:1 rgba(10, 20, 29, 255)'


if __name__ == '__main__':
    # 测试代码
    num_results = search_by_num('101310101')  # [2]城市名称
    print(num_results)
    citys_results = search_by_name('上海')  # [3]城市代码
    print(citys_results)
    citys_results = search_code_by_name('上海')  # [3]城市代码
    print(citys_results)
    get_weather_by_code(3)
