#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster AI剧情理解测试模块

此模块验证大模型理解原片剧情结构的能力，包括：
1. 角色识别和关系分析
2. 情节点提取和排序
3. 情感弧线识别
4. 叙事结构理解
5. 关键场景识别
"""

import os
import sys
import json
import time
import logging
import unittest
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.srt_parser import SRTParser
from src.core.narrative_analyzer import NarrativeAnalyzer
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.language_detector import LanguageDetector
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class PlotUnderstandingResult:
    """剧情理解测试结果数据类"""
    test_name: str
    subtitle_file: str
    language: str
    character_recognition_accuracy: float  # 角色识别准确率
    plot_point_extraction_score: float    # 情节点提取评分
    emotional_arc_score: float            # 情感弧线评分
    narrative_structure_score: float      # 叙事结构评分
    key_scene_identification_score: float # 关键场景识别评分
    overall_understanding_score: float    # 总体理解评分
    processing_time: float
    character_count: int
    plot_points_identified: int
    emotional_transitions: int
    narrative_coherence: float
    detailed_analysis: Dict[str, Any]


class PlotUnderstandingTester:
    """剧情理解测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化剧情理解测试器"""
        self.config = self._load_config(config_path)
        self.srt_parser = SRTParser()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.screenplay_engineer = ScreenplayEngineer()
        self.language_detector = LanguageDetector()
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 测试结果存储
        self.test_results = []
        
        # 评估阈值
        self.thresholds = self.config.get('test_thresholds', {})
        self.min_understanding_score = self.thresholds.get('plot_understanding', 0.85)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载测试配置"""
        if config_path is None:
            config_path = "tests/core_functionality_validation/test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'test_thresholds': {'plot_understanding': 0.85},
                'test_environment': {'log_level': 'INFO'}
            }
    
    def test_plot_understanding(self, subtitle_path: str, golden_standard: Dict[str, Any] = None) -> PlotUnderstandingResult:
        """
        测试剧情理解能力
        
        Args:
            subtitle_path: 字幕文件路径
            golden_standard: 黄金标准参考数据
            
        Returns:
            PlotUnderstandingResult: 测试结果
        """
        start_time = time.time()
        test_name = "plot_understanding"
        
        try:
            # 解析字幕
            subtitles = self.srt_parser.parse(subtitle_path)
            if not subtitles:
                raise ValueError(f"字幕文件解析失败: {subtitle_path}")
            
            # 检测语言
            subtitle_text = " ".join([sub.get('text', '') for sub in subtitles])
            language = self.language_detector.detect_language(subtitle_text)
            
            # 执行剧情分析
            narrative_analysis = self.narrative_analyzer.analyze_narrative_structure(subtitles)
            
            # 角色识别测试
            character_analysis = self._test_character_recognition(subtitles, golden_standard)
            
            # 情节点提取测试
            plot_point_analysis = self._test_plot_point_extraction(narrative_analysis, golden_standard)
            
            # 情感弧线测试
            emotional_analysis = self._test_emotional_arc_recognition(narrative_analysis, golden_standard)
            
            # 叙事结构测试
            structure_analysis = self._test_narrative_structure(narrative_analysis, golden_standard)
            
            # 关键场景识别测试
            scene_analysis = self._test_key_scene_identification(narrative_analysis, golden_standard)
            
            # 计算总体理解评分
            overall_score = self._calculate_overall_understanding_score(
                character_analysis, plot_point_analysis, emotional_analysis,
                structure_analysis, scene_analysis
            )
            
            # 构建详细分析结果
            detailed_analysis = {
                'subtitle_count': len(subtitles),
                'narrative_analysis': narrative_analysis,
                'character_analysis': character_analysis,
                'plot_point_analysis': plot_point_analysis,
                'emotional_analysis': emotional_analysis,
                'structure_analysis': structure_analysis,
                'scene_analysis': scene_analysis
            }
            
            result = PlotUnderstandingResult(
                test_name=test_name,
                subtitle_file=subtitle_path,
                language=language,
                character_recognition_accuracy=character_analysis.get('accuracy', 0.0),
                plot_point_extraction_score=plot_point_analysis.get('score', 0.0),
                emotional_arc_score=emotional_analysis.get('score', 0.0),
                narrative_structure_score=structure_analysis.get('score', 0.0),
                key_scene_identification_score=scene_analysis.get('score', 0.0),
                overall_understanding_score=overall_score,
                processing_time=time.time() - start_time,
                character_count=character_analysis.get('character_count', 0),
                plot_points_identified=plot_point_analysis.get('points_identified', 0),
                emotional_transitions=emotional_analysis.get('transitions', 0),
                narrative_coherence=structure_analysis.get('coherence', 0.0),
                detailed_analysis=detailed_analysis
            )
            
            self.test_results.append(result)
            self.logger.info(f"剧情理解测试完成: {test_name}, 总体评分: {overall_score:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"剧情理解测试失败: {test_name}, 错误: {str(e)}")
            return PlotUnderstandingResult(
                test_name=test_name,
                subtitle_file=subtitle_path,
                language="unknown",
                character_recognition_accuracy=0.0,
                plot_point_extraction_score=0.0,
                emotional_arc_score=0.0,
                narrative_structure_score=0.0,
                key_scene_identification_score=0.0,
                overall_understanding_score=0.0,
                processing_time=time.time() - start_time,
                character_count=0,
                plot_points_identified=0,
                emotional_transitions=0,
                narrative_coherence=0.0,
                detailed_analysis={'error': str(e)}
            )
    
    def _test_character_recognition(self, subtitles: List[Dict], golden_standard: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试角色识别能力"""
        try:
            # 使用叙事分析器识别角色
            characters = self.narrative_analyzer.extract_characters(subtitles)
            
            if golden_standard and 'characters' in golden_standard:
                # 与黄金标准对比
                expected_characters = set(golden_standard['characters'])
                identified_characters = set(characters.keys())
                
                # 计算准确率
                correct_identifications = len(expected_characters.intersection(identified_characters))
                total_expected = len(expected_characters)
                accuracy = correct_identifications / total_expected if total_expected > 0 else 0.0
                
                return {
                    'accuracy': accuracy,
                    'character_count': len(identified_characters),
                    'expected_count': total_expected,
                    'correct_identifications': correct_identifications,
                    'identified_characters': list(identified_characters),
                    'expected_characters': list(expected_characters),
                    'missing_characters': list(expected_characters - identified_characters),
                    'extra_characters': list(identified_characters - expected_characters)
                }
            else:
                # 没有黄金标准，基于启发式规则评估
                character_count = len(characters)
                
                # 基于字幕数量估算合理的角色数量
                subtitle_count = len(subtitles)
                expected_range = (max(1, subtitle_count // 50), min(10, subtitle_count // 10))
                
                # 如果角色数量在合理范围内，给予较高评分
                if expected_range[0] <= character_count <= expected_range[1]:
                    accuracy = 0.8
                elif character_count < expected_range[0]:
                    accuracy = 0.6  # 识别不足
                else:
                    accuracy = 0.7  # 过度识别
                
                return {
                    'accuracy': accuracy,
                    'character_count': character_count,
                    'expected_range': expected_range,
                    'identified_characters': list(characters.keys()),
                    'evaluation_method': 'heuristic'
                }
                
        except Exception as e:
            self.logger.error(f"角色识别测试失败: {str(e)}")
            return {
                'accuracy': 0.0,
                'character_count': 0,
                'error': str(e)
            }
    
    def _test_plot_point_extraction(self, narrative_analysis: Dict, golden_standard: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试情节点提取能力"""
        try:
            plot_points = narrative_analysis.get('plot_points', [])
            
            if golden_standard and 'plot_points' in golden_standard:
                # 与黄金标准对比
                expected_points = golden_standard['plot_points']
                
                # 计算情节点匹配度
                matches = 0
                for expected_point in expected_points:
                    for identified_point in plot_points:
                        if self._is_plot_point_match(expected_point, identified_point):
                            matches += 1
                            break
                
                score = matches / len(expected_points) if expected_points else 0.0
                
                return {
                    'score': score,
                    'points_identified': len(plot_points),
                    'expected_points': len(expected_points),
                    'matches': matches,
                    'plot_points': plot_points,
                    'expected_plot_points': expected_points
                }
            else:
                # 基于启发式规则评估
                points_count = len(plot_points)
                
                # 基于剧情长度估算合理的情节点数量
                total_subtitles = narrative_analysis.get('total_subtitles', 0)
                expected_range = (max(3, total_subtitles // 100), min(15, total_subtitles // 20))
                
                if expected_range[0] <= points_count <= expected_range[1]:
                    score = 0.8
                elif points_count < expected_range[0]:
                    score = 0.6
                else:
                    score = 0.7
                
                return {
                    'score': score,
                    'points_identified': points_count,
                    'expected_range': expected_range,
                    'plot_points': plot_points,
                    'evaluation_method': 'heuristic'
                }
                
        except Exception as e:
            self.logger.error(f"情节点提取测试失败: {str(e)}")
            return {
                'score': 0.0,
                'points_identified': 0,
                'error': str(e)
            }
    
    def _test_emotional_arc_recognition(self, narrative_analysis: Dict, golden_standard: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试情感弧线识别能力"""
        try:
            emotional_arc = narrative_analysis.get('emotional_arc', [])
            
            if golden_standard and 'emotional_arc' in golden_standard:
                # 与黄金标准对比
                expected_arc = golden_standard['emotional_arc']
                
                # 计算情感变化趋势的相似度
                similarity = self._calculate_emotional_arc_similarity(emotional_arc, expected_arc)
                
                return {
                    'score': similarity,
                    'transitions': len(emotional_arc),
                    'expected_transitions': len(expected_arc),
                    'emotional_arc': emotional_arc,
                    'expected_arc': expected_arc,
                    'similarity': similarity
                }
            else:
                # 基于启发式规则评估
                transitions = len(emotional_arc)
                
                # 检查情感变化的合理性
                if transitions >= 2:  # 至少应该有一些情感变化
                    # 检查情感值的变化范围
                    if emotional_arc:
                        emotions = [point.get('emotion_value', 0) for point in emotional_arc]
                        emotion_range = max(emotions) - min(emotions)
                        
                        if emotion_range > 0.3:  # 有明显的情感变化
                            score = 0.8
                        else:
                            score = 0.6
                    else:
                        score = 0.5
                else:
                    score = 0.4  # 情感变化太少
                
                return {
                    'score': score,
                    'transitions': transitions,
                    'emotional_arc': emotional_arc,
                    'evaluation_method': 'heuristic'
                }
                
        except Exception as e:
            self.logger.error(f"情感弧线识别测试失败: {str(e)}")
            return {
                'score': 0.0,
                'transitions': 0,
                'error': str(e)
            }
    
    def _test_narrative_structure(self, narrative_analysis: Dict, golden_standard: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试叙事结构理解能力"""
        try:
            structure = narrative_analysis.get('narrative_structure', {})
            
            if golden_standard and 'narrative_structure' in golden_standard:
                # 与黄金标准对比
                expected_structure = golden_standard['narrative_structure']
                
                # 计算结构匹配度
                structure_score = self._calculate_structure_similarity(structure, expected_structure)
                coherence = structure.get('coherence_score', 0.0)
                
                return {
                    'score': (structure_score + coherence) / 2.0,
                    'coherence': coherence,
                    'structure_match': structure_score,
                    'narrative_structure': structure,
                    'expected_structure': expected_structure
                }
            else:
                # 基于启发式规则评估
                coherence = structure.get('coherence_score', 0.0)
                
                # 检查是否识别出基本的叙事结构元素
                has_beginning = 'beginning' in structure
                has_middle = 'middle' in structure
                has_end = 'end' in structure
                
                structure_completeness = sum([has_beginning, has_middle, has_end]) / 3.0
                
                score = (coherence + structure_completeness) / 2.0
                
                return {
                    'score': score,
                    'coherence': coherence,
                    'structure_completeness': structure_completeness,
                    'narrative_structure': structure,
                    'evaluation_method': 'heuristic'
                }
                
        except Exception as e:
            self.logger.error(f"叙事结构测试失败: {str(e)}")
            return {
                'score': 0.0,
                'coherence': 0.0,
                'error': str(e)
            }
    
    def _test_key_scene_identification(self, narrative_analysis: Dict, golden_standard: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试关键场景识别能力"""
        try:
            key_scenes = narrative_analysis.get('key_scenes', [])
            
            if golden_standard and 'key_scenes' in golden_standard:
                # 与黄金标准对比
                expected_scenes = golden_standard['key_scenes']
                
                # 计算场景匹配度
                matches = 0
                for expected_scene in expected_scenes:
                    for identified_scene in key_scenes:
                        if self._is_scene_match(expected_scene, identified_scene):
                            matches += 1
                            break
                
                score = matches / len(expected_scenes) if expected_scenes else 0.0
                
                return {
                    'score': score,
                    'scenes_identified': len(key_scenes),
                    'expected_scenes': len(expected_scenes),
                    'matches': matches,
                    'key_scenes': key_scenes,
                    'expected_key_scenes': expected_scenes
                }
            else:
                # 基于启发式规则评估
                scenes_count = len(key_scenes)
                
                # 基于剧情长度估算合理的关键场景数量
                total_subtitles = narrative_analysis.get('total_subtitles', 0)
                expected_range = (max(2, total_subtitles // 200), min(8, total_subtitles // 50))
                
                if expected_range[0] <= scenes_count <= expected_range[1]:
                    score = 0.8
                elif scenes_count < expected_range[0]:
                    score = 0.6
                else:
                    score = 0.7
                
                return {
                    'score': score,
                    'scenes_identified': scenes_count,
                    'expected_range': expected_range,
                    'key_scenes': key_scenes,
                    'evaluation_method': 'heuristic'
                }
                
        except Exception as e:
            self.logger.error(f"关键场景识别测试失败: {str(e)}")
            return {
                'score': 0.0,
                'scenes_identified': 0,
                'error': str(e)
            }
    
    def _calculate_overall_understanding_score(self, character_analysis: Dict, plot_point_analysis: Dict,
                                             emotional_analysis: Dict, structure_analysis: Dict,
                                             scene_analysis: Dict) -> float:
        """计算总体理解评分"""
        try:
            # 各项权重
            weights = {
                'character': 0.2,
                'plot_points': 0.25,
                'emotional': 0.2,
                'structure': 0.2,
                'scenes': 0.15
            }
            
            scores = {
                'character': character_analysis.get('accuracy', 0.0),
                'plot_points': plot_point_analysis.get('score', 0.0),
                'emotional': emotional_analysis.get('score', 0.0),
                'structure': structure_analysis.get('score', 0.0),
                'scenes': scene_analysis.get('score', 0.0)
            }
            
            # 计算加权平均分
            weighted_score = sum(scores[key] * weights[key] for key in weights.keys())
            
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            self.logger.error(f"总体评分计算失败: {str(e)}")
            return 0.0
    
    def _is_plot_point_match(self, expected: Dict, identified: Dict) -> bool:
        """判断情节点是否匹配"""
        # 简化的匹配逻辑，实际应该更复杂
        expected_type = expected.get('type', '')
        identified_type = identified.get('type', '')
        
        # 时间位置相近且类型匹配
        expected_time = expected.get('timestamp', 0)
        identified_time = identified.get('timestamp', 0)
        
        time_diff = abs(expected_time - identified_time)
        time_tolerance = 30  # 30秒容忍度
        
        return expected_type == identified_type and time_diff <= time_tolerance
    
    def _calculate_emotional_arc_similarity(self, arc1: List[Dict], arc2: List[Dict]) -> float:
        """计算情感弧线相似度"""
        if not arc1 or not arc2:
            return 0.0
        
        # 简化的相似度计算
        # 实际应该使用更复杂的时间序列相似度算法
        try:
            emotions1 = [point.get('emotion_value', 0) for point in arc1]
            emotions2 = [point.get('emotion_value', 0) for point in arc2]
            
            # 使用皮尔逊相关系数
            if len(emotions1) >= 2 and len(emotions2) >= 2:
                correlation = np.corrcoef(emotions1[:min(len(emotions1), len(emotions2))], 
                                       emotions2[:min(len(emotions1), len(emotions2))])[0, 1]
                return max(0.0, correlation) if not np.isnan(correlation) else 0.0
            else:
                return 0.5
        except Exception:
            return 0.0
    
    def _calculate_structure_similarity(self, structure1: Dict, structure2: Dict) -> float:
        """计算结构相似度"""
        # 简化的结构相似度计算
        common_keys = set(structure1.keys()).intersection(set(structure2.keys()))
        total_keys = set(structure1.keys()).union(set(structure2.keys()))
        
        if not total_keys:
            return 0.0
        
        return len(common_keys) / len(total_keys)
    
    def _is_scene_match(self, expected: Dict, identified: Dict) -> bool:
        """判断场景是否匹配"""
        # 简化的场景匹配逻辑
        expected_importance = expected.get('importance', 0)
        identified_importance = identified.get('importance', 0)
        
        expected_time = expected.get('timestamp', 0)
        identified_time = identified.get('timestamp', 0)
        
        time_diff = abs(expected_time - identified_time)
        importance_diff = abs(expected_importance - identified_importance)
        
        return time_diff <= 60 and importance_diff <= 0.3  # 1分钟时间容忍度，0.3重要性容忍度


class TestPlotUnderstanding(unittest.TestCase):
    """剧情理解测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = PlotUnderstandingTester()
    
    def test_basic_plot_understanding(self):
        """测试基础剧情理解"""
        # 创建测试字幕文件
        test_subtitle_path = "test_data/subtitles/test_plot.srt"
        
        if os.path.exists(test_subtitle_path):
            result = self.tester.test_plot_understanding(test_subtitle_path)
            
            self.assertGreaterEqual(result.overall_understanding_score, 0.85, "总体理解评分应≥0.85")
            self.assertGreater(result.character_count, 0, "应该识别出至少一个角色")
            self.assertGreater(result.plot_points_identified, 0, "应该识别出至少一个情节点")
    
    def test_character_recognition_accuracy(self):
        """测试角色识别准确性"""
        test_subtitle_path = "test_data/subtitles/character_test.srt"
        
        if os.path.exists(test_subtitle_path):
            result = self.tester.test_plot_understanding(test_subtitle_path)
            
            self.assertGreaterEqual(result.character_recognition_accuracy, 0.8, "角色识别准确率应≥80%")
    
    def test_emotional_arc_recognition(self):
        """测试情感弧线识别"""
        test_subtitle_path = "test_data/subtitles/emotional_test.srt"
        
        if os.path.exists(test_subtitle_path):
            result = self.tester.test_plot_understanding(test_subtitle_path)
            
            self.assertGreaterEqual(result.emotional_arc_score, 0.7, "情感弧线评分应≥0.7")
            self.assertGreater(result.emotional_transitions, 1, "应该识别出情感变化")


if __name__ == "__main__":
    unittest.main(verbosity=2)
