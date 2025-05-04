#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感强度图谱可视化

提供情感曲线、情感分布热力图等多种可视化功能。
支持输出为图片、HTML页面或交互式图表。
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from typing import List, Dict, Any, Optional, Tuple, Union
from loguru import logger

# 颜色映射配置
EMOTION_COLORMAP = {
    "positive": "#1E88E5",  # 积极情感 - 蓝色
    "negative": "#E53935",  # 消极情感 - 红色
    "neutral": "#7CB342",   # 中性情感 - 绿色
    "surprise": "#FFC107",  # 惊奇情感 - 黄色
    "background": "#F5F5F5" # 背景色 - 灰白色
}

class EmotionVisualizer:
    """情感图谱可视化工具"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化可视化器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def plot_intensity_curve(self, 
                           curve_data: List[Dict[str, Any]], 
                           title: str = "情感强度曲线",
                           highlight_extremes: bool = True,
                           show_fig: bool = True,
                           save_path: Optional[str] = None) -> Optional[str]:
        """
        绘制情感强度曲线图
        
        Args:
            curve_data: 曲线数据点列表
            title: 图表标题
            highlight_extremes: 是否突出显示极值点
            show_fig: 是否显示图表
            save_path: 保存路径
            
        Returns:
            保存的文件路径或None
        """
        if not curve_data:
            logger.warning("曲线数据为空，无法绘制图表")
            return None
        
        # 提取数据
        x = list(range(len(curve_data)))
        peak_values = [point["peak_value"] for point in curve_data]
        
        # 创建画布
        plt.figure(figsize=(12, 7))
        
        # 绘制基础曲线
        plt.plot(x, peak_values, 'o-', linewidth=2.5, markersize=8, 
                 color=EMOTION_COLORMAP["positive"], label="情感强度")
        
        # 添加平滑曲线
        if len(curve_data) > 3:
            # 使用三次样条插值创建更平滑的曲线
            try:
                from scipy.interpolate import make_interp_spline
                
                x_smooth = np.linspace(0, len(curve_data) - 1, 100)
                spl = make_interp_spline(x, peak_values, k=3)
                y_smooth = spl(x_smooth)
                plt.plot(x_smooth, y_smooth, '-', linewidth=1.5, alpha=0.5, 
                         color=EMOTION_COLORMAP["positive"], label="平滑曲线")
            except ImportError:
                logger.debug("scipy不可用，跳过平滑曲线绘制")
            except Exception as e:
                logger.debug(f"平滑曲线绘制失败: {e}")
        
        # 高亮显示极值点
        if highlight_extremes:
            # 峰值点
            peaks = [(i, point["peak_value"]) for i, point in enumerate(curve_data) 
                    if point.get("is_peak", False)]
            
            if peaks:
                peak_x, peak_y = zip(*peaks)
                plt.plot(peak_x, peak_y, 'o', markersize=10, color='red', label="情感峰值")
            
            # 低谷点
            valleys = [(i, point["peak_value"]) for i, point in enumerate(curve_data) 
                      if point.get("is_valley", False)]
            
            if valleys:
                valley_x, valley_y = zip(*valleys)
                plt.plot(valley_x, valley_y, 'o', markersize=10, color='blue', label="情感低谷")
            
            # 全局极值
            global_peak = [(i, point["peak_value"]) for i, point in enumerate(curve_data) 
                          if point.get("is_global_peak", False)]
            if global_peak:
                gpeak_x, gpeak_y = zip(*global_peak)
                plt.plot(gpeak_x, gpeak_y, '*', markersize=15, color='orange', label="全局峰值")
        
        # 装饰图表
        plt.title(title, fontsize=16)
        plt.xlabel("场景序号", fontsize=14)
        plt.ylabel("情感强度值", fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.ylim(-0.05, 1.05)
        
        # 添加轻微的填充色
        plt.fill_between(x, peak_values, 0, alpha=0.15, color=EMOTION_COLORMAP["positive"])
        
        # 添加场景标签
        if len(curve_data) <= 20:  # 仅在点数较少时添加标签
            scene_labels = [f"{i+1}" for i in range(len(curve_data))]
            plt.xticks(x, scene_labels)
        
        plt.legend()
        plt.tight_layout()
        
        # 保存图表
        saved_path = None
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            saved_path = save_path
            logger.info(f"情感强度曲线图已保存至: {save_path}")
        elif self.output_dir:
            saved_path = os.path.join(self.output_dir, 'emotion_intensity_curve.png')
            plt.savefig(saved_path, dpi=300, bbox_inches='tight')
            logger.info(f"情感强度曲线图已保存至: {saved_path}")
        
        # 显示图表
        if show_fig:
            plt.show()
        else:
            plt.close()
        
        return saved_path
    
    def create_intensity_heatmap(self, 
                               curve_data: List[Dict[str, Any]], 
                               title: str = "情感强度热力图",
                               show_fig: bool = True,
                               save_path: Optional[str] = None) -> Optional[str]:
        """
        创建情感强度热力图
        
        Args:
            curve_data: 曲线数据点列表
            title: 图表标题
            show_fig: 是否显示图表
            save_path: 保存路径
            
        Returns:
            保存的文件路径或None
        """
        if not curve_data:
            logger.warning("曲线数据为空，无法绘制热力图")
            return None
        
        # 提取数据
        scene_ids = [point.get("scene_id", f"场景{i+1}") for i, point in enumerate(curve_data)]
        intensity_values = [point["peak_value"] for point in curve_data]
        
        # 创建热力图数据结构
        data = np.array(intensity_values).reshape(1, -1)
        
        # 创建画布
        plt.figure(figsize=(12, 3))
        
        # 创建热力图
        cmap = plt.cm.get_cmap("RdYlBu_r")
        im = plt.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=1)
        
        # 添加颜色条
        cbar = plt.colorbar(im, orientation='vertical', pad=0.01)
        cbar.set_label('情感强度', fontsize=12)
        
        # 装饰图表
        plt.title(title, fontsize=16)
        plt.yticks([])  # 隐藏y轴刻度
        
        # 添加场景标签
        if len(curve_data) <= 20:  # 仅在点数较少时添加所有标签
            plt.xticks(range(len(scene_ids)), scene_ids, rotation=45, ha='right')
        else:
            # 仅显示部分标签
            step = max(1, len(curve_data) // 10)
            indices = list(range(0, len(curve_data), step))
            if len(curve_data) - 1 not in indices:
                indices.append(len(curve_data) - 1)
            labels = [scene_ids[i] for i in indices]
            plt.xticks(indices, labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # 保存图表
        saved_path = None
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            saved_path = save_path
            logger.info(f"情感强度热力图已保存至: {save_path}")
        elif self.output_dir:
            saved_path = os.path.join(self.output_dir, 'emotion_intensity_heatmap.png')
            plt.savefig(saved_path, dpi=300, bbox_inches='tight')
            logger.info(f"情感强度热力图已保存至: {saved_path}")
        
        # 显示图表
        if show_fig:
            plt.show()
        else:
            plt.close()
        
        return saved_path
    
    def export_interactive_chart(self, 
                               curve_data: List[Dict[str, Any]], 
                               output_path: Optional[str] = None) -> Optional[str]:
        """
        导出交互式HTML图表
        
        Args:
            curve_data: 曲线数据点列表
            output_path: 输出HTML文件路径
            
        Returns:
            保存的文件路径或None
        """
        if not curve_data:
            logger.warning("曲线数据为空，无法创建交互式图表")
            return None
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            logger.warning("plotly库不可用，无法创建交互式图表")
            return None
        
        # 提取数据
        x = list(range(len(curve_data)))
        peak_values = [point["peak_value"] for point in curve_data]
        
        # 提取文本以显示在悬停信息中
        hover_texts = []
        for point in curve_data:
            text = point.get("raw_text", "")
            # 如果文本过长，截断显示
            if len(text) > 50:
                text = text[:47] + "..."
            hover_texts.append(text)
        
        # 创建交互式图表
        fig = make_subplots(rows=1, cols=1)
        
        # 添加主曲线
        fig.add_trace(
            go.Scatter(
                x=x,
                y=peak_values,
                mode='lines+markers',
                name='情感强度',
                hovertext=hover_texts,
                line=dict(color=EMOTION_COLORMAP["positive"], width=3),
                marker=dict(size=8)
            )
        )
        
        # 添加峰值点
        peaks = [(i, point["peak_value"]) for i, point in enumerate(curve_data) 
                if point.get("is_peak", False)]
        
        if peaks:
            peak_x, peak_y = zip(*peaks)
            peak_texts = [hover_texts[i] for i in peak_x]
            
            fig.add_trace(
                go.Scatter(
                    x=peak_x,
                    y=peak_y,
                    mode='markers',
                    name='情感峰值',
                    marker=dict(color='red', size=12, symbol='circle'),
                    hovertext=peak_texts
                )
            )
        
        # 添加全局峰值
        global_peaks = [(i, point["peak_value"]) for i, point in enumerate(curve_data) 
                       if point.get("is_global_peak", False)]
        
        if global_peaks:
            gpeak_x, gpeak_y = zip(*global_peaks)
            gpeak_texts = [hover_texts[i] for i in gpeak_x]
            
            fig.add_trace(
                go.Scatter(
                    x=gpeak_x,
                    y=gpeak_y,
                    mode='markers',
                    name='全局峰值',
                    marker=dict(color='orange', size=15, symbol='star'),
                    hovertext=gpeak_texts
                )
            )
        
        # 更新布局
        fig.update_layout(
            title='情感强度交互图表',
            xaxis_title='场景序号',
            yaxis_title='情感强度值',
            hovermode='closest',
            template='plotly_white',
            yaxis=dict(range=[-0.05, 1.05])
        )
        
        # 确定输出路径
        if not output_path and self.output_dir:
            output_path = os.path.join(self.output_dir, 'emotion_interactive.html')
        
        # 保存HTML文件
        if output_path:
            fig.write_html(output_path)
            logger.info(f"交互式情感图表已保存至: {output_path}")
            return output_path
        
        return None
    
    def export_emotion_data(self, 
                          curve_data: List[Dict[str, Any]], 
                          output_path: Optional[str] = None) -> Optional[str]:
        """
        导出情感数据为JSON文件
        
        Args:
            curve_data: 曲线数据点列表
            output_path: 输出JSON文件路径
            
        Returns:
            保存的文件路径或None
        """
        if not curve_data:
            logger.warning("曲线数据为空，无法导出")
            return None
        
        # 确定输出路径
        if not output_path and self.output_dir:
            output_path = os.path.join(self.output_dir, 'emotion_data.json')
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(curve_data, f, ensure_ascii=False, indent=2)
            logger.info(f"情感数据已导出至: {output_path}")
            return output_path
        
        return None


def visualize_intensity_curve(curve_data: List[Dict[str, Any]], 
                            output_dir: Optional[str] = None,
                            show_fig: bool = True) -> Dict[str, str]:
    """
    可视化情感强度曲线的便捷函数
    
    Args:
        curve_data: 情感曲线数据
        output_dir: 输出目录
        show_fig: 是否显示图表
        
    Returns:
        生成的图表文件路径字典
    """
    visualizer = EmotionVisualizer(output_dir)
    outputs = {}
    
    # 生成曲线图
    curve_path = visualizer.plot_intensity_curve(curve_data, show_fig=show_fig)
    if curve_path:
        outputs['curve'] = curve_path
    
    # 生成热力图
    heatmap_path = visualizer.create_intensity_heatmap(curve_data, show_fig=show_fig)
    if heatmap_path:
        outputs['heatmap'] = heatmap_path
    
    # 导出数据
    data_path = visualizer.export_emotion_data(curve_data)
    if data_path:
        outputs['data'] = data_path
    
    # 尝试创建交互式图表
    try:
        interactive_path = visualizer.export_interactive_chart(curve_data)
        if interactive_path:
            outputs['interactive'] = interactive_path
    except Exception as e:
        logger.debug(f"创建交互式图表失败: {e}")
    
    return outputs 