import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import jdatetime  # 保留原代码的Jalali日期库（虽未直接使用，保持兼容性）


# -------------------------- 1. 目标TG频道列表（使用您提供的newaddresses）
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
# --------------------------


# -------------------------- 2. 定义去重函数（完全复用原代码逻辑）
def remove_duplicates(input_list):
    unique_list = []
    for item in input_list:
        if item not in unique_list:
            unique_list.append(item)
    return unique_list
# --------------------------


# -------------------------- 3. 遍历频道，获取所有网页HTML内容
html_pages = []
print("开始获取TG频道页面内容...")
for idx, url in enumerate(newaddresses, start=1):
    url = url.strip()  # 清除URL首尾空格
    if not url:
        continue
    try:
        # 增加User-Agent，避免被TG服务器屏蔽（原代码未加，此处优化补充）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        # 发送GET请求（超时15秒，避免卡壳）
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 触发HTTP错误（如404、500）
        html_pages.append(response.text)
        print(f"")
    except Exception as e:
        print(f"")

# -------------------------- 4. 多维度提取Telegram Proxy链接（核心修改：适配Proxy格式）
codes = []  # 存储原始提取的Proxy链接
print("")
for page_idx, page in enumerate(html_pages, start=1):
    soup = BeautifulSoup(page, 'html.parser')
    code_tags = soup.find_all('code')
    found_any = False  # 标记当前页面是否已提取到链接

    # 维度1：从<code>标签提取Proxy（参考原代码code标签逻辑）
    for code_tag in code_tags:
        code_content = code_tag.text.strip()
        # 匹配Proxy链接特征：tg://proxy 或 https://t.me/proxy 或 /proxy（相对路径）
        if any(prefix in code_content for prefix in ["tg://proxy", "https://t.me/proxy", "/proxy?server="]):
            # 补全相对路径：/proxy?server= → https://t.me/proxy?server=
            if code_content.startswith("/proxy?server="):
                code_content = "https://t.me" + code_content
            codes.append(code_content)
            found_any = True

    # 维度2：从<a>标签的href提取Proxy（参考原代码a标签逻辑）
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        # 匹配Proxy链接前缀（严格筛选目标格式）
        if href.startswith(("tg://proxy", "https://t.me/proxy", "/proxy?server=")):
            # 补全相对路径 + 清除转义字符（如amp;）
            if href.startswith("/proxy?server="):
                href = "https://t.me" + href
            href = href.replace("amp;", "")  # 处理TG页面常见的转义字符
            codes.append(href)
            found_any = True

    # 维度3：全局正则兜底（参考原代码正则逻辑，避免漏抓纯文本Proxy）
    if not found_any:
        # 正则表达式：匹配 tg://proxy/... 或 https://t.me/proxy/... 或 /proxy?server=...
        # 终止符：空白、引号、尖括号、右括号（避免匹配多余内容）
        proxy_pattern = re.compile(
            r'(?:tg://proxy|https://t\.me/proxy|/proxy\?server=)[^\s\'"<>)]+',
            re.IGNORECASE  # 忽略大小写（如TG://PROXY也能匹配）
        )
        matches = proxy_pattern.findall(page)
        for match in matches:
            # 补全相对路径 + 清除转义字符
            if match.startswith("/proxy?server="):
                match = "https://t.me" + match
            match = match.replace("amp;", "")
            codes.append(match)

# 第一轮去重：用set快速去重（原代码逻辑）
codes = list(set(codes))

# 第二轮去重：用自定义函数保留顺序去重（原代码逻辑）
processed_codes = remove_duplicates(codes)

# 第三轮去重：规范化链接后去重（参考原代码"第三次去重"逻辑，适配Proxy格式）
seen = set()
unique_processed = []
for item in processed_codes:
    # 规范化步骤：1. 清除首尾空格 2. 去除末尾斜杠 3. 统一协议格式
    norm = item.strip()
    norm = norm.rstrip('/')  # 去除末尾多余斜杠（如 tg://proxy/ → tg://proxy）
    norm = norm.replace("amp;", "")  # 再次清除转义字符（双重保险）
    
    # 处理特殊情况：确保链接以目标协议开头
    if not norm.lower().startswith(("tg://proxy", "https://t.me/proxy")):
        # 重新匹配协议位置，截取正确链接（避免残留多余前缀）
        for proto in ("tg://proxy", "https://t.me/proxy"):
            if proto in norm.lower():
                idx = norm.lower().find(proto)
                norm = norm[idx:]  # 从协议开头截取
                break
    
    # 去重：仅保留未出现过的规范化链接
    if norm not in seen:
        seen.add(norm)
        unique_processed.append(item)  # 保留原始链接（仅用norm去重）

processed_codes = unique_processed

# 最终过滤：确保所有链接都是目标格式（双重校验，避免残留无效链接）
final_proxies = []
for link in processed_codes:
    link = link.strip().replace("amp;", "")
    if link.startswith(("tg://proxy", "https://t.me/proxy")):
        final_proxies.append(link)
# -------------------------- 6. 保存到proxylist.txt（按要求格式：每行一个，空行隔开）
if not final_proxies:
    print("")
else:
    # 获取上海时区当前时间（参考原代码时间处理逻辑）
    current_date_time = datetime.now(pytz.timezone('Asia/Shanghai'))
    final_string = current_date_time.strftime("%m月%d日 | %H:%M")  # 中文时间格式
    final_others_string = current_date_time.strftime("%m月%d日")

    # 写入文件（编码UTF-8，避免中文乱码）
    with open("proxylist.txt", "w", encoding="utf-8") as file:
        # 写入头部注释（参考原代码注释逻辑，方便识别）
        file.write(f"# 抓取时间: {final_string}（上海时区）\n")
        file.write(f"# 抓取频道数: {len(newaddresses)} 个\n")
        file.write(f"# 有效Proxy数: {len(final_proxies)} 条\n")
        file.write("-" + "-"*50 + "\n\n")  # 分隔线

        # 按要求写入链接：每行一个，行与行空行隔开
        for proxy in final_proxies:
            file.write(f"{proxy}\n")  # 写入链接
            file.write("\n")  # 空行（行与行隔开）