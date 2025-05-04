#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本可视化模块测试脚本 - 生成示例数据并测试可视化功能
"""

import os
import sys
import json
import random
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # 简化路径计算
root_dir = os.path.dirname(project_root)
sys.path.insert(0, root_dir)

# 导入可视化模块
from src.visualization.script_visualizer import (
    generate_analysis_report,
    export_visualization_report
)

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

def save_test_data(data: Dict[str, Any], output_path: str) -> None:
    """保存测试数据到JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"测试数据已保存到: {output_path}")

def test_visualization() -> None:
    """测试剧本可视化功能"""
    
    # 生成测试数据
    test_data = generate_test_data()
    
    # 保存测试数据
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "data", "test")
    os.makedirs(data_dir, exist_ok=True)
    
    json_path = os.path.join(data_dir, "test_script_data.json")
    save_test_data(test_data, json_path)
    
    # 生成可视化报告
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                          "data", "output", "reports")
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = os.path.join(output_dir, "test_report.html")
    result = export_visualization_report(test_data, report_path)
    
    print(f"生成的报告已保存到: {result}")
    print(f"请在浏览器中打开以查看报告: file://{os.path.abspath(result)}")

if __name__ == "__main__":
    test_visualization() 