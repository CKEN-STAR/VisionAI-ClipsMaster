#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
叙事引擎模块

提供基于大型语言模型的叙事分析和剧本重构功能，
支持不同叙事结构的内容重组和创意转换。
"""

import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union
import importlib.util

# 创建日志记录器
logger = logging.getLogger("narrative_engine")

class PlotStructure(Enum):
    """叙事结构类型枚举"""
    
    LINEAR = "linear"           # 线性结构
    NONLINEAR = "nonlinear"     # 非线性结构
    PARALLEL = "parallel"       # 平行结构
    CIRCULAR = "circular"       # 环形结构
    NESTED = "nested"           # 嵌套结构
    BRANCHING = "branching"     # 分支结构

    @classmethod
    def from_string(cls, structure_name: str) -> 'PlotStructure':
        """从字符串转换为枚举值"""
        if structure_name is None:
            return cls.LINEAR
            
        # 英文名称映射
        english_map = {
            "linear": cls.LINEAR,
            "nonlinear": cls.NONLINEAR, 
            "parallel": cls.PARALLEL,
            "circular": cls.CIRCULAR,
            "nested": cls.NESTED,
            "branching": cls.BRANCHING
        }
        
        # 中文名称映射
        chinese_map = {
            "线性": cls.LINEAR,
            "非线性": cls.NONLINEAR,
            "平行": cls.PARALLEL,
            "环形": cls.CIRCULAR,
            "环状": cls.CIRCULAR,  # 添加"环状"作为"环形"的同义词
            "嵌套": cls.NESTED,
            "分支": cls.BRANCHING
        }
        
        # 统一转为小写处理
        structure_name = structure_name.lower()
        
        # 尝试从英文或中文名称映射
        if structure_name in english_map:
            return english_map[structure_name]
        # 对于中文，不转小写再尝试
        elif structure_name.upper() in [name.upper() for name in chinese_map.keys()]:
            # 不区分大小写找到匹配的键
            for key in chinese_map:
                if key.upper() == structure_name.upper():
                    return chinese_map[key]
        else:
            # 找不到匹配项，使用最接近的字符串匹配
            import difflib
            all_keys = list(english_map.keys()) + list(chinese_map.keys())
            closest = difflib.get_close_matches(structure_name, all_keys, n=1)
            if closest:
                if closest[0] in english_map:
                    return english_map[closest[0]]
                else:
                    return chinese_map[closest[0]]
            # 默认使用线性结构
            return cls.LINEAR


class NarrativeAnalysisError(Exception):
    """叙事分析错误"""
    pass


class NarrativeEngine:
    """叙事引擎核心类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化叙事引擎
        
        Args:
            config: 配置参数，如果为None则使用默认配置
        """
        self.config = config or {}
        
        # 模型管理器属性 - 用于延迟加载解决循环依赖
        self._model_manager = None
        
        # 锚点检测器属性 - 用于延迟加载解决循环依赖
        self._anchor_detector = None
        
        # 结构选择器属性 - 用于延迟加载解决循环依赖
        self._structure_selector = None
        
        logger.info("叙事引擎初始化完成")

    @property
    def model_manager(self):
        """延迟加载模型管理器"""
        if self._model_manager is None:
            try:
                from src.models.model_manager import ModelManager
                self._model_manager = ModelManager()
            except ImportError:
                logger.warning("无法导入模型管理器，使用测试替代")
                # 使用测试替代以避免循环导入
                self._model_manager = type('TestModelManager', (), {
                    'get_completion': lambda s, p, m="mistral": f"Test completion for: {p[:20]}...",
                    'generate_text': lambda s, p, m="mistral": f"Generated text for: {p[:20]}..."
                })()
        return self._model_manager
    
    @property
    def anchor_detector(self):
        """延迟加载锚点检测器"""
        if self._anchor_detector is None:
            try:
                from src.narrative.anchor_detector import AnchorDetector
                self._anchor_detector = AnchorDetector()
            except ImportError:
                logger.warning("无法导入锚点检测器，使用测试替代")
                # 使用测试替代以避免循环导入
                self._anchor_detector = type('TestAnchorDetector', (), {
                    'detect_anchors': lambda s, t: []
                })()
        return self._anchor_detector
    
    @property
    def structure_selector(self):
        """延迟加载结构选择器"""
        if self._structure_selector is None:
            try:
                from src.narrative.structure_selector import StructureSelector
                self._structure_selector = StructureSelector()
            except ImportError:
                logger.warning("无法导入结构选择器，使用测试替代")
                # 使用测试替代以避免循环导入
                self._structure_selector = type('TestStructureSelector', (), {
                    'select_best_fit': lambda s, m, a=None: {
                        "pattern_name": "测试结构",
                        "confidence": 0.8
                    }
                })()
        return self._structure_selector
    
    def analyze_script(self, script_content: Union[str, List[str]]) -> Dict[str, Any]:
        """
        分析剧本内容，提取关键特征和锚点
        
        Args:
            script_content: 剧本内容，可以是字符串或者字符串列表
            
        Returns:
            包含分析结果的字典
        """
        # 确保内容是字符串
        if isinstance(script_content, list):
            script_text = "\n".join(script_content)
        else:
            script_text = script_content
        
        # TODO: 实现真实的分析逻辑
        return {
            "length": len(script_text),
            "scene_count": script_text.count("场景") + script_text.count("Scene"),
            "analysis_completed": True
        }
    
    def remix_plot(self, script_content: Union[str, List[str]], 
                  structure_type: Optional[Union[str, PlotStructure]] = None,
                  **kwargs) -> Dict[str, Any]:
        """
        根据指定的叙事结构重构剧本
        
        Args:
            script_content: 剧本内容，可以是字符串或者字符串列表
            structure_type: 叙事结构类型，可以是PlotStructure枚举或字符串
            **kwargs: 其他参数
            
        Returns:
            包含重构后剧本的字典
        """
        # 将剧本内容转换为标准格式
        if isinstance(script_content, list):
            script_lines = script_content
            script_text = "\n".join(script_content)
        else:
            script_text = script_content
            script_lines = script_content.split("\n")
        
        # 标准化结构类型
        if structure_type is None:
            # 自动选择最佳结构
            script_metadata = self.analyze_script(script_text)
            best_structure = self.structure_selector.select_best_fit(script_metadata)
            structure = best_structure.get("pattern_name", "linear")
            structure_type = PlotStructure.from_string(structure)
        elif isinstance(structure_type, str):
            structure_type = PlotStructure.from_string(structure_type)
        
        # 实现不同结构的重构逻辑
        if structure_type == PlotStructure.LINEAR:
            remixed_content = self._remix_linear(script_lines)
        elif structure_type == PlotStructure.NONLINEAR:
            remixed_content = self._remix_nonlinear(script_lines)
        elif structure_type == PlotStructure.PARALLEL:
            remixed_content = self._remix_parallel(script_lines)
        elif structure_type == PlotStructure.CIRCULAR:
            remixed_content = self._remix_circular(script_lines)
        elif structure_type == PlotStructure.NESTED:
            remixed_content = self._remix_nested(script_lines)
        elif structure_type == PlotStructure.BRANCHING:
            remixed_content = self._remix_branching(script_lines)
        else:
            raise NarrativeAnalysisError(f"不支持的叙事结构类型: {structure_type}")
        
        # 返回结果
        return {
            "original_length": len(script_lines),
            "remixed_length": len(remixed_content),
            "structure_type": structure_type.value,
            "remixed_content": remixed_content,
            "metadata": {
                "structure_description": self._get_structure_description(structure_type)
            }
        }
    
    def _remix_linear(self, script_lines: List[str]) -> List[str]:
        """线性结构重混逻辑"""
        # 这里应该实现实际的线性结构重构逻辑
        # 线性结构通常保持原有的时间线顺序
        return script_lines
    
    def _remix_nonlinear(self, script_lines: List[str]) -> List[str]:
        """非线性结构重混逻辑"""
        # 实现非线性结构重构，如倒叙、插叙等
        # 暂时使用模拟实现
        import random
        
        # 将脚本分成若干段落
        segments = []
        segment = []
        for line in script_lines:
            segment.append(line)
            if len(segment) > 10 and (not line.strip() or line.strip().startswith("场景") or line.strip().startswith("Scene")):
                segments.append(segment)
                segment = []
        
        # 确保最后一个段落被添加
        if segment:
            segments.append(segment)
        
        # 随机打乱段落顺序
        random.shuffle(segments)
        
        # 展平列表
        return [line for segment in segments for line in segment]
    
    def _remix_parallel(self, script_lines: List[str]) -> List[str]:
        """平行结构重混逻辑"""
        # 实现平行结构重构，多条故事线交替呈现
        # 暂时使用模拟实现
        result = []
        # 创建两条故事线
        story_a = script_lines[:len(script_lines)//2]
        story_b = script_lines[len(script_lines)//2:]
        
        # 交错合并
        max_len = max(len(story_a), len(story_b))
        for i in range(max_len):
            # 添加故事线A的片段
            if i < len(story_a):
                result.append("[故事线A]")
                result.extend(story_a[i:i+5 if i+5 < len(story_a) else len(story_a)])
            
            # 添加故事线B的片段
            if i < len(story_b):
                result.append("[故事线B]")
                result.extend(story_b[i:i+5 if i+5 < len(story_b) else len(story_b)])
        
        return result
    
    def _remix_circular(self, script_lines: List[str]) -> List[str]:
        """环形结构重混逻辑"""
        # 实现环形结构重构，首尾呼应
        # 暂时使用模拟实现
        result = []
        
        # 提取开头部分
        intro = script_lines[:min(10, len(script_lines)//10)]
        
        # 添加开头作为引言
        result.extend(intro)
        result.append("\n[正文开始]\n")
        
        # 添加中间内容
        result.extend(script_lines[len(intro):-min(10, len(script_lines)//10)])
        
        # 结尾回到开头，形成环形
        result.append("\n[回到开始]\n")
        result.extend(intro)
        
        return result
    
    def _remix_nested(self, script_lines: List[str]) -> List[str]:
        """嵌套结构重混逻辑"""
        # 实现嵌套结构重构，故事中套故事
        # 暂时使用模拟实现
        result = []
        
        # 将脚本分成三个部分
        part1 = script_lines[:len(script_lines)//3]
        part2 = script_lines[len(script_lines)//3:2*len(script_lines)//3]
        part3 = script_lines[2*len(script_lines)//3:]
        
        # 创建嵌套结构
        result.extend(part1[:len(part1)//2])
        result.append("\n[内部故事开始]\n")
        result.extend(part2)
        result.append("\n[回到外部故事]\n")
        result.extend(part1[len(part1)//2:])
        result.append("\n[另一个内部故事开始]\n")
        result.extend(part3)
        result.append("\n[回到主故事并结束]\n")
        
        return result
    
    def _remix_branching(self, script_lines: List[str]) -> List[str]:
        """分支结构重混逻辑"""
        # 实现分支结构重构，提供多个可能的情节发展
        # 暂时使用模拟实现
        result = []
        
        # 将脚本分成前半部分和后半部分
        midpoint = len(script_lines) // 2
        first_half = script_lines[:midpoint]
        second_half = script_lines[midpoint:]
        
        # 创建两个不同的结局
        ending_a = second_half[:len(second_half)//2]
        ending_b = second_half[len(second_half)//2:]
        
        # 构建分支叙事
        result.extend(first_half)
        result.append("\n[分支A：悲剧结局]\n")
        result.extend(ending_a)
        result.append("\n[分支B：喜剧结局]\n")
        result.extend(ending_b)
        
        return result
    
    def _get_structure_description(self, structure_type: PlotStructure) -> str:
        """获取结构类型的描述"""
        descriptions = {
            PlotStructure.LINEAR: "线性结构保持事件的时间顺序，按照故事发生的先后顺序呈现",
            PlotStructure.NONLINEAR: "非线性结构打破时间顺序，使用倒叙、插叙等手法重组故事",
            PlotStructure.PARALLEL: "平行结构同时展示多条独立但相关的故事线，最终汇聚",
            PlotStructure.CIRCULAR: "环形结构使故事结尾回到开始，形成循环，但角色或情境已有变化",
            PlotStructure.NESTED: "嵌套结构在主要故事中嵌入次要故事，形成故事中的故事",
            PlotStructure.BRANCHING: "分支结构提供多种可能的情节发展路径，展示不同的结局"
        }
        return descriptions.get(structure_type, "未定义的结构类型")


def remix_plot(script_content: Union[str, List[str]], 
              structure_type: Optional[Union[str, PlotStructure]] = None,
              **kwargs) -> Dict[str, Any]:
    """
    根据指定的叙事结构重构剧本的便捷函数
    
    Args:
        script_content: 剧本内容，可以是字符串或者字符串列表
        structure_type: 叙事结构类型，可以是PlotStructure枚举或字符串
        **kwargs: 其他参数
        
    Returns:
        包含重构后剧本的字典
    """
    engine = NarrativeEngine()
    return engine.remix_plot(script_content, structure_type, **kwargs) 