#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计报告面板组件

提供用于显示合规审计报告的UI组件。
支持生成、查看和导出GDPR和个人信息保护法合规的审计报告。
"""

import sys
import os
import datetime
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union

# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 尝试导入tkinter组件
try:
    if sys.version_info.major == 3:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    else:
        import Tkinter as tk
        import ttk
        import tkFileDialog as filedialog
        import tkMessageBox as messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# 导入审计报告功能
from src.exporters.log_audit import (
    generate_audit_report, 
    export_audit_report,
    count_operations,
    list_security_events
)
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("audit_report_panel")

class AuditReportPanel:
    """审计报告面板类"""
    
    def __init__(self, parent=None, master=None):
        """
        初始化审计报告面板
        
        Args:
            parent: 父容器
            master: 主窗口
        """
        self.parent = parent
        self.master = master or parent
        
        # 检查tkinter是否可用
        if not TKINTER_AVAILABLE:
            logger.warning("Tkinter不可用，审计报告面板将不可用")
            self.frame = None
            return
            
        # 创建面板框架
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 设置面板标题
        if master:
            master.title("合规审计报告")
            
        # 初始化组件
        self._init_widgets()
        
        # 设置默认日期
        self._set_default_dates()
    
    def _init_widgets(self):
        """初始化UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="报告设置")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 日期选择
        date_frame = ttk.Frame(control_frame)
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_date_entry = ttk.Entry(date_frame, width=12)
        self.start_date_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(date_frame, text="结束日期:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.end_date_entry = ttk.Entry(date_frame, width=12)
        self.end_date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 日期预设按钮
        presets_frame = ttk.Frame(control_frame)
        presets_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(presets_frame, text="今天", command=lambda: self._set_date_range("today")).pack(side=tk.LEFT, padx=2)
        ttk.Button(presets_frame, text="昨天", command=lambda: self._set_date_range("yesterday")).pack(side=tk.LEFT, padx=2)
        ttk.Button(presets_frame, text="本周", command=lambda: self._set_date_range("this_week")).pack(side=tk.LEFT, padx=2)
        ttk.Button(presets_frame, text="本月", command=lambda: self._set_date_range("this_month")).pack(side=tk.LEFT, padx=2)
        
        # 报告类型
        type_frame = ttk.Frame(control_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="报告类型:").pack(side=tk.LEFT, padx=5)
        self.report_type = tk.StringVar(value="gdpr")
        ttk.Radiobutton(type_frame, text="GDPR", variable=self.report_type, value="gdpr").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="PIPL", variable=self.report_type, value="pipl").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="全部", variable=self.report_type, value="all").pack(side=tk.LEFT)
        
        # 报告格式
        format_frame = ttk.Frame(control_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT, padx=5)
        self.report_format = tk.StringVar(value="text")
        ttk.Radiobutton(format_frame, text="文本", variable=self.report_format, value="text").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="JSON", variable=self.report_format, value="json").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="CSV", variable=self.report_format, value="csv").pack(side=tk.LEFT)
        
        # 详细信息
        details_frame = ttk.Frame(control_frame)
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.include_details = tk.BooleanVar(value=False)
        ttk.Checkbutton(details_frame, text="包含详细信息", variable=self.include_details).pack(side=tk.LEFT, padx=5)
        
        # 操作按钮
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(buttons_frame, text="生成报告", command=self._generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="导出报告", command=self._export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="清空", command=self._clear_report).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建右侧报告显示区域
        report_frame = ttk.LabelFrame(main_frame, text="审计报告")
        report_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 报告文本区域
        self.report_text = tk.Text(report_frame, wrap=tk.WORD, width=80, height=30)
        report_scrollbar = ttk.Scrollbar(report_frame, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 设置初始状态
        self.current_report = None
        self._clear_report()
    
    def _set_default_dates(self):
        """设置默认日期"""
        today = datetime.date.today()
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, today.strftime("%Y-%m-%d"))
    
    def _set_date_range(self, preset: str):
        """
        设置日期范围
        
        Args:
            preset: 日期预设 ('today', 'yesterday', 'this_week', 'this_month')
        """
        today = datetime.date.today()
        
        if preset == "today":
            start_date = today
            end_date = today
        elif preset == "yesterday":
            start_date = today - datetime.timedelta(days=1)
            end_date = today - datetime.timedelta(days=1)
        elif preset == "this_week":
            # 获取本周的星期一
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = today
        elif preset == "this_month":
            # 获取本月第一天
            start_date = today.replace(day=1)
            end_date = today
        else:
            # 默认最近30天
            start_date = today - datetime.timedelta(days=30)
            end_date = today
        
        # 更新日期输入框
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, start_date.strftime("%Y-%m-%d"))
        
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end_date.strftime("%Y-%m-%d"))
    
    def _parse_date(self, date_str: str) -> datetime.date:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串，格式为 YYYY-MM-DD
            
        Returns:
            解析后的日期对象
            
        Raises:
            ValueError: 如果日期格式不正确
        """
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"无效的日期格式: {date_str}，请使用 YYYY-MM-DD 格式")
    
    def _generate_report(self):
        """生成审计报告"""
        # 获取日期范围
        try:
            start_date = self._parse_date(self.start_date_entry.get())
            end_date = self._parse_date(self.end_date_entry.get())
            
            # 如果开始日期晚于结束日期，交换它们
            if start_date > end_date:
                messagebox.showwarning("警告", "开始日期晚于结束日期，将交换这两个日期。")
                start_date, end_date = end_date, start_date
                
                # 更新日期输入框
                self.start_date_entry.delete(0, tk.END)
                self.start_date_entry.insert(0, start_date.strftime("%Y-%m-%d"))
                
                self.end_date_entry.delete(0, tk.END)
                self.end_date_entry.insert(0, end_date.strftime("%Y-%m-%d"))
                
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        
        # 获取报告类型和格式
        report_type = self.report_type.get()
        report_format = self.report_format.get()
        include_details = self.include_details.get()
        
        # 显示进度条
        self.progress.start()
        
        # 清空报告区域
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "正在生成报告，请稍候...\n")
        
        # 在后台线程中生成报告
        def generate_report_thread():
            try:
                report = generate_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    report_type=report_type,
                    output_format=report_format,
                    include_details=include_details
                )
                
                # 保存当前报告
                self.current_report = report
                
                # 在主线程中更新UI
                self.master.after(0, lambda: self._display_report(report))
                
            except Exception as e:
                # 在主线程中显示错误
                self.master.after(0, lambda: self._show_error(f"生成报告时出错: {str(e)}"))
                
            finally:
                # 在主线程中停止进度条
                self.master.after(0, self.progress.stop)
        
        # 启动后台线程
        threading.Thread(target=generate_report_thread, daemon=True).start()
    
    def _display_report(self, report):
        """
        显示报告
        
        Args:
            report: 报告内容（可能是字符串或字典）
        """
        # 清空报告区域
        self.report_text.delete(1.0, tk.END)
        
        # 如果报告是字符串（文本或CSV格式），直接显示
        if isinstance(report, str):
            self.report_text.insert(tk.END, report)
            return
            
        # 如果报告是字典（JSON格式），格式化显示
        if isinstance(report, dict):
            # 显示摘要
            summary = report.get("summary", {})
            self.report_text.insert(tk.END, "=== 审计报告摘要 ===\n\n")
            self.report_text.insert(tk.END, f"报告期间: {report.get('period', '')}\n")
            self.report_text.insert(tk.END, f"总操作数: {summary.get('total_operations', 0)}\n")
            self.report_text.insert(tk.END, f"安全事件数: {summary.get('security_incidents_count', 0)}\n")
            self.report_text.insert(tk.END, f"数据主体数: {summary.get('data_subjects_count', 0)}\n")
            self.report_text.insert(tk.END, f"合规状态: {'合规' if summary.get('compliant', False) else '不合规'}\n\n")
            
            # 显示操作统计
            operations = report.get("operations", {})
            if operations:
                self.report_text.insert(tk.END, "=== 操作统计 ===\n\n")
                for op_type, count in operations.items():
                    if op_type != "total":  # 跳过总数，已在摘要中显示
                        self.report_text.insert(tk.END, f"{op_type}: {count}\n")
                self.report_text.insert(tk.END, "\n")
            
            # 显示安全事件
            security_incidents = report.get("security_incidents", [])
            if security_incidents:
                self.report_text.insert(tk.END, "=== 安全事件 ===\n\n")
                for i, incident in enumerate(security_incidents, 1):
                    timestamp = incident.get('timestamp', '未知时间')
                    incident_type = incident.get('type', '未知类型')
                    description = incident.get('description', '无描述')
                    incident_str = f"{i}. [{timestamp}] {incident_type}: {description}\n"
                    self.report_text.insert(tk.END, incident_str)
                self.report_text.insert(tk.END, "\n")
            
            # 显示数据主体（脱敏）
            data_subjects = report.get("data_subjects", [])
            if data_subjects:
                self.report_text.insert(tk.END, "=== 数据主体 ===\n\n")
                for i, subject in enumerate(data_subjects, 1):
                    user_id = subject.get('user_id_hash', '未知')
                    ops_count = subject.get('operations_count', 0)
                    last_activity = subject.get('last_activity', '未知')
                    subject_str = f"{i}. ID: {user_id}, 操作数: {ops_count}, 最后活动: {last_activity}\n"
                    self.report_text.insert(tk.END, subject_str)
                self.report_text.insert(tk.END, "\n")
            
            # 显示报告指纹
            self.report_text.insert(tk.END, "=== 报告验证 ===\n\n")
            self.report_text.insert(tk.END, f"指纹: {report.get('fingerprint', '')}\n")
            self.report_text.insert(tk.END, f"签名: {report.get('signature', '')}\n")
            
            return
            
        # 如果报告是其他类型，显示错误
        self.report_text.insert(tk.END, f"不支持的报告类型: {type(report)}")
    
    def _export_report(self):
        """导出审计报告"""
        # 检查是否已生成报告
        if self.current_report is None:
            messagebox.showwarning("警告", "请先生成报告")
            return
            
        # 获取报告类型和格式
        report_type = self.report_type.get()
        report_format = self.report_format.get()
        
        # 确定默认文件扩展名
        if report_format == "json":
            file_ext = ".json"
            file_types = [("JSON文件", "*.json"), ("所有文件", "*.*")]
        elif report_format == "csv":
            file_ext = ".csv"
            file_types = [("CSV文件", "*.csv"), ("所有文件", "*.*")]
        else:
            file_ext = ".txt"
            file_types = [("文本文件", "*.txt"), ("所有文件", "*.*")]
        
        # 获取当前日期用于文件名
        today = datetime.date.today().strftime("%Y%m%d")
        
        # 获取导出文件路径
        output_file = filedialog.asksaveasfilename(
            title="导出审计报告",
            defaultextension=file_ext,
            filetypes=file_types,
            initialfile=f"audit_report_{report_type}_{today}{file_ext}"
        )
        
        if not output_file:
            return
            
        # 获取日期范围
        try:
            start_date = self._parse_date(self.start_date_entry.get())
            end_date = self._parse_date(self.end_date_entry.get())
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        
        # 显示进度条
        self.progress.start()
        
        # 在后台线程中导出报告
        def export_report_thread():
            try:
                success = export_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    output_file=output_file,
                    report_type=report_type,
                    output_format=report_format
                )
                
                # 在主线程中显示结果
                if success:
                    self.master.after(0, lambda: messagebox.showinfo("导出成功", f"报告已导出到: {output_file}"))
                else:
                    self.master.after(0, lambda: messagebox.showerror("导出失败", "导出报告时出错"))
                
            except Exception as e:
                # 在主线程中显示错误
                self.master.after(0, lambda: self._show_error(f"导出报告时出错: {str(e)}"))
                
            finally:
                # 在主线程中停止进度条
                self.master.after(0, self.progress.stop)
        
        # 启动后台线程
        threading.Thread(target=export_report_thread, daemon=True).start()
    
    def _clear_report(self):
        """清空报告"""
        self.report_text.delete(1.0, tk.END)
        self.current_report = None
        
        # 显示使用说明
        self.report_text.insert(tk.END, "=== 合规审计报告 ===\n\n")
        self.report_text.insert(tk.END, "该功能用于生成符合GDPR和个人信息保护法的合规审计报告。\n\n")
        self.report_text.insert(tk.END, "使用方法:\n")
        self.report_text.insert(tk.END, "1. 选择报告的日期范围\n")
        self.report_text.insert(tk.END, "2. 选择报告类型（GDPR、PIPL或全部）\n")
        self.report_text.insert(tk.END, "3. 选择输出格式（文本、JSON或CSV）\n")
        self.report_text.insert(tk.END, "4. 点击"生成报告"按钮\n")
        self.report_text.insert(tk.END, "5. 可以通过"导出报告"按钮将报告保存到文件\n\n")
        self.report_text.insert(tk.END, "报告中包含的内容：\n")
        self.report_text.insert(tk.END, "- 操作统计\n")
        self.report_text.insert(tk.END, "- 安全事件\n")
        self.report_text.insert(tk.END, "- 数据主体（脱敏）\n")
        self.report_text.insert(tk.END, "- 数据处理活动\n")
        self.report_text.insert(tk.END, "- 合规状态\n")
    
    def _show_error(self, message: str):
        """
        显示错误信息
        
        Args:
            message: 错误信息
        """
        messagebox.showerror("错误", message)
        self.progress.stop()
        
        # 在报告区域显示错误
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, f"错误: {message}\n")


def create_audit_report_panel(parent=None):
    """
    创建审计报告面板
    
    Args:
        parent: 父容器
        
    Returns:
        审计报告面板实例
    """
    return AuditReportPanel(parent)


if __name__ == "__main__":
    # 如果直接运行，创建一个独立窗口
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        root.geometry("1200x800")
        app = AuditReportPanel(root, root)
        root.mainloop()
    else:
        print("Tkinter不可用，无法显示审计报告面板") 