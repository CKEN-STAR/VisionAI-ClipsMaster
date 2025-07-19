#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事引擎模块

该模块负责处理和转换叙事结构，实现短视频剧情重混功能。
它利用大型语言模型（Mistral-7B用于英文，Qwen2.5-7B用于中文）
分析和重构视频脚本，产生新的叙事形式。
"""

import os
import time
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from enum import Enum

# 导入核心异常类
from src.utils.exceptions import (
    ClipMasterError,
    ModelCorruptionError,
    ProcessingError
)

# 获取日志记录器
logger = logging.getLogger(__name__)

class PlotStructure(Enum):
    """剧情结构类型枚举"""
    LINEAR = "线性结构"             # 传统时间线性叙事
    NONLINEAR = "非线性结构"        # 打乱时间线叙事
    PARALLEL = "平行叙事"           # 多线并行叙事
    CIRCULAR = "循环叙事"           # 结尾回到开始的循环结构
    NESTED = "嵌套叙事"             # 故事中有故事的结构
    BRANCHING = "分支叙事"          # 多条可能的情节线

class NarrativeAnalysisError(ClipMasterError):
    """叙事分析错误异常"""
    
    def __init__(self, message=None, narrative_type=None, details=None):
        """初始化叙事分析错误异常"""
        self.narrative_type = narrative_type
        self.details = details or {}
        
        if message is None:
            message = "叙事分析错误"
            if narrative_type is not None:
                message += f": {narrative_type}"
        
        super().__init__(message, code="PROCESSING_ERROR", critical=False)
    
    def format_error(self) -> Dict[str, Any]:
        """格式化错误信息
        
        Returns:
            Dict[str, Any]: 格式化的错误信息
        """
        return {
            "error_type": "NarrativeAnalysisError",
            "message": str(self),
            "narrative_type": self.narrative_type,
            "details": self.details,
            "timestamp": time.time(),
            "is_critical": False
        }

class NarrativeEngine:
    """叙事引擎类，负责剧情分析和重混"""
    
    def __init__(self, model_switcher=None):
        """初始化叙事引擎
        
        Args:
            model_switcher: 模型切换器，如果不提供则创建新的实例
        """
        # 懒加载模型切换器
        self.model_switcher = model_switcher
        if self.model_switcher is None:
            from src.core.model_switcher import ModelSwitcher
            self.model_switcher = ModelSwitcher()
            
        # 懒加载分析器
        self._analyzer = None
        
        # 懒加载语言检测器
        self._language_detector = None
        
        # 懒加载内存守护
        self._memory_guard = None
        
        # 缓存最近的分析结果
        self.last_analysis = {}
        
        logger.info("叙事引擎初始化完成")
    
    @property
    def analyzer(self):
        """获取叙事分析器"""
        if self._analyzer is None:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            self._analyzer = NarrativeAnalyzer()
        return self._analyzer
    
    @analyzer.setter
    def analyzer(self, value):
        """设置叙事分析器"""
        self._analyzer = value
    
    @property
    def language_detector(self):
        """获取语言检测器"""
        if self._language_detector is None:
            from src.core.language_detector import LanguageDetector
            self._language_detector = LanguageDetector()
        return self._language_detector
    
    @language_detector.setter
    def language_detector(self, value):
        """设置语言检测器"""
        self._language_detector = value
    
    @property
    def memory_guard(self):
        """获取内存守护"""
        if self._memory_guard is None:
            from src.utils.memory_guard import get_memory_guard
            self._memory_guard = get_memory_guard()
        return self._memory_guard
    
    def analyze_script(self, script: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析脚本的叙事结构
        
        Args:
            script: 脚本内容列表，每个元素是一个字幕片段
            
        Returns:
            Dict[str, Any]: 叙事结构分析结果
        """
        if not script:
            raise ValueError("脚本内容为空")
            
        try:
            # 使用叙事分析器进行分析
            analysis = self.analyzer.analyze_script(script)
            self.last_analysis = analysis
            return analysis
        except Exception as e:
            logger.error(f"脚本分析失败: {str(e)}")
            raise NarrativeAnalysisError(f"分析脚本时出错: {str(e)}", narrative_type="analysis")
    
    def remix_plot(self, script: List[Dict[str, Any]], 
                   structure_type: Optional[Union[PlotStructure, str]] = None,
                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """重混剧情结构
        
        根据指定的剧情结构类型，对原始脚本进行重新组织和增强。
        
        Args:
            script: 原始脚本内容
            structure_type: 目标剧情结构类型，如果不指定则自动选择
            params: 额外参数
            
        Returns:
            Dict[str, Any]: 包含重混后的脚本和元数据
        """
        # 如果输入是字符串，则转换为简单的剧本格式
        if isinstance(script, str):
            script = [{"id": 1, "start_time": 0, "end_time": 5, "text": script}]
            
        if not script:
            raise ValueError("脚本内容为空")
            
        # 标准化structure_type参数
        if isinstance(structure_type, str):
            try:
                structure_type = PlotStructure(structure_type)
            except ValueError:
                # 尝试匹配中文名称
                for struct in PlotStructure:
                    if struct.value == structure_type:
                        structure_type = struct
                        break
                # 如果仍然无法匹配，使用默认值
                if isinstance(structure_type, str):
                    structure_type = None
        
        # 如果未指定结构类型，根据脚本内容智能选择
        if structure_type is None:
            structure_type = self._suggest_structure_type(script)
            logger.info(f"自动选择剧情结构: {structure_type.value}")
        
        # 准备处理参数
        process_params = {
            "creativity": 0.7,   # 创造力因子 (0-1)
            "coherence": 0.8,    # 连贯性因子 (0-1)
            "preserve_key_points": True,  # 是否保留关键点
            "max_length_multiplier": 1.2  # 最大长度倍数
        }
        
        # 合并用户提供的参数
        if params:
            process_params.update(params)
        
        try:
            # 检测语言
            sample_text = " ".join([item.get("text", "") for item in script[:10]])
            language = self.language_detector.detect_language(sample_text)
            
            # 选择合适的模型
            model = self.model_switcher.get_model_for_language(language)
            
            # 执行重混逻辑
            if structure_type == PlotStructure.LINEAR:
                result = self._remix_linear(script, model, process_params)
            elif structure_type == PlotStructure.NONLINEAR:
                result = self._remix_nonlinear(script, model, process_params)
            elif structure_type == PlotStructure.PARALLEL:
                result = self._remix_parallel(script, model, process_params)
            elif structure_type == PlotStructure.CIRCULAR:
                result = self._remix_circular(script, model, process_params)
            elif structure_type == PlotStructure.NESTED:
                result = self._remix_nested(script, model, process_params)
            elif structure_type == PlotStructure.BRANCHING:
                result = self._remix_branching(script, model, process_params)
            else:
                # 默认使用通用重混方法
                result = self._remix_general(script, model, process_params)
            
            # 添加元数据
            result["metadata"] = {
                "original_length": len(script),
                "remixed_length": len(result.get("script", [])),
                "structure_type": structure_type.value if isinstance(structure_type, PlotStructure) else str(structure_type),
                "timestamp": time.time(),
                "params": process_params
            }
            
            # 增加分析数据
            if self.last_analysis:
                result["analysis"] = self.last_analysis
            
            return result
            
        except ModelCorruptionError:
            # 模型损坏错误，应当被更高层处理
            raise
        except Exception as e:
            logger.error(f"剧情重混过程出错: {str(e)}")
            raise ProcessingError(f"重混剧情时出错: {str(e)}", processor_name="narrative_engine")
    
    def _suggest_structure_type(self, script: List[Dict[str, Any]]) -> PlotStructure:
        """根据脚本内容建议合适的剧情结构类型
        
        Args:
            script: 脚本内容
            
        Returns:
            PlotStructure: 建议的剧情结构类型
        """
        # 分析脚本内容特征
        try:
            analysis = self.analyze_script(script)
            
            # 获取情感曲线和情节密度
            emotion_curve = analysis.get("emotion_curve", {})
            plot_density = analysis.get("plot_density", {})
            
            # 基于分析结果启发式选择结构类型
            # (这里是一个简化的选择逻辑，实际可能更复杂)
            
            # 检查是否有明显的情感波动
            emotional_variance = emotion_curve.get("variance", 0)
            
            # 检查是否有多个主要角色
            character_count = len(analysis.get("character_interactions", {}).get("main_characters", []))
            
            # 检查是否有明显的转折点
            pivot_points = plot_density.get("pivot_points", [])
            
            # 根据特征选择结构
            if len(pivot_points) >= 3 and emotional_variance > 0.5:
                # 情感波动大且有多个转折点，适合非线性结构
                return PlotStructure.NONLINEAR
            elif character_count >= 3:
                # 多个主要角色，适合平行叙事
                return PlotStructure.PARALLEL
            elif emotional_variance < 0.3:
                # 情感平稳，适合线性结构
                return PlotStructure.LINEAR
            else:
                # 默认使用线性结构
                return PlotStructure.LINEAR
                
        except Exception:
            # 分析失败时使用随机选择
            logger.warning("分析脚本失败，随机选择剧情结构")
            return random.choice([
                PlotStructure.LINEAR, 
                PlotStructure.NONLINEAR,
                PlotStructure.PARALLEL
            ])
    
    def _remix_linear(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """线性结构重混
        
        保持时间线顺序，但加强情节连贯性和情感表达
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 在实际实现中，这里会使用模型对脚本进行增强
        # 这里为简化只实现基本功能
        
        # 创建增强版脚本
        enhanced_script = []
        for item in script:
            enhanced_item = item.copy()
            # 在此处添加模型处理逻辑...
            enhanced_script.append(enhanced_item)
        
        return {
            "script": enhanced_script,
            "structure": "linear"
        }
    
    def _remix_nonlinear(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """非线性结构重混
        
        重新排列时间线，创造悬念和张力
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 分析脚本，找出关键点
        scenes = []
        for i, item in enumerate(script):
            scenes.append({
                "index": i,
                "content": item,
                "importance": random.random()  # 在实际中应使用模型评估重要性
            })
        
        # 按重要性排序
        scenes.sort(key=lambda x: x["importance"], reverse=True)
        
        # 重新排列脚本
        top_scenes = scenes[:len(scenes)//3]  # 取最重要的1/3场景
        rest_scenes = scenes[len(scenes)//3:]  # 其余场景
        
        # 混排场景，先放置一个重要场景，然后是几个其他场景
        remixed_scenes = []
        while top_scenes or rest_scenes:
            # 添加一个重要场景
            if top_scenes:
                remixed_scenes.append(top_scenes.pop(0))
            
            # 添加2-3个其他场景
            count = min(random.randint(2, 3), len(rest_scenes))
            for _ in range(count):
                if rest_scenes:
                    remixed_scenes.append(rest_scenes.pop(0))
        
        # 按原始索引提取内容
        remixed_script = [item["content"] for item in remixed_scenes]
        
        return {
            "script": remixed_script,
            "structure": "nonlinear"
        }
    
    def _remix_parallel(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """平行叙事结构重混
        
        创建多个并行的故事线
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 简化实现，将脚本分为两条故事线交替展示
        story_line_1 = []
        story_line_2 = []
        
        # 简单地将脚本分为两部分
        midpoint = len(script) // 2
        for i, item in enumerate(script):
            if i < midpoint:
                story_line_1.append(item)
            else:
                story_line_2.append(item)
        
        # 交错组合两条故事线
        remixed_script = []
        max_len = max(len(story_line_1), len(story_line_2))
        for i in range(max_len):
            if i < len(story_line_1):
                remixed_script.append(story_line_1[i])
            if i < len(story_line_2):
                remixed_script.append(story_line_2[i])
        
        return {
            "script": remixed_script,
            "structure": "parallel"
        }
    
    def _remix_circular(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """循环叙事结构重混
        
        创建首尾呼应的循环结构
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 简化实现，将结尾部分移到开头，创造首尾呼应的效果
        if len(script) < 4:
            return {"script": script, "structure": "circular"}
            
        # 取结尾部分
        ending = script[-2:]
        # 取中间部分
        middle = script[2:-2]
        # 取开头部分
        beginning = script[:2]
        
        # 重组：结尾+中间+开头
        remixed_script = ending + middle + beginning
        
        return {
            "script": remixed_script,
            "structure": "circular"
        }
    
    def _remix_nested(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """嵌套叙事结构重混
        
        创建故事中有故事的嵌套结构
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 简化实现，创建一个外层故事和内层故事
        if len(script) < 6:
            return {"script": script, "structure": "nested"}
            
        # 外层故事开始
        outer_start = script[:2]
        # 内层故事
        inner_story = script[2:-2]
        # 外层故事结束
        outer_end = script[-2:]
        
        # 添加过渡提示
        transition_in = {"text": "【内层故事开始】", "start_time": inner_story[0]["start_time"], "end_time": inner_story[0]["start_time"]}
        transition_out = {"text": "【回到外层故事】", "start_time": inner_story[-1]["end_time"], "end_time": inner_story[-1]["end_time"]}
        
        # 组合
        remixed_script = outer_start + [transition_in] + inner_story + [transition_out] + outer_end
        
        return {
            "script": remixed_script,
            "structure": "nested"
        }
    
    def _remix_branching(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """分支叙事结构重混
        
        创建多个可能的结局或情节走向
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 简化实现，创建一个主干和两个分支结局
        if len(script) < 6:
            return {"script": script, "structure": "branching"}
            
        # 主干部分
        main_trunk = script[:-4]
        
        # 两个可能的结局
        ending1 = script[-4:-2]
        ending2 = script[-2:]
        
        # 添加分支提示
        branch_point = {"text": "【故事分支点】", "start_time": main_trunk[-1]["end_time"], "end_time": main_trunk[-1]["end_time"]}
        branch1_start = {"text": "【可能的结局一】", "start_time": ending1[0]["start_time"], "end_time": ending1[0]["start_time"]}
        branch2_start = {"text": "【可能的结局二】", "start_time": ending2[0]["start_time"], "end_time": ending2[0]["start_time"]}
        
        # 组合
        remixed_script = main_trunk + [branch_point, branch1_start] + ending1 + [branch2_start] + ending2
        
        return {
            "script": remixed_script,
            "structure": "branching"
        }
    
    def _remix_general(self, script: List[Dict[str, Any]], model: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """通用重混方法
        
        当没有指定特定结构类型时使用的默认方法
        
        Args:
            script: 原始脚本
            model: 语言模型
            params: 处理参数
            
        Returns:
            Dict[str, Any]: 重混结果
        """
        # 为简单起见，这里只实现一个基础的脚本增强
        enhanced_script = []
        
        for item in script:
            # 复制原始条目
            enhanced_item = item.copy()
            # 这里可以添加更多处理...
            enhanced_script.append(enhanced_item)
        
        return {
            "script": enhanced_script,
            "structure": "general"
        } 