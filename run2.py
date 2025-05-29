# ==== 配置区域 ====
cinema_ids = ["25552", "24311"]  # 影院代号列表
keywords = ["杜比影院厅（儿童需购票）"]  # 影院厅名称包含这些关键词的才会被筛选
ics_filename = "movies.ics"  # 输出文件名
# ==================

import csv
import os
import requests
from lxml import etree
from datetime import datetime, timedelta
from ics import Calendar, Event

def gethtml(cinema_id):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    url = f"https://www.maoyan.com/cinema/{cinema_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open("maoyan_cinema.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"影院 {cinema_id} 页面已保存")
    else:
        print(f"请求失败: {cinema_id}")

def parse_html(cinema_name, keyword_list):
    with open("maoyan_cinema.html", "r", encoding="utf-8") as file:
        html = file.read()

    tree = etree.HTML(html)
    index = 3
    matched = []

    while True:
        movie_name_xpath = f'//*[@id="app"]/div[{index}]/div[1]/div[1]/h2'
        movie_name_res = tree.xpath(movie_name_xpath)
        if not movie_name_res:
            break
        movie_name = movie_name_res[0].text
        index2 = 2
        while True:
            date_xpath = f'//*[@id="app"]/div[{index}]/div[2]/span[{index2}]'
            date_res = tree.xpath(date_xpath)
            if not date_res:
                break
            movie_date = date_res[0].text[3:]  # 去掉前缀如 "周五 "
            index3 = 1
            newindex2 = index2 + 1
            while True:
                time_xpath = f'//*[@id="app"]/div[{index}]/div[{newindex2}]/table/tbody/tr[{index3}]/td[1]/span[1]'
                time_res = tree.xpath(time_xpath)
                if not time_res:
                    break
                show_time = time_res[0].text
                room_xpath = f'//*[@id="app"]/div[{index}]/div[{newindex2}]/table/tbody/tr[{index3}]/td[3]/span'
                room_res = tree.xpath(room_xpath)
                room = room_res[0].text if room_res else ""
                if any(k in room for k in keyword_list):
                    matched.append([cinema_name, movie_name, movie_date, show_time, room])
                index3 += 1
            index2 += 1
        index += 1
    return matched

def generate_ics(movie_list, ics_filename="movies.ics"):
    calendar = Calendar()
    for row in movie_list:
        cinema, name, date_str, time_str, room = row
        try:
            # 处理日期
            date_str = date_str.replace("月", "-").replace("日", "")
            show_time = datetime.strptime(f"2025-{date_str} {time_str}", "%Y-%m-%d %H:%M")
            event = Event()
            event.name = f"{name} ({room})"
            event.begin = show_time
            event.duration = timedelta(hours=2)
            event.description = f"{cinema} - {room}"
            calendar.events.add(event)
        except Exception as e:
            print(f"跳过错误行: {row}，原因: {e}")
    with open(ics_filename, "w", encoding="utf-8") as f:
        f.writelines(calendar)
    print(f"已保存为 {ics_filename}")

if __name__ == "__main__":
    all_matches = []
    for cinema_id in cinema_ids:
        cinema_id = cinema_id.strip()
        gethtml(cinema_id)
        matches = parse_html(cinema_id, keywords)
        all_matches.extend(matches)

    if all_matches:
        generate_ics(all_matches, ics_filename=ics_filename)
    else:
        print("未找到匹配的场次")
