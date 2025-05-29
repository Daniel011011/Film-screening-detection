import os
import csv
import requests
from datetime import datetime
from lxml import etree
import pandas as pd
from ics import Calendar, Event

def get_html(cinema_id):
    headers = {
        'Referer': f'https://www.maoyan.com/cinema/{cinema_id}',
        'User-Agent': 'Mozilla/5.0',
    }
    url = f"https://www.maoyan.com/cinema/{cinema_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"请求失败：{response.status_code}")
        return ""

def parse_html(html, cinema_name):
    tree = etree.HTML(html)
    index = 3
    records = []

    while True:
        title_xpath = f'//*[@id="app"]/div[{index}]/div[1]/div[1]/h2'
        title = tree.xpath(title_xpath)
        if not title:
            break
        movie_name = title[0].text
        index2 = 2
        while True:
            date_xpath = f'//*[@id="app"]/div[{index}]/div[2]/span[{index2}]'
            date_node = tree.xpath(date_xpath)
            if not date_node:
                break
            movie_date = date_node[0].text[3:]  # 去掉“周几”
            index3 = 1
            while True:
                table_xpath = f'//*[@id="app"]/div[{index}]/div[{index2 + 1}]/table/tbody/tr[{index3}]'
                time_xpath = f'{table_xpath}/td[1]/span[1]'
                room_xpath = f'{table_xpath}/td[3]/span'
                time_node = tree.xpath(time_xpath)
                room_node = tree.xpath(room_xpath)
                if not time_node:
                    break
                show_time = time_node[0].text
                room = room_node[0].text if room_node else "未知"
                records.append([cinema_name, movie_name, movie_date, show_time, room])
                index3 += 1
            index2 += 1
        index += 1
    return records

def save_and_deduplicate(records, csv_file):
    header = ["Cinema", "Movie", "Date", "Time", "Room"]
    new_df = pd.DataFrame(records, columns=header)

    if os.path.exists(csv_file):
        old_df = pd.read_csv(csv_file, encoding="utf-8")
        merged_df = pd.concat([old_df, new_df]).drop_duplicates()
    else:
        merged_df = new_df

    merged_df.to_csv(csv_file, index=False, encoding="utf-8")
    return merged_df

def write_ics(df, ics_file):
    calendar = Calendar()
    now_year = datetime.now().year

    for _, row in df.iterrows():
        date_str = row["Date"].replace("月", "-").replace("日", "")
        try:
            dt = datetime.strptime(f"{now_year}-{date_str} {row['Time']}", "%Y-%m-%d %H:%M")
        except:
            continue

        e = Event()
        e.name = f"{row['Movie']} - {row['Room']}"
        e.begin = dt
        e.duration = {"hours": 2}  # 默认2小时
        e.location = row["Cinema"]
        calendar.events.add(e)

    with open(ics_file, "w", encoding="utf-8") as f:
        f.writelines(calendar)

if __name__ == "__main__":
    cinemas = {
        "25552": "厦门影院",
        "24311": "其他影院"
    }

    all_records = []
    for cid, name in cinemas.items():
        html = get_html(cid)
        if html:
            records = parse_html(html, name)
            all_records.extend(records)

    csv_file = "cinema_schedule.csv"
    ics_file = "schedule.ics"

    merged_df = save_and_deduplicate(all_records, csv_file)
    write_ics(merged_df, ics_file)
    print("📅 排片已更新并写入 ICS。")
