#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证沙盒模块

提供脚本验证沙盒，用于在实际生成视频前评估脚本的质量和完整性。
可以检测剧情漏洞、角色一致性问题和情感流程缺陷等。
"""

import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# 导入相关模块
from src.utils.log_handler import get_logger
from src.knowledge.graph_builder import build_knowledge_graph
from src.nlp.sentiment_analyzer import analyze_sentiment_batch
from src.core.narrative_analyzer import analyze_narrative_structure
from src.narrative.anchor_detector import detect_anchors
from src.narrative.anchor_types import AnchorType
from src.visualization.script_visualizer import visualize_script

# 配置日志
logger = get_logger("validation_sandbox")

class NarrativeSimulator:
    """
    叙事模拟器，用于模拟脚本的叙事效果
    """
    
    def __init__(self):
        """初始化叙事模拟器"""
        logger.info("初始化叙事模拟器")
    
    def find_plot_holes(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测剧情漏洞
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的剧情漏洞列表，每个漏洞包含位置、严重程度和描述
        """
        logger.info("检测剧情漏洞...")
        holes = []
        
        # 构建知识图谱
        knowledge_graph = build_knowledge_graph(script)
        
        # 获取主要角色
        characters = knowledge_graph.get_character_importance()
        main_characters = {name: rank for name, rank in characters.items() 
                           if rank > 0.3}  # 只考虑重要角色
        
        # 获取主要事件
        events = knowledge_graph.get_events()
        
        # 检查角色突然消失
        character_appearances = {}
        for i, scene in enumerate(script):
            text = scene.get('text', '')
            
            # 更新角色出现情况
            for character in main_characters:
                if character in text:
                    if character not in character_appearances:
                        character_appearances[character] = []
                    character_appearances[character].append(i)
        
        # 检测角色突然消失
        for character, appearances in character_appearances.items():
            if len(appearances) < 2:
                continue
                
            for i in range(1, len(appearances)):
                if appearances[i] - appearances[i-1] > 3:  # 如果角色在连续3个场景都没出现
                    holes.append({
                        'type': 'character_disappearance',
                        'character': character,
                        'position': appearances[i-1],
                        'severity': 'medium',
                        'description': f"角色 '{character}' 在场景 {appearances[i-1]} 之后突然消失，直到场景 {appearances[i]}"
                    })
        
        # 检测情节无关联
        # 找出情节关系断点
        for i in range(1, len(script)-1):
            prev_scene = script[i-1].get('text', '')
            curr_scene = script[i].get('text', '')
            next_scene = script[i+1].get('text', '')
            
            # 计算语义连贯性
            coherence = self._measure_coherence(prev_scene, curr_scene, next_scene)
            
            if coherence < 0.3:  # 低连贯性阈值
                holes.append({
                    'type': 'plot_discontinuity',
                    'position': i,
                    'severity': 'high',
                    'description': f"场景 {i} 与前后场景缺乏情节连贯性，可能造成观众理解断点"
                })
        
        # 检测未解决的悬念
        anchors = detect_anchors(script)
        suspense_anchors = [a for a in anchors if a.anchor_type == AnchorType.SUSPENSE]
        
        for anchor in suspense_anchors:
            # 检查是否有相应的解答
            if not anchor.is_resolved:
                holes.append({
                    'type': 'unresolved_suspense',
                    'position': anchor.start_idx,
                    'severity': 'high',
                    'description': f"在场景 {anchor.start_idx} 设置的悬念 '{anchor.description}' 未得到解答"
                })
        
        # 检测逻辑矛盾
        contradictions = knowledge_graph.find_contradictions()
        for contradiction in contradictions:
            holes.append({
                'type': 'logical_contradiction',
                'position': contradiction.get('position', 0),
                'severity': 'critical',
                'description': contradiction.get('description', '存在逻辑矛盾')
            })
        
        logger.info(f"检测到 {len(holes)} 个剧情漏洞")
        return holes
    
    def _measure_coherence(self, prev_text: str, curr_text: str, next_text: str) -> float:
        """
        测量场景之间的连贯性
        
        Args:
            prev_text: 前一场景文本
            curr_text: 当前场景文本
            next_text: 后一场景文本
            
        Returns:
            连贯性分数，0-1之间
        """
        # 简单实现，可以替换为更复杂的语义相似度计算
        # 通过共同角色和词汇重叠来近似
        
        # 提取词集合
        prev_words = set(prev_text.replace('。', ' ').replace('，', ' ').split())
        curr_words = set(curr_text.replace('。', ' ').replace('，', ' ').split())
        next_words = set(next_text.replace('。', ' ').replace('，', ' ').split())
        
        # 计算重叠率
        prev_overlap = len(prev_words.intersection(curr_words)) / max(1, len(prev_words))
        next_overlap = len(curr_words.intersection(next_words)) / max(1, len(curr_words))
        
        # 综合分数
        coherence = (prev_overlap + next_overlap) / 2
        
        return coherence


def check_character_arcs(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检查角色弧线的完整性和一致性
    
    Args:
        script: 剧本
        
    Returns:
        角色弧线分析结果
    """
    logger.info("分析角色弧线...")
    
    # 构建知识图谱
    knowledge_graph = build_knowledge_graph(script)
    
    # 获取角色重要性
    characters = knowledge_graph.get_character_importance()
    
    # 对于每个主要角色，分析其情感弧线
    character_arcs = {}
    arc_problems = []
    
    # 只分析重要角色
    main_characters = {name: rank for name, rank in characters.items() if rank > 0.3}
    
    for character in main_characters:
        # 提取涉及该角色的场景
        character_scenes = []
        for i, scene in enumerate(script):
            text = scene.get('text', '')
            if character in text:
                # 分析该场景中角色的情感
                sentiment = scene.get('sentiment', {}).get('label', 'NEUTRAL')
                intensity = scene.get('sentiment', {}).get('intensity', 0.5)
                
                character_scenes.append({
                    'scene_idx': i,
                    'sentiment': sentiment,
                    'intensity': intensity,
                    'text': text
                })
        
        # 分析情感变化
        if len(character_scenes) >= 3:
            sentiment_values = []
            
            for scene in character_scenes:
                sentiment = scene['sentiment']
                intensity = scene['intensity']
                
                # 将情感标签转换为数值
                if sentiment == 'POSITIVE':
                    value = intensity
                elif sentiment == 'NEGATIVE':
                    value = -intensity
                else:  # NEUTRAL
                    value = 0
                
                sentiment_values.append(value)
            
            # 检测角色弧线问题
            arc_quality = analyze_character_arc(sentiment_values)
            
            # 记录角色弧线
            character_arcs[character] = {
                'scenes': character_scenes,
                'sentiment_values': sentiment_values,
                'arc_quality': arc_quality
            }
            
            # 检测弧线问题
            if arc_quality < 0.6:  # 弧线质量阈值
                arc_problems.append({
                    'character': character,
                    'problem': '角色情感弧线平坦或不完整',
                    'scenes': [s['scene_idx'] for s in character_scenes]
                })
            
            # 检测情感不连贯处
            for i in range(1, len(sentiment_values)):
                if abs(sentiment_values[i] - sentiment_values[i-1]) > 1.2:  # 剧烈情感变化阈值
                    if i < len(character_scenes):
                        arc_problems.append({
                            'character': character,
                            'problem': '角色情感剧烈变化缺乏铺垫',
                            'scene': character_scenes[i]['scene_idx']
                        })
    
    return {
        'character_arcs': character_arcs,
        'problems': arc_problems
    }


def analyze_character_arc(sentiment_values: List[float]) -> float:
    """
    分析角色情感弧线质量
    
    Args:
        sentiment_values: 情感值序列
        
    Returns:
        弧线质量评分，0-1之间
    """
    if len(sentiment_values) < 3:
        return 0.5  # 数据点太少，无法得出有意义的结论
    
    # 计算弧线变化
    changes = [abs(sentiment_values[i] - sentiment_values[i-1]) 
              for i in range(1, len(sentiment_values))]
    
    # 如果情感变化太少，说明弧线平坦
    if sum(changes) < 0.8:
        return 0.3
    
    # 检查弧线是否有明显的转折点
    has_turning_point = False
    for i in range(1, len(changes)):
        if changes[i] > 0.5 and changes[i-1] < 0.3:
            has_turning_point = True
            break
    
    # 检查情感是否有收尾（开始和结束情感不同）
    has_closure = abs(sentiment_values[0] - sentiment_values[-1]) > 0.5
    
    # 综合评分
    score = 0.5
    if has_turning_point:
        score += 0.25
    if has_closure:
        score += 0.25
    
    return score


def analyze_emotion_curve(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析情感曲线
    
    Args:
        script: 剧本
        
    Returns:
        情感曲线分析结果
    """
    logger.info("分析情感曲线...")
    
    emotion_values = []
    
    # 提取每个场景的情感值
    for scene in script:
        sentiment = scene.get('sentiment', {}).get('label', 'NEUTRAL')
        intensity = scene.get('sentiment', {}).get('intensity', 0.5)
        
        # 将情感标签转换为数值
        if sentiment == 'POSITIVE':
            value = intensity
        elif sentiment == 'NEGATIVE':
            value = -intensity
        else:  # NEUTRAL
            value = 0
        
        emotion_values.append(value)
    
    # 分析情感曲线特性
    analysis = {
        'values': emotion_values,
        'mean': np.mean(emotion_values),
        'std': np.std(emotion_values),
        'max': max(emotion_values),
        'min': min(emotion_values),
        'range': max(emotion_values) - min(emotion_values)
    }
    
    # 检测情感平坦段
    flat_segments = []
    current_flat = None
    
    for i in range(1, len(emotion_values)):
        if abs(emotion_values[i] - emotion_values[i-1]) < 0.15:  # 情感变化阈值
            if current_flat is None:
                current_flat = {
                    'start': i-1,
                    'values': [emotion_values[i-1], emotion_values[i]]
                }
            else:
                current_flat['values'].append(emotion_values[i])
        else:
            if current_flat is not None and len(current_flat['values']) >= 3:
                current_flat['end'] = i - 1
                current_flat['length'] = current_flat['end'] - current_flat['start'] + 1
                flat_segments.append(current_flat)
            current_flat = None
    
    # 处理最后一个平坦段
    if current_flat is not None and len(current_flat['values']) >= 3:
        current_flat['end'] = len(emotion_values) - 1
        current_flat['length'] = current_flat['end'] - current_flat['start'] + 1
        flat_segments.append(current_flat)
    
    analysis['flat_segments'] = flat_segments
    
    # 检测情感高潮点
    peaks = []
    for i in range(1, len(emotion_values) - 1):
        if (emotion_values[i] > emotion_values[i-1] and 
            emotion_values[i] > emotion_values[i+1] and
            abs(emotion_values[i]) > 0.6):  # 高情感强度阈值
            peaks.append({
                'position': i,
                'value': emotion_values[i]
            })
    
    analysis['peaks'] = peaks
    
    # 评估情感曲线质量
    quality = 0.5  # 基础分
    
    # 有足够的情感变化范围
    if analysis['range'] > 1.0:
        quality += 0.1
    
    # 有足够的波动
    if analysis['std'] > 0.3:
        quality += 0.1
    
    # 有情感高潮点
    if len(peaks) > 0:
        quality += 0.1 * min(len(peaks), 3) / 3
    
    # 没有过长的平坦段
    long_flat_segments = [seg for seg in flat_segments if seg['length'] > len(script) / 4]
    if not long_flat_segments:
        quality += 0.1
    else:
        quality -= 0.1 * len(long_flat_segments)
    
    analysis['quality'] = max(0.0, min(1.0, quality))
    
    return analysis


class SandboxValidator:
    """
    沙盒验证器，用于在安全环境中验证脚本
    """
    
    def __init__(self):
        """初始化沙盒验证器"""
        self.simulator = NarrativeSimulator()
        logger.info("初始化沙盒验证器")
    
    def dry_run(self, script: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        在沙盒中运行脚本，检测潜在问题
        
        Args:
            script: 待验证的脚本
            
        Returns:
            验证报告
        """
        logger.info("开始脚本沙盒验证")
        
        # 检查脚本是否为空
        if not script:
            return {
                'status': 'error',
                'message': '脚本为空',
                'timestamp': datetime.now().isoformat()
            }
        
        # 在脚本中没有情感数据的情况下添加情感分析
        if not all('sentiment' in scene for scene in script):
            try:
                texts = [scene.get('text', '') for scene in script]
                sentiments = analyze_sentiment_batch(texts)
                
                for i, sentiment in enumerate(sentiments):
                    if i < len(script):
                        script[i]['sentiment'] = sentiment
            except Exception as e:
                logger.warning(f"添加情感分析时出错: {e}")
        
        # 运行各种检查
        try:
            plot_holes = self.simulator.find_plot_holes(script)
            character_consistency = check_character_arcs(script)
            emotion_flow = analyze_emotion_curve(script)
            
            # 生成综合报告
            report = {
                "plot_holes": plot_holes,
                "character_consistency": character_consistency,
                "emotional_flow": emotion_flow,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            # 评估总体质量
            quality_score = self._evaluate_script_quality(report)
            report['quality_score'] = quality_score
            
            # 添加修改建议
            report['suggestions'] = self._generate_suggestions(report)
            
            return report
            
        except Exception as e:
            logger.error(f"脚本验证失败: {e}")
            return {
                'status': 'error',
                'message': f'验证过程发生错误: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _evaluate_script_quality(self, report: Dict[str, Any]) -> float:
        """
        评估脚本总体质量
        
        Args:
            report: 验证报告
            
        Returns:
            质量评分，0-1之间
        """
        # 剧情漏洞评分
        plot_holes = report.get('plot_holes', [])
        plot_hole_penalty = len(plot_holes) * 0.05
        plot_score = max(0, 1 - plot_hole_penalty)
        
        # 角色一致性评分
        character_consistency = report.get('character_consistency', {})
        character_problems = character_consistency.get('problems', [])
        character_penalty = len(character_problems) * 0.1
        character_score = max(0, 1 - character_penalty)
        
        # 情感流程评分
        emotion_flow = report.get('emotional_flow', {})
        emotion_score = emotion_flow.get('quality', 0.5)
        
        # 综合评分
        quality_score = (plot_score * 0.4 + character_score * 0.3 + emotion_score * 0.3)
        
        return quality_score
    
    def _generate_suggestions(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成改进建议
        
        Args:
            report: 验证报告
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 处理剧情漏洞
        plot_holes = report.get('plot_holes', [])
        for hole in plot_holes:
            suggestion = {
                'type': 'plot_hole',
                'position': hole.get('position', 0),
                'severity': hole.get('severity', 'medium'),
                'description': hole.get('description', ''),
                'fix_suggestion': '添加过渡场景或解释此处的情节断点'
            }
            
            # 针对不同类型的漏洞提供具体建议
            if hole.get('type') == 'character_disappearance':
                suggestion['fix_suggestion'] = f"在场景 {hole.get('position')} 之后添加对角色 '{hole.get('character')}' 的交代或解释"
            elif hole.get('type') == 'unresolved_suspense':
                suggestion['fix_suggestion'] = "添加解答场景，解决此处设置的悬念"
            
            suggestions.append(suggestion)
        
        # 处理角色一致性问题
        character_consistency = report.get('character_consistency', {})
        character_problems = character_consistency.get('problems', [])
        
        for problem in character_problems:
            suggestion = {
                'type': 'character_consistency',
                'character': problem.get('character', ''),
                'description': problem.get('problem', ''),
                'fix_suggestion': f"修正角色 '{problem.get('character', '')}' 的情感发展，使其更加连贯"
            }
            
            if 'scene' in problem:
                suggestion['position'] = problem['scene']
                suggestion['fix_suggestion'] = f"在场景 {problem['scene']} 前添加过渡，为角色情感变化提供铺垫"
            
            suggestions.append(suggestion)
        
        # 处理情感流程问题
        emotion_flow = report.get('emotional_flow', {})
        flat_segments = emotion_flow.get('flat_segments', [])
        
        # 如果有长的情感平坦段
        long_flat_segments = [seg for seg in flat_segments if seg.get('length', 0) > 3]
        if long_flat_segments:
            for segment in long_flat_segments:
                suggestion = {
                    'type': 'emotional_flow',
                    'position': segment.get('start', 0),
                    'description': f"情感曲线在场景 {segment.get('start', 0)} 到 {segment.get('end', 0)} 过于平坦",
                    'fix_suggestion': f"在场景 {segment.get('start', 0) + segment.get('length', 0) // 2} 添加情感波动，避免长期情感平坦"
                }
                suggestions.append(suggestion)
        
        # 如果缺乏情感高潮
        peaks = emotion_flow.get('peaks', [])
        if len(peaks) == 0:
            suggestion = {
                'type': 'emotional_flow',
                'description': "脚本缺乏情感高潮点",
                'fix_suggestion': "在适当位置添加情感强度高的场景，作为故事高潮"
            }
            suggestions.append(suggestion)
        
        return suggestions


def visualize_sandbox(report: Dict[str, Any]) -> None:
    """
    可视化沙盒验证结果
    
    Args:
        report: 验证报告
    """
    plt.figure(figsize=(12, 8))
    
    # 绘制情感曲线
    emotion_flow = report.get('emotional_flow', {})
    values = emotion_flow.get('values', [])
    
    if values:
        x = list(range(len(values)))
        plt.subplot(211)
        plt.plot(x, values, 'b-', linewidth=2)
        plt.fill_between(x, [0] * len(values), values, 
                        where=[v > 0 for v in values], 
                        color='green', alpha=0.3)
        plt.fill_between(x, [0] * len(values), values, 
                        where=[v < 0 for v in values], 
                        color='red', alpha=0.3)
        
        # 标记情感高潮点
        peaks = emotion_flow.get('peaks', [])
        for peak in peaks:
            plt.plot(peak.get('position', 0), peak.get('value', 0), 'ro', markersize=10)
        
        # 标记剧情漏洞
        plot_holes = report.get('plot_holes', [])
        for hole in plot_holes:
            pos = hole.get('position', 0)
            if 0 <= pos < len(values):
                if hole.get('severity') == 'critical':
                    marker = 'rx'
                    size = 12
                else:
                    marker = 'r^'
                    size = 8
                plt.plot(pos, values[pos], marker, markersize=size)
        
        plt.title('情感曲线')
        plt.ylabel('情感值')
        plt.grid(True, alpha=0.3)
    
    # 绘制角色情感弧线
    plt.subplot(212)
    character_consistency = report.get('character_consistency', {})
    character_arcs = character_consistency.get('character_arcs', {})
    
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    
    for i, (character, arc) in enumerate(character_arcs.items()):
        color = colors[i % len(colors)]
        values = arc.get('sentiment_values', [])
        if values:
            plt.plot(range(len(values)), values, f"{color}-", linewidth=2, label=character)
    
    plt.title('角色情感弧线')
    plt.xlabel('场景序号')
    plt.ylabel('情感值')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 总体评分
    quality_score = report.get('quality_score', 0)
    plt.suptitle(f'脚本质量评分: {quality_score:.2f}', fontsize=16)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    
    # 保存图像
    report_dir = "reports/sandbox"
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    plt.savefig(f"{report_dir}/script_analysis_{timestamp}.png")
    
    plt.show()


# 便捷函数
def validate_script(script: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    验证脚本，便捷函数
    
    Args:
        script: 待验证的脚本
        
    Returns:
        验证报告
    """
    validator = SandboxValidator()
    return validator.dry_run(script)


if __name__ == "__main__":
    # 简单测试
    from src.utils.sample_data import get_sample_script
    
    # 获取示例脚本
    script = get_sample_script()
    
    # 验证脚本
    report = validate_script(script)
    
    # 可视化结果
    visualize_sandbox(report)
    
    # 输出报告摘要
    quality = report.get('quality_score', 0)
    print(f"脚本质量评分: {quality:.2f}")
    
    plot_holes = report.get('plot_holes', [])
    print(f"检测到 {len(plot_holes)} 个剧情漏洞")
    
    suggestions = report.get('suggestions', [])
    print(f"提供 {len(suggestions)} 条改进建议") 