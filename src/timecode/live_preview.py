#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时预览模块

此模块提供实时预览和可视化功能，用于：
1. 可视化多轨道时间轴对齐
2. 生成音视频轨道的波形图和时间线图
3. 提供交互式预览和调整功能
4. 支持HTML输出和基于Web的实时预览

主要用于在进行时间轴编辑时提供即时的视觉反馈。
"""

import os
import json
import logging
import tempfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import base64
from io import BytesIO

# 获取日志记录器
logger = logging.getLogger(__name__)

class PreviewGenerator:
    """预览生成器
    
    生成音视频轨道和时间线的实时可视化预览。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化预览生成器
        
        Args:
            config: 配置参数
        """
        # 默认配置
        self.default_config = {
            "width": 10,           # 图形宽度
            "height": 6,           # 图形高度
            "color_scheme": "tab10", # 颜色方案
            "emotion_scale": 10,   # 情感线宽度缩放
            "show_legends": True,  # 显示图例
            "font_size": 10,       # 字体大小
            "dpi": 100,            # 分辨率
            "output_format": "html" # 输出格式:html/png/svg
        }
        
        # 初始化配置
        self.config = self.default_config.copy()
        if config:
            self.config.update(config)
        
        # 设置颜色方案
        self.color_map = plt.get_cmap(self.config["color_scheme"])
        
        logger.info("预览生成器初始化完成")
    
    def generate_waveform(self, scenes: List[Dict[str, Any]]) -> str:
        """生成时间轴波形图
        
        将场景时间和情感强度可视化为波形图，支持情感波动展示
        
        Args:
            scenes: 场景列表，每个场景需包含 start, end, emotion_score 等属性
            
        Returns:
            HTML代码或图片路径
        """
        # 创建图形
        plt.figure(figsize=(self.config["width"], self.config["height"]))
        
        # 绘制每个场景
        for scene in scenes:
            # 获取场景时间范围和情感分数
            start = scene.get("start", 0)
            end = scene.get("end", 0)
            # 情感分数默认为0.5，范围0-1
            emotion_score = scene.get("emotion_score", 0.5)
            
            # 计算线宽，基于情感分数
            linewidth = max(1, emotion_score * self.config["emotion_scale"])
            
            # 绘制场景时间线，y轴设为0表示在底部
            plt.plot([start, end], [0, 0], 
                     linewidth=linewidth,
                     color=self._get_color(scene))
        
        # 设置图形样式
        plt.title("场景时间轴波形图", fontsize=self.config["font_size"] + 2)
        plt.xlabel("时间 (秒)", fontsize=self.config["font_size"])
        plt.ylabel("轨道", fontsize=self.config["font_size"])
        plt.grid(True, alpha=0.3)
        
        # 返回HTML或图片
        return self._plt_to_html(plt)
    
    def generate_track_view(self, tracks: Dict[str, Dict[str, Any]]) -> str:
        """生成多轨道视图
        
        可视化多个轨道的时间轴和相对位置
        
        Args:
            tracks: 轨道字典，格式为 {"track_id": track_data, ...}
                   track_data需包含 duration, type 等字段
            
        Returns:
            HTML代码或图片路径
        """
        # 确保有轨道数据
        if not tracks:
            logger.warning("没有轨道数据，无法生成预览")
            return ""
        
        # 创建图形
        plt.figure(figsize=(self.config["width"], self.config["height"]))
        
        # 计算轨道数
        track_count = len(tracks)
        
        # 为每个轨道分配一个Y轴位置
        y_positions = {}
        for i, track_id in enumerate(tracks.keys()):
            y_positions[track_id] = i
        
        # 绘制每个轨道
        for track_id, track_data in tracks.items():
            # 获取轨道信息
            duration = track_data.get("duration", 0)
            track_type = track_data.get("type", "unknown")
            y_pos = y_positions[track_id]
            
            # 设置轨道颜色
            if track_type == "video":
                color = "red"
            elif track_type == "audio":
                color = "blue"
            elif track_type == "subtitle":
                color = "green"
            else:
                color = "gray"
            
            # 绘制轨道时间线
            plt.plot([0, duration], [y_pos, y_pos], 
                     linewidth=3, 
                     color=color,
                     label=f"{track_id} ({track_type})")
            
            # 添加标签
            plt.text(duration + 0.5, y_pos, 
                     f"{track_id}: {duration:.2f}s", 
                     verticalalignment='center')
            
            # 如果轨道有场景数据，绘制场景
            if "scenes" in track_data and track_data["scenes"]:
                self._draw_scenes(track_data["scenes"], y_pos, color)
        
        # 设置图形样式
        plt.title("多轨道时间轴视图", fontsize=self.config["font_size"] + 2)
        plt.xlabel("时间 (秒)", fontsize=self.config["font_size"])
        plt.ylabel("轨道", fontsize=self.config["font_size"])
        plt.yticks(list(y_positions.values()), list(y_positions.keys()))
        plt.grid(True, alpha=0.3)
        
        # 显示图例
        if self.config["show_legends"]:
            plt.legend()
        
        plt.tight_layout()
        
        # 返回HTML或图片
        return self._plt_to_html(plt)
    
    def generate_alignment_preview(self, before_tracks: Dict[str, Dict[str, Any]], 
                                 after_tracks: Dict[str, Dict[str, Any]]) -> str:
        """生成对齐前后对比预览
        
        显示对齐操作前后的轨道变化
        
        Args:
            before_tracks: 对齐前的轨道数据
            after_tracks: 对齐后的轨道数据
            
        Returns:
            HTML代码或图片路径
        """
        # 创建图形
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.config["width"], self.config["height"]))
        
        # 获取所有轨道ID
        all_track_ids = set(list(before_tracks.keys()) + list(after_tracks.keys()))
        track_count = len(all_track_ids)
        
        # 为每个轨道分配一个Y轴位置
        y_positions = {track_id: i for i, track_id in enumerate(all_track_ids)}
        
        # 绘制对齐前的轨道
        ax1.set_title("对齐前", fontsize=self.config["font_size"] + 2)
        self._draw_tracks_on_axis(ax1, before_tracks, y_positions)
        
        # 绘制对齐后的轨道
        ax2.set_title("对齐后", fontsize=self.config["font_size"] + 2)
        self._draw_tracks_on_axis(ax2, after_tracks, y_positions)
        
        # 设置共享样式
        for ax in [ax1, ax2]:
            ax.set_xlabel("时间 (秒)", fontsize=self.config["font_size"])
            ax.set_ylabel("轨道", fontsize=self.config["font_size"])
            ax.set_yticks(list(y_positions.values()))
            ax.set_yticklabels(list(y_positions.keys()))
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 返回HTML或图片
        return self._plt_to_html(plt)
    
    def generate_interactive_preview(self, tracks: Dict[str, Dict[str, Any]]) -> str:
        """生成交互式预览HTML
        
        提供可交互的HTML预览，支持轨道调整和实时更新
        
        Args:
            tracks: 轨道字典
            
        Returns:
            HTML代码
        """
        # 生成静态预览作为基础
        static_preview = self.generate_track_view(tracks)
        
        # 构建交互式HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>实时轨道预览</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ display: flex; flex-direction: column; }}
                .preview {{ margin-bottom: 20px; }}
                .controls {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
                .track-control {{ 
                    border: 1px solid #ccc; 
                    padding: 10px; 
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                button {{ 
                    background-color: #4CAF50; 
                    color: white; 
                    padding: 8px 16px; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                }}
                button:hover {{ background-color: #45a049; }}
            </style>
        </head>
        <body>
            <h1>多轨道时间轴对齐预览</h1>
            
            <div class="container">
                <div class="preview">
                    {static_preview}
                </div>
                
                <div class="controls">
        """
        
        # 为每个轨道添加控制器
        for track_id, track_data in tracks.items():
            duration = track_data.get("duration", 0)
            track_type = track_data.get("type", "unknown")
            
            html += f"""
                    <div class="track-control">
                        <label>{track_id} ({track_type})</label>
                        <div>
                            <label>时长: <input type="number" id="duration_{track_id}" 
                                         value="{duration}" step="0.1" min="0"> 秒</label>
                        </div>
                        <div>
                            <label>对齐方式:
                                <select id="align_{track_id}">
                                    <option value="stretch">拉伸</option>
                                    <option value="shift">平移</option>
                                    <option value="crop">裁剪</option>
                                    <option value="pad">填充</option>
                                </select>
                            </label>
                        </div>
                    </div>
            """
        
        # 添加控制按钮
        html += """
                </div>
                
                <div>
                    <button id="apply_btn">应用更改</button>
                    <button id="reset_btn">重置</button>
                </div>
            </div>
            
            <script>
                // 这里添加JavaScript交互代码
                // 实际实现中，这需要与后端通信更新预览
                document.getElementById('apply_btn').addEventListener('click', function() {
                    alert('应用更改功能需要连接后端服务');
                });
                
                document.getElementById('reset_btn').addEventListener('click', function() {
                    alert('重置功能需要连接后端服务');
                });
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _draw_tracks_on_axis(self, ax, tracks: Dict[str, Dict[str, Any]], 
                            y_positions: Dict[str, int]) -> None:
        """在指定轴上绘制轨道
        
        内部辅助函数，在给定的轴上绘制轨道
        
        Args:
            ax: Matplotlib轴对象
            tracks: 轨道字典
            y_positions: 轨道ID到Y轴位置的映射
        """
        # 绘制每个轨道
        for track_id, track_data in tracks.items():
            if track_id not in y_positions:
                continue
                
            # 获取轨道信息
            duration = track_data.get("duration", 0)
            track_type = track_data.get("type", "unknown")
            y_pos = y_positions[track_id]
            
            # 设置轨道颜色
            if track_type == "video":
                color = "red"
            elif track_type == "audio":
                color = "blue"
            elif track_type == "subtitle":
                color = "green"
            else:
                color = "gray"
            
            # 绘制轨道时间线
            ax.plot([0, duration], [y_pos, y_pos], 
                   linewidth=3, 
                   color=color,
                   label=f"{track_id} ({track_type})")
            
            # 添加标签
            ax.text(duration + 0.5, y_pos, 
                   f"{duration:.2f}s", 
                   verticalalignment='center')
            
            # 如果轨道有场景数据，绘制场景
            if "scenes" in track_data and track_data["scenes"]:
                for scene in track_data["scenes"]:
                    start = scene.get("start_time", 0)
                    end = scene.get("end_time", 0)
                    ax.plot([start, end], [y_pos, y_pos], 
                           linewidth=6, alpha=0.5,
                           color=color)
    
    def _draw_scenes(self, scenes: List[Dict[str, Any]], y_pos: int, base_color: str) -> None:
        """绘制场景标记
        
        在轨道上绘制场景标记，以便区分不同场景
        
        Args:
            scenes: 场景列表
            y_pos: Y轴位置
            base_color: 基础颜色
        """
        for scene in scenes:
            start = scene.get("start_time", 0)
            end = scene.get("end_time", 0)
            
            # 绘制场景区块
            plt.plot([start, end], [y_pos, y_pos], 
                     linewidth=6, alpha=0.5,
                     color=base_color)
    
    def _get_color(self, scene: Dict[str, Any]) -> str:
        """获取场景颜色
        
        根据场景类型、情感和标签决定颜色
        
        Args:
            scene: 场景数据
            
        Returns:
            颜色代码
        """
        # 默认颜色
        color = "blue"
        
        # 根据情感决定颜色
        sentiment = scene.get("sentiment", "neutral")
        if isinstance(sentiment, str):
            if sentiment.lower() in ["positive", "积极"]:
                color = "green"
            elif sentiment.lower() in ["negative", "消极"]:
                color = "red"
            elif sentiment.lower() in ["neutral", "中性"]:
                color = "blue"
        elif isinstance(sentiment, dict):
            label = sentiment.get("label", "neutral").lower()
            if label in ["positive", "积极"]:
                color = "green"
            elif label in ["negative", "消极"]:
                color = "red"
        
        # 特殊场景类型处理
        if "scene_type" in scene:
            scene_type = scene["scene_type"].lower()
            if scene_type in ["climax", "高潮"]:
                return "purple"
            elif scene_type in ["conflict", "冲突"]:
                return "orange"
        
        # 根据标签修改颜色
        tags = scene.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        
        for tag in tags:
            if tag.lower() in ["important", "重要", "关键"]:
                return "darkred"
        
        return color
    
    def _plt_to_html(self, plt) -> str:
        """将Matplotlib图形转换为HTML格式
        
        Args:
            plt: Matplotlib绘图对象
            
        Returns:
            HTML代码
        """
        # 获取图形数据
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=self.config["dpi"])
        buf.seek(0)
        
        # 将图形转换为base64字符串
        img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        # 构建HTML代码
        html = f'<img src="data:image/png;base64,{img_data}" />'
        
        return html
        
    def wrap_html_content(self, html_content: str, title: str = "VisionAI-ClipsMaster 预览") -> str:
        """将HTML内容包装在完整的HTML页面中
        
        Args:
            html_content: 要包装的HTML内容
            title: 页面标题
            
        Returns:
            完整的HTML页面代码
        """
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #444;
                    margin-top: 20px;
                }}
                .container {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                .footer {{
                    margin-top: 30px;
                    color: #777;
                    font-size: 12px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <h1>VisionAI-ClipsMaster</h1>
            <div class="container">
                {html_content}
            </div>
            <div class="footer">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        
        return full_html

# 辅助函数
def generate_timeline_preview(scenes: List[Dict[str, Any]], 
                             output_format: str = "html") -> str:
    """快速生成时间轴预览
    
    快捷函数，生成场景时间轴预览
    
    Args:
        scenes: 场景列表
        output_format: 输出格式
        
    Returns:
        预览HTML或文件路径
    """
    preview_gen = PreviewGenerator({"output_format": output_format})
    return preview_gen.generate_waveform(scenes)


def generate_tracks_preview(tracks: Dict[str, Dict[str, Any]],
                          output_format: str = "html") -> str:
    """快速生成轨道预览
    
    快捷函数，生成多轨道预览
    
    Args:
        tracks: 轨道字典
        output_format: 输出格式
        
    Returns:
        预览HTML或文件路径
    """
    preview_gen = PreviewGenerator({"output_format": output_format})
    return preview_gen.generate_track_view(tracks)


def generate_alignment_comparison(before: Dict[str, Dict[str, Any]],
                                after: Dict[str, Dict[str, Any]],
                                output_format: str = "html") -> str:
    """快速生成对齐前后比较
    
    快捷函数，生成对齐前后比较视图
    
    Args:
        before: 对齐前轨道字典
        after: 对齐后轨道字典
        output_format: 输出格式
        
    Returns:
        预览HTML或文件路径
    """
    preview_gen = PreviewGenerator({"output_format": output_format})
    return preview_gen.generate_alignment_preview(before, after)


def generate_interactive_view(tracks: Dict[str, Dict[str, Any]]) -> str:
    """生成交互式预览
    
    快捷函数，生成交互式HTML预览
    
    Args:
        tracks: 轨道字典
        
    Returns:
        交互式HTML
    """
    preview_gen = PreviewGenerator({"output_format": "html"})
    return preview_gen.generate_interactive_preview(tracks)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_scenes = [
        {"start": 0, "end": 15, "emotion_score": 0.5, "sentiment": "neutral"},
        {"start": 15, "end": 30, "emotion_score": 0.8, "sentiment": "positive"},
        {"start": 30, "end": 50, "emotion_score": 0.3, "sentiment": "negative"},
        {"start": 50, "end": 75, "emotion_score": 0.9, "scene_type": "climax"}
    ]
    
    # 测试轨道
    test_tracks = {
        "main_video": {
            "type": "video",
            "duration": 75.0,
            "scenes": [
                {"start_time": 0, "end_time": 25},
                {"start_time": 25, "end_time": 50},
                {"start_time": 50, "end_time": 75}
            ]
        },
        "main_audio": {
            "type": "audio",
            "duration": 80.0
        },
        "subtitle": {
            "type": "subtitle",
            "duration": 70.0
        }
    }
    
    # 对齐后轨道
    aligned_tracks = {
        "main_video": {
            "type": "video",
            "duration": 80.0,
            "scenes": [
                {"start_time": 0, "end_time": 26.7},
                {"start_time": 26.7, "end_time": 53.3},
                {"start_time": 53.3, "end_time": 80.0}
            ]
        },
        "main_audio": {
            "type": "audio",
            "duration": 80.0
        },
        "subtitle": {
            "type": "subtitle",
            "duration": 80.0
        }
    }
    
    # 生成预览
    preview_gen = PreviewGenerator()
    
    # 波形图
    waveform = preview_gen.generate_waveform(test_scenes)
    
    # 保存为临时HTML文件
    with open("temp_waveform.html", "w", encoding="utf-8") as f:
        f.write(f"<html><body>{waveform}</body></html>")
    
    # 轨道视图
    tracks_view = preview_gen.generate_track_view(test_tracks)
    
    # 保存为临时HTML文件
    with open("temp_tracks.html", "w", encoding="utf-8") as f:
        f.write(f"<html><body>{tracks_view}</body></html>")
    
    # 对齐前后比较
    alignment_preview = preview_gen.generate_alignment_preview(test_tracks, aligned_tracks)
    
    # 保存为临时HTML文件
    with open("temp_alignment.html", "w", encoding="utf-8") as f:
        f.write(f"<html><body>{alignment_preview}</body></html>")
    
    # 交互式预览
    interactive = preview_gen.generate_interactive_preview(test_tracks)
    
    # 保存为临时HTML文件
    with open("temp_interactive.html", "w", encoding="utf-8") as f:
        f.write(interactive)
    
    print("预览生成器测试完成")
 