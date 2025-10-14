import re

import requests  # 导入requests库，用于发送HTTP请求
from bs4 import BeautifulSoup  # 导入BeautifulSoup库，用于解析HTML
from datetime import datetime, timezone  # 导入datetime库，用于处理日期和时间
import pytz  # 导入pytz库，用于处理时区
import jdatetime  # 导入jdatetime库，用于处理Jalali日期


newaddresses = [
    "https://t.me/s/vmessiran",
    "https://t.me/s/mrsoulb",
    "https://t.me/s/v2xay",
    "https://t.me/s/vpnaloo",
    "https://t.me/s/v2ray_configs_pool",
    "https://t.me/s/V2RAY_VMESS_free",
    "https://t.me/s/FreakConfig",
    "https://t.me/s/v2rayNG_Matsuri",
    "https://t.me/s/meli_proxyy",
    "https://t.me/s/Daily_Configs",
    "https://t.me/s/customv2ray",
    "https://t.me/s/i10VPN ",


]
# 定义去重函数，输入列表，返回去重后的列表
def remove_duplicates(input_list):
    unique_list = []
    for item in input_list:
        if item not in unique_list:
            unique_list.append(item)
    return unique_list

html_pages = []  # 用于存储每个网页的HTML内容

# 遍历所有地址，获取网页内容
for url in newaddresses:
    response = requests.get(url)  # 发送GET请求
    html_pages.append(response.text)  # 保存网页内容

codes = []  # 用于存储所有抓取到的配置代码

# 遍历所有HTML页面，解析并提取code标签内容
for page in html_pages:
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a', href=True)

    found_in_channel = 0
    for link in links:
        href = link.get('href').replace('amp;', '') if link.get('href') else ""
        if any(href.startswith(prefix) for prefix in [
                        "https://t.me/proxy?server=",
                        "tg://proxy?server=",
                        "/proxy?server=",
                        "https://t.me/s/proxy?server="
        ]):
            if href.startswith("/"):
                href = "https://t.me" + href
            self.extracted_links.add(href)
            found_in_channel += 1

codes = list(set(codes))  # 去重

processed_codes = []  # 用于存储处理后的配置

# 获取当前时间（上海时区）
current_date_time = datetime.now(pytz.timezone('Asia/Shanghai'))
current_month = current_date_time.strftime("%m")  # 月份（数字）
current_day = current_date_time.strftime("%d")    # 日期
updated_hour = current_date_time.strftime("%H")   # 小时
updated_minute = current_date_time.strftime("%M") # 分钟
final_string = f"{current_month}月{current_day}日 | {updated_hour}:{updated_minute}"  # 中文格式时间字符串
final_others_string = f"{current_month}月{current_day}日"  # 仅日期字符串
config_string = "#✅ " + str(final_string) + "-"  # 配置头部字符串

processed_codes = remove_duplicates(processed_codes)  # 再次去重

new_processed_codes = []  # 用于存储最终处理后的配置

i = 0  # 初始化服务器计数器
with open("config.txt", "w", encoding="utf-8") as file:  # 以写入模式打开文件
    for code in new_processed_codes:
        if i == 0:
            config_string = "#🌐已更新于" + config_string + " | 每15分钟更新一次"  # 第一行写更新时间
        else:
            config_string = "#🌐服务器" + str(i) + " | " + str(final_others_string) + " |bin1site1.github.io "  # 其他行写服务器编号和日期
        config_final = code + config_string  # 拼接配置和注释
        file.write(config_final + "\n")  # 写入文件并换行
        i += 1  # 服务器计数器加一
