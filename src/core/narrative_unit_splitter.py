#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事单元分割器

将剧本分割为叙事单元，每个单元代表一个相对独立的情节段落。
用于剧本重构和优化，支持灵活组合和重排叙事单元。
"""

import logging
from typing import Dict, List, Any, Optional

# 尝试导入情感分析，如果不可用则使用简单替代
try:
    from src.nlp.sentiment_analyzer import analyze_sentiment
except ImportError:
    # 简单替代函数
    def analyze_sentiment(text: str) -> Dict[str, Any]:
        return {"label": "NEUTRAL", "intensity": 0.5}
    logging.warning("主要情感分析器不可用，使用备用版本")

# 创建日志记录器
logger = logging.getLogger(__name__)

def split_into_units(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将剧本分割为叙事单元
    
    Args:
        script: 剧本场景列表
        
    Returns:
        叙事单元列表，每个单元包含一个或多个相关场景
    """
    if not script:
        return []
    
    # 处理情感分析
    script_with_sentiment = []
    for scene in script:
        if "sentiment" not in scene:
            # 如果没有情感数据，添加情感分析
            text = scene.get("text", "")
            sentiment = analyze_sentiment(text)
            scene_copy = scene.copy()
            scene_copy["sentiment"] = sentiment
            script_with_sentiment.append(scene_copy)
        else:
            script_with_sentiment.append(scene)
    
    # 初始化单元列表
    units = []
    
    # 当前处理的单元
    current_unit = {
        "scenes": [],
        "sentiment": None,
        "characters": set(),
        "main_topic": ""
    }
    
    # 遍历场景
    for i, scene in enumerate(script_with_sentiment):
        # 检查是否应该开始新单元
        start_new_unit = False
        
        # 如果是第一个场景
        if i == 0:
            start_new_unit = True
        
        # 检查情感变化
        elif "sentiment" in scene and current_unit["sentiment"]:
            curr_sentiment = scene["sentiment"]
            prev_sentiment = current_unit["sentiment"]
            
            # 情感标签变化
            if curr_sentiment.get("label") != prev_sentiment.get("label"):
                start_new_unit = True
            
            # 或情感强度变化显著
            elif abs(curr_sentiment.get("intensity", 0.5) - prev_sentiment.get("intensity", 0.5)) > 0.3:
                start_new_unit = True
        
        # 检查角色变化
        if not start_new_unit and "characters" in scene:
            scene_chars = set(scene.get("characters", []))
            if scene_chars and not scene_chars.intersection(current_unit["characters"]):
                # 如果没有共同角色，开始新单元
                start_new_unit = True
        
        # 开始新单元
        if start_new_unit:
            # 保存当前单元（如果非空）
            if current_unit["scenes"]:
                # 计算单元的整体情感
                calculate_unit_properties(current_unit)
                units.append(current_unit)
            
            # 创建新单元
            current_unit = {
                "scenes": [scene],
                "sentiment": scene.get("sentiment"),
                "characters": set(scene.get("characters", [])),
                "main_topic": scene.get("topic", "")
            }
        else:
            # 添加到当前单元
            current_unit["scenes"].append(scene)
            current_unit["characters"].update(set(scene.get("characters", [])))
    
    # 添加最后一个单元
    if current_unit["scenes"]:
        calculate_unit_properties(current_unit)
        units.append(current_unit)
    
    logger.info(f"将{len(script)}个场景分割为{len(units)}个叙事单元")
    return units

def calculate_unit_properties(unit: Dict[str, Any]) -> None:
    """
    计算叙事单元的属性
    
    Args:
        unit: 叙事单元
    """
    scenes = unit["scenes"]
    
    # 计算整体情感
    sentiment_values = []
    for scene in scenes:
        if "sentiment" in scene:
            label = scene["sentiment"].get("label", "NEUTRAL")
            intensity = scene["sentiment"].get("intensity", 0.5)
            
            # 转换为数值
            if label == "POSITIVE":
                value = intensity
            elif label == "NEGATIVE":
                value = -intensity
            else:
                value = 0.0
                
            sentiment_values.append(value)
    
    # 计算平均情感
    if sentiment_values:
        avg_value = sum(sentiment_values) / len(sentiment_values)
        
        # 转换回标签和强度
        if avg_value > 0.1:
            label = "POSITIVE"
            intensity = min(0.9, abs(avg_value))
        elif avg_value < -0.1:
            label = "NEGATIVE"
            intensity = min(0.9, abs(avg_value))
        else:
            label = "NEUTRAL"
            intensity = min(0.7, abs(avg_value) * 5)
            
        unit["sentiment"] = {
            "label": label,
            "intensity": intensity
        }
    
    # 处理角色列表（从集合转为列表）
    unit["characters"] = list(unit["characters"])
    
    # 整合文本
    all_text = " ".join([scene.get("text", "") for scene in scenes])
    unit["text"] = all_text
    
    # 其他可能的属性计算
    unit["scene_count"] = len(scenes)
    unit["start_idx"] = scenes[0].get("index", 0) if scenes else 0
    unit["end_idx"] = scenes[-1].get("index", 0) if scenes else 0


# 兼容旧版函数名
split_into_beats = split_into_units


if __name__ == "__main__":
    # 测试叙事单元分割
    from src.utils.sample_data import get_sample_script
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例脚本
    script = get_sample_script()
    
    # 分割为叙事单元
    units = split_into_units(script)
    
    # 打印结果
    print(f"剧本场景数: {len(script)}")
    print(f"叙事单元数: {len(units)}")
    
    for i, unit in enumerate(units):
        print(f"\n单元 {i+1}:")
        print(f"  场景数: {unit['scene_count']}")
        print(f"  角色数: {len(unit['characters'])}")
        if "sentiment" in unit:
            print(f"  情感: {unit['sentiment']['label']}, "
                 f"强度: {unit['sentiment']['intensity']:.2f}") 