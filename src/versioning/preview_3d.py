#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
三维预览对比器

为版本管理系统提供三维可视化功能，直观展示和比较不同版本的脚本特征。
使用3D空间展示剧本版本的情感走向、场景转换和结构特点。
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.utils.log_handler import get_logger

# 设置日志
logger = get_logger("version_visualizer")

class TimelineVisualizer:
    """时间线可视化工具 - 创建3D视图比较不同版本"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        """
        初始化可视化器
        
        Args:
            width: 图表宽度
            height: 图表高度
        """
        self.width = width
        self.height = height
        self.color_map = px.colors.qualitative.Plotly
        
    def render_3d_comparison(self, versions: List[Dict[str, Any]]) -> str:
        """生成可旋转的三维场景对比视图
        
        Args:
            versions: 版本列表，每个版本包含scenes字段
            
        Returns:
            str: HTML字符串，可渲染为3D图表
        """
        # 创建3D图表
        fig = plt.figure(figsize=(12, 6))
        ax = fig.add_subplot(111, projection='3d')
        
        # 为每个版本绘制3D线图
        for i, v in enumerate(versions):
            if "scenes" not in v:
                logger.warning(f"版本 {i+1} 不包含场景信息，跳过")
                continue
                
            # 提取场景时间点和情感得分
            x = [s.get('start', i) for i, s in enumerate(v.get("scenes", []))]
            y = [s.get('emotion_score', 0) for s in v.get("scenes", [])]
            z = [i] * len(v.get("scenes", []))
            
            # 绘制3D线图
            ax.plot(x, y, z, label=f'Version {i+1}')
        
        # 设置轴标签
        ax.set_xlabel('Scene Timeline')
        ax.set_ylabel('Emotion Intensity')
        ax.set_zlabel('Version')
        
        # 添加图例
        ax.legend()
        
        # 转换为HTML
        from io import BytesIO
        import matplotlib.pyplot as plt
        
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # 嵌入HTML
        import base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        html = f'<img src="data:image/png;base64,{img_str}" />'
        
        plt.close()
        
        return html
    
    def render_plotly_3d_comparison(self, versions: List[Dict[str, Any]]) -> str:
        """使用Plotly生成交互式3D视图
        
        Args:
            versions: 版本列表，每个版本包含scenes字段
            
        Returns:
            str: HTML字符串，可交互式3D图表
        """
        # 创建一个3D散点图
        fig = go.Figure()
        
        for i, version in enumerate(versions):
            scenes = version.get("scenes", [])
            
            if not scenes:
                logger.warning(f"版本 {i+1} 不包含场景信息，跳过")
                continue
            
            # 提取场景信息作为坐标
            x = [s.get('start_time', i) for i, s in enumerate(scenes)]
            
            # 情感值 - Y轴
            y = [s.get('emotion_score', 0) for s in scenes]
            if all(y_val == 0 for y_val in y):
                y = [float(i)/len(scenes) for i in range(len(scenes))]  # 备用值
            
            # 版本索引作为Z轴
            z = [i] * len(scenes)
            
            # 提取场景文本
            text = [s.get('text', f'场景 {j+1}') for j, s in enumerate(scenes)]
            
            # 添加3D散点和线
            fig.add_trace(go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode='lines+markers',
                name=f'版本 {i+1}',
                text=text,
                hoverinfo='text',
                marker=dict(
                    size=5,
                    color=self.color_map[i % len(self.color_map)],
                    opacity=0.8
                ),
                line=dict(
                    color=self.color_map[i % len(self.color_map)],
                    width=3
                )
            ))
        
        # 自定义布局
        fig.update_layout(
            title="多版本对比 - 3D视图",
            scene=dict(
                xaxis_title="时间轴位置",
                yaxis_title="情感强度",
                zaxis_title="版本序号",
                aspectratio=dict(x=1.5, y=1, z=0.5),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            width=self.width,
            height=self.height,
            margin=dict(l=0, r=0, b=0, t=30)
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False)

    def render_emotion_flow(self, versions: List[Dict[str, Any]]) -> str:
        """渲染情感流动对比图
        
        Args:
            versions: 版本列表，每个版本包含scenes字段
            
        Returns:
            str: HTML字符串，情感流动交互图
        """
        # 创建子图
        fig = make_subplots(
            rows=len(versions), 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=[f"版本 {i+1}" for i in range(len(versions))]
        )
        
        # 为每个版本添加情感曲线
        for i, version in enumerate(versions):
            scenes = version.get("scenes", [])
            
            if not scenes:
                continue
                
            # 提取时间和情感数据
            x = [j for j in range(len(scenes))]
            y = [s.get('emotion_score', 0) for s in scenes]
            
            # 使用文本作为悬停信息
            hover_text = [s.get('text', f'场景 {j+1}') for j, s in enumerate(scenes)]
            
            # 添加折线图
            fig.add_trace(
                go.Scatter(
                    x=x, 
                    y=y,
                    mode='lines+markers',
                    name=f'版本 {i+1}',
                    text=hover_text,
                    hoverinfo='text+y',
                    line=dict(width=3, color=self.color_map[i % len(self.color_map)]),
                    fill='tozeroy'
                ),
                row=i+1, 
                col=1
            )
            
            # 添加零线
            fig.add_shape(
                type="line",
                x0=0,
                y0=0,
                x1=len(scenes)-1,
                y1=0,
                line=dict(color="gray", width=1, dash="dash"),
                row=i+1,
                col=1
            )
        
        # 自定义布局
        fig.update_layout(
            title="版本情感流动对比",
            height=200 * len(versions),
            width=self.width,
            showlegend=False,
            hovermode="closest"
        )
        
        # 更新Y轴范围，确保统一缩放
        max_abs_emotion = max([
            max([abs(s.get('emotion_score', 0)) for s in v.get("scenes", [])])
            for v in versions if v.get("scenes")
        ] or [1])
        
        for i in range(len(versions)):
            fig.update_yaxes(range=[-max_abs_emotion, max_abs_emotion], row=i+1, col=1)
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    def fig_to_html(self, fig: plt.Figure) -> str:
        """将Matplotlib图表转换为HTML
        
        Args:
            fig: Matplotlib图表
            
        Returns:
            str: HTML字符串
        """
        from io import BytesIO
        import base64
        
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # 转换为base64
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        html = f'<img src="data:image/png;base64,{img_str}" />'
        
        return html


class VersionPreviewGenerator:
    """版本预览生成器 - 为版本创建预览图和比较视图"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化版本预览生成器
        
        Args:
            cache_dir: 缓存目录，用于保存生成的图表
        """
        self.timeline_vis = TimelineVisualizer()
        
        # 缓存目录
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "cache", "previews"
            )
            
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def create_version_preview(self, version: Dict[str, Any]) -> str:
        """为单个版本创建预览图
        
        Args:
            version: 版本数据
            
        Returns:
            str: 预览图的HTML表示
        """
        scenes = version.get("scenes", [])
        if not scenes:
            logger.warning("无法生成预览：版本不包含场景数据")
            return "<p>无法生成预览：版本不包含场景数据</p>"
        
        # 创建预览图
        fig = plt.figure(figsize=(8, 4))
        
        # 添加情感曲线子图
        ax1 = fig.add_subplot(111)
        
        # 绘制情感曲线
        x = [i for i in range(len(scenes))]
        y = [s.get('emotion_score', 0) for s in scenes]
        
        ax1.plot(x, y, 'o-', linewidth=2)
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.7)
        
        # 设置标题和标签
        ax1.set_title('版本情感流动')
        ax1.set_xlabel('场景序号')
        ax1.set_ylabel('情感强度')
        
        # 添加网格
        ax1.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 转换为HTML
        html_preview = self.timeline_vis.fig_to_html(fig)
        plt.close(fig)
        
        return html_preview
    
    def compare_versions(self, 
                       versions: List[Dict[str, Any]], 
                       mode: str = '3d',
                       cache_id: Optional[str] = None) -> str:
        """比较多个版本并生成可视化
        
        Args:
            versions: 版本列表
            mode: 可视化模式，可选 '3d'、'emotion'、'all'
            cache_id: 缓存ID，可选
            
        Returns:
            str: HTML表示的比较视图
        """
        if not versions:
            return "<p>没有提供版本数据</p>"
            
        # 尝试从缓存加载
        if cache_id:
            cache_path = os.path.join(self.cache_dir, f"{cache_id}_{mode}.html")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.warning(f"从缓存加载预览失败: {str(e)}")
        
        # 根据模式生成不同的比较视图
        html_result = ""
        
        if mode in ['3d', 'all']:
            html_result += self.timeline_vis.render_plotly_3d_comparison(versions)
            
        if mode in ['emotion', 'all']:
            if html_result:
                html_result += "<hr>"
            html_result += self.timeline_vis.render_emotion_flow(versions)
            
        # 保存到缓存
        if cache_id:
            cache_path = os.path.join(self.cache_dir, f"{cache_id}_{mode}.html")
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(html_result)
            except Exception as e:
                logger.warning(f"保存预览到缓存失败: {str(e)}")
                
        return html_result
    
    def generate_diff_view(self, 
                       version1: Dict[str, Any], 
                       version2: Dict[str, Any]) -> str:
        """生成两个版本的差异视图
        
        Args:
            version1: 第一个版本
            version2: 第二个版本
            
        Returns:
            str: HTML表示的差异视图
        """
        if not version1.get("scenes") or not version2.get("scenes"):
            return "<p>版本数据不完整，无法生成差异视图</p>"
            
        # 提取场景数据
        scenes1 = version1.get("scenes", [])
        scenes2 = version2.get("scenes", [])
        
        # 创建新图表
        fig = make_subplots(
            rows=2, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=["版本1", "版本2"]
        )
        
        # 添加第一个版本的情感曲线
        x1 = [i for i in range(len(scenes1))]
        y1 = [s.get('emotion_score', 0) for s in scenes1]
        
        fig.add_trace(
            go.Scatter(
                x=x1, 
                y=y1,
                mode='lines+markers',
                name='版本1',
                line=dict(width=3, color='blue'),
                fill='tozeroy'
            ),
            row=1, 
            col=1
        )
        
        # 添加第二个版本的情感曲线
        x2 = [i for i in range(len(scenes2))]
        y2 = [s.get('emotion_score', 0) for s in scenes2]
        
        fig.add_trace(
            go.Scatter(
                x=x2, 
                y=y2,
                mode='lines+markers',
                name='版本2',
                line=dict(width=3, color='red'),
                fill='tozeroy'
            ),
            row=2, 
            col=1
        )
        
        # 添加零线
        for i in range(1, 3):
            fig.add_shape(
                type="line",
                x0=0,
                y0=0,
                x1=max(len(scenes1), len(scenes2))-1,
                y1=0,
                line=dict(color="gray", width=1, dash="dash"),
                row=i,
                col=1
            )
        
        # 设置布局
        fig.update_layout(
            title="版本差异对比",
            height=500,
            showlegend=True,
            hovermode="closest"
        )
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False)


# 便捷函数
def generate_3d_preview(versions: List[Dict[str, Any]]) -> str:
    """快捷函数：生成3D预览
    
    Args:
        versions: 版本列表
        
    Returns:
        str: HTML表示的3D预览
    """
    preview_gen = VersionPreviewGenerator()
    return preview_gen.compare_versions(versions, mode='3d')

def compare_version_emotions(versions: List[Dict[str, Any]]) -> str:
    """快捷函数：比较版本情感曲线
    
    Args:
        versions: 版本列表
        
    Returns:
        str: HTML表示的情感对比
    """
    preview_gen = VersionPreviewGenerator()
    return preview_gen.compare_versions(versions, mode='emotion')

def visualize_version_diff(version1: Dict[str, Any], version2: Dict[str, Any]) -> str:
    """快捷函数：可视化版本差异
    
    Args:
        version1: 第一个版本
        version2: 第二个版本
        
    Returns:
        str: HTML表示的差异视图
    """
    preview_gen = VersionPreviewGenerator()
    return preview_gen.generate_diff_view(version1, version2)


if __name__ == "__main__":
    # 简单测试
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试版本
    test_versions = [
        {
            "version_id": "v1",
            "scenes": [
                {"scene_id": "s1", "text": "场景1", "start_time": 0, "emotion_score": 0.2},
                {"scene_id": "s2", "text": "场景2", "start_time": 5, "emotion_score": 0.5},
                {"scene_id": "s3", "text": "场景3", "start_time": 10, "emotion_score": 0.8},
                {"scene_id": "s4", "text": "场景4", "start_time": 15, "emotion_score": 0.3},
                {"scene_id": "s5", "text": "场景5", "start_time": 20, "emotion_score": -0.2}
            ]
        },
        {
            "version_id": "v2",
            "scenes": [
                {"scene_id": "s1", "text": "场景1", "start_time": 0, "emotion_score": 0.1},
                {"scene_id": "s2", "text": "场景2", "start_time": 5, "emotion_score": -0.3},
                {"scene_id": "s3", "text": "场景3", "start_time": 10, "emotion_score": -0.7},
                {"scene_id": "s4", "text": "场景4", "start_time": 15, "emotion_score": -0.2},
                {"scene_id": "s5", "text": "场景5", "start_time": 20, "emotion_score": 0.4},
                {"scene_id": "s6", "text": "场景6", "start_time": 25, "emotion_score": 0.6}
            ]
        }
    ]
    
    # 创建预览生成器
    preview_gen = VersionPreviewGenerator()
    
    # 生成比较视图
    html_3d = preview_gen.compare_versions(test_versions, mode='3d')
    html_emotion = preview_gen.compare_versions(test_versions, mode='emotion')
    
    # 保存为HTML文件
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output", "previews")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "3d_preview_test.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>3D预览测试</title></head><body>")
        f.write(html_3d)
        f.write("</body></html>")
        
    with open(os.path.join(output_dir, "emotion_preview_test.html"), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>情感预览测试</title></head><body>")
        f.write(html_emotion)
        f.write("</body></html>")
        
    print(f"测试预览已保存到 {output_dir}") 