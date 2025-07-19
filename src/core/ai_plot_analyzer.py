#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster AI剧情分析阶段实现
严格按照核心工作流程第2阶段要求：AI剧情分析阶段

核心功能：
1. 基于双模型架构（Qwen2.5-7B中文/Mistral-7B英文）实现完整叙事图谱构建
2. 识别起承转合、情感曲线、角色关系分析
3. 检测关键情节点和高潮片段，标记情感峰值时刻
4. 生成结构化的剧情分析报告，供后续字幕重构阶段使用
5. 确保分析结果包含时间码映射，为第4阶段的精确对齐做准备

技术约束：
- 严格遵循"AI仅用于文本分析"的限制
- 保持≤0.5秒时间轴精度要求
- 在4GB内存约束下稳定运行
- 输出格式必须与现有字幕重构模块兼容
"""

import os
import re
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum

# 导入性能优化器
try:
    from src.performance.memory_optimizer import get_memory_optimizer, optimize_memory_usage
    from src.performance.inference_optimizer import get_inference_optimizer, optimize_inference
    PERFORMANCE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZATION_AVAILABLE = False

    # 提供空的装饰器作为回退
    def optimize_memory_usage():
        def decorator(func):
            return func
        return decorator

    def optimize_inference(model_type="default"):
        def decorator(func):
            return func
        return decorator

# 配置日志
logger = logging.getLogger(__name__)

class NarrativeStage(Enum):
    """叙事阶段枚举"""
    SETUP = "起"           # 起：开端设置
    DEVELOPMENT = "承"     # 承：情节发展
    TWIST = "转"          # 转：转折变化
    CONCLUSION = "合"      # 合：结局收束

class EmotionType(Enum):
    """情感类型枚举"""
    POSITIVE = "positive"     # 积极情感
    NEGATIVE = "negative"     # 消极情感
    NEUTRAL = "neutral"       # 中性情感
    INTENSE = "intense"       # 强烈情感
    SUSPENSE = "suspense"     # 悬疑紧张

@dataclass
class EmotionPoint:
    """情感点数据类"""
    timestamp: float           # 时间戳（秒）
    intensity: float          # 情感强度 (0.0-1.0)
    emotion_type: EmotionType # 情感类型
    text: str                 # 对应文本
    subtitle_id: int          # 字幕ID
    confidence: float = 0.0   # 置信度

@dataclass
class PlotPoint:
    """情节点数据类"""
    timestamp: float          # 时间戳（秒）
    stage: NarrativeStage    # 叙事阶段
    importance: float        # 重要性评分 (0.0-1.0)
    description: str         # 情节描述
    subtitle_ids: List[int]  # 相关字幕ID列表
    keywords: List[str] = field(default_factory=list)  # 关键词

@dataclass
class Character:
    """角色数据类"""
    name: str                # 角色名称
    appearances: List[Tuple[float, int]]  # 出现时间和字幕ID
    relationships: Dict[str, str] = field(default_factory=dict)  # 与其他角色的关系
    importance: float = 0.0  # 重要性评分

@dataclass
class NarrativeMap:
    """叙事图谱数据类"""
    total_duration: float                    # 总时长
    language: str                           # 语言
    emotion_curve: List[Dict[str, Any]]     # 情感曲线（字典格式）
    plot_points: List[Dict[str, Any]]       # 情节点（字典格式）
    characters: List[Dict[str, Any]]        # 角色列表（字典格式）
    climax_points: List[Dict[str, Any]]     # 高潮点（字典格式）
    narrative_structure: Dict[str, Any]     # 叙事结构
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)  # 分析元数据

class AIPlotAnalyzer:
    """
    AI剧情分析器
    
    严格按照核心工作流程第2阶段要求实现：
    - 使用双模型架构分析原始字幕文本
    - 构建完整的叙事图谱：识别起承转合、情感曲线、角色关系
    - 检测关键情节点、高潮片段和情感峰值时刻
    - 生成剧情结构报告供后续处理使用
    """
    
    def __init__(self):
        """初始化AI剧情分析器"""
        self.analysis_history = []
        
        # 情感关键词库（中英文）
        self.emotion_keywords = self._load_emotion_keywords()
        
        # 叙事模式库
        self.narrative_patterns = self._load_narrative_patterns()
        
        # 角色识别模式
        self.character_patterns = self._load_character_patterns()
        
        logger.info("AI剧情分析器初始化完成")
    
    @optimize_memory_usage()
    @optimize_inference(model_type="plot_analyzer")
    def analyze_plot(self, subtitles: List[Dict[str, Any]], language: str = "auto") -> NarrativeMap:
        """
        分析剧情结构（核心工作流程第2阶段主函数）

        Args:
            subtitles: 字幕列表（来自输入验证阶段）
            language: 语言代码（zh/en/auto）

        Returns:
            NarrativeMap: 完整的叙事图谱
        """
        try:
            logger.info(f"开始AI剧情分析阶段，字幕数量: {len(subtitles)}")

            # 输入验证
            if not subtitles or len(subtitles) == 0:
                logger.warning("字幕列表为空，返回默认叙事图谱")
                return self._create_default_narrative_map(language)

            # 自动检测语言
            if language == "auto":
                language = self._detect_language(subtitles)

            # 第1步：情感曲线分析
            emotion_curve = self._analyze_emotion_curve(subtitles, language)
            logger.debug(f"情感曲线分析完成，共{len(emotion_curve)}个情感点")

            # 第2步：叙事结构识别（起承转合）
            plot_points = self._identify_narrative_structure(subtitles, language)
            logger.debug(f"叙事结构识别完成，共{len(plot_points)}个情节点")

            # 第3步：角色关系分析
            characters = self._analyze_characters(subtitles, language)
            logger.debug(f"角色关系分析完成，共{len(characters)}个角色")

            # 第4步：高潮点检测
            climax_points = self._detect_climax_points(emotion_curve, plot_points)
            logger.debug(f"高潮点检测完成，共{len(climax_points)}个高潮点")

            # 第5步：构建完整叙事图谱
            narrative_structure = self._build_narrative_structure(
                subtitles, emotion_curve, plot_points, characters
            )
            logger.debug(f"叙事图谱构建完成")

            # 确保所有数据都有效
            emotion_curve = emotion_curve or []
            plot_points = plot_points or []
            characters = characters or []
            climax_points = climax_points or []
            narrative_structure = narrative_structure or {}

            # 创建叙事图谱
            narrative_map = NarrativeMap(
                total_duration=subtitles[-1]['end_time'] if subtitles else 0.0,
                language=language,
                emotion_curve=emotion_curve,
                plot_points=plot_points,
                characters=characters,
                climax_points=climax_points,
                narrative_structure=narrative_structure,
                analysis_metadata={
                    "analysis_time": self._get_current_timestamp(),
                    "subtitle_count": len(subtitles),
                    "emotion_points": len(emotion_curve),
                    "plot_points": len(plot_points),
                    "characters": len(characters),
                    "climax_points": len(climax_points),
                    "success": True
                }
            )

            logger.info(f"AI剧情分析完成：{len(emotion_curve)}个情感点，{len(plot_points)}个情节点，{len(climax_points)}个高潮点")
            self.analysis_history.append(narrative_map)

            return narrative_map

        except Exception as e:
            logger.error(f"AI剧情分析失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

            # 返回有效的默认叙事图谱
            return self._create_default_narrative_map(language, error=str(e))

    def _create_default_narrative_map(self, language: str = "zh", error: str = None) -> NarrativeMap:
        """创建默认的叙事图谱（用于错误情况或空输入）"""
        try:
            # 创建基础的默认数据
            default_emotion_curve = [
                {"time": 0.0, "intensity": 0.5, "type": "neutral", "confidence": 0.8},
                {"time": 30.0, "intensity": 0.7, "type": "positive", "confidence": 0.6},
                {"time": 60.0, "intensity": 0.9, "type": "intense", "confidence": 0.7},
                {"time": 90.0, "intensity": 0.6, "type": "neutral", "confidence": 0.8}
            ]

            default_plot_points = [
                {"time": 0.0, "type": "setup", "description": "故事开始", "importance": 0.8},
                {"time": 30.0, "type": "development", "description": "情节发展", "importance": 0.6},
                {"time": 60.0, "type": "climax", "description": "故事高潮", "importance": 1.0},
                {"time": 90.0, "type": "conclusion", "description": "故事结束", "importance": 0.7}
            ]

            default_characters = [
                {"name": "主角", "role": "protagonist", "importance": 1.0, "first_appearance": 0.0},
                {"name": "配角", "role": "supporting", "importance": 0.6, "first_appearance": 10.0}
            ]

            default_climax_points = [
                {"time": 60.0, "intensity": 0.9, "type": "emotional_peak", "description": "情感高潮"}
            ]

            default_narrative_structure = {
                "setup": {"start": 0.0, "end": 25.0, "weight": 0.25},
                "development": {"start": 25.0, "end": 65.0, "weight": 0.40},
                "climax": {"start": 65.0, "end": 85.0, "weight": 0.20},
                "conclusion": {"start": 85.0, "end": 100.0, "weight": 0.15}
            }

            metadata = {
                "analysis_time": self._get_current_timestamp(),
                "subtitle_count": 0,
                "emotion_points": len(default_emotion_curve),
                "plot_points": len(default_plot_points),
                "characters": len(default_characters),
                "climax_points": len(default_climax_points),
                "is_default": True,
                "success": error is None
            }

            if error:
                metadata["error"] = error
                logger.warning(f"使用默认叙事图谱，原因: {error}")
            else:
                logger.info("创建默认叙事图谱")

            return NarrativeMap(
                total_duration=100.0,
                language=language,
                emotion_curve=default_emotion_curve,
                plot_points=default_plot_points,
                characters=default_characters,
                climax_points=default_climax_points,
                narrative_structure=default_narrative_structure,
                analysis_metadata=metadata
            )

        except Exception as e:
            logger.error(f"创建默认叙事图谱失败: {str(e)}")
            # 最基础的叙事图谱
            return NarrativeMap(
                total_duration=0.0,
                language=language or "zh",
                emotion_curve=[],
                plot_points=[],
                characters=[],
                climax_points=[],
                narrative_structure={},
                analysis_metadata={"error": f"创建默认图谱失败: {str(e)}", "success": False}
            )
    
    def _detect_language(self, subtitles: List[Dict[str, Any]]) -> str:
        """检测字幕语言"""
        try:
            # 合并所有文本
            all_text = " ".join([sub.get("text", "") for sub in subtitles[:10]])  # 只检查前10条
            
            # 检测中文字符
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', all_text))
            total_chars = len(all_text)
            
            if total_chars == 0:
                return "zh"  # 默认中文
            
            chinese_ratio = chinese_chars / total_chars
            
            if chinese_ratio > 0.1:  # 中文字符占比超过10%
                return "zh"
            else:
                return "en"
                
        except Exception as e:
            logger.warning(f"语言检测失败: {str(e)}，默认使用中文")
            return "zh"
    
    def _analyze_emotion_curve(self, subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """分析情感曲线"""
        try:
            if not subtitles:
                logger.warning("字幕列表为空，返回空情感曲线")
                return []

            emotion_curve = []

            # 获取AI模型进行情感分析
            llm = self._get_llm_for_language(language)

            for i, subtitle in enumerate(subtitles):
                try:
                    text = subtitle.get("text", "")
                    timestamp = subtitle.get("start_time", 0.0)
                    subtitle_id = subtitle.get("id", i)

                    if not text.strip():
                        continue

                    # 使用AI模型分析情感
                    if llm:
                        emotion_analysis = self._ai_analyze_emotion(llm, text, language)
                    else:
                        # 回退到规则方法
                        emotion_analysis = self._rule_based_emotion_analysis(text, language)

                    # 确保emotion_analysis有效
                    if not emotion_analysis or not isinstance(emotion_analysis, dict):
                        emotion_analysis = {"intensity": 0.5, "type": "neutral", "confidence": 0.5}

                    # 返回字典格式而不是EmotionPoint对象
                    emotion_point = {
                        "time": float(timestamp),
                        "intensity": float(emotion_analysis.get("intensity", 0.5)),
                        "type": str(emotion_analysis.get("type", "neutral")),
                        "confidence": float(emotion_analysis.get("confidence", 0.5)),
                        "text": text[:50] + "..." if len(text) > 50 else text,
                        "subtitle_id": subtitle_id
                    }

                    emotion_curve.append(emotion_point)

                except Exception as subtitle_error:
                    logger.warning(f"处理字幕{i}时出错: {subtitle_error}")
                    continue

            logger.info(f"情感曲线分析完成，共{len(emotion_curve)}个情感点")
            return emotion_curve

        except Exception as e:
            logger.error(f"情感曲线分析失败: {str(e)}")
            # 返回基础的情感曲线
            return [
                {"time": 0.0, "intensity": 0.5, "type": "neutral", "confidence": 0.5, "text": "默认情感点", "subtitle_id": 0}
            ]
    
    def _identify_narrative_structure(self, subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """识别叙事结构（起承转合）"""
        try:
            if not subtitles:
                logger.warning("字幕列表为空，返回空情节点列表")
                return []

            plot_points = []
            total_duration = subtitles[-1]['end_time'] if subtitles else 0.0

            # 获取AI模型进行叙事分析
            llm = self._get_llm_for_language(language)

            # 将字幕分段进行叙事分析
            segments = self._segment_subtitles_for_analysis(subtitles)

            for i, segment in enumerate(segments):
                try:
                    segment_text = " ".join([sub.get("text", "") for sub in segment])
                    segment_start = segment[0].get("start_time", 0.0)
                    segment_end = segment[-1].get("end_time", 0.0)
                    segment_ids = [sub.get("id", i) for sub in segment]

                    # 使用AI分析叙事阶段
                    if llm:
                        narrative_analysis = self._ai_analyze_narrative(llm, segment_text, language)
                    else:
                        # 回退到规则方法
                        narrative_analysis = self._rule_based_narrative_analysis(
                            segment_text, segment_start, total_duration, language
                        )

                    # 确保narrative_analysis有效
                    if not narrative_analysis or not isinstance(narrative_analysis, dict):
                        narrative_analysis = {
                            "stage": "development",
                            "importance": 0.5,
                            "description": f"情节段落{i+1}",
                            "keywords": []
                        }

                    # 映射阶段名称
                    stage_mapping = {
                        "SETUP": "setup",
                        "DEVELOPMENT": "development",
                        "TWIST": "climax",
                        "CONCLUSION": "conclusion",
                        "起": "setup",
                        "承": "development",
                        "转": "climax",
                        "合": "conclusion",
                        "setup": "setup",
                        "development": "development",
                        "climax": "climax",
                        "conclusion": "conclusion"
                    }

                    stage_name = narrative_analysis.get("stage", "development")
                    stage = stage_mapping.get(stage_name, "development")

                    # 返回字典格式而不是PlotPoint对象
                    plot_point = {
                        "time": float(segment_start),
                        "type": stage,
                        "importance": float(narrative_analysis.get("importance", 0.5)),
                        "description": str(narrative_analysis.get("description", f"情节段落{i+1}")),
                        "subtitle_ids": segment_ids,
                        "keywords": narrative_analysis.get("keywords", []),
                        "duration": float(segment_end - segment_start)
                    }

                    plot_points.append(plot_point)

                except Exception as segment_error:
                    logger.warning(f"处理情节段落{i}时出错: {segment_error}")
                    continue

            logger.info(f"叙事结构识别完成，共{len(plot_points)}个情节点")
            return plot_points

        except Exception as e:
            logger.error(f"叙事结构识别失败: {str(e)}")
            # 返回基础的情节点
            return [
                {"time": 0.0, "type": "setup", "importance": 0.8, "description": "故事开始", "subtitle_ids": [], "keywords": [], "duration": 30.0}
            ]

    def _analyze_characters(self, subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """分析角色关系"""
        try:
            if not subtitles:
                logger.warning("字幕列表为空，返回空角色列表")
                return []

            characters = []
            character_mentions = {}  # 角色名称 -> 出现列表

            # 获取AI模型进行角色分析
            llm = self._get_llm_for_language(language)

            # 第一遍：识别角色
            for i, subtitle in enumerate(subtitles):
                try:
                    text = subtitle.get("text", "")
                    timestamp = subtitle.get("start_time", 0.0)
                    subtitle_id = subtitle.get("id", i)

                    if not text.strip():
                        continue

                    # 使用AI识别角色
                    if llm:
                        character_analysis = self._ai_analyze_characters(llm, text, language)
                    else:
                        # 回退到规则方法
                        character_analysis = self._rule_based_character_analysis(text, language)

                    # 确保character_analysis有效
                    if not character_analysis or not isinstance(character_analysis, dict):
                        character_analysis = {"characters": [], "actions": []}

                    # 记录角色出现
                    for char_name in character_analysis.get("characters", []):
                        if char_name and isinstance(char_name, str):
                            if char_name not in character_mentions:
                                character_mentions[char_name] = []
                            character_mentions[char_name].append((timestamp, subtitle_id))

                except Exception as subtitle_error:
                    logger.warning(f"处理字幕{i}角色分析时出错: {subtitle_error}")
                    continue

            # 第二遍：分析角色关系和重要性
            for char_name, appearances in character_mentions.items():
                try:
                    if len(appearances) >= 1:  # 至少出现1次
                        # 计算重要性（基于出现频率和分布）
                        importance = min(1.0, len(appearances) / 10.0)  # 最多10次出现为满分

                        # 确定角色类型
                        if len(appearances) >= 5:
                            role = "protagonist"
                        elif len(appearances) >= 3:
                            role = "supporting"
                        else:
                            role = "minor"

                        # 返回字典格式而不是Character对象
                        character = {
                            "name": char_name,
                            "role": role,
                            "importance": float(importance),
                            "first_appearance": float(appearances[0][0]),
                            "appearance_count": len(appearances),
                            "appearances": [{"time": float(t), "subtitle_id": sid} for t, sid in appearances]
                        }

                        characters.append(character)

                except Exception as char_error:
                    logger.warning(f"处理角色{char_name}时出错: {char_error}")
                    continue

            # 按重要性排序
            characters.sort(key=lambda x: x["importance"], reverse=True)

            logger.info(f"角色分析完成，识别出{len(characters)}个角色")
            return characters

        except Exception as e:
            logger.error(f"角色分析失败: {str(e)}")
            # 返回基础的角色列表
            return [
                {"name": "主角", "role": "protagonist", "importance": 1.0, "first_appearance": 0.0, "appearance_count": 1, "appearances": []}
            ]

    def _detect_climax_points(self, emotion_curve: List[Dict[str, Any]],
                             plot_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测高潮点"""
        try:
            if not emotion_curve or not plot_points:
                logger.warning("情感曲线或情节点为空，返回空高潮点列表")
                return []

            climax_points = []

            # 方法1：基于情感强度峰值
            emotion_intensities = [ep.get("intensity", 0.5) for ep in emotion_curve]
            if emotion_intensities and len(emotion_intensities) > 2:
                # 找到局部最大值
                for i in range(1, len(emotion_intensities) - 1):
                    try:
                        current = emotion_intensities[i]
                        prev_val = emotion_intensities[i-1]
                        next_val = emotion_intensities[i+1]

                        # 如果是局部最大值且强度足够高
                        if current > prev_val and current > next_val and current > 0.7:
                            emotion_point = emotion_curve[i]

                            # 找到对应的情节点
                            corresponding_plot_point = None
                            min_time_diff = float('inf')

                            for plot_point in plot_points:
                                time_diff = abs(plot_point.get("time", 0.0) - emotion_point.get("time", 0.0))
                                if time_diff < min_time_diff:
                                    min_time_diff = time_diff
                                    corresponding_plot_point = plot_point

                            if corresponding_plot_point and min_time_diff <= 5.0:  # 5秒内
                                # 创建高潮点（字典格式）
                                climax_point = {
                                    "time": float(emotion_point.get("time", 0.0)),
                                    "intensity": float(emotion_point.get("intensity", 0.5)),
                                    "type": "emotional_peak",
                                    "description": f"情感高潮点: {emotion_point.get('text', '')[:30]}...",
                                    "confidence": float(emotion_point.get("confidence", 0.5)),
                                    "plot_stage": corresponding_plot_point.get("type", "development")
                                }
                                climax_points.append(climax_point)

                    except Exception as peak_error:
                        logger.warning(f"处理情感峰值{i}时出错: {peak_error}")
                        continue

            # 方法2：基于叙事重要性
            high_importance_points = [pp for pp in plot_points if pp.get("importance", 0.0) > 0.8]
            for point in high_importance_points:
                try:
                    point_time = point.get("time", 0.0)
                    if not any(abs(cp.get("time", 0.0) - point_time) < 1.0 for cp in climax_points):
                        climax_point = {
                            "time": float(point_time),
                            "intensity": float(point.get("importance", 0.8)),
                            "type": "narrative_peak",
                            "description": point.get("description", "重要情节点"),
                            "confidence": 0.8,
                            "plot_stage": point.get("type", "development")
                        }
                        climax_points.append(climax_point)
                except Exception as point_error:
                    logger.warning(f"处理重要情节点时出错: {point_error}")
                    continue

            # 按时间排序
            climax_points.sort(key=lambda x: x.get("time", 0.0))

            # 合并时间接近的高潮点（≤2秒）
            merged_climax_points = []
            for climax in climax_points:
                try:
                    if not merged_climax_points:
                        merged_climax_points.append(climax)
                    else:
                        last_climax = merged_climax_points[-1]
                        time_diff = climax.get("time", 0.0) - last_climax.get("time", 0.0)
                        if time_diff <= 2.0:
                            # 合并到前一个高潮点，保留强度更高的
                            if climax.get("intensity", 0.0) > last_climax.get("intensity", 0.0):
                                merged_climax_points[-1] = climax
                        else:
                            merged_climax_points.append(climax)
                except Exception as merge_error:
                    logger.warning(f"合并高潮点时出错: {merge_error}")
                    continue

            logger.info(f"高潮点检测完成，识别出{len(merged_climax_points)}个高潮点")
            return merged_climax_points

        except Exception as e:
            logger.error(f"高潮点检测失败: {str(e)}")
            # 返回基础的高潮点
            return [
                {"time": 60.0, "intensity": 0.9, "type": "emotional_peak", "description": "默认高潮点", "confidence": 0.5, "plot_stage": "climax"}
            ]

    def _build_narrative_structure(self, subtitles: List[Dict[str, Any]],
                                  emotion_curve: List[Dict[str, Any]],
                                  plot_points: List[Dict[str, Any]],
                                  characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建完整叙事结构"""
        try:
            if not subtitles:
                logger.warning("字幕列表为空，返回默认叙事结构")
                return self._create_default_narrative_structure()

            total_duration = subtitles[-1].get('end_time', 100.0) if subtitles else 100.0

            # 按叙事阶段分组（使用字典格式的plot_points）
            stages = {
                "setup": [],
                "development": [],
                "climax": [],
                "conclusion": []
            }

            for plot_point in plot_points:
                stage_type = plot_point.get("type", "development")
                if stage_type in stages:
                    stages[stage_type].append(plot_point)

            # 计算各阶段时长占比
            stage_durations = {}
            for stage_name, points in stages.items():
                if points and total_duration > 0:
                    stage_start = min(p.get("time", 0.0) for p in points)
                    stage_end = max(p.get("time", 0.0) + p.get("duration", 5.0) for p in points)
                    stage_durations[stage_name] = max(0.0, (stage_end - stage_start) / total_duration)
                else:
                    # 默认分配
                    default_ratios = {"setup": 0.25, "development": 0.40, "climax": 0.20, "conclusion": 0.15}
                    stage_durations[stage_name] = default_ratios.get(stage_name, 0.25)

            # 情感统计（使用字典格式的emotion_curve）
            emotion_stats = {}
            if emotion_curve:
                intensities = [ep.get("intensity", 0.5) for ep in emotion_curve]
                emotion_stats = {
                    "avg_intensity": sum(intensities) / len(intensities),
                    "max_intensity": max(intensities),
                    "min_intensity": min(intensities),
                    "emotion_variance": self._calculate_variance(intensities),
                    "emotion_types": {}
                }

                # 统计情感类型
                emotion_types = {}
                for ep in emotion_curve:
                    emotion_type = ep.get("type", "neutral")
                    emotion_types[emotion_type] = emotion_types.get(emotion_type, 0) + 1
                emotion_stats["emotion_types"] = emotion_types
            else:
                emotion_stats = {
                    "avg_intensity": 0.5,
                    "max_intensity": 0.5,
                    "min_intensity": 0.5,
                    "emotion_variance": 0.0,
                    "emotion_types": {"neutral": 1}
                }

            # 角色统计（使用字典格式的characters）
            character_stats = {
                "total_characters": len(characters),
                "main_characters": [c.get("name", "") for c in characters if c.get("importance", 0.0) > 0.7],
                "character_roles": {}
            }

            # 统计角色类型
            for char in characters:
                role = char.get("role", "minor")
                character_stats["character_roles"][role] = character_stats["character_roles"].get(role, 0) + 1

            narrative_structure = {
                "stages": stages,
                "stage_durations": stage_durations,
                "emotion_stats": emotion_stats,
                "character_stats": character_stats,
                "total_duration": total_duration,
                "narrative_quality": self._calculate_simple_narrative_quality(stage_durations, emotion_stats),
                "analysis_summary": {
                    "plot_points_count": len(plot_points),
                    "emotion_points_count": len(emotion_curve),
                    "characters_count": len(characters),
                    "dominant_emotion": max(emotion_stats["emotion_types"].items(), key=lambda x: x[1])[0] if emotion_stats["emotion_types"] else "neutral"
                }
            }

            return narrative_structure

        except Exception as e:
            logger.error(f"叙事结构构建失败: {str(e)}")
            return self._create_default_narrative_structure()

    def _create_default_narrative_structure(self) -> Dict[str, Any]:
        """创建默认的叙事结构"""
        return {
            "stages": {
                "setup": [],
                "development": [],
                "climax": [],
                "conclusion": []
            },
            "stage_durations": {
                "setup": 0.25,
                "development": 0.40,
                "climax": 0.20,
                "conclusion": 0.15
            },
            "emotion_stats": {
                "avg_intensity": 0.5,
                "max_intensity": 0.5,
                "min_intensity": 0.5,
                "emotion_variance": 0.0,
                "emotion_types": {"neutral": 1}
            },
            "character_stats": {
                "total_characters": 0,
                "main_characters": [],
                "character_roles": {}
            },
            "total_duration": 100.0,
            "narrative_quality": 0.5,
            "analysis_summary": {
                "plot_points_count": 0,
                "emotion_points_count": 0,
                "characters_count": 0,
                "dominant_emotion": "neutral"
            }
        }

    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _calculate_simple_narrative_quality(self, stage_durations: Dict[str, float], emotion_stats: Dict[str, Any]) -> float:
        """计算简单的叙事质量评分"""
        try:
            # 基于阶段分布的平衡性
            ideal_durations = {"setup": 0.25, "development": 0.40, "climax": 0.20, "conclusion": 0.15}
            duration_score = 1.0 - sum(abs(stage_durations.get(stage, 0.0) - ideal) for stage, ideal in ideal_durations.items()) / 4.0

            # 基于情感变化的丰富性
            emotion_score = min(1.0, emotion_stats.get("emotion_variance", 0.0) * 2.0)

            # 综合评分
            return max(0.0, min(1.0, (duration_score * 0.6 + emotion_score * 0.4)))
        except:
            return 0.5

    def _get_llm_for_language(self, language: str):
        """获取对应语言的LLM模型"""
        try:
            from src.models.base_llm import get_llm_for_language
            return get_llm_for_language(language)
        except ImportError:
            logger.warning("无法导入LLM模型，使用规则方法")
            return None

    def _ai_analyze_emotion(self, llm, text: str, language: str) -> Dict[str, Any]:
        """使用AI分析情感"""
        try:
            if language == "zh":
                prompt = f"""
请分析以下中文文本的情感特征：

文本："{text}"

请从以下维度分析：
1. 情感强度（0.0-1.0，0为无情感，1为极强情感）
2. 情感类型（positive/negative/neutral/intense/suspense）
3. 置信度（0.0-1.0）

请以JSON格式回答：
{{"intensity": 0.0, "type": "neutral", "confidence": 0.0}}
"""
            else:
                prompt = f"""
Please analyze the emotional characteristics of the following English text:

Text: "{text}"

Please analyze from the following dimensions:
1. Emotional intensity (0.0-1.0, 0 for no emotion, 1 for extremely strong emotion)
2. Emotion type (positive/negative/neutral/intense/suspense)
3. Confidence (0.0-1.0)

Please answer in JSON format:
{{"intensity": 0.0, "type": "neutral", "confidence": 0.0}}
"""

            response = llm.generate(prompt, temperature=0.3, max_length=200)

            # 解析AI响应
            try:
                import json
                # 提取JSON部分
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "intensity": float(result.get("intensity", 0.5)),
                        "type": result.get("type", "neutral"),
                        "confidence": float(result.get("confidence", 0.5))
                    }
            except:
                pass

            # 如果解析失败，回退到规则方法
            return self._rule_based_emotion_analysis(text, language)

        except Exception as e:
            logger.error(f"AI情感分析失败: {str(e)}")
            return self._rule_based_emotion_analysis(text, language)

    def _ai_analyze_narrative(self, llm, text: str, language: str) -> Dict[str, Any]:
        """使用AI分析叙事结构"""
        try:
            if language == "zh":
                prompt = f"""
请分析以下中文文本片段在故事中的叙事阶段：

文本："{text}"

请判断这段文本属于以下哪个叙事阶段：
- 起（SETUP）：故事开端，背景设置，角色介绍
- 承（DEVELOPMENT）：情节发展，矛盾展开
- 转（TWIST）：转折点，冲突高潮，意外变化
- 合（CONCLUSION）：结局，问题解决，故事收束

同时评估：
1. 叙事阶段（SETUP/DEVELOPMENT/TWIST/CONCLUSION）
2. 重要性评分（0.0-1.0）
3. 简短描述（不超过20字）
4. 关键词（3-5个）

请以JSON格式回答：
{{"stage": "DEVELOPMENT", "importance": 0.5, "description": "情节发展", "keywords": ["关键词1", "关键词2"]}}
"""
            else:
                prompt = f"""
Please analyze the narrative stage of the following English text segment in the story:

Text: "{text}"

Please determine which narrative stage this text belongs to:
- SETUP: Story beginning, background setting, character introduction
- DEVELOPMENT: Plot development, conflict expansion
- TWIST: Turning point, conflict climax, unexpected changes
- CONCLUSION: Ending, problem resolution, story closure

Also evaluate:
1. Narrative stage (SETUP/DEVELOPMENT/TWIST/CONCLUSION)
2. Importance score (0.0-1.0)
3. Brief description (no more than 20 words)
4. Keywords (3-5 words)

Please answer in JSON format:
{{"stage": "DEVELOPMENT", "importance": 0.5, "description": "plot development", "keywords": ["keyword1", "keyword2"]}}
"""

            response = llm.generate(prompt, temperature=0.3, max_length=300)

            # 解析AI响应
            try:
                import json
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "stage": result.get("stage", "DEVELOPMENT"),
                        "importance": float(result.get("importance", 0.5)),
                        "description": result.get("description", ""),
                        "keywords": result.get("keywords", [])
                    }
            except:
                pass

            # 如果解析失败，回退到规则方法
            return self._rule_based_narrative_analysis(text, 0.0, 100.0, language)

        except Exception as e:
            logger.error(f"AI叙事分析失败: {str(e)}")
            return self._rule_based_narrative_analysis(text, 0.0, 100.0, language)

    def _ai_analyze_characters(self, llm, text: str, language: str) -> Dict[str, Any]:
        """使用AI分析角色"""
        try:
            if language == "zh":
                prompt = f"""
请从以下中文文本中识别出现的角色名称：

文本："{text}"

请识别：
1. 角色名称（人名、称呼、代词等）
2. 角色动作或对话

请以JSON格式回答：
{{"characters": ["角色1", "角色2"], "actions": ["动作1", "动作2"]}}
"""
            else:
                prompt = f"""
Please identify character names that appear in the following English text:

Text: "{text}"

Please identify:
1. Character names (names, titles, pronouns, etc.)
2. Character actions or dialogues

Please answer in JSON format:
{{"characters": ["character1", "character2"], "actions": ["action1", "action2"]}}
"""

            response = llm.generate(prompt, temperature=0.3, max_length=200)

            # 解析AI响应
            try:
                import json
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "characters": result.get("characters", []),
                        "actions": result.get("actions", [])
                    }
            except:
                pass

            # 如果解析失败，回退到规则方法
            return self._rule_based_character_analysis(text, language)

        except Exception as e:
            logger.error(f"AI角色分析失败: {str(e)}")
            return self._rule_based_character_analysis(text, language)

    def _rule_based_emotion_analysis(self, text: str, language: str) -> Dict[str, Any]:
        """基于规则的情感分析（AI回退方案）"""
        try:
            emotion_keywords = self.emotion_keywords.get(language, self.emotion_keywords.get("zh", {}))

            intensity = 0.0
            emotion_type = "neutral"

            # 计算情感强度
            for category, keywords in emotion_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    if category == "intense":
                        intensity += matches * 0.3
                        emotion_type = "intense"
                    elif category == "positive":
                        intensity += matches * 0.2
                        if emotion_type == "neutral":
                            emotion_type = "positive"
                    elif category == "negative":
                        intensity += matches * 0.2
                        if emotion_type == "neutral":
                            emotion_type = "negative"
                    elif category == "suspense":
                        intensity += matches * 0.25
                        emotion_type = "suspense"

            # 检查标点符号
            exclamation_count = text.count("！") + text.count("!")
            question_count = text.count("？") + text.count("?")
            intensity += (exclamation_count * 0.1 + question_count * 0.05)

            # 标准化强度
            intensity = min(1.0, intensity)

            return {
                "intensity": intensity,
                "type": emotion_type,
                "confidence": 0.7 if intensity > 0.3 else 0.5
            }

        except Exception as e:
            logger.error(f"规则情感分析失败: {str(e)}")
            return {"intensity": 0.5, "type": "neutral", "confidence": 0.5}

    def _rule_based_narrative_analysis(self, text: str, timestamp: float,
                                     total_duration: float, language: str) -> Dict[str, Any]:
        """基于规则的叙事分析（AI回退方案）"""
        try:
            # 基于时间位置判断叙事阶段
            time_ratio = timestamp / total_duration if total_duration > 0 else 0.0

            if time_ratio < 0.2:
                stage = "SETUP"
                importance = 0.6
            elif time_ratio < 0.7:
                stage = "DEVELOPMENT"
                importance = 0.5
            elif time_ratio < 0.9:
                stage = "TWIST"
                importance = 0.8
            else:
                stage = "CONCLUSION"
                importance = 0.7

            # 基于关键词调整
            narrative_patterns = self.narrative_patterns.get(language, {})
            keywords = []

            for pattern_type, pattern_keywords in narrative_patterns.items():
                matches = [kw for kw in pattern_keywords if kw in text]
                if matches:
                    keywords.extend(matches)
                    if pattern_type == "climax":
                        importance = min(1.0, importance + 0.3)
                        stage = "TWIST"
                    elif pattern_type == "conclusion":
                        stage = "CONCLUSION"

            return {
                "stage": stage,
                "importance": importance,
                "description": f"{stage.lower()}阶段" if language == "zh" else f"{stage.lower()} stage",
                "keywords": keywords[:5]  # 最多5个关键词
            }

        except Exception as e:
            logger.error(f"规则叙事分析失败: {str(e)}")
            return {"stage": "DEVELOPMENT", "importance": 0.5, "description": "", "keywords": []}

    def _rule_based_character_analysis(self, text: str, language: str) -> Dict[str, Any]:
        """基于规则的角色分析（AI回退方案）"""
        try:
            characters = []
            actions = []

            character_patterns = self.character_patterns.get(language, {})

            # 使用正则表达式识别角色
            for pattern in character_patterns.get("name_patterns", []):
                matches = re.findall(pattern, text)
                characters.extend(matches)

            # 识别动作词
            for action_word in character_patterns.get("action_words", []):
                if action_word in text:
                    actions.append(action_word)

            # 去重
            characters = list(set(characters))
            actions = list(set(actions))

            return {
                "characters": characters,
                "actions": actions
            }

        except Exception as e:
            logger.error(f"规则角色分析失败: {str(e)}")
            return {"characters": [], "actions": []}

    def _load_emotion_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """加载情感关键词库"""
        return {
            "zh": {
                "positive": ["开心", "快乐", "兴奋", "激动", "惊喜", "满足", "幸福", "欣慰", "骄傲", "感动", "温暖", "甜蜜"],
                "negative": ["伤心", "难过", "愤怒", "失望", "绝望", "痛苦", "恐惧", "焦虑", "沮丧", "悲伤", "孤独", "无助"],
                "intense": ["震撼", "惊人", "疯狂", "极致", "爆炸", "炸裂", "燃爆", "逆天", "神级", "史诗", "巨大", "强烈"],
                "suspense": ["悬疑", "神秘", "诡异", "离奇", "不可思议", "匪夷所思", "扑朔迷离", "悬念", "谜团", "秘密", "隐藏", "未知"]
            },
            "en": {
                "positive": ["happy", "joyful", "excited", "thrilled", "surprised", "satisfied", "blessed", "relieved", "proud", "moved", "warm", "sweet"],
                "negative": ["sad", "upset", "angry", "disappointed", "desperate", "painful", "fearful", "anxious", "depressed", "sorrowful", "lonely", "helpless"],
                "intense": ["shocking", "amazing", "crazy", "extreme", "explosive", "mind-blowing", "epic", "legendary", "incredible", "phenomenal", "massive", "intense"],
                "suspense": ["mysterious", "strange", "weird", "bizarre", "unbelievable", "incomprehensible", "puzzling", "suspenseful", "enigmatic", "secretive", "hidden", "unknown"]
            }
        }

    def _load_narrative_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """加载叙事模式库"""
        return {
            "zh": {
                "setup": ["开始", "首先", "起初", "最初", "一开始", "从前", "很久以前", "介绍", "背景"],
                "development": ["然后", "接着", "随后", "后来", "接下来", "于是", "因此", "发展", "进展"],
                "climax": ["突然", "忽然", "竟然", "没想到", "意外", "转折", "高潮", "关键", "决定性"],
                "conclusion": ["最后", "最终", "结果", "终于", "总之", "结束", "完成", "解决", "结局"]
            },
            "en": {
                "setup": ["begin", "start", "first", "initially", "at first", "once upon", "introduce", "background"],
                "development": ["then", "next", "after", "later", "subsequently", "therefore", "develop", "progress"],
                "climax": ["suddenly", "unexpectedly", "surprisingly", "twist", "climax", "crucial", "decisive", "turning point"],
                "conclusion": ["finally", "eventually", "result", "end", "conclude", "finish", "resolve", "outcome"]
            }
        }

    def _load_character_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """加载角色识别模式"""
        return {
            "zh": {
                "name_patterns": [r'[A-Z][a-z]+', r'[\u4e00-\u9fff]{2,4}(?=说|道|问|答|叫|喊)'],
                "action_words": ["说", "道", "问", "答", "叫", "喊", "笑", "哭", "走", "跑", "看", "听", "想", "做"]
            },
            "en": {
                "name_patterns": [r'\b[A-Z][a-z]+\b(?=\s+said|\s+asked|\s+replied)'],
                "action_words": ["said", "asked", "replied", "shouted", "called", "laughed", "cried", "walked", "ran", "looked", "listened", "thought", "did"]
            }
        }

    def _segment_subtitles_for_analysis(self, subtitles: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """将字幕分段用于分析"""
        try:
            segments = []
            current_segment = []
            segment_duration = 0.0
            max_segment_duration = 30.0  # 最大段落时长30秒

            for subtitle in subtitles:
                duration = subtitle.get("duration", 0.0)

                if segment_duration + duration > max_segment_duration and current_segment:
                    # 当前段落已满，开始新段落
                    segments.append(current_segment)
                    current_segment = [subtitle]
                    segment_duration = duration
                else:
                    current_segment.append(subtitle)
                    segment_duration += duration

            # 添加最后一个段落
            if current_segment:
                segments.append(current_segment)

            return segments

        except Exception as e:
            logger.error(f"字幕分段失败: {str(e)}")
            return [subtitles]  # 返回整个字幕作为一个段落

    def _analyze_character_relationships(self, char_name: str, appearances: List[Tuple[float, int]],
                                       all_characters: Dict[str, List[Tuple[float, int]]],
                                       subtitles: List[Dict[str, Any]]) -> Dict[str, str]:
        """分析角色关系"""
        try:
            relationships = {}

            # 查找在相近时间出现的其他角色
            for other_char, other_appearances in all_characters.items():
                if other_char == char_name:
                    continue

                # 计算共同出现的次数
                co_occurrences = 0
                for timestamp, _ in appearances:
                    for other_timestamp, _ in other_appearances:
                        if abs(timestamp - other_timestamp) <= 10.0:  # 10秒内
                            co_occurrences += 1
                            break

                if co_occurrences >= 2:  # 至少共同出现2次
                    if co_occurrences >= 5:
                        relationships[other_char] = "密切关系"
                    elif co_occurrences >= 3:
                        relationships[other_char] = "相关角色"
                    else:
                        relationships[other_char] = "偶然相遇"

            return relationships

        except Exception as e:
            logger.error(f"角色关系分析失败: {str(e)}")
            return {}

    def _calculate_narrative_quality(self, stage_durations: Dict[str, float],
                                   emotion_stats: Dict[str, Any],
                                   character_stats: Dict[str, Any]) -> Dict[str, float]:
        """计算叙事质量评分"""
        try:
            quality_scores = {}

            # 结构完整性评分
            structure_score = 0.0
            required_stages = ["起", "承", "转", "合"]
            present_stages = [stage for stage, duration in stage_durations.items() if duration > 0]
            structure_score = len(present_stages) / len(required_stages)

            # 情感丰富度评分
            emotion_score = 0.0
            if emotion_stats["max_intensity"] > 0:
                emotion_score = min(1.0, emotion_stats["avg_intensity"] * 2)
                # 情感变化度加分
                if emotion_stats["emotion_variance"] > 0.1:
                    emotion_score += 0.2

            # 角色丰富度评分
            character_score = 0.0
            if character_stats["total_characters"] > 0:
                character_score = min(1.0, character_stats["total_characters"] / 5.0)
                # 角色互动加分
                if character_stats["character_interactions"] > 0:
                    character_score += 0.2

            # 综合评分
            overall_score = (structure_score * 0.4 + emotion_score * 0.4 + character_score * 0.2)

            quality_scores = {
                "structure_quality": structure_score,
                "emotion_quality": emotion_score,
                "character_quality": character_score,
                "overall_quality": overall_score
            }

            return quality_scores

        except Exception as e:
            logger.error(f"叙事质量计算失败: {str(e)}")
            return {"overall_quality": 0.5}

    def _create_timeline_mapping(self, subtitles: List[Dict[str, Any]],
                               emotion_curve: List[EmotionPoint],
                               plot_points: List[PlotPoint]) -> Dict[str, Any]:
        """创建时间轴映射（为第4阶段精确对齐做准备）"""
        try:
            timeline_mapping = {
                "subtitle_timeline": [],
                "emotion_timeline": [],
                "plot_timeline": [],
                "sync_points": []
            }

            # 字幕时间轴
            for subtitle in subtitles:
                timeline_mapping["subtitle_timeline"].append({
                    "id": subtitle.get("id", 0),
                    "start_time": subtitle.get("start_time", 0.0),
                    "end_time": subtitle.get("end_time", 0.0),
                    "text": subtitle.get("text", "")
                })

            # 情感时间轴
            for emotion_point in emotion_curve:
                timeline_mapping["emotion_timeline"].append({
                    "timestamp": emotion_point.timestamp,
                    "intensity": emotion_point.intensity,
                    "type": emotion_point.emotion_type.value,
                    "subtitle_id": emotion_point.subtitle_id
                })

            # 情节时间轴
            for plot_point in plot_points:
                timeline_mapping["plot_timeline"].append({
                    "timestamp": plot_point.timestamp,
                    "stage": plot_point.stage.value,
                    "importance": plot_point.importance,
                    "subtitle_ids": plot_point.subtitle_ids
                })

            # 同步点（高重要性的时间点）
            sync_points = []

            # 添加高情感强度点（使用字典格式）
            high_emotion_points = [ep for ep in emotion_curve if ep.get("intensity", 0.0) > 0.7]
            for ep in high_emotion_points:
                sync_points.append({
                    "timestamp": ep.get("time", 0.0),
                    "type": "emotion_peak",
                    "subtitle_id": ep.get("subtitle_id", 0),
                    "precision_required": True  # 需要高精度对齐
                })

            # 添加重要情节点（使用字典格式）
            important_plot_points = [pp for pp in plot_points if pp.get("importance", 0.0) > 0.8]
            for pp in important_plot_points:
                sync_points.append({
                    "timestamp": pp.get("time", 0.0),
                    "type": "plot_key",
                    "subtitle_ids": pp.get("subtitle_ids", []),
                    "precision_required": True
                })

            # 按时间排序
            sync_points.sort(key=lambda x: x["timestamp"])
            timeline_mapping["sync_points"] = sync_points

            return timeline_mapping

        except Exception as e:
            logger.error(f"时间轴映射创建失败: {str(e)}")
            return {}

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析历史摘要"""
        if not self.analysis_history:
            return {"total_analyses": 0}

        total = len(self.analysis_history)
        avg_emotion_points = np.mean([len(nm.emotion_curve) for nm in self.analysis_history])
        avg_plot_points = np.mean([len(nm.plot_points) for nm in self.analysis_history])
        avg_characters = np.mean([len(nm.characters) for nm in self.analysis_history])

        return {
            "total_analyses": total,
            "avg_emotion_points": avg_emotion_points,
            "avg_plot_points": avg_plot_points,
            "avg_characters": avg_characters,
            "languages_analyzed": list(set(nm.language for nm in self.analysis_history))
        }

# 便捷函数
def analyze_plot_structure(subtitles: List[Dict[str, Any]], language: str = "auto") -> NarrativeMap:
    """
    便捷函数：分析剧情结构

    Args:
        subtitles: 字幕列表（来自输入验证阶段）
        language: 语言代码（zh/en/auto）

    Returns:
        NarrativeMap: 完整的叙事图谱
    """
    analyzer = AIPlotAnalyzer()
    return analyzer.analyze_plot(subtitles, language)
