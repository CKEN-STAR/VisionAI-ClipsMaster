#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本建议面板

为主应用提供版本建议功能的集成面板。
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional, Callable

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

from src.ui.version_advisor import suggest_version_with_reason, get_version_features
from src.ui.components.version_suggestion_panel import VersionSuggestionPanel

class MainVersionSuggestionPanel(ttk.Frame):
    """版本建议主面板"""
    
    def __init__(self, parent, project_analyzer=None, **kwargs):
        """
        初始化版本建议面板
        
        Args:
            parent: 父级窗口
            project_analyzer: 项目分析器，用于获取当前项目规格
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.project_analyzer = project_analyzer
        
        # 默认视频规格
        self.current_video_spec = {
            "resolution": [1920, 1080],
            "hdr": False,
            "effects": False,
            "audio_effects": False,
            "multi_track": False
        }
        
        # 创建UI
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 标题标签
        self.title_label = ttk.Label(
            self, 
            text="版本兼容性", 
            font=("Helvetica", 12, "bold")
        )
        self.title_label.pack(pady=(10, 5), anchor="w")
        
        # 分割线
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", pady=5)
        
        # 按钮容器
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 版本建议按钮
        self.suggest_button = ttk.Button(
            button_frame,
            text="获取版本建议",
            command=self._show_version_suggestion
        )
        self.suggest_button.pack(side="left", padx=(0, 5))
        
        # 版本检测按钮
        self.check_button = ttk.Button(
            button_frame,
            text="检查兼容性",
            command=self._check_compatibility
        )
        self.check_button.pack(side="left")
        
        # 当前状态标签
        self.status_frame = ttk.LabelFrame(self, text="当前项目状态")
        self.status_frame.pack(fill="x", expand=False, padx=10, pady=10)
        
        # 状态信息
        status_grid = ttk.Frame(self.status_frame)
        status_grid.pack(fill="x", expand=True, padx=10, pady=5)
        
        # 分辨率
        ttk.Label(status_grid, text="分辨率:").grid(row=0, column=0, sticky="w", pady=2)
        self.resolution_label = ttk.Label(status_grid, text="1920 x 1080")
        self.resolution_label.grid(row=0, column=1, sticky="w", pady=2)
        
        # 当前版本
        ttk.Label(status_grid, text="当前版本:").grid(row=1, column=0, sticky="w", pady=2)
        self.version_label = ttk.Label(status_grid, text="3.0.0")
        self.version_label.grid(row=1, column=1, sticky="w", pady=2)
        
        # 多轨状态
        ttk.Label(status_grid, text="多轨编辑:").grid(row=2, column=0, sticky="w", pady=2)
        self.multi_track_label = ttk.Label(status_grid, text="否")
        self.multi_track_label.grid(row=2, column=1, sticky="w", pady=2)
        
        # 特效状态
        ttk.Label(status_grid, text="使用特效:").grid(row=3, column=0, sticky="w", pady=2)
        self.effects_label = ttk.Label(status_grid, text="否")
        self.effects_label.grid(row=3, column=1, sticky="w", pady=2)
        
        # 更新状态按钮
        self.update_button = ttk.Button(
            self.status_frame,
            text="刷新状态",
            command=self._update_status
        )
        self.update_button.pack(anchor="e", padx=10, pady=(0, 10))
    
    def _show_version_suggestion(self):
        """显示版本建议窗口"""
        # 分析当前项目，获取视频规格
        self._analyze_current_project()
        
        # 创建建议窗口
        suggestion_window = tk.Toplevel(self)
        suggestion_window.title("ClipsMaster 版本建议")
        suggestion_window.geometry("600x450")
        suggestion_window.resizable(True, True)
        
        # 添加版本建议面板
        suggestion_panel = VersionSuggestionPanel(
            suggestion_window,
            self.current_video_spec,
            self._on_version_selected
        )
        suggestion_panel.pack(fill="both", expand=True, padx=15, pady=15)
    
    def _check_compatibility(self):
        """检查项目与当前版本的兼容性"""
        # 分析当前项目
        self._analyze_current_project()
        
        # 获取当前版本
        current_version = "3.0.0"  # 实际项目中应从配置中获取
        
        # 获取版本功能
        features = get_version_features(current_version)
        
        # 检查兼容性问题
        issues = []
        
        # 检查分辨率
        max_width, max_height = features["max_resolution"]
        res_width, res_height = self.current_video_spec["resolution"]
        
        if res_width > max_width or res_height > max_height:
            issues.append(f"项目分辨率 {res_width}x{res_height} 超过当前版本支持的 {max_width}x{max_height}")
        
        # 检查HDR
        if self.current_video_spec["hdr"] and not features["supports_hdr"]:
            issues.append("项目使用了HDR，但当前版本不支持")
        
        # 检查特效
        if self.current_video_spec["effects"] and not features["supports_effects_layers"]:
            issues.append("项目使用了特效，但当前版本不支持")
        
        # 检查音频特效
        if self.current_video_spec["audio_effects"] and not features["supports_audio_effects"]:
            issues.append("项目使用了音频特效，但当前版本不支持")
        
        # 检查多轨
        if self.current_video_spec["multi_track"] and not features["supports_multi_track"]:
            issues.append("项目使用了多轨编辑，但当前版本不支持")
        
        # 显示结果
        if issues:
            message = "发现以下兼容性问题:\n\n" + "\n".join(f"• {issue}" for issue in issues)
            messagebox.warning("兼容性警告", message)
        else:
            messagebox.showinfo("兼容性检查", "项目与当前版本完全兼容。")
    
    def _on_version_selected(self, version):
        """版本选择回调"""
        features = get_version_features(version)
        messagebox.showinfo(
            "版本选择", 
            f"您已选择 {features['display_name']}。\n\n"
            f"此版本最大支持 {features['max_resolution'][0]}x{features['max_resolution'][1]} 分辨率。"
        )
    
    def _analyze_current_project(self):
        """分析当前项目获取视频规格"""
        # 如果有项目分析器，使用它
        if self.project_analyzer:
            self.current_video_spec = self.project_analyzer.get_project_specs()
            return
        
        # 否则使用示例数据
        # 检查当前项目是否有多轨道
        has_multiple_tracks = self._check_multiple_tracks()
        
        # 检查是否使用了特效
        has_effects = self._check_effects_used()
        
        # 检查是否使用了音频效果
        has_audio_effects = self._check_audio_effects()
        
        # 获取项目分辨率
        resolution = self._get_project_resolution()
        
        # 检查是否使用HDR
        has_hdr = self._check_hdr_used()
        
        # 更新视频规格
        self.current_video_spec = {
            "resolution": resolution,
            "hdr": has_hdr,
            "effects": has_effects,
            "audio_effects": has_audio_effects,
            "multi_track": has_multiple_tracks
        }
    
    def _check_multiple_tracks(self):
        """检查是否使用多轨道"""
        # 实际项目中，需要从项目数据中检查
        # 这里仅作示例返回
        return True
    
    def _check_effects_used(self):
        """检查是否使用了特效"""
        # 实际项目中，需要从项目数据中检查
        # 这里仅作示例返回
        return True
    
    def _check_audio_effects(self):
        """检查是否使用了音频效果"""
        # 实际项目中，需要从项目数据中检查
        # 这里仅作示例返回
        return False
    
    def _get_project_resolution(self):
        """获取项目分辨率"""
        # 实际项目中，需要从项目数据中获取
        # 这里仅作示例返回
        return [1920, 1080]
    
    def _check_hdr_used(self):
        """检查是否使用HDR"""
        # 实际项目中，需要从项目数据中检查
        # 这里仅作示例返回
        return False
    
    def _update_status(self):
        """更新当前状态显示"""
        # 分析当前项目
        self._analyze_current_project()
        
        # 更新UI标签
        resolution = self.current_video_spec["resolution"]
        self.resolution_label.config(text=f"{resolution[0]} x {resolution[1]}")
        
        self.multi_track_label.config(text="是" if self.current_video_spec["multi_track"] else "否")
        self.effects_label.config(text="是" if self.current_video_spec["effects"] else "否")
        
        # 获取当前版本（实际项目中应从配置中获取）
        current_version = "3.0.0"
        self.version_label.config(text=current_version)
        
        # 显示更新完成消息
        messagebox.showinfo("状态更新", "项目状态已刷新。")


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("版本建议面板测试")
    root.geometry("500x400")
    
    panel = MainVersionSuggestionPanel(root)
    panel.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop() 