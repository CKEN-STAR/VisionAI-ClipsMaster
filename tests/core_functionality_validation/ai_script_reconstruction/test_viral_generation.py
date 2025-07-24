#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 爆款生成测试模块

此模块验证AI基于"原片字幕→爆款字幕"逻辑生成爆款内容的能力，包括：
1. 内容压缩效果评估
2. 爆款特征匹配度测试
3. 关键信息保留度验证
4. 节奏优化效果评估
5. 吸引力指标分析
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
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.narrative_analyzer import NarrativeAnalyzer
from src.core.language_detector import LanguageDetector
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class ViralGenerationResult:
    """爆款生成测试结果数据类"""
    test_name: str
    original_subtitle_file: str
    generated_subtitle_file: str
    language: str
    compression_ratio: float              # 压缩比
    viral_features_match: float          # 爆款特征匹配度
    key_information_retention: float     # 关键信息保留度
    rhythm_optimization_score: float     # 节奏优化评分
    attractiveness_score: float          # 吸引力评分
    overall_viral_score: float           # 总体爆款评分
    processing_time: float
    original_duration: float
    generated_duration: float
    original_subtitle_count: int
    generated_subtitle_count: int
    detailed_analysis: Dict[str, Any]


class ViralGenerationTester:
    """爆款生成测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化爆款生成测试器"""
        self.config = self._load_config(config_path)
        self.srt_parser = SRTParser()
        self.screenplay_engineer = ScreenplayEngineer()
        self.narrative_analyzer = NarrativeAnalyzer()
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
        self.min_compression_ratio = self.thresholds.get('compression_ratio_min', 0.3)
        self.max_compression_ratio = self.thresholds.get('compression_ratio_max', 0.7)
        self.min_viral_features_match = self.thresholds.get('viral_features_match', 0.75)
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
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
                'test_thresholds': {
                    'compression_ratio_min': 0.3,
                    'compression_ratio_max': 0.7,
                    'viral_features_match': 0.75
                },
                'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp'}
            }
    
    def test_viral_generation(self, original_subtitle_path: str, 
                            viral_reference_path: str = None) -> ViralGenerationResult:
        """
        测试爆款生成能力
        
        Args:
            original_subtitle_path: 原片字幕文件路径
            viral_reference_path: 爆款参考字幕文件路径（可选）
            
        Returns:
            ViralGenerationResult: 测试结果
        """
        start_time = time.time()
        test_name = "viral_generation"
        
        try:
            # 解析原片字幕
            original_subtitles = self.srt_parser.parse(original_subtitle_path)
            if not original_subtitles:
                raise ValueError(f"原片字幕文件解析失败: {original_subtitle_path}")
            
            # 检测语言
            original_text = " ".join([sub.get('text', '') for sub in original_subtitles])
            language = self.language_detector.detect_language(original_text)
            
            # 生成爆款字幕
            generated_subtitles = self.screenplay_engineer.reconstruct_screenplay(
                original_subtitles=original_subtitles,
                target_style="viral",
                language=language
            )
            
            if not generated_subtitles:
                raise ValueError("爆款字幕生成失败")
            
            # 保存生成的字幕文件
            generated_subtitle_file = self.temp_dir / f"generated_viral_{int(time.time())}.srt"
            self._save_subtitles_to_file(generated_subtitles, str(generated_subtitle_file))
            
            # 计算压缩比
            compression_analysis = self._analyze_compression_ratio(original_subtitles, generated_subtitles)
            
            # 分析爆款特征匹配度
            viral_features_analysis = self._analyze_viral_features(generated_subtitles, viral_reference_path)
            
            # 分析关键信息保留度
            information_retention_analysis = self._analyze_information_retention(original_subtitles, generated_subtitles)
            
            # 分析节奏优化效果
            rhythm_analysis = self._analyze_rhythm_optimization(original_subtitles, generated_subtitles)
            
            # 分析吸引力指标
            attractiveness_analysis = self._analyze_attractiveness(generated_subtitles)
            
            # 计算总体爆款评分
            overall_score = self._calculate_overall_viral_score(
                compression_analysis, viral_features_analysis, information_retention_analysis,
                rhythm_analysis, attractiveness_analysis
            )
            
            # 构建详细分析结果
            detailed_analysis = {
                'compression_analysis': compression_analysis,
                'viral_features_analysis': viral_features_analysis,
                'information_retention_analysis': information_retention_analysis,
                'rhythm_analysis': rhythm_analysis,
                'attractiveness_analysis': attractiveness_analysis,
                'original_subtitles_sample': original_subtitles[:5],  # 前5条原始字幕
                'generated_subtitles_sample': generated_subtitles[:5]  # 前5条生成字幕
            }
            
            result = ViralGenerationResult(
                test_name=test_name,
                original_subtitle_file=original_subtitle_path,
                generated_subtitle_file=str(generated_subtitle_file),
                language=language,
                compression_ratio=compression_analysis.get('ratio', 0.0),
                viral_features_match=viral_features_analysis.get('match_score', 0.0),
                key_information_retention=information_retention_analysis.get('retention_score', 0.0),
                rhythm_optimization_score=rhythm_analysis.get('optimization_score', 0.0),
                attractiveness_score=attractiveness_analysis.get('attractiveness_score', 0.0),
                overall_viral_score=overall_score,
                processing_time=time.time() - start_time,
                original_duration=compression_analysis.get('original_duration', 0.0),
                generated_duration=compression_analysis.get('generated_duration', 0.0),
                original_subtitle_count=len(original_subtitles),
                generated_subtitle_count=len(generated_subtitles),
                detailed_analysis=detailed_analysis
            )
            
            self.test_results.append(result)
            self.logger.info(f"爆款生成测试完成: {test_name}, 总体评分: {overall_score:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"爆款生成测试失败: {test_name}, 错误: {str(e)}")
            return ViralGenerationResult(
                test_name=test_name,
                original_subtitle_file=original_subtitle_path,
                generated_subtitle_file="",
                language="unknown",
                compression_ratio=0.0,
                viral_features_match=0.0,
                key_information_retention=0.0,
                rhythm_optimization_score=0.0,
                attractiveness_score=0.0,
                overall_viral_score=0.0,
                processing_time=time.time() - start_time,
                original_duration=0.0,
                generated_duration=0.0,
                original_subtitle_count=0,
                generated_subtitle_count=0,
                detailed_analysis={'error': str(e)}
            )
    
    def _analyze_compression_ratio(self, original_subtitles: List[Dict], 
                                 generated_subtitles: List[Dict]) -> Dict[str, Any]:
        """分析压缩比"""
        try:
            # 计算时长压缩比
            original_duration = self._calculate_total_duration(original_subtitles)
            generated_duration = self._calculate_total_duration(generated_subtitles)
            
            duration_ratio = generated_duration / original_duration if original_duration > 0 else 0.0
            
            # 计算字幕数量压缩比
            count_ratio = len(generated_subtitles) / len(original_subtitles) if original_subtitles else 0.0
            
            # 计算文本长度压缩比
            original_text_length = sum(len(sub.get('text', '')) for sub in original_subtitles)
            generated_text_length = sum(len(sub.get('text', '')) for sub in generated_subtitles)
            
            text_ratio = generated_text_length / original_text_length if original_text_length > 0 else 0.0
            
            # 综合压缩比（以时长为主）
            compression_ratio = duration_ratio
            
            # 评估压缩效果
            is_optimal_compression = self.min_compression_ratio <= compression_ratio <= self.max_compression_ratio
            
            return {
                'ratio': compression_ratio,
                'duration_ratio': duration_ratio,
                'count_ratio': count_ratio,
                'text_ratio': text_ratio,
                'original_duration': original_duration,
                'generated_duration': generated_duration,
                'is_optimal': is_optimal_compression,
                'compression_score': 1.0 if is_optimal_compression else max(0.0, 1.0 - abs(compression_ratio - 0.5) * 2)
            }
            
        except Exception as e:
            self.logger.error(f"压缩比分析失败: {str(e)}")
            return {
                'ratio': 0.0,
                'compression_score': 0.0,
                'error': str(e)
            }
    
    def _analyze_viral_features(self, generated_subtitles: List[Dict], 
                              viral_reference_path: str = None) -> Dict[str, Any]:
        """分析爆款特征匹配度"""
        try:
            viral_features = {
                'hook_opening': 0.0,      # 开头吸引力
                'conflict_tension': 0.0,  # 冲突张力
                'emotional_peaks': 0.0,   # 情感高潮
                'cliffhanger_ending': 0.0, # 悬念结尾
                'pacing_rhythm': 0.0      # 节奏感
            }
            
            # 分析开头吸引力
            if generated_subtitles:
                first_subtitle = generated_subtitles[0].get('text', '')
                viral_features['hook_opening'] = self._analyze_hook_strength(first_subtitle)
            
            # 分析冲突张力
            viral_features['conflict_tension'] = self._analyze_conflict_tension(generated_subtitles)
            
            # 分析情感高潮
            viral_features['emotional_peaks'] = self._analyze_emotional_peaks(generated_subtitles)
            
            # 分析悬念结尾
            if generated_subtitles:
                last_subtitle = generated_subtitles[-1].get('text', '')
                viral_features['cliffhanger_ending'] = self._analyze_cliffhanger_strength(last_subtitle)
            
            # 分析节奏感
            viral_features['pacing_rhythm'] = self._analyze_pacing_rhythm(generated_subtitles)
            
            # 计算总体匹配度
            match_score = np.mean(list(viral_features.values()))
            
            return {
                'match_score': match_score,
                'viral_features': viral_features,
                'meets_threshold': match_score >= self.min_viral_features_match
            }
            
        except Exception as e:
            self.logger.error(f"爆款特征分析失败: {str(e)}")
            return {
                'match_score': 0.0,
                'viral_features': {},
                'error': str(e)
            }
    
    def _analyze_information_retention(self, original_subtitles: List[Dict], 
                                     generated_subtitles: List[Dict]) -> Dict[str, Any]:
        """分析关键信息保留度"""
        try:
            # 提取原片关键信息
            original_keywords = self._extract_keywords(original_subtitles)
            generated_keywords = self._extract_keywords(generated_subtitles)
            
            # 计算关键词保留率
            if original_keywords:
                retained_keywords = set(original_keywords).intersection(set(generated_keywords))
                retention_rate = len(retained_keywords) / len(original_keywords)
            else:
                retention_rate = 0.0
            
            # 分析情节完整性
            plot_completeness = self._analyze_plot_completeness(original_subtitles, generated_subtitles)
            
            # 分析角色保留度
            character_retention = self._analyze_character_retention(original_subtitles, generated_subtitles)
            
            # 综合保留度评分
            retention_score = (retention_rate + plot_completeness + character_retention) / 3.0
            
            return {
                'retention_score': retention_score,
                'keyword_retention_rate': retention_rate,
                'plot_completeness': plot_completeness,
                'character_retention': character_retention,
                'retained_keywords': list(retained_keywords) if 'retained_keywords' in locals() else [],
                'original_keywords_count': len(original_keywords),
                'generated_keywords_count': len(generated_keywords)
            }
            
        except Exception as e:
            self.logger.error(f"信息保留度分析失败: {str(e)}")
            return {
                'retention_score': 0.0,
                'error': str(e)
            }

    def _analyze_rhythm_optimization(self, original_subtitles: List[Dict],
                                   generated_subtitles: List[Dict]) -> Dict[str, Any]:
        """分析节奏优化效果"""
        try:
            # 计算原片节奏指标
            original_rhythm = self._calculate_rhythm_metrics(original_subtitles)
            generated_rhythm = self._calculate_rhythm_metrics(generated_subtitles)

            # 节奏改进评分
            rhythm_improvements = {
                'pace_acceleration': 0.0,    # 节奏加速
                'tension_building': 0.0,     # 张力构建
                'climax_positioning': 0.0,   # 高潮定位
                'transition_smoothness': 0.0 # 转场流畅性
            }

            # 分析节奏加速效果
            if original_rhythm['avg_interval'] > 0:
                pace_improvement = (original_rhythm['avg_interval'] - generated_rhythm['avg_interval']) / original_rhythm['avg_interval']
                rhythm_improvements['pace_acceleration'] = max(0.0, min(1.0, pace_improvement))

            # 分析张力构建
            rhythm_improvements['tension_building'] = self._analyze_tension_building(generated_subtitles)

            # 分析高潮定位
            rhythm_improvements['climax_positioning'] = self._analyze_climax_positioning(generated_subtitles)

            # 分析转场流畅性
            rhythm_improvements['transition_smoothness'] = self._analyze_transition_smoothness(generated_subtitles)

            # 计算总体优化评分
            optimization_score = np.mean(list(rhythm_improvements.values()))

            return {
                'optimization_score': optimization_score,
                'rhythm_improvements': rhythm_improvements,
                'original_rhythm': original_rhythm,
                'generated_rhythm': generated_rhythm
            }

        except Exception as e:
            self.logger.error(f"节奏优化分析失败: {str(e)}")
            return {
                'optimization_score': 0.0,
                'error': str(e)
            }

    def _analyze_attractiveness(self, generated_subtitles: List[Dict]) -> Dict[str, Any]:
        """分析吸引力指标"""
        try:
            attractiveness_metrics = {
                'curiosity_triggers': 0.0,   # 好奇心触发
                'emotional_engagement': 0.0, # 情感参与度
                'surprise_elements': 0.0,    # 惊喜元素
                'relatability': 0.0,         # 共鸣度
                'shareability': 0.0          # 分享价值
            }

            # 分析好奇心触发
            attractiveness_metrics['curiosity_triggers'] = self._analyze_curiosity_triggers(generated_subtitles)

            # 分析情感参与度
            attractiveness_metrics['emotional_engagement'] = self._analyze_emotional_engagement(generated_subtitles)

            # 分析惊喜元素
            attractiveness_metrics['surprise_elements'] = self._analyze_surprise_elements(generated_subtitles)

            # 分析共鸣度
            attractiveness_metrics['relatability'] = self._analyze_relatability(generated_subtitles)

            # 分析分享价值
            attractiveness_metrics['shareability'] = self._analyze_shareability(generated_subtitles)

            # 计算总体吸引力评分
            attractiveness_score = np.mean(list(attractiveness_metrics.values()))

            return {
                'attractiveness_score': attractiveness_score,
                'attractiveness_metrics': attractiveness_metrics
            }

        except Exception as e:
            self.logger.error(f"吸引力分析失败: {str(e)}")
            return {
                'attractiveness_score': 0.0,
                'error': str(e)
            }

    def _calculate_overall_viral_score(self, compression_analysis: Dict, viral_features_analysis: Dict,
                                     information_retention_analysis: Dict, rhythm_analysis: Dict,
                                     attractiveness_analysis: Dict) -> float:
        """计算总体爆款评分"""
        try:
            # 各项权重
            weights = {
                'compression': 0.2,      # 压缩效果权重
                'viral_features': 0.25,  # 爆款特征权重
                'information': 0.2,      # 信息保留权重
                'rhythm': 0.2,           # 节奏优化权重
                'attractiveness': 0.15   # 吸引力权重
            }

            scores = {
                'compression': compression_analysis.get('compression_score', 0.0),
                'viral_features': viral_features_analysis.get('match_score', 0.0),
                'information': information_retention_analysis.get('retention_score', 0.0),
                'rhythm': rhythm_analysis.get('optimization_score', 0.0),
                'attractiveness': attractiveness_analysis.get('attractiveness_score', 0.0)
            }

            # 计算加权平均分
            weighted_score = sum(scores[key] * weights[key] for key in weights.keys())

            return max(0.0, min(1.0, weighted_score))

        except Exception as e:
            self.logger.error(f"总体评分计算失败: {str(e)}")
            return 0.0

    # 辅助方法
    def _calculate_total_duration(self, subtitles: List[Dict]) -> float:
        """计算字幕总时长"""
        if not subtitles:
            return 0.0

        try:
            last_subtitle = subtitles[-1]
            end_time_str = last_subtitle.get('end_time', '')
            return self._parse_timestamp(end_time_str) or 0.0
        except Exception:
            return 0.0

    def _parse_timestamp(self, timestamp_str: str) -> Optional[float]:
        """解析时间戳字符串为秒数"""
        try:
            if not timestamp_str or '-->' in timestamp_str:
                return None

            timestamp_str = timestamp_str.strip()

            if ',' in timestamp_str:
                time_part, ms_part = timestamp_str.split(',')
                milliseconds = int(ms_part)
            else:
                time_part = timestamp_str
                milliseconds = 0

            time_components = time_part.split(':')
            if len(time_components) != 3:
                return None

            hours = int(time_components[0])
            minutes = int(time_components[1])
            seconds = int(time_components[2])

            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds

        except (ValueError, IndexError):
            return None

    def _save_subtitles_to_file(self, subtitles: List[Dict], file_path: str):
        """保存字幕到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, subtitle in enumerate(subtitles, 1):
                    f.write(f"{i}\n")
                    f.write(f"{subtitle.get('start_time', '')} --> {subtitle.get('end_time', '')}\n")
                    f.write(f"{subtitle.get('text', '')}\n\n")
        except Exception as e:
            self.logger.error(f"保存字幕文件失败: {str(e)}")

    # 简化的分析方法（实际实现应该更复杂）
    def _analyze_hook_strength(self, text: str) -> float:
        """分析开头吸引力"""
        hook_keywords = ['突然', '竟然', '没想到', '震惊', '意外', 'suddenly', 'shocking', 'unexpected']
        score = sum(1 for keyword in hook_keywords if keyword in text.lower())
        return min(1.0, score / 3.0)

    def _analyze_conflict_tension(self, subtitles: List[Dict]) -> float:
        """分析冲突张力"""
        tension_keywords = ['冲突', '矛盾', '争吵', '对抗', 'conflict', 'tension', 'argument']
        total_score = 0
        for subtitle in subtitles:
            text = subtitle.get('text', '').lower()
            total_score += sum(1 for keyword in tension_keywords if keyword in text)
        return min(1.0, total_score / len(subtitles) if subtitles else 0.0)

    def _analyze_emotional_peaks(self, subtitles: List[Dict]) -> float:
        """分析情感高潮"""
        # 简化实现：检查情感强烈的词汇
        emotional_keywords = ['激动', '愤怒', '感动', '震撼', 'excited', 'angry', 'moved', 'shocked']
        peak_count = 0
        for subtitle in subtitles:
            text = subtitle.get('text', '').lower()
            if any(keyword in text for keyword in emotional_keywords):
                peak_count += 1
        return min(1.0, peak_count / max(1, len(subtitles) // 10))

    def _analyze_cliffhanger_strength(self, text: str) -> float:
        """分析悬念结尾"""
        cliffhanger_patterns = ['...', '？', '?', '待续', 'to be continued', '下集']
        score = sum(1 for pattern in cliffhanger_patterns if pattern in text)
        return min(1.0, score / 2.0)

    def _analyze_pacing_rhythm(self, subtitles: List[Dict]) -> float:
        """分析节奏感"""
        if len(subtitles) < 2:
            return 0.5

        # 计算字幕间隔的变化
        intervals = []
        for i in range(1, len(subtitles)):
            prev_end = self._parse_timestamp(subtitles[i-1].get('end_time', ''))
            curr_start = self._parse_timestamp(subtitles[i].get('start_time', ''))
            if prev_end and curr_start:
                intervals.append(curr_start - prev_end)

        if not intervals:
            return 0.5

        # 节奏变化的标准差，适度变化表示好的节奏感
        std_dev = np.std(intervals)
        optimal_std = 2.0  # 2秒的标准差被认为是理想的
        rhythm_score = 1.0 - abs(std_dev - optimal_std) / optimal_std
        return max(0.0, min(1.0, rhythm_score))

    def _extract_keywords(self, subtitles: List[Dict]) -> List[str]:
        """提取关键词"""
        # 简化实现：提取常见的重要词汇
        text = " ".join([sub.get('text', '') for sub in subtitles])
        # 这里应该使用更复杂的NLP技术
        words = text.split()
        # 过滤停用词并返回重要词汇
        important_words = [word for word in words if len(word) > 2]
        return list(set(important_words))[:20]  # 返回前20个唯一词汇

    def _analyze_plot_completeness(self, original_subtitles: List[Dict],
                                 generated_subtitles: List[Dict]) -> float:
        """分析情节完整性"""
        # 简化实现：基于长度比例估算
        if not original_subtitles:
            return 0.0

        length_ratio = len(generated_subtitles) / len(original_subtitles)
        # 如果生成的字幕保持了原片30%-70%的长度，认为情节相对完整
        if 0.3 <= length_ratio <= 0.7:
            return 0.8
        elif length_ratio < 0.3:
            return 0.5  # 过度压缩
        else:
            return 0.6  # 压缩不足

    def _analyze_character_retention(self, original_subtitles: List[Dict],
                                   generated_subtitles: List[Dict]) -> float:
        """分析角色保留度"""
        # 简化实现：检查对话标识符
        original_speakers = set()
        generated_speakers = set()

        for subtitle in original_subtitles:
            text = subtitle.get('text', '')
            if ':' in text:
                speaker = text.split(':')[0].strip()
                original_speakers.add(speaker)

        for subtitle in generated_subtitles:
            text = subtitle.get('text', '')
            if ':' in text:
                speaker = text.split(':')[0].strip()
                generated_speakers.add(speaker)

        if not original_speakers:
            return 0.5  # 无法判断

        retained_speakers = original_speakers.intersection(generated_speakers)
        return len(retained_speakers) / len(original_speakers)

    def _calculate_rhythm_metrics(self, subtitles: List[Dict]) -> Dict[str, float]:
        """计算节奏指标"""
        if len(subtitles) < 2:
            return {'avg_interval': 0.0, 'interval_variance': 0.0}

        intervals = []
        for i in range(1, len(subtitles)):
            prev_end = self._parse_timestamp(subtitles[i-1].get('end_time', ''))
            curr_start = self._parse_timestamp(subtitles[i].get('start_time', ''))
            if prev_end and curr_start:
                intervals.append(curr_start - prev_end)

        if not intervals:
            return {'avg_interval': 0.0, 'interval_variance': 0.0}

        return {
            'avg_interval': np.mean(intervals),
            'interval_variance': np.var(intervals)
        }

    # 其他简化的分析方法
    def _analyze_tension_building(self, subtitles: List[Dict]) -> float:
        """分析张力构建"""
        return 0.7  # 简化返回固定值

    def _analyze_climax_positioning(self, subtitles: List[Dict]) -> float:
        """分析高潮定位"""
        return 0.8  # 简化返回固定值

    def _analyze_transition_smoothness(self, subtitles: List[Dict]) -> float:
        """分析转场流畅性"""
        return 0.75  # 简化返回固定值

    def _analyze_curiosity_triggers(self, subtitles: List[Dict]) -> float:
        """分析好奇心触发"""
        return 0.7  # 简化返回固定值

    def _analyze_emotional_engagement(self, subtitles: List[Dict]) -> float:
        """分析情感参与度"""
        return 0.8  # 简化返回固定值

    def _analyze_surprise_elements(self, subtitles: List[Dict]) -> float:
        """分析惊喜元素"""
        return 0.6  # 简化返回固定值

    def _analyze_relatability(self, subtitles: List[Dict]) -> float:
        """分析共鸣度"""
        return 0.75  # 简化返回固定值

    def _analyze_shareability(self, subtitles: List[Dict]) -> float:
        """分析分享价值"""
        return 0.7  # 简化返回固定值


class TestViralGeneration(unittest.TestCase):
    """爆款生成测试用例类"""

    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = ViralGenerationTester()

    def test_compression_ratio(self):
        """测试压缩比"""
        test_subtitle_path = "test_data/subtitles/test_original.srt"

        if os.path.exists(test_subtitle_path):
            result = self.tester.test_viral_generation(test_subtitle_path)

            self.assertGreaterEqual(result.compression_ratio, 0.3, "压缩比应≥30%")
            self.assertLessEqual(result.compression_ratio, 0.7, "压缩比应≤70%")

    def test_viral_features_match(self):
        """测试爆款特征匹配"""
        test_subtitle_path = "test_data/subtitles/test_original.srt"

        if os.path.exists(test_subtitle_path):
            result = self.tester.test_viral_generation(test_subtitle_path)

            self.assertGreaterEqual(result.viral_features_match, 0.75, "爆款特征匹配度应≥75%")

    def test_information_retention(self):
        """测试信息保留度"""
        test_subtitle_path = "test_data/subtitles/test_original.srt"

        if os.path.exists(test_subtitle_path):
            result = self.tester.test_viral_generation(test_subtitle_path)

            self.assertGreaterEqual(result.key_information_retention, 0.6, "关键信息保留度应≥60%")


if __name__ == "__main__":
    unittest.main(verbosity=2)
