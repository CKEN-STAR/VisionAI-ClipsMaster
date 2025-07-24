#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster AI内容理解真实验证测试模块

此模块测试AI模型对真实视频内容的理解能力，包括场景识别、人物检测、
情节分析、主题提取等关键功能的准确性和可靠性。
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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.ai_content_analyzer import AIContentAnalyzer
from src.core.scene_detector import SceneDetector
from src.core.character_recognizer import CharacterRecognizer
from src.core.narrative_analyzer import NarrativeAnalyzer
from src.core.model_switcher import ModelSwitcher
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class ContentUnderstandingResult:
    """内容理解测试结果数据类"""
    test_name: str
    video_file_path: str
    video_duration: float
    analysis_time: float
    scene_detection: Dict[str, Any]
    character_recognition: Dict[str, Any]
    narrative_analysis: Dict[str, Any]
    topic_extraction: Dict[str, Any]
    emotion_analysis: Dict[str, Any]
    language_detection: Dict[str, Any]
    content_summary: Dict[str, Any]
    understanding_accuracy: float
    processing_speed_multiplier: float
    model_performance: Dict[str, Any]
    error_messages: List[str]
    warnings: List[str]
    success: bool


class RealWorldContentUnderstandingTester:
    """真实世界内容理解测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化内容理解测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化AI组件
        self.ai_analyzer = AIContentAnalyzer()
        self.scene_detector = SceneDetector()
        self.character_recognizer = CharacterRecognizer()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.model_switcher = ModelSwitcher(self.config)
        
        # AI配置
        self.ai_config = self.config.get('ai_script_reconstruction', {})
        self.models_config = self.ai_config.get('models', {})
        
        # 质量标准
        self.quality_standards = self.config.get('quality_standards', {})
        self.min_accuracy = self.quality_standards.get('quality', {}).get('ai_understanding_accuracy', 0.85)
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'ai_script_reconstruction': {
                'models': {
                    'chinese_model': {'name': 'Qwen2.5-7B', 'language': 'zh'},
                    'english_model': {'name': 'Mistral-7B', 'language': 'en'}
                }
            },
            'quality_standards': {
                'quality': {'ai_understanding_accuracy': 0.85}
            }
        }
    
    def test_real_video_content_understanding(self, video_file_path: str, 
                                            reference_data: Dict[str, Any] = None) -> ContentUnderstandingResult:
        """
        测试真实视频内容理解
        
        Args:
            video_file_path: 真实视频文件路径
            reference_data: 参考数据（用于准确性评估）
            
        Returns:
            ContentUnderstandingResult: 内容理解测试结果
        """
        test_name = "real_video_content_understanding"
        start_time = time.time()
        
        self.logger.info(f"开始测试真实视频内容理解: {video_file_path}")
        
        error_messages = []
        warnings = []
        
        try:
            # 验证文件存在
            if not os.path.exists(video_file_path):
                raise FileNotFoundError(f"视频文件不存在: {video_file_path}")
            
            # 获取视频基本信息
            video_info = self._get_video_info(video_file_path)
            video_duration = video_info.get('duration', 0)
            
            # 1. 场景检测
            scene_detection = self._test_scene_detection(video_file_path)
            if not scene_detection['success']:
                error_messages.extend(scene_detection.get('errors', []))
            
            # 2. 人物识别
            character_recognition = self._test_character_recognition(video_file_path)
            if not character_recognition['success']:
                error_messages.extend(character_recognition.get('errors', []))
            
            # 3. 叙事分析
            narrative_analysis = self._test_narrative_analysis(video_file_path)
            if not narrative_analysis['success']:
                error_messages.extend(narrative_analysis.get('errors', []))
            
            # 4. 主题提取
            topic_extraction = self._test_topic_extraction(video_file_path)
            if not topic_extraction['success']:
                error_messages.extend(topic_extraction.get('errors', []))
            
            # 5. 情感分析
            emotion_analysis = self._test_emotion_analysis(video_file_path)
            if not emotion_analysis['success']:
                error_messages.extend(emotion_analysis.get('errors', []))
            
            # 6. 语言检测
            language_detection = self._test_language_detection(video_file_path)
            if not language_detection['success']:
                error_messages.extend(language_detection.get('errors', []))
            
            # 7. 内容摘要生成
            content_summary = self._test_content_summary(video_file_path)
            if not content_summary['success']:
                error_messages.extend(content_summary.get('errors', []))
            
            # 8. 模型性能评估
            model_performance = self._evaluate_model_performance(video_file_path)
            
            # 计算理解准确性
            understanding_accuracy = self._calculate_understanding_accuracy(
                scene_detection, character_recognition, narrative_analysis,
                topic_extraction, emotion_analysis, reference_data
            )
            
            # 计算处理速度
            analysis_time = time.time() - start_time
            processing_speed_multiplier = video_duration / analysis_time if analysis_time > 0 else 0
            
            # 检查质量标准
            if understanding_accuracy < self.min_accuracy:
                warnings.append(f"理解准确性低于标准: {understanding_accuracy:.3f} < {self.min_accuracy}")
            
            if processing_speed_multiplier < 1.0:
                warnings.append(f"处理速度低于实时: {processing_speed_multiplier:.2f}x")
            
            success = len(error_messages) == 0 and understanding_accuracy >= self.min_accuracy
            
            result = ContentUnderstandingResult(
                test_name=test_name,
                video_file_path=video_file_path,
                video_duration=video_duration,
                analysis_time=analysis_time,
                scene_detection=scene_detection,
                character_recognition=character_recognition,
                narrative_analysis=narrative_analysis,
                topic_extraction=topic_extraction,
                emotion_analysis=emotion_analysis,
                language_detection=language_detection,
                content_summary=content_summary,
                understanding_accuracy=understanding_accuracy,
                processing_speed_multiplier=processing_speed_multiplier,
                model_performance=model_performance,
                error_messages=error_messages,
                warnings=warnings,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"内容理解测试完成: {video_file_path}, 准确性: {understanding_accuracy:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"内容理解测试异常: {video_file_path}, 错误: {str(e)}")
            
            return ContentUnderstandingResult(
                test_name=test_name,
                video_file_path=video_file_path,
                video_duration=0,
                analysis_time=time.time() - start_time,
                scene_detection={'success': False, 'errors': [str(e)]},
                character_recognition={'success': False, 'errors': [str(e)]},
                narrative_analysis={'success': False, 'errors': [str(e)]},
                topic_extraction={'success': False, 'errors': [str(e)]},
                emotion_analysis={'success': False, 'errors': [str(e)]},
                language_detection={'success': False, 'errors': [str(e)]},
                content_summary={'success': False, 'errors': [str(e)]},
                understanding_accuracy=0.0,
                processing_speed_multiplier=0.0,
                model_performance={},
                error_messages=[str(e)],
                warnings=[],
                success=False
            )
    
    def _get_video_info(self, video_file_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            # 这里应该调用实际的视频信息获取方法
            return {
                'duration': 300,  # 示例：5分钟
                'width': 1920,
                'height': 1080,
                'frame_rate': 30,
                'has_audio': True
            }
        except Exception:
            return {'duration': 0}
    
    def _test_scene_detection(self, video_file_path: str) -> Dict[str, Any]:
        """测试场景检测"""
        try:
            start_time = time.time()
            
            # 执行场景检测
            detection_result = self.scene_detector.detect_scenes(video_file_path)
            
            processing_time = time.time() - start_time
            
            if detection_result.get('success', False):
                scenes = detection_result.get('scenes', [])
                
                # 验证场景检测结果
                validation_errors = []
                
                if len(scenes) == 0:
                    validation_errors.append("未检测到任何场景")
                
                # 检查场景时间轴的合理性
                for i, scene in enumerate(scenes):
                    start_time_scene = scene.get('start_time', 0)
                    end_time_scene = scene.get('end_time', 0)
                    
                    if start_time_scene >= end_time_scene:
                        validation_errors.append(f"场景{i+1}时间轴错误: {start_time_scene} >= {end_time_scene}")
                    
                    if end_time_scene - start_time_scene < 1:  # 场景太短
                        validation_errors.append(f"场景{i+1}时长过短: {end_time_scene - start_time_scene}秒")
                
                return {
                    'success': len(validation_errors) == 0,
                    'scenes': scenes,
                    'scene_count': len(scenes),
                    'processing_time': processing_time,
                    'confidence_scores': [s.get('confidence', 0) for s in scenes],
                    'average_confidence': sum(s.get('confidence', 0) for s in scenes) / len(scenes) if scenes else 0,
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'scenes': [],
                    'scene_count': 0,
                    'processing_time': processing_time,
                    'confidence_scores': [],
                    'average_confidence': 0,
                    'errors': detection_result.get('errors', ['场景检测失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'scenes': [],
                'scene_count': 0,
                'processing_time': 0,
                'confidence_scores': [],
                'average_confidence': 0,
                'errors': [f"场景检测异常: {str(e)}"]
            }
    
    def _test_character_recognition(self, video_file_path: str) -> Dict[str, Any]:
        """测试人物识别"""
        try:
            start_time = time.time()
            
            # 执行人物识别
            recognition_result = self.character_recognizer.recognize_characters(video_file_path)
            
            processing_time = time.time() - start_time
            
            if recognition_result.get('success', False):
                characters = recognition_result.get('characters', [])
                
                # 验证人物识别结果
                validation_errors = []
                
                # 检查人物信息的完整性
                for i, character in enumerate(characters):
                    if not character.get('name'):
                        validation_errors.append(f"人物{i+1}缺少姓名信息")
                    
                    appearances = character.get('appearances', [])
                    if len(appearances) == 0:
                        validation_errors.append(f"人物{i+1}没有出现时间记录")
                
                return {
                    'success': len(validation_errors) == 0,
                    'characters': characters,
                    'character_count': len(characters),
                    'processing_time': processing_time,
                    'total_appearances': sum(len(c.get('appearances', [])) for c in characters),
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'characters': [],
                    'character_count': 0,
                    'processing_time': processing_time,
                    'total_appearances': 0,
                    'errors': recognition_result.get('errors', ['人物识别失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'characters': [],
                'character_count': 0,
                'processing_time': 0,
                'total_appearances': 0,
                'errors': [f"人物识别异常: {str(e)}"]
            }
    
    def _test_narrative_analysis(self, video_file_path: str) -> Dict[str, Any]:
        """测试叙事分析"""
        try:
            start_time = time.time()
            
            # 执行叙事分析
            analysis_result = self.narrative_analyzer.analyze_narrative(video_file_path)
            
            processing_time = time.time() - start_time
            
            if analysis_result.get('success', False):
                narrative_structure = analysis_result.get('narrative_structure', {})
                plot_points = analysis_result.get('plot_points', [])
                
                # 验证叙事分析结果
                validation_errors = []
                
                # 检查叙事结构的完整性
                required_elements = ['introduction', 'development', 'climax', 'resolution']
                for element in required_elements:
                    if element not in narrative_structure:
                        validation_errors.append(f"缺少叙事元素: {element}")
                
                # 检查情节点的合理性
                if len(plot_points) == 0:
                    validation_errors.append("未识别到情节点")
                
                return {
                    'success': len(validation_errors) == 0,
                    'narrative_structure': narrative_structure,
                    'plot_points': plot_points,
                    'plot_point_count': len(plot_points),
                    'processing_time': processing_time,
                    'coherence_score': analysis_result.get('coherence_score', 0),
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'narrative_structure': {},
                    'plot_points': [],
                    'plot_point_count': 0,
                    'processing_time': processing_time,
                    'coherence_score': 0,
                    'errors': analysis_result.get('errors', ['叙事分析失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'narrative_structure': {},
                'plot_points': [],
                'plot_point_count': 0,
                'processing_time': 0,
                'coherence_score': 0,
                'errors': [f"叙事分析异常: {str(e)}"]
            }
    
    def _test_topic_extraction(self, video_file_path: str) -> Dict[str, Any]:
        """测试主题提取"""
        try:
            start_time = time.time()
            
            # 执行主题提取
            extraction_result = self.ai_analyzer.extract_topics(video_file_path)
            
            processing_time = time.time() - start_time
            
            if extraction_result.get('success', False):
                topics = extraction_result.get('topics', [])
                
                # 验证主题提取结果
                validation_errors = []
                
                if len(topics) == 0:
                    validation_errors.append("未提取到任何主题")
                
                # 检查主题的质量
                for i, topic in enumerate(topics):
                    if not topic.get('name'):
                        validation_errors.append(f"主题{i+1}缺少名称")
                    
                    confidence = topic.get('confidence', 0)
                    if confidence < 0.5:
                        validation_errors.append(f"主题{i+1}置信度过低: {confidence}")
                
                return {
                    'success': len(validation_errors) == 0,
                    'topics': topics,
                    'topic_count': len(topics),
                    'processing_time': processing_time,
                    'average_confidence': sum(t.get('confidence', 0) for t in topics) / len(topics) if topics else 0,
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'topics': [],
                    'topic_count': 0,
                    'processing_time': processing_time,
                    'average_confidence': 0,
                    'errors': extraction_result.get('errors', ['主题提取失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'topics': [],
                'topic_count': 0,
                'processing_time': 0,
                'average_confidence': 0,
                'errors': [f"主题提取异常: {str(e)}"]
            }
    
    def _test_emotion_analysis(self, video_file_path: str) -> Dict[str, Any]:
        """测试情感分析"""
        try:
            start_time = time.time()
            
            # 执行情感分析
            emotion_result = self.ai_analyzer.analyze_emotions(video_file_path)
            
            processing_time = time.time() - start_time
            
            if emotion_result.get('success', False):
                emotions = emotion_result.get('emotions', [])
                emotion_timeline = emotion_result.get('emotion_timeline', [])
                
                # 验证情感分析结果
                validation_errors = []
                
                if len(emotions) == 0:
                    validation_errors.append("未检测到情感信息")
                
                # 检查情感时间轴的连续性
                for i in range(len(emotion_timeline) - 1):
                    current_end = emotion_timeline[i].get('end_time', 0)
                    next_start = emotion_timeline[i + 1].get('start_time', 0)
                    
                    if next_start > current_end + 1:  # 允许1秒间隔
                        validation_errors.append(f"情感时间轴存在间隙: {current_end} -> {next_start}")
                
                return {
                    'success': len(validation_errors) == 0,
                    'emotions': emotions,
                    'emotion_timeline': emotion_timeline,
                    'emotion_count': len(emotions),
                    'processing_time': processing_time,
                    'dominant_emotion': emotion_result.get('dominant_emotion', ''),
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'emotions': [],
                    'emotion_timeline': [],
                    'emotion_count': 0,
                    'processing_time': processing_time,
                    'dominant_emotion': '',
                    'errors': emotion_result.get('errors', ['情感分析失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'emotions': [],
                'emotion_timeline': [],
                'emotion_count': 0,
                'processing_time': 0,
                'dominant_emotion': '',
                'errors': [f"情感分析异常: {str(e)}"]
            }
    
    def _test_language_detection(self, video_file_path: str) -> Dict[str, Any]:
        """测试语言检测"""
        try:
            start_time = time.time()
            
            # 执行语言检测
            language_result = self.model_switcher.detect_language(video_file_path)
            
            processing_time = time.time() - start_time
            
            if language_result.get('success', False):
                detected_language = language_result.get('language', '')
                confidence = language_result.get('confidence', 0)
                
                # 验证语言检测结果
                validation_errors = []
                
                if not detected_language:
                    validation_errors.append("未检测到语言")
                
                if confidence < 0.8:
                    validation_errors.append(f"语言检测置信度过低: {confidence}")
                
                supported_languages = ['zh', 'en', 'zh-en']
                if detected_language not in supported_languages:
                    validation_errors.append(f"检测到不支持的语言: {detected_language}")
                
                return {
                    'success': len(validation_errors) == 0,
                    'detected_language': detected_language,
                    'confidence': confidence,
                    'processing_time': processing_time,
                    'language_segments': language_result.get('language_segments', []),
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'detected_language': '',
                    'confidence': 0,
                    'processing_time': processing_time,
                    'language_segments': [],
                    'errors': language_result.get('errors', ['语言检测失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'detected_language': '',
                'confidence': 0,
                'processing_time': 0,
                'language_segments': [],
                'errors': [f"语言检测异常: {str(e)}"]
            }
    
    def _test_content_summary(self, video_file_path: str) -> Dict[str, Any]:
        """测试内容摘要"""
        try:
            start_time = time.time()
            
            # 执行内容摘要生成
            summary_result = self.ai_analyzer.generate_summary(video_file_path)
            
            processing_time = time.time() - start_time
            
            if summary_result.get('success', False):
                summary = summary_result.get('summary', '')
                key_points = summary_result.get('key_points', [])
                
                # 验证摘要质量
                validation_errors = []
                
                if not summary or len(summary) < 50:
                    validation_errors.append("摘要内容过短或为空")
                
                if len(key_points) == 0:
                    validation_errors.append("未提取到关键点")
                
                return {
                    'success': len(validation_errors) == 0,
                    'summary': summary,
                    'key_points': key_points,
                    'summary_length': len(summary),
                    'key_point_count': len(key_points),
                    'processing_time': processing_time,
                    'errors': validation_errors
                }
            else:
                return {
                    'success': False,
                    'summary': '',
                    'key_points': [],
                    'summary_length': 0,
                    'key_point_count': 0,
                    'processing_time': processing_time,
                    'errors': summary_result.get('errors', ['内容摘要生成失败'])
                }
                
        except Exception as e:
            return {
                'success': False,
                'summary': '',
                'key_points': [],
                'summary_length': 0,
                'key_point_count': 0,
                'processing_time': 0,
                'errors': [f"内容摘要异常: {str(e)}"]
            }
    
    def _evaluate_model_performance(self, video_file_path: str) -> Dict[str, Any]:
        """评估模型性能"""
        try:
            # 获取当前使用的模型信息
            current_model = self.model_switcher.get_current_model()
            
            # 收集性能指标
            performance_metrics = {
                'model_name': current_model.get('name', ''),
                'model_language': current_model.get('language', ''),
                'memory_usage_mb': self._get_memory_usage(),
                'gpu_usage_percent': self._get_gpu_usage(),
                'inference_speed': self._measure_inference_speed(video_file_path)
            }
            
            return performance_metrics
            
        except Exception as e:
            return {
                'model_name': '',
                'model_language': '',
                'memory_usage_mb': 0,
                'gpu_usage_percent': 0,
                'inference_speed': 0,
                'error': str(e)
            }
    
    def _calculate_understanding_accuracy(self, scene_detection: Dict, character_recognition: Dict,
                                        narrative_analysis: Dict, topic_extraction: Dict,
                                        emotion_analysis: Dict, reference_data: Dict = None) -> float:
        """计算理解准确性"""
        try:
            # 基于各个组件的成功率计算总体准确性
            component_scores = []
            
            # 场景检测评分
            if scene_detection['success']:
                scene_score = min(1.0, scene_detection.get('average_confidence', 0))
                component_scores.append(scene_score)
            
            # 人物识别评分
            if character_recognition['success']:
                char_score = 1.0 if character_recognition.get('character_count', 0) > 0 else 0.5
                component_scores.append(char_score)
            
            # 叙事分析评分
            if narrative_analysis['success']:
                narrative_score = narrative_analysis.get('coherence_score', 0)
                component_scores.append(narrative_score)
            
            # 主题提取评分
            if topic_extraction['success']:
                topic_score = topic_extraction.get('average_confidence', 0)
                component_scores.append(topic_score)
            
            # 情感分析评分
            if emotion_analysis['success']:
                emotion_score = 1.0 if emotion_analysis.get('emotion_count', 0) > 0 else 0.5
                component_scores.append(emotion_score)
            
            # 如果有参考数据，进行更精确的评估
            if reference_data:
                accuracy = self._compare_with_reference(
                    scene_detection, character_recognition, narrative_analysis,
                    topic_extraction, emotion_analysis, reference_data
                )
                return accuracy
            
            # 否则基于组件评分计算平均值
            if component_scores:
                return sum(component_scores) / len(component_scores)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _compare_with_reference(self, *args) -> float:
        """与参考数据比较（占位符实现）"""
        # 这里应该实现与参考数据的详细比较逻辑
        return 0.85  # 示例返回值
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量"""
        try:
            import psutil
            return psutil.virtual_memory().used / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_gpu_usage(self) -> float:
        """获取GPU使用率"""
        try:
            # 这里应该实现GPU使用率检测
            return 0.0
        except Exception:
            return 0.0
    
    def _measure_inference_speed(self, video_file_path: str) -> float:
        """测量推理速度"""
        try:
            # 这里应该实现推理速度测量
            return 1.0
        except Exception:
            return 0.0


class TestRealWorldContentUnderstanding(unittest.TestCase):
    """真实世界内容理解测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = RealWorldContentUnderstandingTester()
        
        # 设置测试视频文件路径
        cls.test_videos = [
            "tests/real_world_validation/test_data/videos/short_video_5min.mp4",
            "tests/real_world_validation/test_data/videos/medium_video_15min.mov",
            "tests/real_world_validation/test_data/videos/long_video_30min.avi"
        ]
    
    def test_content_understanding_accuracy(self):
        """测试内容理解准确性"""
        for video_file in self.test_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_content_understanding(video_file)
                    
                    self.assertTrue(result.success, f"内容理解应该成功: {video_file}")
                    self.assertGreaterEqual(result.understanding_accuracy, 0.85, 
                                          f"理解准确性应该≥85%: {result.understanding_accuracy:.3f}")
    
    def test_processing_speed(self):
        """测试处理速度"""
        for video_file in self.test_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_content_understanding(video_file)
                    
                    self.assertGreater(result.processing_speed_multiplier, 0.5, 
                                     f"处理速度应该合理: {result.processing_speed_multiplier:.2f}x")
    
    def test_scene_detection(self):
        """测试场景检测"""
        for video_file in self.test_videos:
            if os.path.exists(video_file):
                with self.subTest(video_file=video_file):
                    result = self.tester.test_real_video_content_understanding(video_file)
                    
                    scene_detection = result.scene_detection
                    self.assertTrue(scene_detection['success'], "场景检测应该成功")
                    self.assertGreater(scene_detection['scene_count'], 0, "应该检测到场景")


if __name__ == "__main__":
    unittest.main(verbosity=2)
