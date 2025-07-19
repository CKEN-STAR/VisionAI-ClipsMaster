#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时空连续性检验模块 - 检查混剪片段之间的时空连贯性
确保剧情逻辑合理，提高观感质量
"""

import os
import logging
import yaml
import json
from typing import Dict, List, Any, Tuple, Set, Optional
import numpy as np
from datetime import timedelta

# 导入日志模块
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("spatial_temporal_checker")

# 配置目录路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs")


class SceneConsistencyValidator:
    """场景连续性验证器，检查场景切换的合理性"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化场景连续性验证器
        
        参数:
            config_path: 配置文件路径，若为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 加载时空约束规则
        self.time_constraints = self.config.get('time_constraints', {
            'max_time_jump': 30 * 60,  # 默认允许最大时间跳跃30分钟
            'min_transition_time': 0.5, # 最小过渡时间0.5秒
            'location_change_time': 30  # 地点变化至少需要30秒
        })
        
        # 场景连续性规则
        self.continuity_rules = self.config.get('continuity_rules', {
            'location_tracking': True,   # 追踪场景地点变化
            'character_tracking': True,  # 追踪角色进出场
            'object_tracking': True,     # 追踪关键道具
            'time_of_day_tracking': True # 追踪时间段变化(白天/夜晚)
        })
        
        # 关键道具连续性清单(例如手机、眼镜、武器等容易出现连续性错误的物品)
        self.key_props = self.config.get('key_props', [
            '手机', '眼镜', '钱包', '包', '车钥匙', '文件',
            'phone', 'glasses', 'wallet', 'bag', 'car key', 'document'
        ])
        
        # 预定义的场景位置类型
        self.location_types = self.config.get('location_types', [
            '室内', '室外', '家', '办公室', '学校', '商店', '餐厅', '车内',
            'indoor', 'outdoor', 'home', 'office', 'school', 'store', 'restaurant', 'car'
        ])
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        参数:
            config_path: 配置文件路径
            
        返回:
            配置字典
        """
        try:
            # 如果提供了配置路径且文件存在
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        return yaml.safe_load(f)
                    elif config_path.endswith('.json'):
                        return json.load(f)
            
            # 尝试加载默认配置文件
            default_config_path = os.path.join(CONFIG_DIR, "continuity_rules.yaml")
            if os.path.exists(default_config_path):
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            
            # 如果没有配置文件，使用默认值
            logger.warning("未找到时空连续性配置文件，使用默认配置")
            return {
                'time_constraints': {
                    'max_time_jump': 30 * 60,  # 最大时间跳跃(秒)
                    'min_transition_time': 0.5, # 最小过渡时间(秒)
                    'location_change_time': 30  # 地点变化最小时间(秒)
                },
                'continuity_rules': {
                    'location_tracking': True,
                    'character_tracking': True,
                    'object_tracking': True,
                    'time_of_day_tracking': True
                },
                'key_props': [
                    '手机', '眼镜', '钱包', '包', '车钥匙', '文件',
                    'phone', 'glasses', 'wallet', 'bag', 'car key', 'document'
                ],
                'location_types': [
                    '室内', '室外', '家', '办公室', '学校', '商店', '餐厅', '车内',
                    'indoor', 'outdoor', 'home', 'office', 'school', 'store', 'restaurant', 'car'
                ]
            }
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {
                'time_constraints': {},
                'continuity_rules': {},
                'key_props': [],
                'location_types': []
            }
    
    def validate(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """
        检验两个场景之间的时空连续性
        
        参数:
            prev_scene: 前一个场景信息
            curr_scene: 当前场景信息
            
        返回:
            连续性问题列表，空列表表示没有问题
        """
        # 结果列表
        errors = []
        
        # 检查时间连续性
        time_errors = self._check_time_consistency(prev_scene, curr_scene)
        errors.extend(time_errors)
        
        # 检查地点连续性
        if self.continuity_rules.get('location_tracking', True):
            location_errors = self._check_location_consistency(prev_scene, curr_scene)
            errors.extend(location_errors)
        
        # 检查角色连续性
        if self.continuity_rules.get('character_tracking', True):
            character_errors = self._check_character_consistency(prev_scene, curr_scene)
            errors.extend(character_errors)
        
        # 检查道具连续性
        if self.continuity_rules.get('object_tracking', True):
            prop_errors = self._check_prop_consistency(prev_scene, curr_scene)
            errors.extend(prop_errors)
        
        # 检查日夜连续性
        if self.continuity_rules.get('time_of_day_tracking', True):
            tod_errors = self._check_time_of_day_consistency(prev_scene, curr_scene)
            errors.extend(tod_errors)
        
        return errors
    
    def _check_time_consistency(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """检查时间连续性"""
        errors = []
        
        # 检查场景是否包含时间信息
        if 'time' not in prev_scene or 'time' not in curr_scene:
            return []
        
        # 获取时间信息
        prev_end = prev_scene['time'].get('end', 0)
        curr_start = curr_scene['time'].get('start', 0)
        
        # 检查时间是否倒退
        if curr_start < prev_end:
            errors.append(f"时间倒退: {prev_end} -> {curr_start}")
        
        # 检查时间跳跃是否过大
        max_jump = self.time_constraints.get('max_time_jump', 30 * 60)  # 默认30分钟
        if 'original_time' in curr_scene and 'original_time' in prev_scene:
            # 使用原始时间计算跳跃
            original_time_gap = curr_scene['original_time'].get('start', 0) - prev_scene['original_time'].get('end', 0)
            if original_time_gap > max_jump:
                # 格式化显示
                time_str = str(timedelta(seconds=int(original_time_gap)))
                errors.append(f"时间跳跃过大: {time_str}")
        
        return errors
    
    def _check_location_consistency(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """检查地点连续性"""
        errors = []
        
        # 如果场景没有位置信息，则跳过
        if 'location' not in prev_scene or 'location' not in curr_scene:
            return []
        
        # 获取位置信息
        prev_loc = prev_scene['location']
        curr_loc = curr_scene['location']
        
        # 检查位置变化
        if prev_loc != curr_loc:
            # 获取场景时间信息
            if 'time' in prev_scene and 'time' in curr_scene:
                prev_end = prev_scene['time'].get('end', 0)
                curr_start = curr_scene['time'].get('start', 0)
                
                # 计算场景间隔时间
                time_gap = curr_start - prev_end
                min_location_change_time = self.time_constraints.get('location_change_time', 30)
                
                # 如果地点变化但时间间隔太短，可能是连续性问题
                if time_gap < min_location_change_time:
                    errors.append(f"地点变化但时间间隔过短: {prev_loc}->{curr_loc}, 间隔: {time_gap:.1f}秒")
            
            # 如果有交通工具属性，则检查是否合理
            if 'props' in prev_scene and 'props' in curr_scene:
                # 检查是否有交通工具可以解释位置变化
                transportation_props = ['车', '自行车', '公交', '地铁', '飞机', '火车', 'car', 'bike', 'bus', 'subway', 'plane', 'train']
                has_transportation = any(prop in prev_scene.get('props', []) for prop in transportation_props)
                
                if not has_transportation:
                    # 检查距离是否需要交通工具
                    if 'location_distance' in self.config:
                        # 未来可添加地点距离计算
                        pass
        
        return errors
    
    def _check_character_consistency(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """检查角色连续性"""
        errors = []
        
        # 如果场景没有角色信息，则跳过
        if 'characters' not in prev_scene or 'characters' not in curr_scene:
            return []
        
        # 获取角色信息
        prev_chars = set(prev_scene['characters'])
        curr_chars = set(curr_scene['characters'])
        
        # 检查角色是否突然消失或出现
        disappeared = prev_chars - curr_chars
        appeared = curr_chars - prev_chars
        
        # 地点变化可以解释角色变化
        location_changed = prev_scene.get('location', '') != curr_scene.get('location', '')
        
        # 如果地点没变但角色变化了，可能是连续性问题
        if not location_changed:
            if disappeared:
                for char in disappeared:
                    # 检查是否有离开的描述
                    has_exit_desc = False
                    if 'text' in prev_scene:
                        exit_terms = ['离开', '走了', '出去', '再见', 'left', 'gone', 'exit', 'goodbye']
                        has_exit_desc = any(term in prev_scene['text'] for term in exit_terms)
                    
                    if not has_exit_desc:
                        errors.append(f"角色连续性: {char} 在场景切换时突然消失")
            
            if appeared:
                for char in appeared:
                    # 检查是否有进入的描述
                    has_entrance_desc = False
                    if 'text' in curr_scene:
                        entrance_terms = ['进来', '回来', '出现', '来了', 'entered', 'came in', 'appeared', 'arrived']
                        has_entrance_desc = any(term in curr_scene['text'] for term in entrance_terms)
                    
                    if not has_entrance_desc:
                        errors.append(f"角色连续性: {char} 在场景切换时突然出现")
        
        return errors
    
    def _check_prop_consistency(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """检查道具连续性"""
        errors = []
        
        # 如果场景没有道具信息，则跳过
        if 'props' not in prev_scene or 'props' not in curr_scene:
            return []
        
        # 获取道具信息
        prev_props = set(prev_scene['props'])
        curr_props = set(curr_scene['props'])
        
        # 重点关注关键道具的连续性
        key_props_changed = []
        for prop in self.key_props:
            if prop in prev_props and prop not in curr_props:
                key_props_changed.append(f"{prop}消失")
            elif prop not in prev_props and prop in curr_props:
                key_props_changed.append(f"{prop}出现")
        
        # 如果关键道具变化，检查是否合理
        if key_props_changed:
            # 检查是否有道具交接的描述
            has_prop_exchange = False
            if 'text' in prev_scene or 'text' in curr_scene:
                exchange_terms = ['拿', '给', '放', '收', '带', 'take', 'give', 'put', 'store', 'bring']
                prev_text = prev_scene.get('text', '')
                curr_text = curr_scene.get('text', '')
                has_prop_exchange = any(term in prev_text or term in curr_text for term in exchange_terms)
            
            if not has_prop_exchange:
                props_str = ", ".join(key_props_changed)
                errors.append(f"道具连续性: 关键道具变化 ({props_str}) 但无交接描述")
        
        return errors
    
    def _check_time_of_day_consistency(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """检查日夜连续性"""
        errors = []
        
        # 如果场景没有时间段信息，则跳过
        if 'time_of_day' not in prev_scene or 'time_of_day' not in curr_scene:
            return []
        
        # 获取时间段信息
        prev_tod = prev_scene['time_of_day']
        curr_tod = curr_scene['time_of_day']
        
        # 检查时间段是否合理变化
        time_of_day_order = ['早晨', '上午', '中午', '下午', '傍晚', '晚上', '深夜', 
                           'morning', 'forenoon', 'noon', 'afternoon', 'evening', 'night', 'midnight']
        
        # 如果能找到两个时间段在列表中的位置
        if prev_tod in time_of_day_order and curr_tod in time_of_day_order:
            prev_idx = time_of_day_order.index(prev_tod)
            curr_idx = time_of_day_order.index(curr_tod)
            
            # 检查时间是否倒退或跳跃过大
            if prev_idx > curr_idx:
                # 检查是否有日期变化的描述
                has_date_change = False
                if 'text' in prev_scene or 'text' in curr_scene:
                    date_terms = ['第二天', '明天', '下一天', '后一天', 'next day', 'tomorrow']
                    prev_text = prev_scene.get('text', '')
                    curr_text = curr_scene.get('text', '')
                    has_date_change = any(term in prev_text or term in curr_text for term in date_terms)
                
                if not has_date_change:
                    errors.append(f"时间段连续性: 从 {prev_tod} 到 {curr_tod} 时间倒退")
            elif curr_idx - prev_idx > 2:
                # 时间段跳跃超过2个单位，可能需要过渡说明
                has_time_skip = False
                if 'text' in prev_scene or 'text' in curr_scene:
                    skip_terms = ['过了', 'later', '之后', '随后', '后来', 'after', 'later', 'subsequently']
                    prev_text = prev_scene.get('text', '')
                    curr_text = curr_scene.get('text', '')
                    has_time_skip = any(term in prev_text or term in curr_text for term in skip_terms)
                
                if not has_time_skip:
                    errors.append(f"时间段连续性: 从 {prev_tod} 到 {curr_tod} 跳跃过大，缺少过渡")
        
        return errors
    
    def validate_sequence(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证整个场景序列的时空连续性
        
        参数:
            scenes: 场景列表
            
        返回:
            包含所有连续性问题和统计信息的字典
        """
        results = {
            'total_scenes': len(scenes),
            'total_errors': 0,
            'error_details': [],
            'error_counts': {
                'time': 0,
                'location': 0,
                'character': 0,
                'prop': 0,
                'time_of_day': 0
            }
        }
        
        if len(scenes) < 2:
            return results
        
        # 逐对检查场景
        for i in range(1, len(scenes)):
            prev_scene = scenes[i-1]
            curr_scene = scenes[i]
            
            # 检查连续性
            errors = self.validate(prev_scene, curr_scene)
            
            # 记录错误
            if errors:
                error_info = {
                    'scene_pair': (i-1, i),
                    'prev_scene_text': prev_scene.get('text', ''),
                    'curr_scene_text': curr_scene.get('text', ''),
                    'errors': errors
                }
                results['error_details'].append(error_info)
                results['total_errors'] += len(errors)
                
                # 统计各类错误
                for error in errors:
                    if '时间' in error:
                        results['error_counts']['time'] += 1
                    elif '地点' in error:
                        results['error_counts']['location'] += 1
                    elif '角色' in error:
                        results['error_counts']['character'] += 1
                    elif '道具' in error:
                        results['error_counts']['prop'] += 1
                    elif '时间段' in error:
                        results['error_counts']['time_of_day'] += 1
        
        return results
    
    def enhance_scene_metadata(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强场景元数据，提取或推断缺失的时空信息
        
        参数:
            scene: 场景信息
            
        返回:
            增强后的场景信息
        """
        enhanced_scene = scene.copy()
        
        # 尝试从文本中提取地点信息
        if 'location' not in enhanced_scene and 'text' in enhanced_scene:
            text = enhanced_scene['text']
            enhanced_scene['location'] = self._extract_location_from_text(text)
        
        # 尝试从文本中提取时间段信息
        if 'time_of_day' not in enhanced_scene and 'text' in enhanced_scene:
            text = enhanced_scene['text']
            enhanced_scene['time_of_day'] = self._extract_time_of_day_from_text(text)
        
        # 尝试从文本中提取角色信息
        if 'characters' not in enhanced_scene and 'text' in enhanced_scene:
            text = enhanced_scene['text']
            enhanced_scene['characters'] = self._extract_characters_from_text(text)
        
        # 尝试从文本中提取道具信息
        if 'props' not in enhanced_scene and 'text' in enhanced_scene:
            text = enhanced_scene['text']
            enhanced_scene['props'] = self._extract_props_from_text(text)
        
        return enhanced_scene
    
    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """从文本中提取地点信息"""
        # 常见地点关键词
        location_keywords = [
            '在', '到', '去', '位于', '回到', 
            'at', 'in', 'to', 'located', 'back to'
        ]
        
        # 地点类型
        for loc_type in self.location_types:
            if loc_type in text:
                for keyword in location_keywords:
                    # 查找 "在XX" 或 "去XX" 这样的模式
                    idx = text.find(f"{keyword}{loc_type}")
                    if idx >= 0:
                        # 尝试提取完整地点名称
                        end_idx = idx + len(keyword) + len(loc_type)
                        # 提取后续可能的地点修饰词
                        while end_idx < len(text) and (text[end_idx].isalnum() or text[end_idx] in ['的', '里', '中']):
                            end_idx += 1
                        return text[idx+len(keyword):end_idx]
                
                # 如果没有找到更具体的地点，返回地点类型
                return loc_type
        
        return None
    
    def _extract_time_of_day_from_text(self, text: str) -> Optional[str]:
        """从文本中提取时间段信息"""
        time_of_day_terms = {
            '早晨': '早晨', '早上': '早晨', '一大早': '早晨',
            '上午': '上午', 
            '中午': '中午', '午时': '中午',
            '下午': '下午', 
            '傍晚': '傍晚', '黄昏': '傍晚', '日落': '傍晚',
            '晚上': '晚上', '夜晚': '晚上', '夜里': '晚上',
            '深夜': '深夜', '午夜': '深夜', '凌晨': '深夜',
            'morning': 'morning', 'dawn': 'morning',
            'noon': 'noon', 'midday': 'noon',
            'afternoon': 'afternoon',
            'evening': 'evening', 'dusk': 'evening',
            'night': 'night', 
            'midnight': 'midnight', 'late night': 'midnight'
        }
        
        for term, normalized in time_of_day_terms.items():
            if term in text:
                return normalized
        
        return None
    
    def _extract_characters_from_text(self, text: str) -> List[str]:
        """从文本中提取角色信息"""
        # 这里需要更复杂的NLP技术才能准确提取角色
        # 简单示例，在真实项目中应使用NER
        characters = []
        common_names = [
            '小明', '小红', '小刚', '小芳', '老师', '妈妈', '爸爸',
            'John', 'Mary', 'Tom', 'teacher', 'mom', 'dad'
        ]
        
        for name in common_names:
            if name in text:
                characters.append(name)
        
        return characters
    
    def _extract_props_from_text(self, text: str) -> List[str]:
        """从文本中提取道具信息"""
        props = []
        
        # 检查常见道具
        for prop in self.key_props:
            if prop in text:
                props.append(prop)
        
        return props


# 创建便捷函数
def validate_scenes(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    验证场景序列的时空连续性
    
    参数:
        scenes: 场景列表
        
    返回:
        连续性验证结果
    """
    validator = SceneConsistencyValidator()
    return validator.validate_sequence(scenes)

def enhance_scene_data(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    增强场景数据，补充时空信息
    
    参数:
        scenes: 原始场景列表
        
    返回:
        增强后的场景列表
    """
    validator = SceneConsistencyValidator()
    return [validator.enhance_scene_metadata(scene) for scene in scenes]


if __name__ == "__main__":
    # 简单测试
    test_scenes = [
        {
            "text": "小明在教室里正在认真听讲。",
            "time": {"start": 0, "end": 3},
            "location": "教室",
            "characters": ["小明", "老师"],
            "time_of_day": "上午"
        },
        {
            "text": "下课铃响了，小明收拾书包。",
            "time": {"start": 3, "end": 6},
            "location": "教室",
            "characters": ["小明"],
            "time_of_day": "上午"
        },
        {
            "text": "小明在操场上和小红打篮球。",
            "time": {"start": 6, "end": 9},
            "location": "操场",
            "characters": ["小明", "小红"],
            "time_of_day": "上午"
        },
        {
            "text": "晚上，小明在家里写作业。",
            "time": {"start": 9, "end": 12},
            "location": "家",
            "characters": ["小明"],
            "time_of_day": "晚上"
        }
    ]
    
    print("场景连续性检查测试:")
    results = validate_scenes(test_scenes)
    
    print(f"总场景数: {results['total_scenes']}")
    print(f"发现问题: {results['total_errors']}")
    
    for category, count in results['error_counts'].items():
        if count > 0:
            print(f"  {category}: {count}个问题")
    
    if results['error_details']:
        print("\n详细问题:")
        for detail in results['error_details']:
            print(f"场景对 {detail['scene_pair'][0]}-{detail['scene_pair'][1]}:")
            for error in detail['errors']:
                print(f"  - {error}") 