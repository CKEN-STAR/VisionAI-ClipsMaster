#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本建议面板组件

该组件用于在UI中展示版本建议信息，帮助用户选择适合的版本。
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Dict, Any, List, Callable, Optional

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ''))
sys.path.insert(0, root_dir)

from src.ui.version_advisor import (
    suggest_version_with_reason,
    get_version_features
)

class VersionSuggestionPanel(ttk.Frame):
    """版本建议面板组件"""
    
    def __init__(self, parent, video_spec: Dict[str, Any] = None, callback: Optional[Callable] = None, **kwargs):
        """
        初始化版本建议面板
        
        Args:
            parent: 父级窗口
            video_spec: 视频规格信息
            callback: 版本选择回调函数
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.video_spec = video_spec or {}
        self.callback = callback
        
        # 创建UI组件
        self._create_widgets()
        
        # 更新版本建议
        self.update_suggestion(self.video_spec)
    
    def _create_widgets(self):
        """创建UI组件"""
        # 标题标签
        self.title_label = ttk.Label(self, text="版本建议", font=("Helvetica", 12, "bold"))
        self.title_label.pack(pady=(10, 5), anchor="w")
        
        # 分割线
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", pady=5)
        
        # 版本信息框
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 版本标签
        self.version_label = ttk.Label(info_frame, text="推荐版本: ", font=("Helvetica", 10, "bold"))
        self.version_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.version_value = ttk.Label(info_frame, text="加载中...", font=("Helvetica", 10))
        self.version_value.grid(row=0, column=1, sticky="w", pady=5)
        
        # 原因标签
        reasons_label = ttk.Label(info_frame, text="推荐原因:", font=("Helvetica", 10, "bold"))
        reasons_label.grid(row=1, column=0, sticky="nw", pady=5)
        
        # 原因列表框
        self.reasons_frame = ttk.Frame(info_frame)
        self.reasons_frame.grid(row=1, column=1, sticky="w", pady=5)
        
        # 功能标签
        features_label = ttk.Label(info_frame, text="版本功能:", font=("Helvetica", 10, "bold"))
        features_label.grid(row=2, column=0, sticky="nw", pady=5)
        
        # 功能列表框
        self.features_frame = ttk.Frame(info_frame)
        self.features_frame.grid(row=2, column=1, sticky="w", pady=5)
        
        # 选择按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.select_button = ttk.Button(button_frame, text="选择此版本", command=self._on_select)
        self.select_button.pack(side="right")
        
        self.more_info_button = ttk.Button(button_frame, text="更多信息", command=self._show_more_info)
        self.more_info_button.pack(side="right", padx=5)
    
    def update_suggestion(self, video_spec: Dict[str, Any]):
        """
        更新版本建议
        
        Args:
            video_spec: 视频规格
        """
        self.video_spec = video_spec
        
        # 获取版本建议
        version, reasons = suggest_version_with_reason(video_spec)
        self.suggested_version = version
        
        # 获取版本功能
        features = get_version_features(version)
        
        # 更新UI
        self.version_value.config(text=features["display_name"])
        
        # 清除原有内容
        for widget in self.reasons_frame.winfo_children():
            widget.destroy()
            
        for widget in self.features_frame.winfo_children():
            widget.destroy()
        
        # 添加原因列表
        for i, reason in enumerate(reasons):
            reason_label = ttk.Label(self.reasons_frame, text=f"• {reason}", wraplength=350)
            reason_label.grid(row=i, column=0, sticky="w", pady=2)
        
        # 添加功能列表
        feature_texts = []
        
        # 添加分辨率
        max_width, max_height = features["max_resolution"]
        feature_texts.append(f"最大分辨率: {max_width}x{max_height}")
        
        # 添加其他功能
        if features["supports_hdr"]:
            feature_texts.append("支持HDR")
            
        if features["supports_nested_sequences"]:
            feature_texts.append("支持嵌套序列")
            
        if features["supports_effects_layers"]:
            feature_texts.append("支持效果层")
            
        if features["supports_keyframes"]:
            feature_texts.append("支持关键帧")
            
        if features["supports_3d_effects"]:
            feature_texts.append("支持3D效果")
            
        if features["supports_color_grading"]:
            feature_texts.append("支持色彩分级")
            
        if features["supports_audio_effects"]:
            feature_texts.append("支持音频效果")
            
        if features["supports_multi_track"]:
            feature_texts.append("支持多轨道编辑")
        
        # 添加到UI
        for i, feature_text in enumerate(feature_texts):
            feature_label = ttk.Label(self.features_frame, text=f"• {feature_text}")
            feature_label.grid(row=i, column=0, sticky="w", pady=2)
    
    def _on_select(self):
        """选择按钮点击事件"""
        if self.callback:
            self.callback(self.suggested_version)
    
    def _show_more_info(self):
        """显示更多信息"""
        # 创建新窗口
        info_window = tk.Toplevel(self)
        info_window.title("版本详细信息")
        info_window.geometry("500x400")
        info_window.resizable(True, True)
        
        # 添加版本比较表格
        frame = ttk.Frame(info_window, padding=10)
        frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = ttk.Label(frame, text="版本功能比较", font=("Helvetica", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建表格
        columns = ("功能", "基础版 (2.0.0)", "标准版 (2.5.0)", "高级版 (2.9.5)", "专业版 (3.0.0)")
        
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        tree.pack(fill="both", expand=True)
        
        # 设置列宽
        tree.column("功能", width=150, anchor="w")
        tree.column("基础版 (2.0.0)", width=100, anchor="center")
        tree.column("标准版 (2.5.0)", width=100, anchor="center")
        tree.column("高级版 (2.9.5)", width=100, anchor="center")
        tree.column("专业版 (3.0.0)", width=100, anchor="center")
        
        # 添加表头
        for col in columns:
            tree.heading(col, text=col)
        
        # 表格数据
        features_data = [
            ("最大分辨率", "720p", "1080p", "1080p", "4K"),
            ("HDR支持", "✗", "✗", "✗", "✓"),
            ("嵌套序列", "✗", "✗", "✗", "✓"),
            ("效果层", "✗", "✗", "✓", "✓"),
            ("关键帧", "✗", "✗", "✓", "✓"),
            ("3D效果", "✗", "✗", "✗", "✓"),
            ("色彩分级", "✗", "✗", "✓", "✓"),
            ("音频效果", "✗", "✗", "✓", "✓"),
            ("多轨道编辑", "✗", "✓", "✓", "✓"),
        ]
        
        # 添加数据到表格
        for row_data in features_data:
            tree.insert("", "end", values=row_data)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # 强调推荐版本
        highlight_version = f"{get_version_features(self.suggested_version)['display_name']}"
        
        # 提示标签
        if highlight_version:
            highlight_label = ttk.Label(
                frame, 
                text=f"推荐版本: {highlight_version}",
                font=("Helvetica", 10, "bold")
            )
            highlight_label.pack(pady=10)
        
        # 关闭按钮
        close_button = ttk.Button(frame, text="关闭", command=info_window.destroy)
        close_button.pack(pady=10)


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("版本建议面板测试")
    root.geometry("500x500")
    
    def version_selected(version):
        print(f"选择的版本: {version}")
    
    # 测试视频规格
    test_spec = {
        "resolution": [3840, 2160],
        "hdr": True,
        "effects": True,
        "audio_effects": True,
        "multi_track": True
    }
    
    panel = VersionSuggestionPanel(root, test_spec, version_selected)
    panel.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop() 