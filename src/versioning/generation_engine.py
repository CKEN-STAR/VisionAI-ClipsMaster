#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多策略生成引擎 - 简化版

提供多种文本生成策略，适配简化版参数管理器
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional, Union, Callable
import random
import logging

# 修改导入
from src.versioning.param_manager import prepare_params, get_params

# 删除diversity_manager导入
# from src.versioning.diversity_manager import DiversityManager, ensure_version_diversity

# 设置日志
logger = logging.getLogger(__name__)

class GenerationStrategy:
    """生成策略基类"""
    
    def __init__(self, name: str):
        """初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        # 使用延迟导入
        self._screenplay_engineer = None
        
    @property
    def screenplay_engineer(self):
        """延迟加载ScreenplayEngineer以避免循环导入"""
        if self._screenplay_engineer is None:
            # 仅在需要时导入
            from src.core.screenplay_engineer import ScreenplayEngineer
            self._screenplay_engineer = ScreenplayEngineer()
        return self._screenplay_engineer
        
    def execute(self, base_script: List[Dict[str, Any]], 
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行策略，生成新的剧本
        
        Args:
            base_script: 原始字幕
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含生成剧本和元数据的字典
        """
        # 基础实现，子类需要重写
        result = self.screenplay_engineer.generate_screenplay(
            base_script,
            preset_name=params.get("preset_name") if params else None,
            custom_params=params
        )
        
        # 添加策略信息
        if isinstance(result, dict):
            result["strategy"] = {
                "name": self.name,
                "description": self.__doc__,
                "timestamp": time.time()
            }
        
        return result


class ReverseNarrativeStrategy(GenerationStrategy):
    """反向叙事策略 - 颠覆传统线性叙事，创造"倒叙"效果"""
    
    def __init__(self):
        super().__init__("倒叙重构")
    
    def execute(self, base_script: List[Dict[str, Any]], 
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行反向叙事策略
        
        Args:
            base_script: 原始字幕
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含生成剧本和元数据的字典
        """
        # 确保有适当的参数
        strategy_params = {
            "linearity": 0.3,  # 低线性度
            "context_preservation": 0.7,  # 高上下文保留
            "cliffhanger_freq": 0.7,  # 高悬念频率
            "emotion_intensity": 0.8,  # 较高情感强度
        }
        
        # 合并自定义参数
        if params:
            strategy_params.update(params)
        
        # 1. 分析原始剧本的叙事结构
        anchors = detect_anchors(base_script)
        
        # 2. 选择关键锚点（起点、高潮点、结局点）
        key_anchors = []
        if anchors:
            anchor_types = ["结局", "高潮", "导入"]
            for anchor_type in anchor_types:
                matching = [a for a in anchors if a.get("type") == anchor_type]
                if matching:
                    key_anchors.append(matching[0])
        
        # 3. 重排剧本片段 - 反转叙事顺序
        restructured_script = base_script.copy()
        
        # 如果有关键锚点，使用它们来重构剧本
        if len(key_anchors) >= 2:
            # 按时间排序锚点
            key_anchors.sort(key=lambda x: x.get("start_time", 0))
            
            # 标记不同区域的片段
            regions = []
            for i in range(len(key_anchors)):
                current = key_anchors[i]
                next_anchor = key_anchors[i+1] if i < len(key_anchors)-1 else None
                
                region_start = current.get("start_time", 0)
                region_end = next_anchor.get("start_time", float("inf")) if next_anchor else float("inf")
                
                # 收集该区域的片段
                region_segments = [
                    seg for seg in base_script 
                    if seg.get("start_time", 0) >= region_start and seg.get("start_time", 0) < region_end
                ]
                
                regions.append({
                    "anchor": current,
                    "segments": region_segments
                })
            
            # 反转区域顺序，但保持区域内部顺序
            regions.reverse()
            
            # 重构剧本
            restructured_script = []
            for region in regions:
                restructured_script.extend(region["segments"])
        else:
            # 简单的整体反序重构
            # 将剧本按叙事单元分组
            narrative_units = select_narrative_structure(base_script, structure_type="scenes")
            
            # 反转叙事单元顺序，但保持单元内的顺序
            narrative_units.reverse()
            
            # 重建剧本
            restructured_script = []
            for unit in narrative_units:
                restructured_script.extend(unit.get("segments", []))
        
        # 4. 使用基础引擎进一步处理
        result = self.screenplay_engineer.generate_screenplay(
            restructured_script,
            preset_name=strategy_params.get("preset_name", "悬念优先"),
            custom_params=strategy_params
        )
        
        # 添加策略信息
        result["strategy"] = {
            "name": self.name,
            "description": self.__doc__,
            "timestamp": time.time(),
            "reverse_narrative": True
        }
        
        return result


class ParallelThreadsStrategy(GenerationStrategy):
    """多线叙事策略 - 关注多个角色视角，创造多线叙事效果"""
    
    def __init__(self):
        super().__init__("多线交织")
    
    def execute(self, base_script: List[Dict[str, Any]], 
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行多线叙事策略
        
        Args:
            base_script: 原始字幕
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含生成剧本和元数据的字典
        """
        # 确保有适当的参数
        strategy_params = {
            "character_focus": 4,  # 关注多角色
            "subplot": 4,  # 多支线
            "linearity": 0.4,  # 中低线性度
            "context_preservation": 0.6,  # 中高上下文保留
        }
        
        # 合并自定义参数
        if params:
            strategy_params.update(params)
        
        # 1. 识别剧本中的主要角色
        from src.knowledge.graph_builder import build_knowledge_graph
        knowledge_graph = build_knowledge_graph(base_script)
        
        # 获取主要角色（至多4个）
        character_importance = knowledge_graph.get_character_importance()
        main_characters = list(character_importance.keys())[:4]
        
        if not main_characters:
            # 如果未找到角色，使用默认处理
            return super().execute(base_script, strategy_params)
        
        # 2. 为每个角色创建一个"线程"（片段集合）
        character_threads = {char: [] for char in main_characters}
        
        # 根据对话内容和提及将片段分配给角色
        for segment in base_script:
            text = segment.get("text", "")
            
            # 检查是否是角色对话
            is_assigned = False
            for char in main_characters:
                # 如果文本以"角色名:"开头，或包含角色名
                if text.startswith(f"{char}:") or text.startswith(f"{char}：") or char in text:
                    character_threads[char].append(segment)
                    is_assigned = True
                    break
            
            # 如果无法分配给特定角色，添加到所有线程
            if not is_assigned:
                for char in main_characters:
                    character_threads[char].append(segment)
        
        # 3. 交织不同角色的线程
        interleaved_script = []
        
        # 确保每个角色线程有内容
        active_threads = {char: thread for char, thread in character_threads.items() if thread}
        
        if not active_threads:
            # 如果没有有效线程，使用默认处理
            return super().execute(base_script, strategy_params)
        
        # 交织线程 - 轮流从每个角色线程取片段
        while any(len(thread) > 0 for thread in active_threads.values()):
            for char, thread in active_threads.items():
                if thread:
                    # 每次从角色线程取出一个叙事单位（1-3个片段）
                    unit_size = min(2, len(thread))
                    unit = thread[:unit_size]
                    interleaved_script.extend(unit)
                    
                    # 从线程中移除已使用的片段
                    active_threads[char] = thread[unit_size:]
        
        # 4. 确保时间轴连续性
        sorted_script = sorted(interleaved_script, key=lambda x: x.get("start_time", 0))
        
        # 5. 使用基础引擎进一步处理
        result = self.screenplay_engineer.generate_screenplay(
            sorted_script,
            preset_name=strategy_params.get("preset_name", "复杂叙事"),
            custom_params=strategy_params
        )
        
        # 添加策略信息
        result["strategy"] = {
            "name": self.name,
            "description": self.__doc__,
            "timestamp": time.time(),
            "character_threads": list(character_threads.keys())
        }
        
        return result


class EmotionAmplificationStrategy(GenerationStrategy):
    """情感放大策略 - 强化情感高潮，创造强烈的情感共鸣"""
    
    def __init__(self):
        super().__init__("情感放大")
    
    def execute(self, base_script: List[Dict[str, Any]], 
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行情感放大策略
        
        Args:
            base_script: 原始字幕
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含生成剧本和元数据的字典
        """
        # 确保有适当的参数
        strategy_params = {
            "emotion_intensity": 0.9,  # 高情感强度
            "punchline_ratio": 0.25,  # 高金句保留
            "pace": 0.8,  # 较慢节奏
            "character_focus": 2,  # 聚焦少数角色
        }
        
        # 合并自定义参数
        if params:
            strategy_params.update(params)
        
        # 1. 分析字幕的情感曲线
        from src.nlp.sentiment_analyzer import analyze_sentiment_batch
        sentiment_analysis = analyze_sentiment_batch([seg.get("text", "") for seg in base_script])
        
        # 2. 识别情感高潮点 - 使用备用方法，因为find_emotional_focus可能不存在
        try:
            # 尝试导入情感定位器
            from src.emotion.focus_locator import find_emotional_focus
            emotion_peaks = find_emotional_focus(base_script, sentiment_analysis)
        except ImportError:
            # 备用方法：根据情感分析找出情感波动最大的点
            logger.warning("情感定位器不可用，使用备用方法查找情感高潮")
            emotion_peaks = self._fallback_find_emotion_peaks(base_script, sentiment_analysis)
        
        # 3. 围绕情感高潮构建剧本
        enhanced_script = base_script.copy()
        
        # 如果找到情感高潮点
        if emotion_peaks:
            # 标记情感高潮片段
            peak_segments = []
            for peak in emotion_peaks:
                peak_index = peak.get("index", -1)
                if 0 <= peak_index < len(enhanced_script):
                    peak_segments.append(enhanced_script[peak_index])
            
            # 确保有足够的情感高潮片段
            if len(peak_segments) < 3 and len(enhanced_script) > 5:
                # 添加情感波动明显的片段
                try:
                    # 尝试导入情感强度映射
                    from src.emotion.intensity_mapper import map_emotion_intensity
                    emotion_variations = map_emotion_intensity(enhanced_script, sentiment_analysis)
                except ImportError:
                    # 备用方法：计算情感变化
                    logger.warning("情感强度映射器不可用，使用备用方法计算情感变化")
                    emotion_variations = self._fallback_map_emotion_intensity(enhanced_script, sentiment_analysis)
                
                high_variation_segments = [
                    enhanced_script[i] for i, var in enumerate(emotion_variations) 
                    if var > 0.7 and enhanced_script[i] not in peak_segments
                ]
                
                # 添加到高潮片段集合
                peak_segments.extend(high_variation_segments[:3])
            
            # 重新排序剧本，使情感高潮点分布更合理
            if peak_segments:
                # 根据原始顺序排序高潮片段
                peak_segments = sorted(peak_segments, key=lambda x: x.get("start_time", 0))
                
                # 计算理想的高潮点位置
                ideal_positions = []
                segment_count = len(enhanced_script)
                peak_count = len(peak_segments)
                
                if peak_count == 1:
                    # 单个高潮点 - 放在3/4处
                    ideal_positions = [int(segment_count * 0.75)]
                elif peak_count == 2:
                    # 双高潮点 - 放在1/3和2/3处
                    ideal_positions = [int(segment_count * 0.33), int(segment_count * 0.67)]
                else:
                    # 多个高潮点 - 放在1/4, 1/2, 3/4处
                    ideal_positions = [
                        int(segment_count * (i + 1) / (peak_count + 1))
                        for i in range(peak_count)
                    ]
                
                # 将高潮片段插入理想位置
                # 首先移除原始高潮片段
                for peak in peak_segments:
                    if peak in enhanced_script:
                        enhanced_script.remove(peak)
                
                # 然后插入到理想位置
                for i, position in enumerate(ideal_positions):
                    if i < len(peak_segments) and position < len(enhanced_script):
                        enhanced_script.insert(position, peak_segments[i])
        
        # 4. 使用基础引擎进一步处理
        result = self.screenplay_engineer.generate_screenplay(
            enhanced_script,
            preset_name=strategy_params.get("preset_name", "深度情感"),
            custom_params=strategy_params
        )
        
        # 添加策略信息
        result["strategy"] = {
            "name": self.name,
            "description": self.__doc__,
            "timestamp": time.time(),
            "emotion_peaks_count": len(emotion_peaks) if emotion_peaks else 0
        }
        
        return result
    
    def _fallback_find_emotion_peaks(self, segments: List[Dict[str, Any]], 
                                     sentiment_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """备用方法：找出情感高潮点
        
        Args:
            segments: 字幕片段列表
            sentiment_analysis: 情感分析结果
            
        Returns:
            List[Dict[str, Any]]: 情感高潮点列表
        """
        peaks = []
        
        # 确保情感分析结果与片段数量匹配
        if len(sentiment_analysis) != len(segments):
            return peaks
            
        # 计算情感变化曲线
        sentiment_scores = []
        for analysis in sentiment_analysis:
            # 提取情感分数 (可能是极性或强度)
            score = 0.0
            if isinstance(analysis, dict):
                score = analysis.get("score", 0.0)
            elif hasattr(analysis, "polarity"):
                score = analysis.polarity
                
            sentiment_scores.append(score)
        
        # 检测情感峰值 (使用简单的局部最大值检测)
        window_size = 3  # 局部窗口大小
        
        for i in range(window_size, len(sentiment_scores) - window_size):
            current = sentiment_scores[i]
            is_peak = True
            
            # 检查是否是局部最大值
            for j in range(i - window_size, i + window_size + 1):
                if j != i and sentiment_scores[j] > current:
                    is_peak = False
                    break
            
            # 如果是情感峰值，添加到结果
            if is_peak and abs(current) > 0.4:  # 阈值：确保峰值足够显著
                peaks.append({
                    "index": i,
                    "score": current,
                    "type": "positive" if current > 0 else "negative"
                })
        
        # 如果没有找到足够的峰值，添加绝对值最大的几个点
        if len(peaks) < 2:
            # 按情感强度排序
            sorted_indices = sorted(range(len(sentiment_scores)), 
                                  key=lambda i: abs(sentiment_scores[i]),
                                  reverse=True)
            
            # 添加最强的情感点 (最多3个)
            for idx in sorted_indices[:3]:
                if {"index": idx} not in [{"index": p["index"]} for p in peaks]:
                    peaks.append({
                        "index": idx,
                        "score": sentiment_scores[idx],
                        "type": "extreme"
                    })
        
        return peaks
    
    def _fallback_map_emotion_intensity(self, segments: List[Dict[str, Any]], 
                                       sentiment_analysis: List[Dict[str, Any]]) -> List[float]:
        """备用方法：计算情感变化强度
        
        Args:
            segments: 字幕片段列表
            sentiment_analysis: 情感分析结果
            
        Returns:
            List[float]: 情感变化强度列表
        """
        variations = []
        
        # 确保情感分析结果与片段数量匹配
        if len(sentiment_analysis) != len(segments):
            return [0.0] * len(segments)
            
        # 提取情感分数
        sentiment_scores = []
        for analysis in sentiment_analysis:
            # 提取情感分数 (可能是极性或强度)
            score = 0.0
            if isinstance(analysis, dict):
                score = analysis.get("score", 0.0)
            elif hasattr(analysis, "polarity"):
                score = analysis.polarity
                
            sentiment_scores.append(score)
        
        # 计算情感变化 (基于差分)
        for i in range(len(sentiment_scores)):
            if i == 0:
                # 第一个片段没有前一个片段，使用下一个片段的差异
                variation = abs(sentiment_scores[i] - sentiment_scores[i+1]) if i+1 < len(sentiment_scores) else 0.0
            elif i == len(sentiment_scores) - 1:
                # 最后一个片段使用与前一个片段的差异
                variation = abs(sentiment_scores[i] - sentiment_scores[i-1])
            else:
                # 其他片段使用前后差异的平均
                prev_diff = abs(sentiment_scores[i] - sentiment_scores[i-1])
                next_diff = abs(sentiment_scores[i] - sentiment_scores[i+1])
                variation = (prev_diff + next_diff) / 2.0
            
            # 归一化到0-1范围 (使用简单阈值)
            normalized_variation = min(1.0, variation / 0.5)
            variations.append(normalized_variation)
        
        return variations


class MinimalistAdaptationStrategy(GenerationStrategy):
    """极简改编策略 - 削减次要元素，专注核心冲突和主线"""
    
    def __init__(self):
        super().__init__("极简主义")
    
    def execute(self, base_script: List[Dict[str, Any]], 
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行极简改编策略
        
        Args:
            base_script: 原始字幕
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含生成剧本和元数据的字典
        """
        # 确保有适当的参数
        strategy_params = {
            "pace": 1.2,  # 较快节奏
            "subplot": 1,  # 单一主线
            "character_focus": 1,  # 聚焦单一角色
            "context_preservation": 0.4,  # 较低上下文保留
            "linearity": 0.85,  # 高线性度
        }
        
        # 合并自定义参数
        if params:
            strategy_params.update(params)
        
        # 1. 识别主要角色和主要冲突
        from src.knowledge.graph_builder import build_knowledge_graph
        knowledge_graph = build_knowledge_graph(base_script)
        
        # 获取最重要的角色
        character_importance = knowledge_graph.get_character_importance()
        main_character = list(character_importance.keys())[0] if character_importance else None
        
        # 获取核心事件（冲突点）
        core_events = knowledge_graph.get_key_events(top_k=3)
        
        # 2. 寻找与核心冲突相关的片段
        core_segments = []
        
        if main_character:
            # 收集主角相关片段
            for segment in base_script:
                text = segment.get("text", "")
                if main_character in text or text.startswith(f"{main_character}:") or text.startswith(f"{main_character}："):
                    core_segments.append(segment)
        
        # 如果没有找到足够的核心片段，根据事件关键词查找
        if len(core_segments) < len(base_script) * 0.3 and core_events:
            for segment in base_script:
                if segment not in core_segments:
                    text = segment.get("text", "")
                    for event in core_events:
                        if event in text:
                            core_segments.append(segment)
                            break
        
        # 如果仍然没有足够片段，使用强度调整选择片段
        if len(core_segments) < len(base_script) * 0.3:
            try:
                # 尝试导入强度调整器
                from src.adaptation.dynamic_intensity_adjuster import adjust_intensity
                intensity_map = adjust_intensity(base_script, target_ratio=0.4)
            except ImportError:
                # 备用方法：简单分配重要性分数
                logger.warning("强度调整器不可用，使用备用方法选择重要片段")
                intensity_map = self._fallback_adjust_intensity(base_script, target_ratio=0.4)
                
            core_segments = [
                segment for i, segment in enumerate(base_script)
                if i < len(intensity_map) and intensity_map[i] > 0.6
            ]
        
        # 确保至少有一些片段
        if not core_segments:
            # 如果没有核心片段，使用原始片段的一部分
            core_segments = base_script[:max(3, len(base_script) // 3)]
        
        # 3. 按时间顺序排序核心片段
        minimalist_script = sorted(core_segments, key=lambda x: x.get("start_time", 0))
        
        # 4. 使用基础引擎进一步处理
        result = self.screenplay_engineer.generate_screenplay(
            minimalist_script,
            preset_name=strategy_params.get("preset_name", "剧情紧凑"),
            custom_params=strategy_params
        )
        
        # 添加策略信息
        result["strategy"] = {
            "name": self.name,
            "description": self.__doc__,
            "timestamp": time.time(),
            "main_character": main_character,
            "reduction_ratio": len(minimalist_script) / len(base_script) if base_script else 1.0
        }
        
        return result

    def _fallback_adjust_intensity(self, segments: List[Dict[str, Any]], target_ratio: float = 0.5) -> List[float]:
        """备用方法：根据内容特征分配重要性分数
        
        Args:
            segments: 字幕片段列表
            target_ratio: 目标保留比例
            
        Returns:
            List[float]: 重要性分数列表 (0-1)
        """
        # 为每个片段分配重要性分数
        importance_scores = []
        
        for i, segment in enumerate(segments):
            text = segment.get("text", "")
            duration = segment.get("end_time", 0) - segment.get("start_time", 0)
            
            # 基础分数
            score = 0.5
            
            # 文本长度因素 (较长文本可能更重要)
            if len(text) > 50:
                score += 0.1
            elif len(text) < 10:
                score -= 0.1
                
            # 位置因素 (开头和结尾通常更重要)
            position_ratio = i / max(1, len(segments) - 1)
            if position_ratio < 0.2 or position_ratio > 0.8:
                score += 0.15
                
            # 持续时间因素 (时间较长可能更重要)
            if duration > 3.0:
                score += 0.1
                
            # 问号和感叹号可能表示重要内容
            if "?" in text or "！" in text or "?" in text or "!" in text:
                score += 0.15
                
            # 确保分数在0-1范围内
            importance_scores.append(max(0.0, min(1.0, score)))
        
        # 调整分数以匹配目标比例
        threshold = sorted(importance_scores, reverse=True)[
            min(int(len(segments) * target_ratio), len(segments) - 1)
        ]
        
        # 根据阈值标准化分数
        normalized_scores = [
            1.0 if score >= threshold else score / max(threshold, 0.001)
            for score in importance_scores
        ]
        
        return normalized_scores


class MultiStrategyEngine:
    """多策略生成引擎，协调多种生成策略"""
    
    def __init__(self):
        """初始化多策略引擎"""
        # 初始化策略
        self.strategies = {
            "倒叙重构": ReverseNarrativeStrategy(),
            "多线交织": ParallelThreadsStrategy(),
            "情感强化": EmotionAmplificationStrategy(),
            "简约风格": MinimalistAdaptationStrategy(),
        }
        
    def generate(self, base_script: List[Dict[str, Any]], 
                strategy_names: List[str] = None,
                base_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        使用多种策略生成不同的剧本版本
        
        Args:
            base_script: 原始字幕
            strategy_names: 策略名称列表，None表示使用全部策略
            base_params: 基础参数，会被各策略特定参数覆盖
            
        Returns:
            List[Dict[str, Any]]: 生成的剧本版本列表
        """
        if strategy_names is None:
            strategy_names = list(self.strategies.keys())
        
        logger.info(f"使用策略: {', '.join(strategy_names)}")
        
        # 准备基础参数
        base_params = base_params or {}
        
        # 策略执行结果
        results = []
        successful_results = []
        
        # 使用线程池并行执行策略
        with ThreadPoolExecutor(max_workers=min(len(strategy_names), 4)) as executor:
            # 提交任务
            future_to_strategy = {}
            
            for strategy_name in strategy_names:
                if strategy_name in self.strategies:
                    strategy = self.strategies[strategy_name]
                    
                    future = executor.submit(
                        strategy.execute,
                        base_script,
                        base_params
                    )
                    
                    future_to_strategy[future] = strategy_name
                else:
                    logger.warning(f"未知策略: {strategy_name}")
            
            # 收集结果
            for future in as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                
                try:
                    result = future.result()
                    if result:
                        result["strategy_name"] = strategy_name
                        results.append(result)
                        
                        # 多样性检查
                        if successful_results:
                            # 确保与已有结果有足够差异
                            prev_results_texts = [self._extract_text_for_comparison(r) for r in successful_results]
                            current_text = self._extract_text_for_comparison(result)
                            
                            # 计算与已有结果的相似度
                            is_diverse = True
                            for prev_text in prev_results_texts:
                                from src.nlp.text_embeddings import get_document_embedding, calculate_cosine_similarity
                                
                                # 获取文档嵌入
                                current_emb = get_document_embedding(current_text)
                                prev_emb = get_document_embedding(prev_text)
                                
                                # 计算相似度
                                similarity = calculate_cosine_similarity(current_emb, prev_emb)
                                
                                if similarity >= self.diversity_manager.similarity_threshold:
                                    logger.warning(f"策略 '{strategy_name}' 生成的剧本与现有版本相似度过高 ({similarity:.2f})")
                                    is_diverse = False
                                    break
                            
                            if is_diverse:
                                successful_results.append(result)
                                logger.info(f"策略 '{strategy_name}' 生成的剧本通过多样性检查")
                            else:
                                result["warning"] = "与其他版本过于相似，可能需要调整参数"
                        else:
                            # 第一个结果直接添加
                            successful_results.append(result)
                            
                        logger.info(f"策略 '{strategy_name}' 生成完成")
                    else:
                        logger.warning(f"策略 '{strategy_name}' 生成结果为空")
                        
                except Exception as e:
                    logger.error(f"策略 '{strategy_name}' 执行失败: {str(e)}")
        
        # 如果成功结果少于原始策略数量，可以尝试重新生成
        if len(successful_results) < len(strategy_names) and len(successful_results) > 0:
            # 再次尝试失败的策略，但使用不同参数
            failed_strategies = [name for name in strategy_names 
                                if name not in [r.get("strategy_name") for r in successful_results]]
            
            if failed_strategies:
                logger.info(f"尝试调整参数重新生成: {', '.join(failed_strategies)}")
                
                # 对失败的策略稍微调整参数再次尝试
                retry_params = base_params.copy()
                
                # 修改一些参数以增加多样性
                multipliers = {
                    "linearity": 0.7,
                    "context_preservation": 0.8, 
                    "emotion_intensity": 1.2,
                    "pace": 1.3
                }
                
                for param, multiplier in multipliers.items():
                    if param in retry_params:
                        retry_params[param] = max(0.1, min(1.0, retry_params[param] * multiplier))
                
                # 重试失败的策略
                for strategy_name in failed_strategies:
                    if strategy_name in self.strategies:
                        try:
                            strategy = self.strategies[strategy_name]
                            result = strategy.execute(base_script, retry_params)
                            
                            if result:
                                result["strategy_name"] = strategy_name
                                result["is_retry"] = True
                                
                                # 检查多样性
                                is_diverse = self._check_diversity_against_existing(result, successful_results)
                                
                                if is_diverse:
                                    successful_results.append(result)
                                    logger.info(f"重试策略 '{strategy_name}' 成功")
                                else:
                                    result["warning"] = "重试生成，但与其他版本仍过于相似"
                                    results.append(result)
                        except Exception as e:
                            logger.error(f"重试策略 '{strategy_name}' 失败: {str(e)}")
        
        # 将成功通过多样性检查的结果添加到最终结果
        for result in successful_results:
            if result not in results:
                results.append(result)
        
        return results
    
    def _extract_text_for_comparison(self, result: Dict[str, Any]) -> str:
        """从结果中提取文本用于比较"""
        text = ""
        
        # 从不同格式中提取文本
        if "screenplay" in result and isinstance(result["screenplay"], list):
            for scene in result["screenplay"]:
                if isinstance(scene, dict):
                    if "content" in scene:
                        text += scene["content"] + "\n"
                    if "dialogue" in scene and isinstance(scene["dialogue"], list):
                        for line in scene["dialogue"]:
                            if isinstance(line, dict) and "text" in line:
                                text += line["text"] + "\n"
                            elif isinstance(line, str):
                                text += line + "\n"
        
        # 如果是字幕格式
        elif "subtitles" in result and isinstance(result["subtitles"], list):
            for subtitle in result["subtitles"]:
                if isinstance(subtitle, dict) and "text" in subtitle:
                    text += subtitle["text"] + "\n"
        
        # 如果有脚本文本字段
        elif "script_text" in result and isinstance(result["script_text"], str):
            text += result["script_text"]
            
        return text
    
    def _check_diversity_against_existing(self, new_result: Dict[str, Any], 
                                         existing_results: List[Dict[str, Any]]) -> bool:
        """检查新结果与现有结果的多样性"""
        if not existing_results:
            return True
            
        new_text = self._extract_text_for_comparison(new_result)
        
        for existing in existing_results:
            existing_text = self._extract_text_for_comparison(existing)
            
            from src.nlp.text_embeddings import get_document_embedding, calculate_cosine_similarity
            
            # 获取文档嵌入
            new_emb = get_document_embedding(new_text)
            existing_emb = get_document_embedding(existing_text)
            
            # 计算相似度
            similarity = calculate_cosine_similarity(new_emb, existing_emb)
            
            if similarity >= self.diversity_manager.similarity_threshold:
                return False
                
        return True


def run_multi_strategy(subtitles: List[Dict[str, Any]], 
                      strategies: List[str] = None, 
                      params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """快捷函数: 执行多策略生成
    
    Args:
        subtitles: 原始字幕
        strategies: 策略名称列表
        params: 基础参数
        
    Returns:
        List[Dict[str, Any]]: 生成结果列表
    """
    engine = MultiStrategyEngine()
    return engine.generate(subtitles, strategies, params) 