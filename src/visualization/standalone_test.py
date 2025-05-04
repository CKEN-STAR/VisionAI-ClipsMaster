#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化模块独立测试脚本 - 生成示例数据并测试可视化功能
不依赖其他模块，可单独运行
"""

import os
import sys
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入必要的可视化库
import jinja2
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visualization_test")

# 颜色方案
COLOR_SCHEME = {
    "primary": "#3498db",      # 主要颜色
    "secondary": "#2ecc71",    # 次要颜色
    "accent": "#e74c3c",       # 强调颜色
    "neutral": "#95a5a6",      # 中性颜色
    "background": "#f8f9fa",   # 背景色
    "text": "#2c3e50",         # 文本颜色
    
    # 情感颜色
    "emotion": {
        "positive": "#2ecc71",  # 积极情绪 (绿色)
        "negative": "#e74c3c",  # 消极情绪 (红色)
        "neutral": "#95a5a6",   # 中性情绪 (灰色)
    },
    
    # 节点颜色
    "nodes": {
        "character": "#3498db",   # 角色节点 (蓝色)
        "location": "#27ae60",    # 位置节点 (绿色)
        "event": "#e67e22",       # 事件节点 (橙色)
        "unknown": "#95a5a6",     # 未知节点 (灰色)
    }
}

def generate_test_data() -> Dict[str, Any]:
    """生成测试用的剧本数据"""
    
    # 示例角色
    characters = ["李明", "张红", "王芳", "赵刚", "陈静"]
    
    # 情感标签
    sentiments = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    
    # 生成随机片段
    segments = []
    start_time = 0
    
    for i in range(20):
        # 随机时长 (2-10秒)
        duration = random.uniform(2, 10)
        end_time = start_time + duration
        
        # 随机情感
        sentiment_type = random.choice(sentiments)
        sentiment_score = random.uniform(-0.8, 0.8)
        if sentiment_type == "POSITIVE":
            sentiment_score = abs(sentiment_score)
        elif sentiment_type == "NEGATIVE":
            sentiment_score = -abs(sentiment_score)
        else:
            sentiment_score = sentiment_score * 0.3  # 减小中性情感的极值
        
        # 随机内容
        if random.random() > 0.5:
            # 对话形式
            speaker = random.choice(characters)
            content = f"{speaker}：{'这是一段测试对话内容，用于演示剧本分析可视化功能' + str(i)}"
        else:
            # 旁白形式
            content = f"{'这是一段旁白描述内容，用于演示剧本分析可视化功能' + str(i)}"
        
        # 添加片段
        segments.append({
            "time": {
                "start": start_time,
                "end": end_time
            },
            "content": content,
            "sentiment": {
                "label": sentiment_type,
                "score": sentiment_score
            }
        })
        
        # 更新下一个片段的开始时间
        start_time = end_time
    
    # 构建完整数据结构
    script_data = {
        "process_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "language": "zh",
        "total_duration": start_time,
        "template_used": "conflict_resolution,emotional_rollercoaster",
        "key_characters": characters[:3],
        "scene_count": 5,
        "segments": segments
    }
    
    return script_data

def plot_timeline(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    绘制剧本时间线
    
    Args:
        script_data: 剧本数据，包含片段和时间信息
        
    Returns:
        时间线数据
    """
    segments = script_data.get("segments", [])
    
    # 构建时间线数据
    timeline_data = {
        "segments": []
    }
    
    # 添加每个片段
    for i, segment in enumerate(segments):
        # 获取时间信息
        start_time = segment.get("time", {}).get("start", 0)
        end_time = segment.get("time", {}).get("end", 0)
        duration = end_time - start_time
        
        # 获取情感值（如果有）
        sentiment = segment.get("sentiment", {}).get("label", "NEUTRAL")
        sentiment_score = segment.get("sentiment", {}).get("score", 0)
        
        # 颜色映射
        if sentiment == "POSITIVE":
            color = COLOR_SCHEME["emotion"]["positive"]
        elif sentiment == "NEGATIVE":
            color = COLOR_SCHEME["emotion"]["negative"]
        else:
            color = COLOR_SCHEME["emotion"]["neutral"]
            
        # 添加片段信息
        timeline_data["segments"].append({
            "id": i,
            "start": start_time,
            "end": end_time,
            "duration": duration,
            "content": segment.get("content", "").split("\n")[0][:30] + "..." if len(segment.get("content", "")) > 30 else segment.get("content", ""),
            "sentiment": sentiment,
            "color": color,
            "opacity": min(0.3 + abs(sentiment_score) * 0.7, 1.0)  # 情感强度影响透明度
        })
    
    return timeline_data

def render_character_graph(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    渲染角色关系网络图
    
    Args:
        script_data: 剧本数据，包含角色和关系信息
        
    Returns:
        网络图数据，包含节点和边
    """
    # 角色列表
    characters = script_data.get("key_characters", [])
    
    # 如果没有角色信息，尝试从segments中提取
    if not characters and "segments" in script_data:
        character_set = set()
        for segment in script_data.get("segments", []):
            content = segment.get("content", "")
            if "：" in content or ":" in content:
                # 简单解析对话格式 "角色：内容"
                parts = content.split("：", 1) if "：" in content else content.split(":", 1)
                if len(parts) >= 2:
                    character = parts[0].strip()
                    if character:
                        character_set.add(character)
        
        characters = list(character_set)
    
    # 构建简单的角色关系图
    graph_data = {
        "nodes": [],
        "edges": []
    }
    
    # 添加角色节点
    for i, character in enumerate(characters):
        graph_data["nodes"].append({
            "id": character,
            "name": character,
            "type": "character",
            "size": 30,
            "color": COLOR_SCHEME["nodes"]["character"]
        })
        
    # 添加角色间关系（简化为线性关系）
    for i in range(len(characters) - 1):
        char1 = characters[i]
        char2 = characters[i + 1]
        graph_data["edges"].append({
            "source": char1,
            "target": char2,
            "weight": 1,
            "color": COLOR_SCHEME["neutral"]
        })
    
    # 如果有更多角色，连接首尾以形成环形结构
    if len(characters) > 2:
        graph_data["edges"].append({
            "source": characters[-1],
            "target": characters[0],
            "weight": 0.5,
            "color": COLOR_SCHEME["neutral"]
        })
    
    return graph_data

def generate_analysis_report(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成分析报告数据结构
    
    Args:
        script_data: 剧本数据
        
    Returns:
        报告数据
    """
    # 构建报告结构
    report = {
        "title": "剧本分析可视化报告",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "script_id": script_data.get("process_id", "unknown"),
        "language": script_data.get("language", "auto"),
        "duration": script_data.get("total_duration", 0),
        "scene_count": script_data.get("scene_count", 0),
        
        # 可视化组件
        "timeline": plot_timeline(script_data),
        "character_network": render_character_graph(script_data),
        "emotion_curve": {
            "x": [s.get("time", {}).get("start", i) for i, s in enumerate(script_data.get("segments", []))],
            "y": [s.get("sentiment", {}).get("score", 0) for s in script_data.get("segments", [])]
        },
        
        # 标签
        "tags": []
    }
    
    # 提取情感基调
    sentiment_scores = [s.get("sentiment", {}).get("score", 0) for s in script_data.get("segments", [])]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    if avg_sentiment > 0.3:
        emotional_tone = "积极"
    elif avg_sentiment < -0.3:
        emotional_tone = "消极"
    else:
        emotional_tone = "中性"
        
    report["emotional_tone"] = emotional_tone
    
    # 添加标签
    template_name = script_data.get("template_used", "unknown")
    if isinstance(template_name, str) and template_name != "unknown":
        for name in template_name.split(","):
            if name.strip():
                report["tags"].append({
                    "name": name.strip(),
                    "color": COLOR_SCHEME["primary"]
                })
    
    # 添加关键角色标签
    for character in script_data.get("key_characters", [])[:3]:
        report["tags"].append({
            "name": character,
            "color": COLOR_SCHEME["nodes"]["character"]
        })
        
    return report

def render_html_template(report: Dict[str, Any]) -> str:
    """
    渲染HTML模板
    
    Args:
        report: 报告数据
        
    Returns:
        渲染后的HTML字符串
    """
    try:
        # 获取模板路径
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        template_path = os.path.join(template_dir, "report_template.html")
        
        # 加载模板
        with open(template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        # 创建Jinja2环境
        template = jinja2.Template(template_str)
        
        # 渲染模板
        return template.render(report=report)
    except Exception as e:
        logger.error(f"渲染HTML模板失败: {str(e)}")
        # 返回简单的错误页面
        return f"""
        <html>
        <body>
            <h1>模板渲染失败</h1>
            <p>错误信息: {str(e)}</p>
        </body>
        </html>
        """

def export_visualization_report(script_data: Dict[str, Any], output_path: str) -> str:
    """
    导出可视化报告
    
    Args:
        script_data: 剧本数据
        output_path: 输出路径
        
    Returns:
        报告文件路径
    """
    try:
        # 生成报告数据
        report = generate_analysis_report(script_data)
        
        # 渲染HTML
        html_content = render_html_template(report)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logger.info(f"报告已导出至: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        return str(e)

def save_test_data(data: Dict[str, Any], output_path: str) -> None:
    """保存测试数据到JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"测试数据已保存到: {output_path}")

def test_visualization() -> None:
    """测试剧本可视化功能"""
    
    # 生成测试数据
    logger.info("生成测试数据...")
    test_data = generate_test_data()
    
    # 保存测试数据
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "data", "test")
    os.makedirs(data_dir, exist_ok=True)
    
    json_path = os.path.join(data_dir, "test_script_data.json")
    save_test_data(test_data, json_path)
    
    # 生成可视化报告
    logger.info("生成可视化报告...")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                          "data", "output", "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "test_report.html")
    result = export_visualization_report(test_data, report_path)
    
    logger.info(f"生成的报告已保存到: {result}")
    logger.info(f"请在浏览器中打开以查看报告: file://{os.path.abspath(result)}")

if __name__ == "__main__":
    test_visualization() 