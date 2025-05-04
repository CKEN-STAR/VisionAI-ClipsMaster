#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事结构分析器

分析脚本的叙事结构，检测情节流向、角色弧线和情感变化等。
该模块为验证沙盒和其他模块提供叙事结构分析支持。
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# 获取日志记录器
logger = logging.getLogger(__name__)

def analyze_narrative_structure(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析脚本的叙事结构
    
    Args:
        script: 脚本场景列表
        
    Returns:
        叙事结构分析结果
    """
    if not script:
        return {"status": "error", "message": "脚本为空"}
    
    # 分析情感曲线
    emotion_curve = analyze_emotion_curve(script)
    
    # 分析场景连贯性
    coherence = analyze_scene_coherence(script)
    
    # 分析角色互动
    character_interactions = analyze_character_interactions(script)
    
    # 分析情节密度
    plot_density = analyze_plot_density(script)
    
    # 整合分析结果
    return {
        "status": "success",
        "emotion_curve": emotion_curve,
        "coherence": coherence,
        "character_interactions": character_interactions,
        "plot_density": plot_density
    }

def analyze_emotion_curve(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析情感曲线
    
    Args:
        script: 脚本场景列表
        
    Returns:
        情感曲线分析结果
    """
    # 提取情感值
    emotion_values = []
    
    for scene in script:
        sentiment = scene.get('sentiment', {})
        label = sentiment.get('label', 'NEUTRAL')
        intensity = sentiment.get('intensity', 0.5)
        
        # 转换为数值
        if label == 'POSITIVE':
            value = intensity
        elif label == 'NEGATIVE':
            value = -intensity
        else:  # NEUTRAL
            value = 0.0
            
        emotion_values.append(value)
    
    # 分析情感曲线特征
    mean_emotion = np.mean(emotion_values)
    std_emotion = np.std(emotion_values)
    emotion_range = max(emotion_values) - min(emotion_values)
    
    # 检测情感平坦段
    flat_segments = []
    current_segment = None
    
    for i in range(1, len(emotion_values)):
        if abs(emotion_values[i] - emotion_values[i-1]) < 0.15:  # 平坦阈值
            if current_segment is None:
                current_segment = {'start': i-1, 'values': [emotion_values[i-1], emotion_values[i]]}
            else:
                current_segment['values'].append(emotion_values[i])
        else:
            if current_segment and len(current_segment['values']) >= 3:
                current_segment['end'] = i - 1
                current_segment['length'] = current_segment['end'] - current_segment['start'] + 1
                flat_segments.append(current_segment)
            current_segment = None
    
    # 处理最后一个平坦段
    if current_segment and len(current_segment['values']) >= 3:
        current_segment['end'] = len(emotion_values) - 1
        current_segment['length'] = current_segment['end'] - current_segment['start'] + 1
        flat_segments.append(current_segment)
    
    # 检测情感高潮点
    peaks = []
    for i in range(1, len(emotion_values) - 1):
        if (emotion_values[i] > emotion_values[i-1] and 
            emotion_values[i] > emotion_values[i+1] and
            abs(emotion_values[i]) > 0.6):  # 高潮阈值
            peaks.append({'position': i, 'value': emotion_values[i]})
    
    return {
        'values': emotion_values,
        'mean': mean_emotion,
        'std': std_emotion,
        'range': emotion_range,
        'flat_segments': flat_segments,
        'peaks': peaks
    }

def analyze_scene_coherence(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析场景连贯性
    
    Args:
        script: 脚本场景列表
        
    Returns:
        场景连贯性分析结果
    """
    coherence_scores = []
    
    for i in range(1, len(script)):
        prev_scene = script[i-1].get('text', '')
        curr_scene = script[i].get('text', '')
        
        # 计算连贯性（简化版本）
        words_prev = set(prev_scene.replace('。', ' ').replace('，', ' ').split())
        words_curr = set(curr_scene.replace('。', ' ').replace('，', ' ').split())
        
        overlap = len(words_prev.intersection(words_curr))
        coherence = overlap / max(1, min(len(words_prev), len(words_curr)))
        
        coherence_scores.append(coherence)
    
    # 计算平均连贯性
    if coherence_scores:
        average_coherence = sum(coherence_scores) / len(coherence_scores)
    else:
        average_coherence = 0.0
    
    # 找出连贯性低的转场
    low_coherence_transitions = []
    for i, score in enumerate(coherence_scores):
        if score < 0.1:  # 低连贯性阈值
            low_coherence_transitions.append({
                'position': i + 1,  # 场景索引
                'score': score
            })
    
    return {
        'scores': coherence_scores,
        'average': average_coherence,
        'low_coherence_transitions': low_coherence_transitions
    }

def analyze_character_interactions(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析角色互动
    
    Args:
        script: 脚本场景列表
        
    Returns:
        角色互动分析结果
    """
    # 提取角色
    import re
    character_pattern = r'([A-Z一-龥]{2,})[:：]'
    
    all_characters = set()
    character_scenes = {}
    
    for i, scene in enumerate(script):
        text = scene.get('text', '')
        
        # 提取角色
        characters = set(re.findall(character_pattern, text))
        all_characters.update(characters)
        
        # 记录角色出现的场景
        for character in characters:
            if character not in character_scenes:
                character_scenes[character] = []
            character_scenes[character].append(i)
    
    # 分析角色互动
    interactions = {}
    for char1 in all_characters:
        for char2 in all_characters:
            if char1 != char2:
                # 计算两个角色共同出现的场景
                char1_scenes = set(character_scenes.get(char1, []))
                char2_scenes = set(character_scenes.get(char2, []))
                common_scenes = char1_scenes.intersection(char2_scenes)
                
                if common_scenes:
                    key = tuple(sorted([char1, char2]))
                    interactions[key] = {
                        'count': len(common_scenes),
                        'scenes': sorted(list(common_scenes))
                    }
    
    return {
        'characters': list(all_characters),
        'character_scenes': character_scenes,
        'interactions': interactions
    }

def analyze_plot_density(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析情节密度
    
    Args:
        script: 脚本场景列表
        
    Returns:
        情节密度分析结果
    """
    # 根据场景标签和情感变化评估情节密度
    densities = []
    
    for i in range(len(script)):
        # 获取当前场景
        scene = script[i]
        
        # 基础密度分数
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
        density += (intensity - 0.5) * 0.3  # 情感强度影响密度
        
        # 确保密度在0-1范围内
        density = max(0.0, min(1.0, density))
        densities.append(density)
    
    # 计算平均密度和变化
    average_density = sum(densities) / len(densities) if densities else 0.0
    density_changes = [abs(densities[i] - densities[i-1]) for i in range(1, len(densities))]
    average_change = sum(density_changes) / len(density_changes) if density_changes else 0.0
    
    return {
        'values': densities,
        'average': average_density,
        'changes': density_changes,
        'average_change': average_change
    }

if __name__ == "__main__":
    # 测试叙事分析
    from src.utils.sample_data import get_sample_script
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例脚本
    script = get_sample_script()
    
    # 分析叙事结构
    analysis = analyze_narrative_structure(script)
    
    # 输出分析结果
    print("脚本叙事结构分析结果:")
    print(f"情感曲线: 均值={analysis['emotion_curve']['mean']:.2f}, " +
         f"标准差={analysis['emotion_curve']['std']:.2f}, " +
         f"情感范围={analysis['emotion_curve']['range']:.2f}")
    print(f"情感高潮点: {len(analysis['emotion_curve']['peaks'])}")
    
    print(f"场景连贯性: 平均分数={analysis['coherence']['average']:.2f}")
    print(f"低连贯性转场: {len(analysis['coherence']['low_coherence_transitions'])}")
    
    print(f"角色数量: {len(analysis['character_interactions']['characters'])}")
    print(f"角色互动对数: {len(analysis['character_interactions']['interactions'])}")
    
    print(f"情节密度: 平均={analysis['plot_density']['average']:.2f}, " +
         f"平均变化={analysis['plot_density']['average_change']:.2f}")
