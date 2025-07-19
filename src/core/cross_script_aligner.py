"""
跨剧本模式对齐模块

该模块负责分析原片剧本模式与爆款剧本模式之间的关系，执行以下功能:
1. 识别添加的模式：在爆款中新增但原片中不存在的元素
2. 识别移除的模式：在原片中存在但爆款中被移除的元素
3. 发现强化模式：在原片和爆款中都存在，但在爆款中被强化的模式
"""

import os
import re
import json
import yaml
from typing import Dict, List, Any, Tuple, Set, Optional
import numpy as np
from loguru import logger

from src.utils.memory_guard import track_memory
from src.knowledge.pattern_analyzer import PatternAnalyzer


class CrossScriptAligner:
    """跨剧本模式对齐器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化跨剧本模式对齐器
        
        Args:
            config_path: 配置文件路径，为None时使用默认配置
        """
        self.config = self._load_config(config_path)
        self.pattern_analyzer = PatternAnalyzer()
        logger.info("跨剧本模式对齐器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "alignment": {
                "similarity_threshold": 0.3,  # 模式相似度阈值
                "intensification_factor": 1.5,  # 强化因子阈值
                "max_patterns": 50,  # 最大返回模式数
                "min_impact_score": 0.4  # 最小影响力分数
            },
            "intensification_types": {
                "duration_extension": 1.35,  # 时长延长因子
                "emotion_amplification": 1.5,  # 情感放大因子
                "conflict_escalation": 2.0,  # 冲突升级因子
                "surprise_enhancement": 1.8,  # 惊喜增强因子
                "suspense_building": 1.7  # 悬念构建因子
            }
        }
        
        # 如果提供了配置路径，尝试加载自定义配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = yaml.safe_load(f)
                
                # 递归合并配置
                for key, value in custom_config.items():
                    if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    @track_memory("cross_script_alignment")
    def align_patterns(self, origin_patterns: List[Dict], hit_patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """
        对齐原片模式和爆款模式
        
        Args:
            origin_patterns: 原片模式列表
            hit_patterns: 爆款模式列表
            
        Returns:
            对齐结果，包含添加、移除和强化三类模式
        """
        logger.info(f"开始对齐模式: 原片 {len(origin_patterns)} 个, 爆款 {len(hit_patterns)} 个")
        
        # 结果容器
        alignment = {
            'added': [],      # 添加的模式
            'removed': [],    # 移除的模式
            'enhanced': []    # 强化的模式
        }
        
        # 1. 查找添加的模式 (在爆款中但不在原片中)
        alignment['added'] = self._find_added_patterns(origin_patterns, hit_patterns)
        logger.debug(f"找到 {len(alignment['added'])} 个添加的模式")
        
        # 2. 查找移除的模式 (在原片中但不在爆款中)
        alignment['removed'] = self._find_removed_patterns(origin_patterns, hit_patterns)
        logger.debug(f"找到 {len(alignment['removed'])} 个移除的模式")
        
        # 3. 查找强化的模式 (在两者中都有，但在爆款中被强化)
        alignment['enhanced'] = self._find_intensified_patterns(origin_patterns, hit_patterns)
        logger.debug(f"找到 {len(alignment['enhanced'])} 个强化的模式")
        
        # 对每类模式按影响力排序
        for key in alignment:
            alignment[key] = sorted(
                alignment[key], 
                key=lambda x: x.get('impact_score', 0), 
                reverse=True
            )
            
            # 限制返回数量
            max_patterns = self.config.get('alignment', {}).get('max_patterns', 50)
            alignment[key] = alignment[key][:max_patterns]
        
        logger.info("模式对齐完成")
        return alignment
    
    def _find_added_patterns(self, origin_patterns: List[Dict], hit_patterns: List[Dict]) -> List[Dict]:
        """
        查找添加的模式
        
        Args:
            origin_patterns: 原片模式列表
            hit_patterns: 爆款模式列表
            
        Returns:
            添加的模式列表
        """
        # 将原片模式转为可比较格式
        origin_set = self._patterns_to_comparable_set(origin_patterns)
        
        # 查找爆款中特有的模式
        added_patterns = []
        for hit_pattern in hit_patterns:
            # 提取模式核心特征
            pattern_key = self._get_pattern_key(hit_pattern)
            
            # 检查是否在原片模式中
            if pattern_key not in origin_set:
                # 添加影响力分数
                hit_pattern['impact_score'] = hit_pattern.get('support', 0.5) * hit_pattern.get('confidence', 1.0)
                added_patterns.append(hit_pattern)
        
        return added_patterns
    
    def _find_removed_patterns(self, origin_patterns: List[Dict], hit_patterns: List[Dict]) -> List[Dict]:
        """
        查找移除的模式
        
        Args:
            origin_patterns: 原片模式列表
            hit_patterns: 爆款模式列表
            
        Returns:
            移除的模式列表
        """
        # 将爆款模式转为可比较格式
        hit_set = self._patterns_to_comparable_set(hit_patterns)
        
        # 查找原片中特有的模式
        removed_patterns = []
        for origin_pattern in origin_patterns:
            # 提取模式核心特征
            pattern_key = self._get_pattern_key(origin_pattern)
            
            # 检查是否在爆款模式中
            if pattern_key not in hit_set:
                # 添加影响力分数
                origin_pattern['impact_score'] = origin_pattern.get('support', 0.5) * origin_pattern.get('confidence', 1.0)
                removed_patterns.append(origin_pattern)
        
        return removed_patterns
    
    def _find_intensified_patterns(self, origin_patterns: List[Dict], hit_patterns: List[Dict]) -> List[Dict]:
        """
        查找强化的模式
        
        Args:
            origin_patterns: 原片模式列表
            hit_patterns: 爆款模式列表
            
        Returns:
            强化的模式列表
        """
        # 将模式转换为字典，便于快速查找
        origin_dict = {self._get_pattern_key(p): p for p in origin_patterns}
        hit_dict = {self._get_pattern_key(p): p for p in hit_patterns}
        
        # 查找两者共有并且在爆款中被强化的模式
        enhanced_patterns = []
        
        # 获取强化类型配置
        intensification_types = self.config.get('intensification_types', {})
        intensification_factor = self.config.get('alignment', {}).get('intensification_factor', 1.5)
        
        # 遍历爆款模式查找强化
        for pattern_key, hit_pattern in hit_dict.items():
            if pattern_key in origin_dict:
                origin_pattern = origin_dict[pattern_key]
                
                # 检查是否存在强化
                enhancements = self._detect_enhancements(origin_pattern, hit_pattern, intensification_types)
                
                if enhancements:
                    # 存在强化，构建强化模式对象
                    enhanced_pattern = hit_pattern.copy()
                    enhanced_pattern['origin_pattern'] = origin_pattern
                    enhanced_pattern['enhancements'] = enhancements
                    
                    # 计算影响力分数
                    support_ratio = hit_pattern.get('support', 0.5) / max(origin_pattern.get('support', 0.5), 0.001)
                    enhancement_factor = max([e['factor'] for e in enhancements])
                    enhanced_pattern['impact_score'] = support_ratio * enhancement_factor
                    
                    enhanced_patterns.append(enhanced_pattern)
        
        return enhanced_patterns
    
    def _patterns_to_comparable_set(self, patterns: List[Dict]) -> Set[str]:
        """
        将模式列表转换为可比较的集合
        
        Args:
            patterns: 模式列表
            
        Returns:
            模式键集合
        """
        return {self._get_pattern_key(pattern) for pattern in patterns}
    
    def _get_pattern_key(self, pattern: Dict) -> str:
        """
        获取模式的唯一键表示
        
        Args:
            pattern: 模式对象
            
        Returns:
            模式键字符串
        """
        # 根据模式类型选择不同的键生成策略
        if 'pattern' in pattern and isinstance(pattern['pattern'], (list, tuple)):
            # 序列模式
            return "|".join(sorted(str(item) for item in pattern['pattern']))
        elif 'pattern_type' in pattern and 'sequence' in pattern:
            # 叙事模式
            return f"{pattern['pattern_type']}:{','.join(pattern['sequence'])}"
        else:
            # 其他模式，尝试将关键字段序列化为字符串
            key_fields = ['type', 'category', 'elements', 'sequence']
            components = []
            for field in key_fields:
                if field in pattern:
                    value = pattern[field]
                    if isinstance(value, (list, tuple)):
                        components.append(f"{field}:[{','.join(sorted(str(v) for v in value))}]")
                    else:
                        components.append(f"{field}:{value}")
            
            return "||".join(components) if components else str(hash(str(pattern)))
    
    def _detect_enhancements(self, origin_pattern: Dict, hit_pattern: Dict, 
                            intensification_types: Dict[str, float]) -> List[Dict]:
        """
        检测模式强化类型
        
        Args:
            origin_pattern: 原片模式
            hit_pattern: 爆款模式
            intensification_types: 强化类型配置
            
        Returns:
            强化描述列表
        """
        enhancements = []
        
        # 情感强度检查
        if 'emotion_intensity' in hit_pattern and 'emotion_intensity' in origin_pattern:
            hit_intensity = hit_pattern['emotion_intensity']
            origin_intensity = origin_pattern['emotion_intensity']
            emotion_factor = intensification_types.get('emotion_amplification', 1.5)
            
            if hit_intensity > origin_intensity * emotion_factor:
                enhancements.append({
                    'type': 'emotion_amplification',
                    'description': f"情感强度增强了{hit_intensity/origin_intensity:.1f}倍",
                    'factor': hit_intensity/origin_intensity
                })
        
        # 时长检查
        if 'duration' in hit_pattern and 'duration' in origin_pattern:
            hit_duration = hit_pattern['duration']
            origin_duration = origin_pattern['duration']
            duration_factor = intensification_types.get('duration_extension', 1.35)
            
            if hit_duration > origin_duration * duration_factor:
                enhancements.append({
                    'type': 'duration_extension',
                    'description': f"时长延长了{hit_duration/origin_duration:.1f}倍",
                    'factor': hit_duration/origin_duration
                })
        
        # 冲突强度检查
        if 'conflict_level' in hit_pattern and 'conflict_level' in origin_pattern:
            hit_conflict = hit_pattern['conflict_level']
            origin_conflict = origin_pattern['conflict_level']
            conflict_factor = intensification_types.get('conflict_escalation', 2.0)
            
            if hit_conflict > origin_conflict * conflict_factor:
                enhancements.append({
                    'type': 'conflict_escalation',
                    'description': f"冲突强度提升了{hit_conflict/origin_conflict:.1f}倍",
                    'factor': hit_conflict/origin_conflict
                })
        
        # 如果是序列模式，检查重复频率
        if 'frequency' in hit_pattern and 'frequency' in origin_pattern:
            hit_freq = hit_pattern['frequency']
            origin_freq = origin_pattern['frequency']
            
            if hit_freq > origin_freq * 1.5:
                enhancements.append({
                    'type': 'frequency_increase',
                    'description': f"出现频率增加了{hit_freq/origin_freq:.1f}倍",
                    'factor': hit_freq/origin_freq
                })
        
        # 检查支持度变化
        if 'support' in hit_pattern and 'support' in origin_pattern:
            hit_support = hit_pattern['support']
            origin_support = origin_pattern['support']
            
            if hit_support > origin_support * 1.8:
                enhancements.append({
                    'type': 'prevalence_increase',
                    'description': f"普遍性提升了{hit_support/origin_support:.1f}倍",
                    'factor': hit_support/origin_support
                })
        
        return enhancements


# 全局函数接口
def align_patterns(origin_patterns: List[Dict], hit_patterns: List[Dict]) -> Dict[str, List[Dict]]:
    """
    对齐原片模式和爆款模式
    
    Args:
        origin_patterns: 原片模式列表
        hit_patterns: 爆款模式列表
        
    Returns:
        对齐结果，包含添加、移除和强化三类模式
    """
    aligner = CrossScriptAligner()
    return aligner.align_patterns(origin_patterns, hit_patterns) 