#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误监控看板演示

演示如何在应用中集成错误监控看板，包括实时错误跟踪和可视化
"""

import os
import sys
import time
import random
import logging
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext

# 确保能够导入src模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入错误相关模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
    from src.exporters.error_dashboard import get_error_monitor
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保您在正确的目录中运行此示例")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("error_dashboard_demo")


class ErrorDashboardUI:
    """错误监控看板UI演示"""
    
    def __init__(self, root):
        """初始化UI
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("VisionAI-ClipsMaster 错误监控看板")
        self.root.geometry("800x600")
        
        # 获取错误监控实例
        self.monitor = get_error_monitor()
        
        # 创建UI组件
        self._create_widgets()
        
        # 注册错误回调
        self.monitor.register_callback(self.update_dashboard)
        
        # 启动监控
        self.monitor.start_monitoring()
        
        # 初始状态
        self.is_generating_errors = False
        self.error_thread = None
        
        # 初始更新
        self.update_dashboard(self.monitor.get_dashboard_data())
    
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部状态栏
        status_frame = ttk.Frame(self.root, padding=10)
        status_frame.pack(fill=tk.X)
        
        ttk.Label(status_frame, text="状态:").grid(row=0, column=0, padx=5)
        self.status_label = ttk.Label(status_frame, text="正常", foreground="green")
        self.status_label.grid(row=0, column=1, padx=5)
        
        ttk.Label(status_frame, text="总错误数:").grid(row=0, column=2, padx=5)
        self.error_count_label = ttk.Label(status_frame, text="0")
        self.error_count_label.grid(row=0, column=3, padx=5)
        
        ttk.Label(status_frame, text="最近更新:").grid(row=0, column=4, padx=5)
        self.update_time_label = ttk.Label(status_frame, text="无")
        self.update_time_label.grid(row=0, column=5, padx=5)
        
        # 控制按钮
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)
        
        self.generate_button = ttk.Button(
            control_frame, 
            text="开始生成错误", 
            command=self.toggle_error_generation
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(
            control_frame, 
            text="清除错误", 
            command=self.clear_errors
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 错误列表
        list_frame = ttk.LabelFrame(self.root, text="最近错误", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("时间", "代码", "组件", "严重程度", "消息")
        self.error_list = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.error_list.heading(col, text=col)
            if col == "消息":
                self.error_list.column(col, width=300)
            else:
                self.error_list.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.error_list.yview)
        self.error_list.configure(yscrollcommand=scrollbar.set)
        
        self.error_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 错误详情框
        details_frame = ttk.LabelFrame(self.root, text="错误详情", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # 当选择错误时显示详情
        self.error_list.bind("<<TreeviewSelect>>", self.show_error_details)
        
        # 底部状态栏
        footer_frame = ttk.Frame(self.root, padding=5)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_bar = ttk.Label(
            footer_frame, 
            text="错误监控看板已启动", 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.LEFT)
        
        # 分类统计
        stats_frame = ttk.LabelFrame(self.root, text="错误统计", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=4)
        self.stats_text.pack(fill=tk.BOTH)
    
    def update_dashboard(self, metrics):
        """更新仪表盘
        
        Args:
            metrics: 错误监控指标
        """
        # 更新错误计数
        total_errors = metrics.get("total_errors", 0)
        self.error_count_label.config(text=str(total_errors))
        
        # 更新状态
        if total_errors == 0:
            self.status_label.config(text="正常", foreground="green")
        elif total_errors < 5:
            self.status_label.config(text="注意", foreground="blue")
        elif total_errors < 10:
            self.status_label.config(text="警告", foreground="orange")
        else:
            self.status_label.config(text="严重", foreground="red")
        
        # 更新最近更新时间
        last_update = metrics.get("last_update", 0)
        if last_update:
            self.update_time_label.config(
                text=f"{last_update:.1f}秒前"
            )
        
        # 更新错误列表
        self.error_list.delete(*self.error_list.get_children())
        for error in metrics.get("recent_errors", []):
            timestamp = datetime.fromtimestamp(error.get("timestamp", 0)).strftime("%H:%M:%S")
            self.error_list.insert(
                "", "end",
                values=(
                    timestamp,
                    error.get("error_code", ""),
                    error.get("component", ""),
                    error.get("severity", ""),
                    error.get("message", "")
                )
            )
        
        # 更新统计信息
        stats_text = ""
        
        # 错误类别统计
        stats_text += "错误类别: "
        for category, count in metrics.get("error_categories", {}).items():
            stats_text += f"{category}({count}) "
        stats_text += "\n"
        
        # 组件错误统计
        stats_text += "组件错误: "
        for component, count in metrics.get("component_errors", {}).items():
            stats_text += f"{component}({count}) "
        stats_text += "\n"
        
        # 错误类型统计
        stats_text += "错误类型: "
        for error_type, count in list(metrics.get("error_types", {}).items())[:5]:
            stats_text += f"{error_type}({count}) "
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)
        
        # 更新状态栏
        self.status_bar.config(
            text=f"最后更新: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def show_error_details(self, event):
        """显示所选错误的详情"""
        selection = self.error_list.selection()
        if not selection:
            return
        
        # 获取所选项
        item = self.error_list.item(selection[0])
        values = item["values"]
        
        # 获取错误详情
        dashboard_data = self.monitor.get_dashboard_data()
        for error in dashboard_data.get("recent_errors", []):
            # 匹配选中的错误
            error_time = datetime.fromtimestamp(error.get("timestamp", 0)).strftime("%H:%M:%S")
            if (error_time == values[0] and 
                error.get("error_code") == values[1] and 
                error.get("message") == values[4]):
                
                # 显示详情
                details = (
                    f"时间: {error_time}\n"
                    f"错误代码: {error.get('error_code', '')}\n"
                    f"组件: {error.get('component', '')}\n"
                    f"阶段: {error.get('phase', '')}\n"
                    f"严重程度: {error.get('severity', '')}\n"
                    f"消息: {error.get('message', '')}\n"
                    f"建议: {error.get('suggestion', '')}\n"
                )
                
                self.details_text.delete(1.0, tk.END)
                self.details_text.insert(tk.END, details)
                return
    
    def toggle_error_generation(self):
        """切换错误生成状态"""
        if self.is_generating_errors:
            # 停止生成错误
            self.is_generating_errors = False
            self.generate_button.config(text="开始生成错误")
            if self.error_thread and self.error_thread.is_alive():
                # 线程会自行检查标志并退出
                pass
        else:
            # 开始生成错误
            self.is_generating_errors = True
            self.generate_button.config(text="停止生成错误")
            
            # 启动错误生成线程
            self.error_thread = threading.Thread(
                target=self.generate_random_errors,
                daemon=True
            )
            self.error_thread.start()
    
    def generate_random_errors(self):
        """生成随机错误的线程"""
        error_types = [
            (ErrorCode.FILE_NOT_FOUND, "文件未找到", {"path": "test.mp4"}),
            (ErrorCode.PERMISSION_DENIED, "权限被拒绝", {"path": "access.log"}),
            (ErrorCode.MODEL_ERROR, "模型加载失败", {"model": "qwen2.5-7b-zh"}),
            (ErrorCode.NETWORK_ERROR, "网络连接失败", {"url": "api.example.com"}),
            (ErrorCode.VALIDATION_ERROR, "验证失败", {"field": "resolution"}),
            (ErrorCode.TIMEOUT_ERROR, "操作超时", {"operation": "export"}),
            (ErrorCode.MEMORY_ERROR, "内存不足", {"required": "8GB", "available": "4GB"}),
            (ErrorCode.PROCESSING_ERROR, "处理失败", {"stage": "encode"}),
        ]
        
        components = [
            "file_manager", "model_loader", "video_processor", 
            "network", "ui", "exporter", "validator"
        ]
        
        phases = [
            "init", "loading", "processing", "validation", "export"
        ]
        
        severities = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        
        while self.is_generating_errors:
            # 随机选择错误类型
            error_code, message, details = random.choice(error_types)
            
            # 随机选择组件和阶段
            component = random.choice(components)
            phase = random.choice(phases)
            
            # 有10%的概率是严重错误
            severity = random.choices(
                severities, 
                weights=[0.1, 0.4, 0.4, 0.1], 
                k=1
            )[0]
            
            # 创建错误
            error = ClipMasterError(
                message, 
                code=error_code,
                details=details
            )
            
            # 添加额外属性
            setattr(error, "component", component)
            setattr(error, "phase", phase)
            setattr(error, "severity", severity)
            
            # 更新错误监控看板
            self.monitor.update_dashboard(error)
            
            # 暂停1-3秒
            time.sleep(random.uniform(1, 3))
    
    def clear_errors(self):
        """清除所有错误数据"""
        # 停止监控
        self.monitor.stop_monitoring()
        
        # 重启监控
        self.monitor.start_monitoring()
        
        # 更新UI
        self.update_dashboard(self.monitor.get_dashboard_data())
        
        # 清空详情
        self.details_text.delete(1.0, tk.END)
    
    def on_close(self):
        """关闭窗口时的清理工作"""
        # 停止错误生成
        self.is_generating_errors = False
        
        # 停止监控
        self.monitor.stop_monitoring()
        
        # 关闭窗口
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = ErrorDashboardUI(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    
    # 启动UI循环
    root.mainloop()


if __name__ == "__main__":
    main() 