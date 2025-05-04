"""
时空折叠引擎 - 核心组件

将线性时间轴重构为非线性叙事结构的核心功能模块
"""

import os
import logging
import copy
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import numpy as np

from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.narrative.structure_selector import StructureSelector
from src.utils.validators import validate_float_range

# 创建日志记录器
logger = logging.getLogger("time_folder")

class FoldingMode(Enum):
    """折叠模式枚举"""
    PRESERVE_ANCHORS = "preserve_anchors"  # 保留关键锚点
    CONDENSE_SIMILAR = "condense_similar"  # 压缩相似场景
    HIGHLIGHT_CONTRAST = "highlight_contrast"  # 强调对比场景
    NARRATIVE_DRIVEN = "narrative_driven"  # 叙事驱动折叠

class TimeFoldingStrategy:
    """时间折叠策略"""
    
    def __init__(self, name: str, description: str, structure_types: List[str]):
        """
        初始化时间折叠策略
        
        Args:
            name: 策略名称
            description: 策略描述
            structure_types: 适用的叙事结构类型列表
        """
        self.name = name
        self.description = description
        self.structure_types = structure_types
        self.anchor_weights = {
            AnchorType.EMOTION: 1.0,
            AnchorType.SUSPENSE: 1.0,
            AnchorType.CHARACTER: 1.0,
            AnchorType.TRANSITION: 1.0,
            AnchorType.CLIMAX: 1.0,
            AnchorType.REVELATION: 1.0,
            AnchorType.RESOLUTION: 1.0
        }
        self.fold_ratio = 0.4  # 默认折叠率(非关键场景压缩40%)
        self.preserve_start = True  # 默认保留开始场景
        self.preserve_end = True    # 默认保留结束场景
        
    def set_anchor_weight(self, anchor_type: AnchorType, weight: float) -> None:
        """
        设置特定类型锚点的权重
        
        Args:
            anchor_type: 锚点类型
            weight: 权重值(0.0-2.0)
        """
        validated_weight = validate_float_range(weight, 0.0, 2.0)
        self.anchor_weights[anchor_type] = validated_weight
    
    def set_fold_ratio(self, ratio: float) -> None:
        """
        设置折叠率
        
        Args:
            ratio: 折叠率(0.0-1.0)，表示要压缩的比例
        """
        validated_ratio = validate_float_range(ratio, 0.0, 0.9)
        self.fold_ratio = validated_ratio

class TimeFolder:
    """时空折叠引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化时空折叠引擎
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 初始化折叠策略库
        self.strategies = self._init_strategies()
        
        # 加载配置
        self._load_config(config_path)
        
        # 初始化叙事结构选择器（用于结构匹配）
        self.structure_selector = StructureSelector()
        
        logger.info("时空折叠引擎初始化完成")
    
    def _init_strategies(self) -> Dict[str, TimeFoldingStrategy]:
        """初始化内置折叠策略库"""
        strategies = {}
        
        # 1. 倒叙折叠策略
        flashback = TimeFoldingStrategy(
            "倒叙风暴", 
            "从高潮点开始，通过回忆和闪回构建叙事",
            ["倒叙风暴", "flashback_storm"]
        )
        flashback.set_anchor_weight(AnchorType.CLIMAX, 2.0)
        flashback.set_anchor_weight(AnchorType.EMOTION, 1.5)
        flashback.set_fold_ratio(0.5)
        strategies["倒叙风暴"] = flashback
        
        # 2. 多线交织策略
        multithread = TimeFoldingStrategy(
            "多线织网",
            "交织多条故事线，强调人物关系和情感变化",
            ["多线织网", "multi_thread"]
        )
        multithread.set_anchor_weight(AnchorType.CHARACTER, 1.8)
        multithread.set_anchor_weight(AnchorType.TRANSITION, 1.5)
        multithread.set_fold_ratio(0.3)
        strategies["多线织网"] = multithread
        
        # 3. 环形叙事策略
        circular = TimeFoldingStrategy(
            "环形结构",
            "首尾呼应，形成循环叙事结构",
            ["环形结构", "circular_narrative"]
        )
        circular.set_anchor_weight(AnchorType.TRANSITION, 1.7)
        circular.set_anchor_weight(AnchorType.RESOLUTION, 1.6)
        circular.set_fold_ratio(0.4)
        strategies["环形结构"] = circular
        
        # 4. 高潮递进策略
        escalating = TimeFoldingStrategy(
            "高潮迭起",
            "多个高潮点递进，不断提升紧张感",
            ["高潮迭起", "escalating_peaks"]
        )
        escalating.set_anchor_weight(AnchorType.CLIMAX, 1.9)
        escalating.set_anchor_weight(AnchorType.EMOTION, 1.6)
        escalating.set_fold_ratio(0.25)
        strategies["高潮迭起"] = escalating
        
        # 5. 并行蒙太奇策略
        parallel = TimeFoldingStrategy(
            "并行蒙太奇",
            "两条故事线并行发展，通过交替场景展现",
            ["并行交替", "parallel_montage"]
        )
        parallel.set_anchor_weight(AnchorType.CHARACTER, 1.6)
        parallel.set_anchor_weight(AnchorType.TRANSITION, 1.8)
        parallel.set_fold_ratio(0.3)
        strategies["并行蒙太奇"] = parallel
        
        return strategies
    
    def _load_config(self, config_path: Optional[str] = None) -> None:
        """加载配置文件"""
        # 使用默认配置
        self.config = {
            "default_strategy": "倒叙风暴",
            "preserve_anchor_threshold": 0.7,  # 保留锚点的重要性阈值
            "scene_similarity_threshold": 0.8,  # 场景相似度阈值
            "min_scene_duration": 2.0,  # 最小场景时长(秒)
            "allow_adaptive_folding": True  # 允许自适应折叠
        }
        
        # TODO: 如果指定了配置文件路径，加载自定义配置
        
        # 初始化默认折叠模式
        self.default_mode = FoldingMode.PRESERVE_ANCHORS
    
    def fold_timeline(self, 
                     scenes: List[Dict[str, Any]], 
                     anchors: List[AnchorInfo],
                     structure_name: Optional[str] = None, 
                     strategy_name: Optional[str] = None,
                     mode: Optional[FoldingMode] = None) -> List[Dict[str, Any]]:
        """
        根据指定的叙事结构和策略折叠时间轴
        
        Args:
            scenes: 场景列表
            anchors: 识别出的锚点列表
            structure_name: 叙事结构名称，如果为None则使用默认
            strategy_name: 折叠策略名称，如果为None则根据结构自动选择
            mode: 折叠模式，如果为None则使用默认模式
            
        Returns:
            折叠后的场景列表
        """
        if not scenes or not anchors:
            logger.warning("场景或锚点为空，无法进行时间折叠")
            return scenes
        
        # 确定叙事结构
        if not structure_name:
            structure_name = self.config.get("default_structure", "倒叙风暴")
        
        # 确定折叠策略
        strategy = self._get_strategy_for_structure(structure_name, strategy_name)
        
        # 确定折叠模式
        folding_mode = mode if mode else self.default_mode
        
        # 执行折叠操作
        if folding_mode == FoldingMode.PRESERVE_ANCHORS:
            folded_scenes = self._fold_preserve_anchors(scenes, anchors, strategy)
        elif folding_mode == FoldingMode.CONDENSE_SIMILAR:
            folded_scenes = self._fold_condense_similar(scenes, anchors, strategy)
        elif folding_mode == FoldingMode.HIGHLIGHT_CONTRAST:
            folded_scenes = self._fold_highlight_contrast(scenes, anchors, strategy)
        elif folding_mode == FoldingMode.NARRATIVE_DRIVEN:
            folded_scenes = self._fold_narrative_driven(scenes, anchors, strategy, structure_name)
        else:
            logger.warning(f"未知的折叠模式: {folding_mode}，使用默认模式")
            folded_scenes = self._fold_preserve_anchors(scenes, anchors, strategy)
        
        # 添加折叠信息
        for scene in folded_scenes:
            scene["folded"] = True
            scene["folding_strategy"] = strategy.name
            scene["structure_name"] = structure_name
        
        logger.info(f"完成时间轴折叠: {len(scenes)}个场景 -> {len(folded_scenes)}个场景")
        return folded_scenes
    
    def _get_strategy_for_structure(self, 
                                   structure_name: str, 
                                   strategy_name: Optional[str] = None) -> TimeFoldingStrategy:
        """
        根据叙事结构获取最合适的折叠策略
        
        Args:
            structure_name: 叙事结构名称
            strategy_name: 指定的策略名称，可选
            
        Returns:
            折叠策略对象
        """
        # 如果指定了策略名称，直接使用
        if strategy_name and strategy_name in self.strategies:
            return self.strategies[strategy_name]
        
        # 否则，根据结构名称匹配适当的策略
        for strategy in self.strategies.values():
            if structure_name in strategy.structure_types:
                return strategy
        
        # 如果没有匹配的策略，使用默认策略
        default_strategy_name = self.config.get("default_strategy", "倒叙风暴")
        return self.strategies.get(default_strategy_name, next(iter(self.strategies.values())))
    
    def _fold_preserve_anchors(self, 
                              scenes: List[Dict[str, Any]], 
                              anchors: List[AnchorInfo],
                              strategy: TimeFoldingStrategy) -> List[Dict[str, Any]]:
        """
        保留关键锚点的折叠方法，压缩非关键场景
        
        Args:
            scenes: 场景列表
            anchors: 锚点列表
            strategy: 折叠策略
            
        Returns:
            折叠后的场景列表
        """
        if not scenes:
            return []
        
        # 创建场景副本
        scenes_copy = copy.deepcopy(scenes)
        
        # 计算每个场景的重要性分数
        scene_importance = self._calculate_scene_importance(scenes_copy, anchors, strategy)
        
        # 获取重要性阈值
        threshold = self.config.get("preserve_anchor_threshold", 0.7)
        
        # 将场景分为重要和不重要两组
        important_scenes = []
        less_important_scenes = []
        
        for idx, scene in enumerate(scenes_copy):
            # 首尾场景特殊处理
            if idx == 0 and strategy.preserve_start:
                important_scenes.append(scene)
            elif idx == len(scenes_copy) - 1 and strategy.preserve_end:
                important_scenes.append(scene)
            # 基于重要性分数决定保留或压缩
            elif scene_importance.get(scene.get("id", str(idx)), 0) >= threshold:
                important_scenes.append(scene)
            else:
                less_important_scenes.append(scene)
        
        # 对不重要的场景应用折叠率
        fold_ratio = strategy.fold_ratio
        num_to_keep = max(1, int(len(less_important_scenes) * (1 - fold_ratio)))
        
        # 如果不重要场景很少，保留全部
        if len(less_important_scenes) <= 3:
            selected_less_important = less_important_scenes
        else:
            # 选择保留的不重要场景
            indices = np.linspace(0, len(less_important_scenes) - 1, num_to_keep, dtype=int)
            selected_less_important = [less_important_scenes[i] for i in indices]
        
        # 合并重要场景和保留的不重要场景
        all_selected_scenes = important_scenes + selected_less_important
        
        # 按原始顺序排序
        all_selected_scenes.sort(key=lambda s: scenes_copy.index(s))
        
        return all_selected_scenes
    
    def _fold_condense_similar(self,
                              scenes: List[Dict[str, Any]],
                              anchors: List[AnchorInfo],
                              strategy: TimeFoldingStrategy) -> List[Dict[str, Any]]:
        """
        压缩相似场景的折叠方法
        
        Args:
            scenes: 场景列表
            anchors: 锚点列表
            strategy: 折叠策略
            
        Returns:
            折叠后的场景列表
        """
        if not scenes:
            return []
        
        # 创建场景副本
        scenes_copy = copy.deepcopy(scenes)
        
        # 相似度阈值
        similarity_threshold = self.config.get("scene_similarity_threshold", 0.8)
        
        # 结果场景列表
        folded_scenes = []
        skip_indices = set()
        
        for i in range(len(scenes_copy)):
            if i in skip_indices:
                continue
                
            current_scene = scenes_copy[i]
            folded_scenes.append(current_scene)
            
            # 查找与当前场景相似的后续场景
            for j in range(i + 1, len(scenes_copy)):
                if j in skip_indices:
                    continue
                    
                next_scene = scenes_copy[j]
                
                # 检查两个场景是否相似
                if self._calculate_scene_similarity(current_scene, next_scene) >= similarity_threshold:
                    # 合并场景信息
                    if "duration" in current_scene and "duration" in next_scene:
                        current_scene["duration"] = current_scene["duration"] + next_scene["duration"] * 0.3
                    
                    if "similar_to" not in current_scene:
                        current_scene["similar_to"] = []
                    current_scene["similar_to"].append(next_scene.get("id", str(j)))
                    
                    skip_indices.add(j)
                else:
                    # 如果不相似，停止查找
                    break
        
        return folded_scenes
    
    def _fold_highlight_contrast(self,
                                scenes: List[Dict[str, Any]],
                                anchors: List[AnchorInfo],
                                strategy: TimeFoldingStrategy) -> List[Dict[str, Any]]:
        """
        强调情感对比的折叠方法
        
        Args:
            scenes: 场景列表
            anchors: 锚点列表
            strategy: 折叠策略
            
        Returns:
            折叠后的场景列表
        """
        if not scenes:
            return []
            
        # 创建场景副本
        scenes_copy = copy.deepcopy(scenes)
        
        # 提取情感锚点
        emotion_anchors = [a for a in anchors if a.type == AnchorType.EMOTION]
        
        # 如果没有情感锚点，回退到保留锚点的方法
        if not emotion_anchors:
            return self._fold_preserve_anchors(scenes, anchors, strategy)
        
        # 对情感锚点按位置排序
        emotion_anchors.sort(key=lambda a: a.position)
        
        # 寻找情感对比点
        contrast_points = []
        for i in range(1, len(emotion_anchors)):
            prev = emotion_anchors[i-1]
            curr = emotion_anchors[i]
            
            # 检查前后情感是否存在对比
            if abs((prev.emotion_score or 0) - (curr.emotion_score or 0)) > 0.5:  # 情感值差异大于0.5认为是对比
                scene_index = int(curr.position * len(scenes))
                contrast_points.append(scene_index)
        
        # 预先保留的场景：开头、结尾、对比点
        preserved_indices = set(contrast_points)
        if strategy.preserve_start:
            preserved_indices.add(0)
        if strategy.preserve_end:
            preserved_indices.add(len(scenes) - 1)
        
        # 计算每个场景的重要性
        scene_importance = self._calculate_scene_importance(scenes_copy, anchors, strategy)
        
        # 按重要性排序场景
        scenes_with_importance = [(i, s, scene_importance.get(s.get("id", str(i)), 0)) 
                                  for i, s in enumerate(scenes_copy)]
        scenes_with_importance.sort(key=lambda x: x[2], reverse=True)
        
        # 确定要保留的场景数量
        keep_ratio = 1 - strategy.fold_ratio
        num_to_keep = max(len(preserved_indices), int(len(scenes) * keep_ratio))
        
        # 从重要性排序中选择场景，但确保关键对比点被保留
        selected_indices = set(preserved_indices)
        for idx, _, _ in scenes_with_importance:
            if idx not in selected_indices:
                selected_indices.add(idx)
                if len(selected_indices) >= num_to_keep:
                    break
        
        # 按原始顺序选择场景
        folded_scenes = [scenes_copy[i] for i in sorted(selected_indices)]
        
        return folded_scenes
    
    def _fold_narrative_driven(self,
                               scenes: List[Dict[str, Any]],
                               anchors: List[AnchorInfo],
                               strategy: TimeFoldingStrategy,
                               structure_name: str) -> List[Dict[str, Any]]:
        """
        叙事驱动折叠方法
        
        Args:
            scenes: 场景列表
            anchors: 锚点列表
            strategy: 折叠策略
            structure_name: 叙事结构名称
            
        Returns:
            折叠后的场景列表
        """
        if not scenes or not anchors:
            logger.warning("场景或锚点为空，无法进行叙事驱动折叠")
            return scenes
        
        # 创建场景副本
        scenes_copy = copy.deepcopy(scenes)
        folded_scenes = []
        
        # 根据不同的叙事结构执行不同的折叠策略
        if structure_name in ["倒叙风暴", "flashback_storm"]:
            # 倒叙风暴结构: 将高潮场景前置，然后通过闪回展现前因后果
            
            # 寻找情感/戏剧高潮场景
            climax_anchors = [a for a in anchors if a.type == AnchorType.CLIMAX]
            emotion_peak_anchors = [a for a in anchors if a.type == AnchorType.EMOTION and a.importance > 0.7]
            
            # 选择最重要的高潮
            peak_anchors = climax_anchors if climax_anchors else emotion_peak_anchors
            if not peak_anchors:
                # 如果没有显式的高潮锚点，尝试使用情感分数找出高潮
                emotion_scenes = [(i, s) for i, s in enumerate(scenes_copy) 
                                if "emotion_score" in s and isinstance(s["emotion_score"], (int, float))]
                
                if emotion_scenes:
                    # 找出情感绝对值最高的场景
                    peak_idx, _ = max(emotion_scenes, 
                                    key=lambda x: abs(x[1]["emotion_score"]) if isinstance(x[1]["emotion_score"], (int, float)) else 0)
                    peak_scene_idx = peak_idx
                else:
                    # 如果没有情感信息，使用靠后的场景作为高潮
                    peak_scene_idx = int(len(scenes_copy) * 0.7)
            else:
                # 使用最重要的高潮锚点
                peak_anchor = max(peak_anchors, key=lambda a: a.importance)
                peak_scene_idx = min(int(peak_anchor.position * len(scenes_copy)), len(scenes_copy) - 1)
            
            # 创建结果列表，首先添加高潮场景
            climax_scene = scenes_copy[peak_scene_idx]
            climax_scene["is_climax"] = True
            folded_scenes.append(climax_scene)
            
            # 添加回闪场景
            flashback_scenes = []
            for i, scene in enumerate(scenes_copy):
                if i != peak_scene_idx:
                    # 添加回闪标记
                    scene["is_flashback"] = True if i < peak_scene_idx else False
                    flashback_scenes.append(scene)
            
            # 对回闪场景排序：优先保留重要锚点场景，其他场景按重要性排序
            scene_importance = self._calculate_scene_importance(flashback_scenes, anchors, strategy)
            
            # 按重要性排序
            flashback_scenes.sort(key=lambda s: scene_importance.get(s.get("id", str(flashback_scenes.index(s))), 0), 
                                reverse=True)
            
            # 确定要保留的场景数量
            keep_ratio = 1 - strategy.fold_ratio
            num_to_keep = max(1, int(len(flashback_scenes) * keep_ratio))
            
            # 选择保留的场景
            selected_flashbacks = flashback_scenes[:num_to_keep]
            
            # 按原始时间顺序排序这些场景
            selected_flashbacks.sort(key=lambda s: scenes_copy.index(s))
            
            # 将回闪场景添加到结果中
            folded_scenes.extend(selected_flashbacks)
            
        elif structure_name in ["环形结构", "circular_narrative"]:
            # 环形结构: 首尾呼应，形成循环叙事结构
            
            # 保留首尾场景
            first_scene = scenes_copy[0]
            last_scene = scenes_copy[-1]
            
            # 添加标记
            first_scene["is_opening"] = True
            last_scene["is_closing"] = True
            
            # 计算场景重要性
            scene_importance = self._calculate_scene_importance(scenes_copy, anchors, strategy)
            
            # 选择中间的场景
            middle_scenes = scenes_copy[1:-1]
            
            # 按重要性排序
            middle_scenes.sort(key=lambda s: scene_importance.get(s.get("id", str(middle_scenes.index(s) + 1)), 0),
                              reverse=True)
            
            # 确定要保留的场景数量
            keep_ratio = 1 - strategy.fold_ratio
            num_to_keep = max(1, int(len(middle_scenes) * keep_ratio))
            
            # 选择保留的场景
            selected_middle = middle_scenes[:num_to_keep]
            
            # 按原始顺序排序
            selected_middle.sort(key=lambda s: scenes_copy.index(s))
            
            # 添加首场景
            folded_scenes.append(first_scene)
            
            # 添加中间场景
            folded_scenes.extend(selected_middle)
            
            # 添加尾场景
            folded_scenes.append(last_scene)
            
        elif structure_name in ["多线织网", "multi_thread"]:
            # 多线织网结构: 交织多条故事线，强调人物关系
            
            # 计算场景重要性
            scene_importance = self._calculate_scene_importance(scenes_copy, anchors, strategy)
            
            # 按角色分组场景
            character_scenes = {}
            for i, scene in enumerate(scenes_copy):
                chars = scene.get("characters", [])
                if not chars:
                    continue
                    
                for char in chars:
                    if char not in character_scenes:
                        character_scenes[char] = []
                    character_scenes[char].append((i, scene))
            
            # 找出主要角色
            main_characters = sorted(character_scenes.keys(), 
                                    key=lambda c: len(character_scenes[c]), 
                                    reverse=True)[:3]  # 最多3个主要角色
            
            # 为每个主要角色选择重要场景
            selected_indices = set()
            for char in main_characters:
                char_scenes = character_scenes.get(char, [])
                if not char_scenes:
                    continue
                
                # 按重要性排序
                char_scenes.sort(key=lambda x: scene_importance.get(x[1].get("id", str(x[0])), 0),
                                reverse=True)
                
                # 选择前几个重要场景
                num_to_keep = max(1, int(len(char_scenes) * (1 - strategy.fold_ratio)))
                for i in range(min(num_to_keep, len(char_scenes))):
                    selected_indices.add(char_scenes[i][0])
            
            # 确保首尾场景被保留
            if strategy.preserve_start:
                selected_indices.add(0)
            if strategy.preserve_end:
                selected_indices.add(len(scenes_copy) - 1)
            
            # 按原始顺序添加场景
            folded_scenes = [scenes_copy[i] for i in sorted(selected_indices)]
            
            # 添加角色标记
            for scene in folded_scenes:
                chars = scene.get("characters", [])
                for char in chars:
                    if char in main_characters:
                        if "main_characters" not in scene:
                            scene["main_characters"] = []
                        scene["main_characters"].append(char)
            
        elif structure_name in ["高潮迭起", "escalating_peaks"]:
            # 高潮迭起结构: 多个高潮点递进，不断提升紧张感
            
            # 寻找所有高潮点
            climax_anchors = [a for a in anchors if a.type == AnchorType.CLIMAX]
            emotion_peak_anchors = [a for a in anchors if a.type == AnchorType.EMOTION and a.importance > 0.6]
            
            # 合并所有高潮点
            peak_anchors = climax_anchors + emotion_peak_anchors
            
            # 如果没有足够的高潮点，回退到保留锚点方法
            if len(peak_anchors) < 2:
                return self._fold_preserve_anchors(scenes, anchors, strategy)
            
            # 按位置排序
            peak_anchors.sort(key=lambda a: a.position)
            
            # 找出高潮点对应的场景索引
            peak_indices = []
            for anchor in peak_anchors:
                idx = min(int(anchor.position * len(scenes_copy)), len(scenes_copy) - 1)
                peak_indices.append(idx)
            
            # 确保首尾场景被保留
            if strategy.preserve_start and 0 not in peak_indices:
                peak_indices.insert(0, 0)
            if strategy.preserve_end and (len(scenes_copy) - 1) not in peak_indices:
                peak_indices.append(len(scenes_copy) - 1)
            
            # 预先选择所有高潮场景
            selected_indices = set(peak_indices)
            
            # 为了保持叙事连贯性，在高潮点之间选择一些过渡场景
            for i in range(len(peak_indices) - 1):
                start_idx = peak_indices[i]
                end_idx = peak_indices[i + 1]
                
                # 如果高潮点相邻，不需要添加过渡场景
                if end_idx - start_idx <= 1:
                    continue
                
                # 在相邻高潮点之间均匀选择过渡场景
                num_transitions = max(1, int((end_idx - start_idx) * (1 - strategy.fold_ratio)))
                if num_transitions > 0:
                    # 均匀选择过渡场景
                    step = (end_idx - start_idx) / (num_transitions + 1)
                    for j in range(1, num_transitions + 1):
                        trans_idx = start_idx + int(j * step)
                        if start_idx < trans_idx < end_idx:
                            selected_indices.add(trans_idx)
            
            # 按原始顺序添加场景
            folded_scenes = [scenes_copy[i] for i in sorted(selected_indices)]
            
            # 标记高潮场景
            for i, scene in enumerate(folded_scenes):
                scene_idx = scenes_copy.index(scene)
                if scene_idx in peak_indices:
                    scene["is_peak"] = True
            
        elif structure_name in ["并行蒙太奇", "parallel_montage"]:
            # 并行蒙太奇结构: 两条故事线并行发展，通过交替场景展现
            
            # 计算场景重要性
            scene_importance = self._calculate_scene_importance(scenes_copy, anchors, strategy)
            
            # 寻找场景转换点
            transition_anchors = [a for a in anchors if a.type == AnchorType.TRANSITION]
            
            # 如果没有转换锚点，回退到保留锚点方法
            if not transition_anchors:
                return self._fold_preserve_anchors(scenes, anchors, strategy)
            
            # 按位置排序
            transition_anchors.sort(key=lambda a: a.position)
            
            # 找出转换点对应的场景索引
            transition_indices = []
            for anchor in transition_anchors:
                idx = min(int(anchor.position * len(scenes_copy)), len(scenes_copy) - 1)
                transition_indices.append(idx)
            
            # 确保首尾场景被保留
            selected_indices = set(transition_indices)
            if strategy.preserve_start:
                selected_indices.add(0)
            if strategy.preserve_end:
                selected_indices.add(len(scenes_copy) - 1)
            
            # 分割场景为两条线
            line_indices = {
                "line_a": transition_indices[::2],  # 奇数索引
                "line_b": transition_indices[1::2]  # 偶数索引
            }
            
            # 按重要性为每条线选择一些额外场景
            for line_name, line_idx in line_indices.items():
                # 为每条线找出所有可能的场景
                line_candidate_scenes = []
                for i in range(len(line_idx) - 1):
                    start_idx = line_idx[i]
                    end_idx = line_idx[i + 1]
                    # 选择这两个转换点之间的所有场景
                    for j in range(start_idx + 1, end_idx):
                        if j not in selected_indices:
                            line_candidate_scenes.append((j, scenes_copy[j]))
                
                # 按重要性排序
                line_candidate_scenes.sort(
                    key=lambda x: scene_importance.get(x[1].get("id", str(x[0])), 0),
                    reverse=True
                )
                
                # 选择前几个重要场景
                num_to_keep = max(1, int(len(line_candidate_scenes) * (1 - strategy.fold_ratio)))
                for i in range(min(num_to_keep, len(line_candidate_scenes))):
                    selected_indices.add(line_candidate_scenes[i][0])
            
            # 按原始顺序添加场景
            folded_scenes = [scenes_copy[i] for i in sorted(selected_indices)]
            
            # 标记场景所属的线
            for scene in folded_scenes:
                scene_idx = scenes_copy.index(scene)
                for line_name, line_idx in line_indices.items():
                    if scene_idx in line_idx:
                        scene["story_line"] = line_name
                        break
        
        else:
            # 未知结构，使用默认保留锚点方法
            logger.warning(f"未知的叙事结构: {structure_name}，使用默认折叠方法")
            return self._fold_preserve_anchors(scenes, anchors, strategy)
        
        return folded_scenes
    
    def _calculate_scene_importance(self,
                                   scenes: List[Dict[str, Any]], 
                                   anchors: List[AnchorInfo],
                                   strategy: TimeFoldingStrategy) -> Dict[str, float]:
        """
        计算每个场景的重要性分数
        
        Args:
            scenes: 场景列表
            anchors: 锚点列表
            strategy: 折叠策略
            
        Returns:
            场景ID到重要性分数的映射
        """
        importance_scores = {}
        
        # 无效输入检查
        if not scenes or not anchors:
            return importance_scores
        
        # 初始化每个场景的基础重要性
        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", str(i))
            importance_scores[scene_id] = 0.3  # 基础重要性
        
        # 根据锚点分配重要性
        for anchor in anchors:
            # 获取锚点在场景列表中的索引
            anchor_pos = anchor.position  # 0.0 到 1.0 之间的相对位置
            scene_idx = min(int(anchor_pos * len(scenes)), len(scenes) - 1)
            scene_id = scenes[scene_idx].get("id", str(scene_idx))
            
            # 获取锚点类型权重
            anchor_weight = strategy.anchor_weights.get(anchor.type, 1.0)
            
            # 计算重要性增量
            importance_increment = anchor.importance * anchor_weight
            
            # 应用到场景
            importance_scores[scene_id] = max(importance_scores[scene_id], importance_increment)
            
            # 对相邻场景也施加影响，但强度降低
            if scene_idx > 0:
                prev_id = scenes[scene_idx - 1].get("id", str(scene_idx - 1))
                importance_scores[prev_id] = max(importance_scores[prev_id], 
                                                importance_increment * 0.7)
            
            if scene_idx < len(scenes) - 1:
                next_id = scenes[scene_idx + 1].get("id", str(scene_idx + 1))
                importance_scores[next_id] = max(importance_scores[next_id], 
                                               importance_increment * 0.7)
        
        return importance_scores
    
    def _calculate_scene_similarity(self, 
                                   scene1: Dict[str, Any], 
                                   scene2: Dict[str, Any]) -> float:
        """
        计算两个场景之间的相似度
        
        Args:
            scene1: 第一个场景
            scene2: 第二个场景
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        # 简单相似度计算，可以根据需要扩展为更复杂的算法
        similarity = 0.0
        
        # 检查场景文本相似度
        if "text" in scene1 and "text" in scene2:
            # 这里应该使用实际的相似度计算
            # 例如：TF-IDF，词向量，或其他文本相似度算法
            # 但作为简单实现，我们使用长度比较
            text1 = scene1["text"]
            text2 = scene2["text"]
            
            # 文本长度相近的场景可能内容相似
            if text1 and text2:
                length_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))
                similarity += length_ratio * 0.3
        
        # 检查情感分数相似度
        if "emotion_score" in scene1 and "emotion_score" in scene2:
            emotion1 = scene1["emotion_score"]
            emotion2 = scene2["emotion_score"]
            
            if isinstance(emotion1, (int, float)) and isinstance(emotion2, (int, float)):
                emotion_diff = abs(emotion1 - emotion2)
                if emotion_diff < 0.2:
                    similarity += 0.4
                elif emotion_diff < 0.4:
                    similarity += 0.2
        
        # 检查角色相似度
        if "characters" in scene1 and "characters" in scene2:
            chars1 = set(scene1["characters"])
            chars2 = set(scene2["characters"])
            
            if chars1 and chars2:
                # 计算Jaccard相似度
                intersection = len(chars1.intersection(chars2))
                union = len(chars1.union(chars2))
                
                if union > 0:
                    char_similarity = intersection / union
                    similarity += char_similarity * 0.3
        
        return min(1.0, similarity)
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """
        获取所有可用的折叠策略
        
        Returns:
            策略信息列表
        """
        return [
            {
                "name": strategy.name,
                "description": strategy.description,
                "structure_types": strategy.structure_types,
                "fold_ratio": strategy.fold_ratio
            }
            for strategy in self.strategies.values()
        ]


# 便捷函数

def fold_timeline(scenes: List[Dict[str, Any]], 
                 anchors: List[AnchorInfo],
                 structure_name: Optional[str] = None,
                 strategy_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    折叠时间轴（便捷函数）
    
    Args:
        scenes: 场景列表
        anchors: 锚点列表
        structure_name: 叙事结构名称，可选
        strategy_name: 折叠策略名称，可选
        
    Returns:
        折叠后的场景列表
    """
    folder = TimeFolder()
    return folder.fold_timeline(scenes, anchors, structure_name, strategy_name)

def get_folding_strategy(strategy_name: str) -> Optional[Dict[str, Any]]:
    """
    获取指定名称的折叠策略信息（便捷函数）
    
    Args:
        strategy_name: 策略名称
        
    Returns:
        策略信息字典，如果不存在则返回None
    """
    folder = TimeFolder()
    for strategy in folder.get_available_strategies():
        if strategy["name"] == strategy_name:
            return strategy
    return None

def list_folding_strategies() -> List[str]:
    """
    列出所有可用的折叠策略名称（便捷函数）
    
    Returns:
        策略名称列表
    """
    folder = TimeFolder()
    return [strategy["name"] for strategy in folder.get_available_strategies()] 