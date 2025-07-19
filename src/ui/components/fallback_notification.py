#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回退通知UI组件

当版本安全回退机制被激活时，向用户显示友好的通知。
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Callable

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

class FallbackNotification:
    """回退通知UI组件"""
    
    def __init__(self, parent, on_details_click: Optional[Callable] = None):
        """
        初始化回退通知组件
        
        Args:
            parent: 父级UI组件
            on_details_click: 点击详情按钮的回调函数
        """
        self.parent = parent
        self.on_details_click = on_details_click
        self.notification_frame = None
        self.issues = []
        self.target_version = ""
        
        # 样式设置
        self.style = ttk.Style()
        self.setup_styles()
    
    def setup_styles(self):
        """设置样式"""
        self.style.configure("Fallback.TFrame", background="#FFF3CD")
        self.style.configure("Fallback.TLabel", background="#FFF3CD", foreground="#856404")
        self.style.configure("Fallback.TButton", background="#FFF3CD", foreground="#856404")
    
    def show(self, target_version: str, issues: List[str] = None):
        """
        显示回退通知
        
        Args:
            target_version: 目标版本
            issues: 不兼容的问题列表
        """
        self.target_version = target_version
        self.issues = issues or []
        
        # 如果已有通知框，先销毁
        if self.notification_frame:
            self.notification_frame.destroy()
        
        # 创建通知框
        self.notification_frame = ttk.Frame(self.parent, style="Fallback.TFrame", padding=10)
        self.notification_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 图标和标题行
        title_frame = ttk.Frame(self.notification_frame, style="Fallback.TFrame")
        title_frame.pack(fill=tk.X)
        
        warning_label = ttk.Label(
            title_frame, 
            text="⚠️", 
            font=("TkDefaultFont", 14),
            style="Fallback.TLabel"
        )
        warning_label.pack(side=tk.LEFT, padx=(0, 5))
        
        title_label = ttk.Label(
            title_frame, 
            text=f"版本兼容性警告", 
            font=("TkDefaultFont", 11, "bold"),
            style="Fallback.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        close_button = ttk.Button(
            title_frame, 
            text="×", 
            width=2,
            command=self.hide,
            style="Fallback.TButton"
        )
        close_button.pack(side=tk.RIGHT)
        
        # 消息内容
        message = f"项目与版本 {self.target_version} 不兼容，已启用安全回退机制。系统已创建一个与目标版本兼容的基础项目。"
        message_label = ttk.Label(
            self.notification_frame, 
            text=message, 
            wraplength=500,
            justify=tk.LEFT,
            style="Fallback.TLabel"
        )
        message_label.pack(fill=tk.X, pady=(5, 0))
        
        # 如果有详细问题，添加详情按钮
        if self.issues and self.on_details_click:
            details_frame = ttk.Frame(self.notification_frame, style="Fallback.TFrame")
            details_frame.pack(fill=tk.X, pady=(5, 0))
            
            details_button = ttk.Button(
                details_frame, 
                text="查看详情", 
                command=self._on_details_click,
                style="Fallback.TButton"
            )
            details_button.pack(side=tk.RIGHT)
    
    def hide(self):
        """隐藏通知"""
        if self.notification_frame:
            self.notification_frame.destroy()
            self.notification_frame = None
    
    def _on_details_click(self):
        """点击详情按钮的处理函数"""
        if self.on_details_click:
            self.on_details_click(self.target_version, self.issues)

class FallbackDetailsDialog:
    """回退详情对话框"""
    
    def __init__(self, parent):
        """
        初始化回退详情对话框
        
        Args:
            parent: 父级UI组件
        """
        self.parent = parent
        self.dialog = None
    
    def show(self, target_version: str, issues: List[str]):
        """
        显示详情对话框
        
        Args:
            target_version: 目标版本
            issues: 不兼容的问题列表
        """
        # 如果已有对话框，先销毁
        if self.dialog:
            self.dialog.destroy()
        
        # 创建对话框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("版本兼容性详情")
        self.dialog.geometry("600x400")
        self.dialog.minsize(500, 300)
        
        # 标题
        title_label = ttk.Label(
            self.dialog, 
            text=f"版本 {target_version} 兼容性问题", 
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(10, 5), padx=10, anchor=tk.W)
        
        # 描述
        desc_label = ttk.Label(
            self.dialog, 
            text="以下功能或结构与目标版本不兼容，在回退版本中已被移除或修改:", 
            wraplength=580,
        )
        desc_label.pack(pady=(0, 10), padx=10, anchor=tk.W)
        
        # 创建问题列表框
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建列表框
        issues_list = tk.Listbox(
            frame, 
            yscrollcommand=scrollbar.set,
            font=("TkDefaultFont", 10),
            activestyle="none",
            bd=1,
            selectbackground="#e0e0e0",
            selectforeground="#000000"
        )
        issues_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=issues_list.yview)
        
        # 添加问题列表
        for i, issue in enumerate(issues):
            issues_list.insert(tk.END, f"{i+1}. {issue}")
        
        # 添加底部按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        close_button = ttk.Button(
            button_frame, 
            text="关闭", 
            command=self.hide
        )
        close_button.pack(side=tk.RIGHT)
    
    def hide(self):
        """隐藏对话框"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None

# 简单的演示程序
if __name__ == "__main__":
    root = tk.Tk()
    root.title("回退通知演示")
    root.geometry("800x600")
    
    def show_details(version, issues):
        details_dialog = FallbackDetailsDialog(root)
        details_dialog.show(version, issues)
    
    notification = FallbackNotification(root, on_details_click=show_details)
    
    # 创建示例问题列表
    example_issues = [
        "分辨率 3840x2160 超过版本2.0.0支持的最大分辨率 (1280x720)",
        "HDR功能在版本2.0.0中不支持",
        "嵌套序列功能在版本2.0.0中不支持",
        "3D效果在版本2.0.0中不支持",
        "音频效果在版本2.0.0中不支持",
        "关键帧动画在版本2.0.0中不支持"
    ]
    
    # 创建演示按钮
    demo_frame = ttk.Frame(root, padding=20)
    demo_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Button(
        demo_frame, 
        text="显示回退通知", 
        command=lambda: notification.show("2.0.0", example_issues)
    ).pack(pady=10)
    
    ttk.Button(
        demo_frame, 
        text="隐藏回退通知", 
        command=notification.hide
    ).pack(pady=10)
    
    ttk.Button(
        demo_frame, 
        text="直接显示详情对话框", 
        command=lambda: show_details("2.0.0", example_issues)
    ).pack(pady=10)
    
    root.mainloop() 