#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI驱动的病毒传播字幕转换器
实现真正的"原始→爆款"转换逻辑，基于大语言模型的智能字幕重构
"""

import os
import time
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

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

class AIViralTransformer:
    """
    AI驱动的病毒传播字幕转换器
    
    核心功能：
    1. 叙事结构分析
    2. 情感强度评估
    3. 病毒传播潜力评分
    4. AI驱动的字幕重构
    """
    
    def __init__(self):
        """初始化AI病毒传播转换器"""
        self.viral_templates = self._load_viral_templates()
        self.emotion_keywords = self._load_emotion_keywords()
        self.narrative_patterns = self._load_narrative_patterns()
        
    @optimize_memory_usage()
    @optimize_inference(model_type="viral_transformer")
    def transform_to_viral(self, subtitles: List[Dict[str, Any]],
                          language: str = "auto",
                          style: str = "viral",
                          intensity: float = 0.8) -> List[Dict[str, Any]]:
        """
        将原始字幕转换为爆款风格
        
        Args:
            subtitles: 原始字幕列表
            language: 语言代码
            style: 转换风格
            intensity: 转换强度 (0.0-1.0)
            
        Returns:
            List[Dict[str, Any]]: 转换后的爆款字幕
        """
        try:
            logger.info(f"开始AI病毒传播转换，输入{len(subtitles)}条字幕")
            
            # 第一步：叙事结构分析
            narrative_analysis = self._analyze_narrative_structure(subtitles, language)
            
            # 第二步：情感强度分析
            emotion_analysis = self._analyze_emotion_intensity(subtitles, language)
            
            # 第三步：识别关键片段
            key_segments = self._identify_key_segments(subtitles, narrative_analysis, emotion_analysis)
            
            # 第四步：AI驱动的内容重构
            viral_segments = self._ai_reconstruct_content(key_segments, language, style, intensity)
            
            # 第五步：病毒传播潜力优化
            optimized_segments = self._optimize_viral_potential(viral_segments, language)
            
            logger.info(f"AI转换完成，输出{len(optimized_segments)}条爆款字幕")
            return optimized_segments
            
        except Exception as e:
            logger.error(f"AI病毒传播转换失败: {str(e)}")
            return self._fallback_transformation(subtitles, style, intensity)
    
    def _analyze_narrative_structure(self, subtitles: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """
        分析叙事结构
        
        Args:
            subtitles: 字幕列表
            language: 语言代码
            
        Returns:
            Dict[str, Any]: 叙事结构分析结果
        """
        try:
            texts = [sub.get("text", "") for sub in subtitles]
            
            # 识别叙事节拍
            narrative_beats = self._identify_narrative_beats(texts, language)
            
            # 检测高潮点
            climax_points = self._detect_climax_points(texts, subtitles)
            
            # 分析角色关系
            character_analysis = self._analyze_characters(texts, language)
            
            # 计算叙事密度
            narrative_density = self._calculate_narrative_density(texts)
            
            return {
                "narrative_beats": narrative_beats,
                "climax_points": climax_points,
                "character_analysis": character_analysis,
                "narrative_density": narrative_density,
                "total_segments": len(subtitles)
            }
            
        except Exception as e:
            logger.error(f"叙事结构分析失败: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_emotion_intensity(self, subtitles: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """
        分析情感强度
        
        Args:
            subtitles: 字幕列表
            language: 语言代码
            
        Returns:
            Dict[str, Any]: 情感分析结果
        """
        try:
            emotion_curve = []
            peak_emotions = []
            
            for i, subtitle in enumerate(subtitles):
                text = subtitle.get("text", "")
                
                # 计算情感强度
                intensity = self._calculate_emotion_intensity(text, language)
                
                # 识别情感类型
                emotion_type = self._identify_emotion_type(text, language)
                
                emotion_data = {
                    "index": i,
                    "intensity": intensity,
                    "emotion_type": emotion_type,
                    "text": text,
                    "start_time": subtitle.get("start_time", 0)
                }
                
                emotion_curve.append(emotion_data)
                
                # 识别情感峰值
                if intensity > 0.7:
                    peak_emotions.append(emotion_data)
            
            # 计算整体情感统计
            if emotion_curve:
                avg_intensity = sum(e["intensity"] for e in emotion_curve) / len(emotion_curve)
                max_intensity = max(e["intensity"] for e in emotion_curve)
                min_intensity = min(e["intensity"] for e in emotion_curve)
            else:
                avg_intensity = max_intensity = min_intensity = 0.0
            
            return {
                "emotion_curve": emotion_curve,
                "peak_emotions": peak_emotions,
                "avg_intensity": avg_intensity,
                "max_intensity": max_intensity,
                "emotional_range": max_intensity - min_intensity
            }
            
        except Exception as e:
            logger.error(f"情感强度分析失败: {str(e)}")
            return {"error": str(e)}
    
    def _identify_key_segments(self, subtitles: List[Dict[str, Any]], 
                              narrative_analysis: Dict[str, Any],
                              emotion_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别关键片段
        
        Args:
            subtitles: 原始字幕
            narrative_analysis: 叙事分析结果
            emotion_analysis: 情感分析结果
            
        Returns:
            List[Dict[str, Any]]: 关键片段列表
        """
        try:
            key_segments = []
            
            # 获取高潮点
            climax_points = narrative_analysis.get("climax_points", [])
            peak_emotions = emotion_analysis.get("peak_emotions", [])
            
            # 合并高潮点和情感峰值
            key_indices = set()
            
            # 添加叙事高潮点
            for climax in climax_points:
                key_indices.add(climax.get("index", 0))
            
            # 添加情感峰值点
            for peak in peak_emotions:
                key_indices.add(peak.get("index", 0))
            
            # 确保至少有30%的原始内容
            min_segments = max(3, int(len(subtitles) * 0.3))
            if len(key_indices) < min_segments:
                # 按情感强度排序，补充关键片段
                emotion_curve = emotion_analysis.get("emotion_curve", [])
                sorted_emotions = sorted(emotion_curve, key=lambda x: x["intensity"], reverse=True)
                
                for emotion_data in sorted_emotions[:min_segments]:
                    key_indices.add(emotion_data["index"])
            
            # 构建关键片段
            for index in sorted(key_indices):
                if index < len(subtitles):
                    segment = subtitles[index].copy()
                    segment["viral_score"] = self._calculate_viral_score(segment, narrative_analysis, emotion_analysis)
                    key_segments.append(segment)
            
            logger.info(f"识别出{len(key_segments)}个关键片段")
            return key_segments
            
        except Exception as e:
            logger.error(f"关键片段识别失败: {str(e)}")
            return subtitles[:int(len(subtitles) * 0.5)]  # 回退方案
    
    def _ai_reconstruct_content(self, segments: List[Dict[str, Any]], 
                               language: str, style: str, intensity: float) -> List[Dict[str, Any]]:
        """
        AI驱动的内容重构
        
        Args:
            segments: 关键片段
            language: 语言代码
            style: 风格
            intensity: 强度
            
        Returns:
            List[Dict[str, Any]]: 重构后的片段
        """
        try:
            # 尝试获取对应语言的LLM模型
            try:
                from src.models.base_llm import get_llm_for_language
                llm = get_llm_for_language(language)
            except ImportError:
                llm = None
            
            if not llm:
                logger.warning(f"无法获取{language}语言模型，使用规则重构")
                return self._rule_based_reconstruction(segments, style, intensity)
            
            reconstructed_segments = []
            
            for segment in segments:
                try:
                    # 构建重构提示词
                    prompt = self._build_reconstruction_prompt(segment, language, style, intensity)
                    
                    # 调用AI模型
                    ai_response = llm.generate(prompt, temperature=0.8, max_length=256)
                    
                    # 解析AI响应
                    reconstructed_text = self._parse_ai_reconstruction(ai_response, segment["text"])
                    
                    # 更新片段
                    new_segment = segment.copy()
                    new_segment["text"] = reconstructed_text
                    new_segment["original_text"] = segment["text"]
                    new_segment["reconstruction_method"] = "ai_driven"
                    
                    reconstructed_segments.append(new_segment)
                    
                except Exception as e:
                    logger.error(f"单个片段AI重构失败: {str(e)}")
                    # 使用规则重构作为回退
                    reconstructed_segments.append(self._rule_reconstruct_single(segment, style, intensity))
            
            return reconstructed_segments
            
        except Exception as e:
            logger.error(f"AI内容重构失败: {str(e)}")
            return self._rule_based_reconstruction(segments, style, intensity)

    def _calculate_viral_score(self, segment: Dict[str, Any],
                              narrative_analysis: Dict[str, Any],
                              emotion_analysis: Dict[str, Any]) -> float:
        """
        计算病毒传播潜力评分

        Args:
            segment: 字幕片段
            narrative_analysis: 叙事分析
            emotion_analysis: 情感分析

        Returns:
            float: 病毒传播评分 (0.0-1.0)
        """
        try:
            text = segment.get("text", "")
            score = 0.0

            # 情感强度权重 (40%)
            emotion_score = self._calculate_emotion_intensity(text, "auto")
            score += emotion_score * 0.4

            # 关键词匹配权重 (30%)
            keyword_score = self._calculate_keyword_score(text)
            score += keyword_score * 0.3

            # 叙事位置权重 (20%)
            narrative_score = self._calculate_narrative_position_score(segment, narrative_analysis)
            score += narrative_score * 0.2

            # 长度适宜性权重 (10%)
            length_score = self._calculate_length_score(text)
            score += length_score * 0.1

            return min(1.0, max(0.0, score))

        except Exception as e:
            logger.error(f"病毒传播评分计算失败: {str(e)}")
            return 0.5  # 默认中等评分

    def _load_viral_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """加载病毒传播模板"""
        return {
            "zh": {
                "prefixes": ["【震撼】", "【独家】", "【揭秘】", "【必看】", "【紧急】", "【重磅】", "【突发】", "【首发】", "【爆料】", "【惊呆】"],
                "suffixes": ["太震撼了！", "简直难以置信！", "史诗级体验！", "满分推荐！", "不容错过！", "超乎想象！", "前所未见！", "必看系列！"],
                "intensifiers": ["竟然", "居然", "简直", "完全", "绝对", "超级", "极其", "非常"],
                "hooks": ["你绝对想不到", "这一幕让所有人", "没想到最后", "真相竟然是", "结局太意外了"]
            },
            "en": {
                "prefixes": ["【SHOCKING】", "【EXCLUSIVE】", "【REVEALED】", "【MUST SEE】", "【URGENT】", "【BREAKING】", "【FIRST】", "【LEAKED】", "【AMAZING】"],
                "suffixes": ["So shocking!", "Unbelievable!", "Epic experience!", "Highly recommended!", "Don't miss it!", "Beyond imagination!", "Never seen before!", "Must watch!"],
                "intensifiers": ["absolutely", "completely", "totally", "extremely", "incredibly", "amazingly", "surprisingly", "definitely"],
                "hooks": ["You won't believe", "This scene made everyone", "Didn't expect the ending", "The truth is actually", "The ending is too unexpected"]
            }
        }

    def _load_emotion_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """加载情感关键词库"""
        return {
            "zh": {
                "positive": ["开心", "快乐", "兴奋", "激动", "惊喜", "满足", "幸福", "欣慰", "骄傲", "感动"],
                "negative": ["伤心", "难过", "愤怒", "失望", "绝望", "痛苦", "恐惧", "焦虑", "沮丧", "悲伤"],
                "intense": ["震撼", "惊人", "疯狂", "极致", "爆炸", "炸裂", "燃爆", "逆天", "神级", "史诗"],
                "suspense": ["悬疑", "神秘", "诡异", "离奇", "不可思议", "匪夷所思", "扑朔迷离", "悬念", "谜团", "秘密"]
            },
            "en": {
                "positive": ["happy", "joyful", "excited", "thrilled", "surprised", "satisfied", "blessed", "relieved", "proud", "moved"],
                "negative": ["sad", "upset", "angry", "disappointed", "desperate", "painful", "fearful", "anxious", "depressed", "sorrowful"],
                "intense": ["shocking", "amazing", "crazy", "extreme", "explosive", "mind-blowing", "epic", "legendary", "incredible", "phenomenal"],
                "suspense": ["mysterious", "strange", "weird", "bizarre", "unbelievable", "incomprehensible", "puzzling", "suspenseful", "enigmatic", "secretive"]
            }
        }

    def _load_narrative_patterns(self) -> Dict[str, Any]:
        """加载叙事模式"""
        return {
            "viral_patterns": {
                "hook_opening": {"weight": 0.9, "description": "开头吸引注意力"},
                "conflict_escalation": {"weight": 0.8, "description": "冲突升级"},
                "emotional_peak": {"weight": 0.85, "description": "情感高潮"},
                "surprise_twist": {"weight": 0.9, "description": "意外转折"},
                "cliffhanger": {"weight": 0.8, "description": "悬念结尾"}
            },
            "beat_types": ["setup", "inciting_incident", "plot_point_1", "midpoint", "plot_point_2", "climax", "resolution"]
        }

    def _calculate_emotion_intensity(self, text: str, language: str) -> float:
        """计算文本情感强度"""
        try:
            if not text.strip():
                return 0.0

            # 获取情感关键词
            emotion_keywords = self.emotion_keywords.get(language, self.emotion_keywords.get("zh", {}))

            intensity = 0.0
            word_count = len(text.split())

            # 检查各类情感词汇
            for category, keywords in emotion_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if category == "intense":
                    intensity += matches * 0.3  # 强烈词汇权重更高
                elif category in ["positive", "negative"]:
                    intensity += matches * 0.2
                elif category == "suspense":
                    intensity += matches * 0.25

            # 检查标点符号强度
            exclamation_count = text.count("！") + text.count("!")
            question_count = text.count("？") + text.count("?")
            intensity += (exclamation_count * 0.1 + question_count * 0.05)

            # 标准化到0-1范围
            normalized_intensity = min(1.0, intensity / max(1, word_count * 0.1))

            return normalized_intensity

        except Exception as e:
            logger.error(f"情感强度计算失败: {str(e)}")
            return 0.5

    def _identify_emotion_type(self, text: str, language: str) -> str:
        """识别情感类型"""
        try:
            emotion_keywords = self.emotion_keywords.get(language, self.emotion_keywords.get("zh", {}))

            scores = {}
            for category, keywords in emotion_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                scores[category] = score

            if not scores or max(scores.values()) == 0:
                return "neutral"

            return max(scores, key=scores.get)

        except Exception as e:
            logger.error(f"情感类型识别失败: {str(e)}")
            return "neutral"

    def _identify_narrative_beats(self, texts: List[str], language: str) -> List[Dict[str, Any]]:
        """识别叙事节拍"""
        try:
            beats = []
            total_texts = len(texts)

            # 简化的叙事节拍识别
            beat_positions = {
                "setup": (0, int(total_texts * 0.15)),
                "inciting_incident": (int(total_texts * 0.15), int(total_texts * 0.25)),
                "plot_point_1": (int(total_texts * 0.25), int(total_texts * 0.4)),
                "midpoint": (int(total_texts * 0.4), int(total_texts * 0.6)),
                "plot_point_2": (int(total_texts * 0.6), int(total_texts * 0.8)),
                "climax": (int(total_texts * 0.8), int(total_texts * 0.9)),
                "resolution": (int(total_texts * 0.9), total_texts)
            }

            for beat_type, (start, end) in beat_positions.items():
                if start < total_texts:
                    beats.append({
                        "type": beat_type,
                        "start_index": start,
                        "end_index": min(end, total_texts),
                        "texts": texts[start:min(end, total_texts)]
                    })

            return beats

        except Exception as e:
            logger.error(f"叙事节拍识别失败: {str(e)}")
            return []

    def _detect_climax_points(self, texts: List[str], subtitles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测高潮点"""
        try:
            climax_points = []

            for i, text in enumerate(texts):
                # 计算情感强度
                intensity = self._calculate_emotion_intensity(text, "auto")

                # 检查是否为局部最大值
                is_peak = True
                window_size = 2

                for j in range(max(0, i - window_size), min(len(texts), i + window_size + 1)):
                    if j != i:
                        neighbor_intensity = self._calculate_emotion_intensity(texts[j], "auto")
                        if neighbor_intensity >= intensity:
                            is_peak = False
                            break

                # 如果是峰值且强度足够高
                if is_peak and intensity > 0.6:
                    climax_points.append({
                        "index": i,
                        "intensity": intensity,
                        "text": text,
                        "start_time": subtitles[i].get("start_time", 0) if i < len(subtitles) else 0
                    })

            # 按强度排序，取前5个
            climax_points.sort(key=lambda x: x["intensity"], reverse=True)
            return climax_points[:5]

        except Exception as e:
            logger.error(f"高潮点检测失败: {str(e)}")
            return []

    def _analyze_characters(self, texts: List[str], language: str) -> Dict[str, Any]:
        """分析角色关系"""
        try:
            # 简化的角色识别（基于对话模式）
            characters = set()
            dialogue_patterns = []

            if language == "zh":
                # 中文对话模式
                dialogue_markers = ["说", "道", "问", "答", "喊", "叫", "笑", "哭"]
            else:
                # 英文对话模式
                dialogue_markers = ["said", "asked", "replied", "shouted", "called", "laughed", "cried"]

            for text in texts:
                # 检测对话
                for marker in dialogue_markers:
                    if marker in text:
                        dialogue_patterns.append(text)
                        break

            return {
                "character_count": len(characters),
                "dialogue_ratio": len(dialogue_patterns) / len(texts) if texts else 0,
                "dialogue_patterns": dialogue_patterns[:10]  # 保留前10个对话模式
            }

        except Exception as e:
            logger.error(f"角色分析失败: {str(e)}")
            return {"character_count": 0, "dialogue_ratio": 0}

    def _calculate_narrative_density(self, texts: List[str]) -> float:
        """计算叙事密度"""
        try:
            if not texts:
                return 0.0

            total_words = sum(len(text.split()) for text in texts)
            avg_words_per_segment = total_words / len(texts)

            # 叙事密度基于平均字数和变化程度
            word_counts = [len(text.split()) for text in texts]
            variance = sum((count - avg_words_per_segment) ** 2 for count in word_counts) / len(word_counts)

            # 标准化密度值
            density = min(1.0, (avg_words_per_segment / 20) * (1 + variance / 100))

            return density

        except Exception as e:
            logger.error(f"叙事密度计算失败: {str(e)}")
            return 0.5

    def _build_reconstruction_prompt(self, segment: Dict[str, Any],
                                   language: str, style: str, intensity: float) -> str:
        """构建AI重构提示词"""
        try:
            original_text = segment.get("text", "")

            if language == "zh":
                base_prompt = f"""
请将以下字幕文本重构为更具病毒传播潜力的爆款风格：

原始文本："{original_text}"

重构要求：
1. 风格：{style}（爆款/病毒传播）
2. 强度：{intensity:.1f}（0.0-1.0）
3. 保持原意的同时增强吸引力
4. 使用更有冲击力的词汇
5. 增加情感强度和悬念感
6. 长度控制在原文的80%-120%之间

重构后的文本：
"""
            else:
                base_prompt = f"""
Please reconstruct the following subtitle text into a more viral and engaging style:

Original text: "{original_text}"

Requirements:
1. Style: {style} (viral/engaging)
2. Intensity: {intensity:.1f} (0.0-1.0)
3. Maintain original meaning while enhancing appeal
4. Use more impactful vocabulary
5. Increase emotional intensity and suspense
6. Keep length between 80%-120% of original

Reconstructed text:
"""

            return base_prompt

        except Exception as e:
            logger.error(f"提示词构建失败: {str(e)}")
            return f"Rewrite this text to be more engaging: {segment.get('text', '')}"

    def _parse_ai_reconstruction(self, ai_response: str, original_text: str) -> str:
        """解析AI重构响应"""
        try:
            # 清理AI响应
            cleaned_response = ai_response.strip()

            # 移除可能的引号
            if cleaned_response.startswith('"') and cleaned_response.endswith('"'):
                cleaned_response = cleaned_response[1:-1]

            # 如果响应为空或过短，使用原文
            if not cleaned_response or len(cleaned_response) < len(original_text) * 0.5:
                return original_text

            # 长度检查
            if len(cleaned_response) > len(original_text) * 2:
                cleaned_response = cleaned_response[:len(original_text) * 2]

            return cleaned_response

        except Exception as e:
            logger.error(f"AI响应解析失败: {str(e)}")
            return original_text

    def _rule_based_reconstruction(self, segments: List[Dict[str, Any]],
                                  style: str, intensity: float) -> List[Dict[str, Any]]:
        """基于规则的重构（AI回退方案）"""
        try:
            reconstructed = []

            for segment in segments:
                reconstructed_segment = self._rule_reconstruct_single(segment, style, intensity)
                reconstructed.append(reconstructed_segment)

            return reconstructed

        except Exception as e:
            logger.error(f"规则重构失败: {str(e)}")
            return segments

    def _rule_reconstruct_single(self, segment: Dict[str, Any],
                                style: str, intensity: float) -> Dict[str, Any]:
        """单个片段的规则重构"""
        try:
            original_text = segment.get("text", "")

            # 检测语言
            language = "zh" if re.search(r'[\u4e00-\u9fff]', original_text) else "en"
            templates = self.viral_templates.get(language, self.viral_templates["zh"])

            # 应用强度调节
            if intensity > 0.7:
                # 高强度：添加前缀和后缀
                prefix = templates["prefixes"][hash(original_text) % len(templates["prefixes"])]
                suffix = templates["suffixes"][hash(original_text) % len(templates["suffixes"])]
                reconstructed_text = f"{prefix} {original_text} {suffix}"
            elif intensity > 0.4:
                # 中强度：添加强化词
                intensifier = templates["intensifiers"][hash(original_text) % len(templates["intensifiers"])]
                reconstructed_text = f"{intensifier}{original_text}"
            else:
                # 低强度：保持原文
                reconstructed_text = original_text

            new_segment = segment.copy()
            new_segment["text"] = reconstructed_text
            new_segment["original_text"] = original_text
            new_segment["reconstruction_method"] = "rule_based"

            return new_segment

        except Exception as e:
            logger.error(f"单片段规则重构失败: {str(e)}")
            return segment

    def _optimize_viral_potential(self, segments: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """优化病毒传播潜力"""
        try:
            # 按病毒传播评分排序
            scored_segments = []

            for segment in segments:
                viral_score = segment.get("viral_score", 0.5)
                if viral_score < 0.3:
                    # 低分片段进行二次优化
                    segment = self._boost_viral_potential(segment, language)

                scored_segments.append(segment)

            # 按评分和时间排序
            scored_segments.sort(key=lambda x: (x.get("viral_score", 0), x.get("start_time", 0)), reverse=True)

            # 保留前80%的高质量片段
            keep_count = max(3, int(len(scored_segments) * 0.8))
            optimized_segments = scored_segments[:keep_count]

            # 按时间重新排序
            optimized_segments.sort(key=lambda x: x.get("start_time", 0))

            return optimized_segments

        except Exception as e:
            logger.error(f"病毒传播潜力优化失败: {str(e)}")
            return segments

    def _boost_viral_potential(self, segment: Dict[str, Any], language: str) -> Dict[str, Any]:
        """提升单个片段的病毒传播潜力"""
        try:
            text = segment.get("text", "")
            templates = self.viral_templates.get(language, self.viral_templates["zh"])

            # 添加吸引力钩子
            hook = templates["hooks"][hash(text) % len(templates["hooks"])]
            boosted_text = f"{hook}：{text}"

            boosted_segment = segment.copy()
            boosted_segment["text"] = boosted_text
            boosted_segment["viral_score"] = min(1.0, segment.get("viral_score", 0.5) + 0.2)
            boosted_segment["boost_applied"] = True

            return boosted_segment

        except Exception as e:
            logger.error(f"病毒传播潜力提升失败: {str(e)}")
            return segment

    def _calculate_keyword_score(self, text: str) -> float:
        """计算关键词评分"""
        try:
            # 检测语言
            language = "zh" if re.search(r'[\u4e00-\u9fff]', text) else "en"
            emotion_keywords = self.emotion_keywords.get(language, {})

            score = 0.0
            total_words = len(text.split())

            for category, keywords in emotion_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    if category == "intense":
                        score += matches * 0.3
                    elif category == "suspense":
                        score += matches * 0.25
                    else:
                        score += matches * 0.2

            return min(1.0, score / max(1, total_words * 0.1))

        except Exception as e:
            logger.error(f"关键词评分计算失败: {str(e)}")
            return 0.0

    def _calculate_narrative_position_score(self, segment: Dict[str, Any],
                                          narrative_analysis: Dict[str, Any]) -> float:
        """计算叙事位置评分"""
        try:
            # 高潮点和关键位置获得更高评分
            climax_points = narrative_analysis.get("climax_points", [])
            segment_time = segment.get("start_time", 0)

            # 检查是否接近高潮点
            for climax in climax_points:
                climax_time = climax.get("start_time", 0)
                if abs(segment_time - climax_time) < 10:  # 10秒内
                    return 0.9

            # 基于叙事位置的基础评分
            narrative_beats = narrative_analysis.get("narrative_beats", [])
            for beat in narrative_beats:
                if beat["type"] in ["climax", "plot_point_2", "midpoint"]:
                    return 0.7
                elif beat["type"] in ["inciting_incident", "plot_point_1"]:
                    return 0.6

            return 0.5  # 默认评分

        except Exception as e:
            logger.error(f"叙事位置评分计算失败: {str(e)}")
            return 0.5

    def _calculate_length_score(self, text: str) -> float:
        """计算长度适宜性评分"""
        try:
            length = len(text)

            # 理想长度范围：10-50字符
            if 10 <= length <= 50:
                return 1.0
            elif 5 <= length < 10 or 50 < length <= 80:
                return 0.8
            elif length < 5 or length > 80:
                return 0.5
            else:
                return 0.3

        except Exception as e:
            logger.error(f"长度评分计算失败: {str(e)}")
            return 0.5

    def _fallback_transformation(self, subtitles: List[Dict[str, Any]],
                                style: str, intensity: float) -> List[Dict[str, Any]]:
        """回退转换方案"""
        try:
            logger.info("使用回退转换方案")

            # 简单的情感强度筛选
            filtered_segments = []

            for subtitle in subtitles:
                text = subtitle.get("text", "")
                emotion_intensity = self._calculate_emotion_intensity(text, "auto")

                if emotion_intensity > 0.4:  # 保留中等以上情感强度的片段
                    filtered_segments.append(subtitle)

            # 确保至少有30%的原始内容
            min_segments = max(3, int(len(subtitles) * 0.3))
            if len(filtered_segments) < min_segments:
                # 按情感强度排序补充
                all_with_scores = [(sub, self._calculate_emotion_intensity(sub.get("text", ""), "auto"))
                                 for sub in subtitles]
                all_with_scores.sort(key=lambda x: x[1], reverse=True)
                filtered_segments = [item[0] for item in all_with_scores[:min_segments]]

            return filtered_segments[:int(len(subtitles) * 0.8)]  # 最多保留80%

        except Exception as e:
            logger.error(f"回退转换失败: {str(e)}")
            return subtitles[:len(subtitles)//2]  # 最后的回退：返回前一半
