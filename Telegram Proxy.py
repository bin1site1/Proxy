import requests
from bs4 import BeautifulSoup
import os
import datetime
import sys
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import re
import pyperclip

# 尝试导入 colorama，如果没有安装则忽略（GUI模式不需要）
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

class TGProxyCrawler:
    def __init__(self, root):
        self.root = root
        self.root.title("TG 代理链接批量抓取工具 V2.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.setup_fonts()
        
        # 全局状态
        self.loading_stop = [False]
        self.failed_count = 0
        self.extracted_links = set()
        self.is_running = False
        
        # 配置目标URLs
        self.urls = [
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
        ]
        
        self.total_channels = len(self.urls)
        self.start_time = None
        
        # 创建UI
        self.create_widgets()
    
    def setup_fonts(self):
        """设置支持中文的字体"""
        default_font = ('SimHei', 10)
        self.root.option_add("*Font", default_font)
    
    def create_widgets(self):
        """创建所有UI组件"""
        # 顶部软件名称
        header_frame = tk.Frame(self.root, pady=10)
        header_frame.pack(fill=tk.X, padx=10)
        
        title_label = tk.Label(
            header_frame, 
            text="TG 代理链接批量抓取工具 V2.0", 
            font=('SimHei', 16, 'bold')
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame, 
            text="自动抓取多个频道代理，支持一键复制结果", 
            fg="#666666"
        )
        subtitle_label.pack()
        
        # 中间分隔面板
        middle_frame = tk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 自定义数据源输入框
        custom_source_frame = tk.LabelFrame(middle_frame, text="自定义数据源", padx=5, pady=5)
        custom_source_frame.pack(fill=tk.X, padx=0, pady=(0, 5))
        
        self.custom_urls_entry = scrolledtext.ScrolledText(
            custom_source_frame,
            wrap=tk.WORD,
            height=3
        )
        self.custom_urls_entry.pack(fill=tk.X, expand=False)
        
        hint_label = tk.Label(
            custom_source_frame,
            text="提示：每行输入一个URL，为空则使用默认数据源",
            fg="#666666",
            font=('SimHei', 8)
        )
        hint_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 执行日志面板
        log_frame = tk.LabelFrame(middle_frame, text="执行日志", padx=5, pady=5)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            bg="#f0f0f0"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 输出结果面板
        result_frame = tk.LabelFrame(middle_frame, text="输出完整结果", padx=5, pady=5)
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮面板（已移除“清空日志”和“清空结果”按钮）
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack(fill=tk.X, padx=10)
        
        # 按钮样式
        button_style = {'padx': 15, 'pady': 5, 'width': 12}
        
        self.start_btn = tk.Button(
            button_frame, 
            text="开始处理", 
            command=self.start_processing,
            **button_style,
            bg="#4CAF50",
            fg="white"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_btn = tk.Button(
            button_frame, 
            text="一键复制结果", 
            command=self.copy_results,
            **button_style,
            bg="#2196F3",
            fg="white"
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清除自定义数据源按钮
        self.clear_custom_btn = tk.Button(
            button_frame, 
            text="清除自定义数据源", 
            command=self.clear_custom_source,
            **button_style,
            bg="#f44336",
            fg="white"
        )
        self.clear_custom_btn.pack(side=tk.LEFT)
        
        # 进度条
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        self.progress_label = tk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def clear_custom_source(self):
        """清除自定义数据源输入框内容"""
        self.custom_urls_entry.delete(1.0, tk.END)
        self.log("自定义数据源已清空")
    
    def get_effective_urls(self):
        """获取有效的URL列表（自定义或默认），并自动补全格式"""
        custom_urls_text = self.custom_urls_entry.get(1.0, tk.END).strip()
        
        if custom_urls_text:
            # 处理自定义URL，过滤空行并补全格式
            custom_urls = []
            for url in custom_urls_text.split('\n'):
                url = url.strip()
                if not url:
                    continue
                # 补全URL格式：将 https://t.me/xxx 转换为 https://t.me/s/xxx
                if re.match(r'^https://t\.me/[^/]+$', url):
                    corrected_url = url.replace('https://t.me/', 'https://t.me/s/')
                    self.log(f"自动补全URL格式: {url} -> {corrected_url}")
                    custom_urls.append(corrected_url)
                else:
                    custom_urls.append(url)
            return custom_urls
        else:
            # 使用默认URL
            return self.urls.copy()
    
    def log(self, message, is_error=False):
        """向日志文本框添加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        
        if is_error:
            self.log_text.insert(tk.END, f"[{timestamp}] 错误: {message}\n", "error")
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            
        self.log_text.tag_config("error", foreground="red")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_results(self):
        """更新结果文本框"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        for link in sorted(self.extracted_links):
            self.result_text.insert(tk.END, f"{link}\n\n")
            
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def copy_results(self):
        """复制结果到剪贴板"""
        if not self.extracted_links:
            messagebox.showinfo("提示", "没有可复制的结果")
            return
            
        result_str = "\n\n".join(sorted(self.extracted_links))
        pyperclip.copy(result_str)
        self.log("结果已复制到剪贴板")
    
    def start_processing(self):
        """开始处理任务（在新线程中运行）"""
        if self.is_running:
            messagebox.showinfo("提示", "任务正在运行中")
            return
            
        self.is_running = True
        self.start_btn.config(text="处理中...", state=tk.DISABLED)
        self.extracted_links.clear()
        self.failed_count = 0
        self.start_time = datetime.datetime.now()
        
        # 获取有效的URL列表
        self.effective_urls = self.get_effective_urls()
        self.total_channels = len(self.effective_urls)
        
        # 重置进度条
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        
        self.log("开始抓取代理链接...")
        self.log(f"目标频道数: {self.total_channels} 个")
        self.log(f"启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 在新线程中执行抓取任务，避免UI冻结
        threading.Thread(target=self.process_channels, daemon=True).start()
    
    def process_channels(self):
        """处理所有频道"""
        for idx, url in enumerate(self.effective_urls, start=1):
            if not self.is_running:  # 检查是否需要停止
                break
                
            channel_name = url.split('/')[-1]
            self.loading_stop[0] = False
            
            # 更新状态栏
            self.status_var.set(f"正在处理: {channel_name} ({idx}/{self.total_channels})")
            
            try:
                # 启动加载动画（在主线程更新UI）
                self.root.after(0, self.update_loading, channel_name)
                
                # 网络请求
                response = requests.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'},
                    timeout=12
                )
                response.raise_for_status()
                self.loading_stop[0] = False
                
                # 解析链接
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', href=True)
                
                found_in_channel = 0
                for link in links:
                    href = link.get('href').replace('amp;', '') if link.get('href') else ""
                    # 代理链接前缀判断
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
                
                self.log(f"处理完成: {channel_name}，找到 {found_in_channel} 条代理")
                # 更新结果显示
                self.root.after(0, self.update_results)
                
            except requests.exceptions.RequestException as e:
                self.failed_count += 1
                self.log(f"网络错误 - 频道[{channel_name}]: {str(e)[:50]}", is_error=True)
            except Exception as e:
                self.failed_count += 1
                self.log(f"解析错误 - 频道[{channel_name}]: {str(e)[:50]}", is_error=True)
            finally:
                self.loading_stop[0] = True
            
            # 更新进度条
            progress = (idx / self.total_channels) * 100
            self.root.after(0, self.update_progress, progress)
            self.status_var.set(f"处理进度: {progress:.1f}% ({idx}/{self.total_channels})")
        
        # 任务完成
        self.root.after(0, self.complete_processing)
    
    def update_progress(self, value):
        """更新进度条显示"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value:.1f}%")
    
    def update_loading(self, channel_name):
        """更新加载动画（在主线程中执行）"""
        if not self.loading_stop[0] and self.is_running:
            current_text = self.status_var.get()
            if not re.search(r'[|/\-\\]$', current_text):
                self.status_var.set(f"正在请求: {channel_name} |")
            elif current_text.endswith('|'):
                self.status_var.set(f"正在请求: {channel_name} /")
            elif current_text.endswith('/'):
                self.status_var.set(f"正在请求: {channel_name} -")
            elif current_text.endswith('-'):
                self.status_var.set(f"正在请求: {channel_name} \\")
            
            # 继续更新动画
            self.root.after(150, self.update_loading, channel_name)
    
    def complete_processing(self):
        """完成处理任务"""
        elapsed = (datetime.datetime.now() - self.start_time).total_seconds()
        success_count = self.total_channels - self.failed_count
        success_rate = (success_count / self.total_channels * 100) if self.total_channels > 0 else 0
        
        self.log("\n===== 抓取任务完成 =====")
        self.log(f"总频道数: {self.total_channels}")
        self.log(f"成功解析: {success_count}")
        self.log(f"解析失败: {self.failed_count}")
        self.log(f"有效代理: {len(self.extracted_links)}")
        self.log(f"总耗时: {elapsed:.2f}秒")
        self.log(f"成功率: {success_rate:.1f}%")
        
        # 确保进度条显示100%
        self.root.after(0, self.update_progress, 100)
        self.status_var.set("就绪")
        self.start_btn.config(text="开始处理", state=tk.NORMAL)
        self.is_running = False
        
        # 保存结果到文件
        if self.extracted_links:
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
                output_file = os.path.join(desktop_path, f"TG代理_{len(self.extracted_links)}条_{timestamp}.txt")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    for link in sorted(self.extracted_links):
                        f.write(f"{link}\n\n")
                
                self.log(f"结果已保存至: {output_file}")
            except Exception as e:
                self.log(f"保存文件失败: {str(e)}", is_error=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = TGProxyCrawler(root)
    root.mainloop()