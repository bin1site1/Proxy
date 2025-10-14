import re
import requests  # 导入requests库，用于发送HTTP请求
from bs4 import BeautifulSoup  # 导入BeautifulSoup库，用于解析HTML
from datetime import datetime, timezone  # 导入datetime库，用于处理日期和时间
import pytz  # 导入pytz库，用于处理时区
import jdatetime  # 导入jdatetime库，用于处理Jalali日期


# 待抓取的Telegram频道链接（可根据需求补充/修改）
newaddresses = [
    "https://t.me/s/gaosuwang",
    "https://t.me/s/ProxyMTProting",
    "https://t.me/s/hgwzcd",
    "https://t.me/s/GSDL6",
    "https://t.me/s/changanhutui",
    "https://t.me/s/qiuyue2",
    "https://t.me/s/gsdl01",
    "https://t.me/s/juzibaipiao",
    "https://t.me/s/daili81",
    "https://t.me/s/hbgzs1",
    "https://t.me/s/VPNzhilian",
    "https://t.me/s/duxiangdail",
    "https://t.me/s/XB811",
    "https://t.me/s/ngg789",
    "https://t.me/s/TGTW88",
    "https://t.me/s/afeiSSS",
    "https://t.me/s/feijidailil",
    "https://t.me/s/dail99",
]

# -------------------------- 核心配置：Telegram代理链接格式 --------------------------
TARGET_PROXY_PATTERNS = (
    "https://t.me/proxy?server=",
    "tg://proxy?server=",
    "/proxy?server=",
    "https://t.me/s/proxy?server="
)


# 定义去重函数，输入列表，返回去重后的列表
def remove_duplicates(input_list):
    unique_list = []
    for item in input_list:
        if item not in unique_list:
            unique_list.append(item)
    return unique_list


# 1. 遍历所有频道地址，获取网页HTML内容
html_pages = []
for url in newaddresses:
    try:
        response = requests.get(url, timeout=10)  # 增加超时防止卡壳
        response.raise_for_status()  # 若请求失败（如404/500），抛出异常
        html_pages.append(response.text)
    except Exception as e:
        print(f"获取 {url} 失败：{str(e)}")  # 捕获异常并提示，避免程序中断


# 2. 从HTML中提取Telegram代理链接
codes = []
for page in html_pages:
    soup = BeautifulSoup(page, 'html.parser')
    found_any = False

    # 2.1 先从 <code> 标签提取（部分频道会用code标签包裹代理）
    code_tags = soup.find_all('code')
    for code_tag in code_tags:
        code_content = code_tag.text.strip()
        # 判断是否包含目标Telegram代理格式
        if any(pattern in code_content for pattern in TARGET_PROXY_PATTERNS):
            codes.append(code_content)
            found_any = True

    # 2.2 再从 <a> 标签的href提取（部分代理是链接形式）
    a_tags = soup.find_all('a', href=True)
    for a_tag in a_tags:
        href = a_tag['href'].strip()
        # 判断href是否以目标格式开头
        if href.startswith(TARGET_PROXY_PATTERNS):
            codes.append(href)
            found_any = True

    # 2.3 最后用正则全局抓取（应对纯文本/无标签包裹的代理）
    if not found_any:
        # 正则匹配：以4种格式开头，后续字符排除空白/引号/尖括号等无效字符
        proxy_pattern = re.compile(
            r'(?:https://t\.me/proxy\?server=|https://t\.me/s/proxy\?server=|tg://proxy\?server=|/proxy\?server=)[^\s\'"<>)]+',
            re.IGNORECASE  # 忽略大小写（避免因大小写差异漏抓）
        )
        matches = proxy_pattern.findall(page)
        codes.extend(matches)


# 3. 多层去重（确保无重复代理）
# 3.1 第一次去重：基础去重
codes = list(set(codes))
# 3.2 第二次去重：按规范化格式去重（处理链接尾部多余字符）
processed_codes = []
seen = set()
for item in codes:
    # 规范化处理：去除尾部斜杠、参数分隔符后的内容
    norm_item = item.strip().rstrip('/')
    # 若包含查询参数/分隔符，只保留核心代理部分
    for sep in ('?', '&', ';'):
        if sep in norm_item:
            norm_item = norm_item.split(sep, 1)[0]
            break
    # 验证是否为目标格式，避免无效数据
    if any(norm_item.startswith(pattern) for pattern in TARGET_PROXY_PATTERNS):
        if norm_item not in seen:
            seen.add(norm_item)
            processed_codes.append(item)  # 保留原始链接，仅用规范化格式去重


# 4. 过滤无效链接（排除空字符串/格式错误的链接）
valid_proxies = []
for proxy in processed_codes:
    cleaned_proxy = proxy.split("#")[0].strip()  # 去除#后的注释内容
    # 最终验证：非空且符合目标格式
    if cleaned_proxy and any(cleaned_proxy.startswith(pattern) for pattern in TARGET_PROXY_PATTERNS):
        valid_proxies.append(cleaned_proxy)


# 5. 写入文件（带时间标记，格式清晰）
# 获取上海时区当前时间
current_time = datetime.now(pytz.timezone('Asia/Shanghai'))
time_mark = current_time.strftime("%m月%d日 | %H:%M")  # 时间格式：05月20日 | 14:30

# 写入proxylist.txt（UTF-8编码，避免中文乱码）
with open("proxylist.txt", "w", encoding="utf-8") as f:
    # 写入时间标记（便于追溯代理更新时间）
    f.write(f"# Telegram代理列表 - 更新时间：{time_mark}\n")
    f.write("# " + "-"*50 + "\n\n")
    # 写入代理（一行一个，空行分隔，格式清晰）
    f.write("\n\n".join(valid_proxies))
    # 结尾加换行符，保证文件格式规范
    f.write("\n")


print(f"抓取完成！共获取 {len(valid_proxies)} 个有效Telegram代理，已保存到 proxylist.txt")