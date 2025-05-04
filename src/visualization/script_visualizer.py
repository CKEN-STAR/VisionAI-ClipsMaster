#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本可视化器

提供剧本可视化功能，支持情感曲线、角色关系和情节流可视化等。
生成直观的图表和图形，帮助理解和分析剧本结构。
"""

import os
import json
import logging
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# 获取日志记录器
logger = logging.getLogger(__name__)

def visualize_script(script: List[Dict[str, Any]], 
                    output_dir: Optional[str] = None,
                    show_plots: bool = True) -> Dict[str, str]:
    """
    可视化剧本
    
    Args:
        script: 剧本场景列表
        output_dir: 输出目录路径
        show_plots: 是否显示图表
        
    Returns:
        保存的图表文件路径字典
    """
    if not script:
        logger.warning("输入剧本为空，无法可视化")
        return {}
    
    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 生成各种可视化图表
    outputs = {}
    
    # 情感曲线
    emotion_path = _visualize_emotion_curve(script, output_dir, show_plots)
    if emotion_path:
        outputs['emotion_curve'] = emotion_path
    
    # 角色出现频率
    character_path = _visualize_character_frequency(script, output_dir, show_plots)
    if character_path:
        outputs['character_frequency'] = character_path
    
    # 情节密度
    plot_density_path = _visualize_plot_density(script, output_dir, show_plots)
    if plot_density_path:
        outputs['plot_density'] = plot_density_path
    
    # 添加更多可视化...
    
    return outputs

def _visualize_emotion_curve(script: List[Dict[str, Any]], 
                           output_dir: Optional[str] = None,
                           show_plots: bool = True) -> Optional[str]:
    """可视化情感曲线"""
    # 提取情感数据
    emotions = []
    for scene in script:
        sentiment = scene.get('sentiment', {})
        label = sentiment.get('label', 'NEUTRAL')
        intensity = sentiment.get('intensity', 0.5)
        
        # 转换为数值
        if label == 'POSITIVE':
            value = intensity
        elif label == 'NEGATIVE':
            value = -intensity
        else:
            value = 0.0
            
        emotions.append(value)
    
    # 创建情感曲线图
    plt.figure(figsize=(10, 6))
    
    # 绘制曲线
    x = list(range(len(emotions)))
    plt.plot(x, emotions, 'o-', color='blue', linewidth=2, markersize=8)
    
    # 添加零线
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.6)
    
    # 装饰图表
    plt.title('剧本情感曲线', fontsize=16)
    plt.xlabel('场景序号', fontsize=14)
    plt.ylabel('情感值 (正值=积极, 负值=消极)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(-1.1, 1.1)
    
    # 填充颜色
    plt.fill_between(x, emotions, 0, where=[e > 0 for e in emotions], color='lightgreen', alpha=0.5, label='积极情感')
    plt.fill_between(x, emotions, 0, where=[e < 0 for e in emotions], color='lightcoral', alpha=0.5, label='消极情感')
    
    plt.legend()
    plt.tight_layout()
    
    # 保存图表
    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, 'emotion_curve.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"情感曲线图已保存至: {output_path}")
    
    # 显示图表
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    return output_path

def _visualize_character_frequency(script: List[Dict[str, Any]], 
                                 output_dir: Optional[str] = None, 
                                 show_plots: bool = True) -> Optional[str]:
    """可视化角色出现频率"""
    # 计算角色出现频率
    character_freq = {}
    
    for scene in script:
        # 提取角色
        characters = scene.get('characters', [])
        if isinstance(characters, str):
            characters = [characters]
        
        # 计数
        for char in characters:
            if char in character_freq:
                character_freq[char] += 1
            else:
                character_freq[char] = 1
    
    # 如果没有角色数据，尝试从文本中提取
    if not character_freq:
        import re
        pattern = r'([A-Z一-龥]{2,})[:：]'
        
        for scene in script:
            text = scene.get('text', '')
            matches = re.findall(pattern, text)
            
            for char in matches:
                if char in character_freq:
                    character_freq[char] += 1
                else:
                    character_freq[char] = 1
    
    # 如果仍然没有角色数据，返回None
    if not character_freq:
        logger.warning("未找到角色数据，无法创建角色频率图")
        return None
    
    # 按频率排序
    sorted_chars = sorted(character_freq.items(), key=lambda x: x[1], reverse=True)
    
    # 只取前10个角色
    if len(sorted_chars) > 10:
        sorted_chars = sorted_chars[:10]
    
    chars = [item[0] for item in sorted_chars]
    freqs = [item[1] for item in sorted_chars]
    
    # 创建条形图
    plt.figure(figsize=(10, 6))
    
    # 生成颜色
    colors = plt.cm.viridis(np.linspace(0, 1, len(chars)))
    
    # 绘制条形图
    bars = plt.bar(chars, freqs, color=colors, width=0.6)
    
    # 装饰图表
    plt.title('角色出现频率', fontsize=16)
    plt.xlabel('角色', fontsize=14)
    plt.ylabel('出现次数', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', alpha=0.3)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.0f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # 保存图表
    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, 'character_frequency.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"角色频率图已保存至: {output_path}")
    
    # 显示图表
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    return output_path

def _visualize_plot_density(script: List[Dict[str, Any]], 
                          output_dir: Optional[str] = None, 
                          show_plots: bool = True) -> Optional[str]:
    """可视化情节密度"""
    # 计算每个场景的情节密度
    densities = []
    
    for scene in script:
        # 基础密度
        density = 0.5
        
        # 根据标签调整
        tags = scene.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        # 高密度标签
        high_density_tags = ['转折', '冲突', '高潮', '危机', '突发事件']
        for tag in high_density_tags:
            if tag in tags:
                density += 0.2
                break
        
        # 情感强度影响
        sentiment = scene.get('sentiment', {})
        intensity = sentiment.get('intensity', 0.5)
        density += (intensity - 0.5) * 0.3
        
        # 确保密度在0-1范围内
        density = max(0.0, min(1.0, density))
        densities.append(density)
    
    # 创建情节密度图
    plt.figure(figsize=(10, 6))
    
    # 绘制曲线
    x = list(range(len(densities)))
    plt.plot(x, densities, 'o-', color='purple', linewidth=2, markersize=8)
    
    # 装饰图表
    plt.title('剧本情节密度', fontsize=16)
    plt.xlabel('场景序号', fontsize=14)
    plt.ylabel('情节密度', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)
    
    # 填充颜色
    plt.fill_between(x, densities, 0, color='lavender', alpha=0.5)
    
    plt.tight_layout()
    
    # 保存图表
    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, 'plot_density.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"情节密度图已保存至: {output_path}")
    
    # 显示图表
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    return output_path

def visualize_analysis_results(analysis: Dict[str, Any], 
                             output_dir: Optional[str] = None,
                             show_plots: bool = True) -> Dict[str, str]:
    """
    可视化分析结果
    
    Args:
        analysis: 分析结果字典
        output_dir: 输出目录路径
        show_plots: 是否显示图表
        
    Returns:
        保存的图表文件路径字典
    """
    if not analysis:
        logger.warning("分析结果为空，无法可视化")
        return {}
    
    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 生成各种可视化图表
    outputs = {}
    
    # 情感曲线
    if 'emotion_curve' in analysis:
        emotion_path = _visualize_emotion_curve_from_analysis(analysis['emotion_curve'], output_dir, show_plots)
        if emotion_path:
            outputs['emotion_curve'] = emotion_path
    
    # 情节密度
    if 'plot_density' in analysis:
        density_path = _visualize_density_from_analysis(analysis['plot_density'], output_dir, show_plots)
        if density_path:
            outputs['plot_density'] = density_path
    
    # 角色互动
    if 'character_interactions' in analysis:
        interaction_path = _visualize_character_interactions(analysis['character_interactions'], output_dir, show_plots)
        if interaction_path:
            outputs['character_interactions'] = interaction_path
    
    return outputs

def _visualize_emotion_curve_from_analysis(emotion_data: Dict[str, Any],
                                        output_dir: Optional[str] = None,
                                        show_plots: bool = True) -> Optional[str]:
    """从分析结果可视化情感曲线"""
    if 'values' not in emotion_data:
        return None
    
    # 提取情感值
    emotions = emotion_data['values']
    
    # 创建情感曲线图
    plt.figure(figsize=(10, 6))
    
    # 绘制曲线
    x = list(range(len(emotions)))
    plt.plot(x, emotions, 'o-', color='blue', linewidth=2, markersize=8)
    
    # 添加零线
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.6)
    
    # 装饰图表
    plt.title('剧本情感曲线 (分析结果)', fontsize=16)
    plt.xlabel('场景序号', fontsize=14)
    plt.ylabel('情感值 (正值=积极, 负值=消极)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(-1.1, 1.1)
    
    # 填充颜色
    plt.fill_between(x, emotions, 0, where=[e > 0 for e in emotions], color='lightgreen', alpha=0.5, label='积极情感')
    plt.fill_between(x, emotions, 0, where=[e < 0 for e in emotions], color='lightcoral', alpha=0.5, label='消极情感')
    
    # 标记情感高潮点
    if 'peaks' in emotion_data:
        for peak in emotion_data['peaks']:
            pos = peak.get('position', 0)
            val = peak.get('value', 0)
            plt.plot(pos, val, 'ro', markersize=10, label='高潮点' if 'peak_legend' not in locals() else '')
            plt.text(pos, val + 0.05, f'峰值', ha='center')
            locals()['peak_legend'] = True
    
    plt.legend()
    plt.tight_layout()
    
    # 保存图表
    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, 'emotion_curve_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"情感曲线分析图已保存至: {output_path}")
    
    # 显示图表
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    return output_path

def _visualize_density_from_analysis(density_data: Dict[str, Any],
                                   output_dir: Optional[str] = None,
                                   show_plots: bool = True) -> Optional[str]:
    """从分析结果可视化情节密度"""
    if 'values' not in density_data:
        return None
    
    # 提取密度值
    densities = density_data['values']
    
    # 创建情节密度图
    plt.figure(figsize=(10, 6))
    
    # 绘制曲线
    x = list(range(len(densities)))
    plt.plot(x, densities, 'o-', color='purple', linewidth=2, markersize=8)
    
    # 添加平均线
    avg_density = density_data.get('average', sum(densities) / len(densities))
    plt.axhline(y=avg_density, color='red', linestyle='--', alpha=0.6, label=f'平均密度: {avg_density:.2f}')
    
    # 装饰图表
    plt.title('剧本情节密度 (分析结果)', fontsize=16)
    plt.xlabel('场景序号', fontsize=14)
    plt.ylabel('情节密度', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.1)
    
    # 填充颜色
    plt.fill_between(x, densities, 0, color='lavender', alpha=0.5)
    
    plt.legend()
    plt.tight_layout()
    
    # 保存图表
    output_path = None
    if output_dir:
        output_path = os.path.join(output_dir, 'plot_density_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"情节密度分析图已保存至: {output_path}")
    
    # 显示图表
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    return output_path

def _visualize_character_interactions(character_data: Dict[str, Any],
                                    output_dir: Optional[str] = None,
                                    show_plots: bool = True) -> Optional[str]:
    """可视化角色互动"""
    if 'characters' not in character_data or 'interactions' not in character_data:
        return None
    
    characters = character_data['characters']
    interactions = character_data['interactions']
    
    # 如果角色太少，无法创建有意义的图
    if len(characters) < 2:
        return None
    
    try:
        import networkx as nx
        
        # 创建图形
        G = nx.Graph()
        
        # 添加节点
        for char in characters:
            G.add_node(char)
        
        # 添加边
        for relation, details in interactions.items():
            if isinstance(relation, str):
                # 解析字符串键 "(char1, char2)"
                import ast
                relation_tuple = ast.literal_eval(relation)
                char1, char2 = relation_tuple
            else:
                # 已经是元组
                char1, char2 = relation
                
            weight = details.get('count', 1)
            G.add_edge(char1, char2, weight=weight)
        
        # 创建图形
        plt.figure(figsize=(12, 10))
        
        # 设置布局
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        # 获取边权重
        edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
        max_weight = max(edge_weights) if edge_weights else 1
        normalized_weights = [3 + (w / max_weight) * 5 for w in edge_weights]
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue', alpha=0.8)
        
        # 绘制边
        nx.draw_networkx_edges(G, pos, width=normalized_weights, alpha=0.7, edge_color='gray')
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')
        
        # 绘制边标签
        edge_labels = {(u, v): f"{G[u][v]['weight']}" for u, v in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)
        
        plt.title('角色互动关系图', fontsize=16)
        plt.axis('off')
        
        # 保存图表
        output_path = None
        if output_dir:
            output_path = os.path.join(output_dir, 'character_interactions.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"角色互动图已保存至: {output_path}")
        
        # 显示图表
        if show_plots:
            plt.show()
        else:
            plt.close()
        
        return output_path
    
    except ImportError:
        logger.warning("无法导入networkx，无法创建角色互动图")
        return None


if __name__ == "__main__":
    # 测试可视化功能
    from src.utils.sample_data import get_sample_script
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例脚本
    script = get_sample_script()
    
    # 进行可视化
    outputs = visualize_script(script, output_dir="visualization_output")
    
    print("已生成以下可视化图表:")
    for name, path in outputs.items():
        print(f"  {name}: {path}") 