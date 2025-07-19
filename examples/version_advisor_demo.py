#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本建议演示程序

展示如何基于视频规格推荐最适合的ClipsMaster版本。
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from PIL import Image, ImageTk
import threading

# 添加项目根目录到系统路径
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ''))
sys.path.insert(0, root_dir)

try:
    from src.ui.version_advisor import suggest_version_with_reason, get_version_features
    from src.ui.components.version_suggestion_panel import VersionSuggestionPanel
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

class VersionAdvisorDemo(tk.Tk):
    """版本建议演示应用"""
    
    def __init__(self):
        super().__init__()
        self.title("ClipsMaster 版本建议")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # 设置应用样式
        self.style = ttk.Style()
        self.style.theme_use("clam")  # 使用clam主题
        
        # 设置颜色
        bg_color = "#f5f5f5"
        self.configure(bg=bg_color)
        
        # 配置样式
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, font=("Helvetica", 10))
        self.style.configure("TButton", font=("Helvetica", 10))
        self.style.configure("Header.TLabel", background=bg_color, font=("Helvetica", 12, "bold"))
        
        # 当前视频规格
        self.video_spec = {
            "resolution": [1920, 1080],
            "hdr": False,
            "effects": False,
            "audio_effects": False,
            "multi_track": False
        }
        
        # 创建主界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="ClipsMaster 版本建议", 
            font=("Helvetica", 16, "bold"),
            style="Header.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # 创建两列布局
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # 左侧：规格选择面板
        spec_frame = ttk.LabelFrame(content_frame, text="视频规格")
        spec_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 规格选择控件
        self._create_spec_controls(spec_frame)
        
        # 右侧：版本建议面板
        advice_frame = ttk.LabelFrame(content_frame, text="版本建议")
        advice_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # 版本建议面板
        self.version_panel = VersionSuggestionPanel(
            advice_frame, 
            self.video_spec, 
            self._on_version_selected
        )
        self.version_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        load_button = ttk.Button(button_frame, text="导入视频规格", command=self._load_spec)
        load_button.pack(side="left")
        
        save_button = ttk.Button(button_frame, text="保存视频规格", command=self._save_spec)
        save_button.pack(side="left", padx=5)
        
        exit_button = ttk.Button(button_frame, text="退出", command=self.quit)
        exit_button.pack(side="right")
        
    def _create_spec_controls(self, parent):
        """创建规格选择控件"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 分辨率选择
        res_label = ttk.Label(controls_frame, text="分辨率:")
        res_label.grid(row=0, column=0, sticky="w", pady=5)
        
        res_options = ["1280 x 720 (720p)", "1920 x 1080 (1080p)", "3840 x 2160 (4K)"]
        self.res_var = tk.StringVar(value=res_options[1])  # 默认选择1080p
        
        res_combo = ttk.Combobox(controls_frame, textvariable=self.res_var, values=res_options, state="readonly")
        res_combo.grid(row=0, column=1, sticky="w", pady=5)
        res_combo.bind("<<ComboboxSelected>>", self._update_spec)
        
        # HDR 支持
        self.hdr_var = tk.BooleanVar(value=False)
        hdr_check = ttk.Checkbutton(
            controls_frame, 
            text="支持HDR", 
            variable=self.hdr_var,
            command=self._update_spec
        )
        hdr_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # 特效选项
        self.effects_var = tk.BooleanVar(value=False)
        effects_check = ttk.Checkbutton(
            controls_frame, 
            text="使用视频特效", 
            variable=self.effects_var,
            command=self._update_spec
        )
        effects_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        # 音频效果
        self.audio_effects_var = tk.BooleanVar(value=False)
        audio_effects_check = ttk.Checkbutton(
            controls_frame, 
            text="使用音频效果", 
            variable=self.audio_effects_var,
            command=self._update_spec
        )
        audio_effects_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # 多轨编辑
        self.multi_track_var = tk.BooleanVar(value=False)
        multi_track_check = ttk.Checkbutton(
            controls_frame, 
            text="使用多轨编辑", 
            variable=self.multi_track_var,
            command=self._update_spec
        )
        multi_track_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # 分割线
        separator = ttk.Separator(controls_frame, orient="horizontal")
        separator.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        # 预设按钮
        presets_label = ttk.Label(controls_frame, text="快速预设:")
        presets_label.grid(row=6, column=0, sticky="w", pady=5)
        
        presets_frame = ttk.Frame(controls_frame)
        presets_frame.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)
        
        # 基础编辑预设
        basic_button = ttk.Button(
            presets_frame, 
            text="基础编辑", 
            command=lambda: self._load_preset("basic")
        )
        basic_button.pack(side="left", padx=(0, 5))
        
        # 影视制作预设
        film_button = ttk.Button(
            presets_frame, 
            text="影视制作", 
            command=lambda: self._load_preset("film")
        )
        film_button.pack(side="left", padx=5)
        
        # 专业制作预设
        pro_button = ttk.Button(
            presets_frame, 
            text="专业制作", 
            command=lambda: self._load_preset("pro")
        )
        pro_button.pack(side="left", padx=5)
        
        # 更新按钮
        update_button = ttk.Button(
            controls_frame,
            text="更新建议",
            command=self._update_suggestion
        )
        update_button.grid(row=8, column=0, columnspan=2, sticky="e", pady=10)
    
    def _update_spec(self, event=None):
        """更新视频规格"""
        # 解析分辨率
        res_str = self.res_var.get()
        if "720p" in res_str:
            resolution = [1280, 720]
        elif "4K" in res_str:
            resolution = [3840, 2160]
        else:  # 默认1080p
            resolution = [1920, 1080]
        
        # 更新视频规格
        self.video_spec = {
            "resolution": resolution,
            "hdr": self.hdr_var.get(),
            "effects": self.effects_var.get(),
            "audio_effects": self.audio_effects_var.get(),
            "multi_track": self.multi_track_var.get()
        }
    
    def _update_suggestion(self):
        """更新版本建议"""
        self._update_spec()
        self.version_panel.update_suggestion(self.video_spec)
    
    def _load_preset(self, preset_type):
        """加载预设"""
        if preset_type == "basic":
            # 基础编辑预设
            self.res_var.set("1280 x 720 (720p)")
            self.hdr_var.set(False)
            self.effects_var.set(False)
            self.audio_effects_var.set(False)
            self.multi_track_var.set(False)
        elif preset_type == "film":
            # 影视制作预设
            self.res_var.set("1920 x 1080 (1080p)")
            self.hdr_var.set(False)
            self.effects_var.set(True)
            self.audio_effects_var.set(True)
            self.multi_track_var.set(True)
        elif preset_type == "pro":
            # 专业制作预设
            self.res_var.set("3840 x 2160 (4K)")
            self.hdr_var.set(True)
            self.effects_var.set(True)
            self.audio_effects_var.set(True)
            self.multi_track_var.set(True)
        
        # 更新建议
        self._update_suggestion()
    
    def _load_spec(self):
        """从文件导入视频规格"""
        file_path = filedialog.askopenfilename(
            title="选择视频规格文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    spec = json.load(f)
                
                # 更新UI和规格
                self._apply_spec(spec)
                self._update_suggestion()
                
                messagebox.showinfo("成功", "已成功导入视频规格")
            except Exception as e:
                messagebox.showerror("错误", f"导入视频规格失败: {str(e)}")
    
    def _save_spec(self):
        """保存视频规格到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存视频规格",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                # 确保规格是最新的
                self._update_spec()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.video_spec, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("成功", "已成功保存视频规格")
            except Exception as e:
                messagebox.showerror("错误", f"保存视频规格失败: {str(e)}")
    
    def _apply_spec(self, spec):
        """应用视频规格到UI"""
        # 设置分辨率
        resolution = spec.get('resolution', [1920, 1080])
        if isinstance(resolution, list) and len(resolution) >= 2:
            width, height = resolution[0], resolution[1]
            
            if width <= 1280 and height <= 720:
                self.res_var.set("1280 x 720 (720p)")
            elif width <= 1920 and height <= 1080:
                self.res_var.set("1920 x 1080 (1080p)")
            else:
                self.res_var.set("3840 x 2160 (4K)")
        
        # 设置其他选项
        self.hdr_var.set(spec.get('hdr', False))
        self.effects_var.set(spec.get('effects', False))
        self.audio_effects_var.set(spec.get('audio_effects', False))
        self.multi_track_var.set(spec.get('multi_track', False))
        
        # 更新规格
        self._update_spec()
    
    def _on_version_selected(self, version):
        """版本选择回调"""
        features = get_version_features(version)
        messagebox.showinfo(
            "版本选择", 
            f"您已选择 {features['display_name']}。\n\n"
            f"此版本最大支持 {features['max_resolution'][0]}x{features['max_resolution'][1]} 分辨率。"
        )


def main():
    """主函数"""
    app = VersionAdvisorDemo()
    app.mainloop()


if __name__ == "__main__":
    main() 