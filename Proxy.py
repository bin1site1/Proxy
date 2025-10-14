import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import urllib.parse  # 用于URL解码和解析（解决转义字符、编码问题）
# jdatetime 未实际使用，保留注释说明（避免冗余依赖）
# import jdatetime  


# -------------------------- 核心配置（无代理相关项，用户可修改）
# 1. 目标TG频道列表（保持原列表）
TG_CHANNELS = [
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

# 2. 抓取配置（超时时间、目标Proxy格式）
TIMEOUT = 15  # 请求超时时间（避免卡死后台）
PROXY_PREFIXES = ("tg://proxy", "https://t.me/proxy", "/proxy?server=")  # 目标Proxy前缀
OUTPUT_FILE = "proxylist.txt"  # 输出文件名
# --------------------------


# -------------------------- 工具函数（去重、URL处理）
def remove_duplicates(input_list):
    """保留顺序的去重函数（增加类型校验，避免无效数据）"""
    unique_list = []
    for item in input_list:
        if isinstance(item, str) and item.strip() not in unique_list:
            unique_list.append(item.strip())
    return unique_list


def normalize_proxy_url(url):
    """标准化Proxy URL（解决转义、路径补全、格式统一问题）"""
    if not isinstance(url, str):
        return ""
    
    # 步骤1：清除空格 + URL解码（处理%26、amp;等转义字符）
    normalized = url.strip()
    normalized = urllib.parse.unquote(normalized)  # 解码URL编码字符
    normalized = normalized.replace("amp;", "")    # 处理TG常见的amp;转义
    
    # 步骤2：补全相对路径（/proxy?server= → https://t.me/proxy?server=）
    if normalized.startswith("/proxy?server="):
        normalized = "https://t.me" + normalized
    
    # 步骤3：统一格式（去除末尾斜杠、协议小写）
    normalized = normalized.rstrip("/")  # 避免 tg://proxy/ 和 tg://proxy 被判定为不同
    parsed = urllib.parse.urlparse(normalized)
    if parsed.scheme:
        normalized = normalized.replace(parsed.scheme, parsed.scheme.lower())  # 协议小写（如TG:// → tg://）
    
    # 步骤4：校验是否为有效Proxy格式
    return normalized if normalized.startswith(PROXY_PREFIXES) else ""
# --------------------------


# -------------------------- 核心抓取逻辑（移除代理参数，保留异常处理）
def fetch_tg_proxies(channels, timeout=10):
    """
    抓取TG频道中的Proxy链接（无代理版本）
    :param channels: TG频道URL列表
    :param timeout: 请求超时时间
    :return: 原始Proxy列表（未去重）
    """
    raw_proxies = []
    total_channels = len(channels)
    success_count = 0  # 统计成功请求的频道数

    print(f"开始抓取 {total_channels} 个TG频道（无代理模式）...\n")

    for idx, channel_url in enumerate(channels, 1):
        print(f"[{idx}/{total_channels}] 正在请求：{channel_url}")
        try:
            # 发起请求（移除proxies参数，保留SSL警告禁用和超时）
            requests.packages.urllib3.disable_warnings()  # 解决TG SSL证书可能的警告
            response = requests.get(
                url=channel_url,
                timeout=timeout,
                verify=False  # 部分TG镜像可能存在SSL证书问题，临时禁用
            )
            response.raise_for_status()  # 触发HTTP错误（如404、500）
            success_count += 1

        except requests.exceptions.ConnectionError:
            print(f"❌ 请求失败：无法连接到频道（注意：国内无代理环境可能无法访问TG）\n")
            continue
        except requests.exceptions.Timeout:
            print(f"❌ 请求失败：超时（建议调整TIMEOUT参数）\n")
            continue
        except requests.exceptions.HTTPError as e:
            print(f"❌ 请求失败：HTTP错误 {e.response.status_code}（频道可能不存在或已失效）\n")
            continue
        except Exception as e:
            print(f"❌ 请求失败：未知错误 {str(e)}\n")
            continue

        # 解析HTML，提取Proxy
        soup = BeautifulSoup(response.text, "lxml" if "lxml" in BeautifulSoup.__modules__ else "html.parser")
        found_in_channel = False

        # 维度1：从<code>标签提取（优先，Proxy常放在代码块中）
        for code_tag in soup.find_all("code"):
            code_text = code_tag.text.strip()
            normalized = normalize_proxy_url(code_text)
            if normalized and normalized not in raw_proxies:
                raw_proxies.append(normalized)
                found_in_channel = True

        # 维度2：从<a>标签的href提取（链接形式的Proxy）
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            normalized = normalize_proxy_url(href)
            if normalized and normalized not in raw_proxies:
                raw_proxies.append(normalized)
                found_in_channel = True

        # 维度3：全局正则兜底（纯文本中隐藏的Proxy）
        if not found_in_channel:
            proxy_pattern = re.compile(
                r'(tg://proxy|https://t\.me/proxy|/proxy\?server=)[^\s\'"<>)]+',
                re.IGNORECASE | re.MULTILINE
            )
            matches = proxy_pattern.findall(response.text)
            for match in matches:
                normalized = normalize_proxy_url(match)
                if normalized and normalized not in raw_proxies:
                    raw_proxies.append(normalized)
                    found_in_channel = True

        print(f"✅ {'已找到Proxy' if found_in_channel else '未找到Proxy'}（当前累计：{len(raw_proxies)} 条）\n")

    print(f"抓取完成：{success_count}/{total_channels} 个频道请求成功，共抓取 {len(raw_proxies)} 条原始Proxy")
    return raw_proxies
# --------------------------


# -------------------------- 数据处理与文件写入（移除代理相关校验）
def process_and_save_proxies(raw_proxies):
    """处理（去重、过滤）Proxy并写入文件"""
    # 第一轮去重：保留顺序去重
    unique_proxies = remove_duplicates(raw_proxies)
    # 第二轮过滤：确保最终都是有效Proxy格式
    final_proxies = [p for p in unique_proxies if p.startswith(PROXY_PREFIXES)]

    # 获取上海时区时间（容错处理）
    try:
        sh_tz = pytz.timezone("Asia/Shanghai")
        current_time = datetime.now(sh_tz).strftime("%Y年%m月%d日 | %H:%M:%S")
    except pytz.UnknownTimeZoneError:
        current_time = datetime.now().strftime("%Y年%m月%d日 | %H:%M:%S")
        print("⚠️  上海时区未找到，使用系统默认时区")

    # 写入文件（保留权限异常处理）
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            # 头部注释（补充无代理说明）
            f.write(f"# TG Proxy 抓取结果（无代理模式）\n")
            f.write(f"# 抓取时间：{current_time}（上海时区）\n")
            f.write(f"# 目标频道数：{len(TG_CHANNELS)} 个\n")
            f.write(f"# 成功请求数：{len([c for c in TG_CHANNELS if _check_channel_accessible(c)]):d} 个（实时校验）\n")
            f.write(f"# 原始抓取数：{len(raw_proxies)} 条\n")
            f.write(f"# 最终有效数：{len(final_proxies)} 条\n")
            f.write(f"# 注意：无代理模式下，国内环境可能无法访问TG，导致抓取失败\n")
            f.write(f"# --------------------------\n\n")

            # 写入Proxy（每行1个，空行分隔）
            if final_proxies:
                for idx, proxy in enumerate(final_proxies, 1):
                    f.write(f"{idx}. {proxy}\n\n")
            else:
                f.write("# 未找到任何有效Proxy（可能原因：频道无数据、格式变更，或无代理无法访问TG）\n")

        print(f"\n✅ 文件写入成功！路径：{OUTPUT_FILE}")
        print(f"📊 最终统计：{len(final_proxies)} 条有效Proxy")

    except PermissionError:
        print(f"❌ 文件写入失败：无权限（请将代码移到桌面/文档等非系统目录）")
    except Exception as e:
        print(f"❌ 文件写入失败：未知错误 {str(e)}")


def _check_channel_accessible(channel_url):
    """辅助函数：检查频道是否可访问（无代理）"""
    try:
        requests.packages.urllib3.disable_warnings()
        response = requests.get(channel_url, timeout=5, verify=False)
        return response.status_code == 200
    except:
        return False
# --------------------------


# -------------------------- 主函数（移除代理依赖检测）
if __name__ == "__main__":
    # 1. 缺失依赖检测（移除requests[socks]，仅保留核心依赖）
    required_packages = ["requests", "beautifulsoup4", "pytz", "lxml"]
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)
    
    if missing_packages:
        print(f"⚠️  检测到缺失依赖：{', '.join(missing_packages)}")
        print(f"请先执行命令安装：pip install {' '.join(missing_packages)}")
        exit()

    # 2. 执行抓取、处理、写入（无代理调用）
    raw_proxies = fetch_tg_proxies(
        channels=TG_CHANNELS,
        timeout=TIMEOUT
    )
    process_and_save_proxies(raw_proxies)