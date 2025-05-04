#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
道具线索追踪系统

此模块提供用于追踪视频剪辑中道具使用一致性的工具。主要功能包括：
1. 道具出现记录 - 记录道具首次出现的场景及其来源
2. 道具使用追踪 - 跟踪道具在不同场景中的使用情况
3. 道具消失验证 - 确认道具的消失是否合理（如被销毁、交给他人等）
4. 道具一致性检查 - 验证道具在整个视频中的使用是否符合逻辑

使用这些工具可以避免混剪过程中出现道具突然出现或消失等连续性错误，提高视频的专业性。
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import logging
from collections import defaultdict

# 配置日志
logger = logging.getLogger(__name__)

class PropTracker:
    """
    道具追踪器
    
    追踪道具的出现、使用和消失，确保视频中道具使用的连续性。
    """
    
    def __init__(self):
        """初始化道具追踪器"""
        self.prop_records = defaultdict(list)  # 道具出现时间线
        self.prop_origins = {}  # 道具来源记录
        self.prop_status = {}  # 道具当前状态
        self.character_props = defaultdict(set)  # 角色持有的道具
    
    def track_prop_usage(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        追踪场景序列中的道具使用
        
        Args:
            scenes: 场景列表
            
        Returns:
            道具使用问题列表
        """
        issues = []
        
        # 按顺序处理所有场景
        for scene_index, scene in enumerate(scenes):
            scene_issues = self._process_scene_props(scene, scene_index)
            issues.extend(scene_issues)
        
        # 处理完所有场景后，检查未处理的道具
        unresolved_issues = self._check_unresolved_props()
        issues.extend(unresolved_issues)
        
        return issues
    
    def _process_scene_props(self, scene: Dict[str, Any], scene_index: int) -> List[Dict[str, Any]]:
        """
        处理单个场景中的道具
        
        Args:
            scene: 场景数据
            scene_index: 场景索引
            
        Returns:
            此场景中发现的道具问题
        """
        issues = []
        
        # 跳过没有props字段的场景
        if "props" not in scene:
            return issues
            
        props = scene["props"]
        scene_id = scene.get("id", f"scene_{scene_index}")
        character = scene.get("character", None)
        
        # 统一处理不同类型的props字段
        prop_list = self._normalize_props(props)
        
        # 检查每个道具
        for prop in prop_list:
            # 如果是字典，提取更详细的信息
            prop_name = prop
            prop_origin = None
            prop_status = "present"
            
            if isinstance(prop, dict):
                prop_name = prop.get("name", "未命名道具")
                prop_origin = prop.get("origin", None)
                prop_status = prop.get("status", "present")
            
            # 记录道具出现
            self.prop_records[prop_name].append({
                "scene_id": scene_id,
                "scene_index": scene_index,
                "character": character,
                "status": prop_status
            })
            
            # 检查道具来源
            if prop_name not in self.prop_origins:
                # 首次出现的道具
                if prop_origin:
                    self.prop_origins[prop_name] = prop_origin
                elif "origin" in scene.get("tags", []) or prop_status == "created":
                    self.prop_origins[prop_name] = f"创建于场景 {scene_id}"
                else:
                    # 道具突然出现，没有明确来源
                    issues.append({
                        "type": "prop_origin",
                        "prop": prop_name,
                        "scene_id": scene_id,
                        "scene_index": scene_index,
                        "message": f"道具「{prop_name}」未说明来源"
                    })
            
            # 更新道具状态
            self.prop_status[prop_name] = prop_status
            
            # 更新角色持有的道具
            if character and prop_status in ["present", "obtained", "created", "using"]:
                self.character_props[character].add(prop_name)
            elif character and prop_status in ["destroyed", "lost", "given"]:
                if prop_name in self.character_props[character]:
                    self.character_props[character].remove(prop_name)
        
        # 检查应该出现但未在当前场景中出现的道具
        if character:
            expected_props = self.character_props[character]
            for prop_name in expected_props.copy():
                if prop_name not in prop_list and not self._is_prop_exempt_in_scene(prop_name, scene):
                    # 检查道具是否已被标记为"隐藏"状态
                    last_status = self._get_last_prop_status(prop_name)
                    if last_status not in ["hidden", "stored", "inactive"]:
                        issues.append({
                            "type": "prop_continuity",
                            "prop": prop_name,
                            "character": character,
                            "scene_id": scene_id,
                            "scene_index": scene_index,
                            "message": f"角色「{character}」应持有道具「{prop_name}」但未在场景中出现"
                        })
        
        return issues
    
    def _normalize_props(self, props) -> List:
        """
        将不同格式的props字段统一为列表格式
        
        Args:
            props: 场景中的props字段，可能是列表、集合或字典
            
        Returns:
            标准化的道具列表
        """
        if isinstance(props, (list, set)):
            return list(props)
        elif isinstance(props, dict):
            # 如果是字典，将键和对象类型的值都视为道具
            result = []
            for key, value in props.items():
                result.append(key)
                if isinstance(value, dict):
                    result.append(value)
            return result
        else:
            return []
    
    def _is_prop_exempt_in_scene(self, prop_name: str, scene: Dict[str, Any]) -> bool:
        """
        检查道具是否在当前场景中免于出现
        
        某些特殊场景（如闪回、梦境、特写等）中，角色持有的道具可能不需要显示
        
        Args:
            prop_name: 道具名称
            scene: 场景数据
            
        Returns:
            是否免于在当前场景出现
        """
        # 检查场景标签是否表明这是特殊场景
        special_tags = ["flashback", "dream", "closeup", "memory", "闪回", "梦境", "特写", "回忆"]
        if "tags" in scene and isinstance(scene["tags"], (list, set)):
            for tag in special_tags:
                if tag in scene["tags"]:
                    return True
        
        # 检查场景类型
        if scene.get("type") in ["transition", "montage", "过渡", "蒙太奇"]:
            return True
            
        return False
    
    def _get_last_prop_status(self, prop_name: str) -> Optional[str]:
        """
        获取道具最近一次记录的状态
        
        Args:
            prop_name: 道具名称
            
        Returns:
            道具最近状态，如果没有记录则返回None
        """
        records = self.prop_records.get(prop_name, [])
        if not records:
            return None
        
        return records[-1].get("status", "present")
    
    def _check_unresolved_props(self) -> List[Dict[str, Any]]:
        """
        检查未妥善处理的道具
        
        在视频结束时，检查是否有道具的状态未得到适当的解决
        
        Returns:
            未解决的道具问题列表
        """
        issues = []
        
        for prop_name, records in self.prop_records.items():
            if not records:
                continue
                
            last_record = records[-1]
            last_status = last_record.get("status", "present")
            
            # 检查可能的问题状态
            if last_status not in ["destroyed", "lost", "given", "returned", "stored"]:
                # 这些道具的最终去向没有交代
                issues.append({
                    "type": "prop_unresolved",
                    "prop": prop_name,
                    "last_scene_id": last_record.get("scene_id", "未知场景"),
                    "message": f"道具「{prop_name}」的最终去向未交代"
                })
        
        return issues
    
    def get_prop_timeline(self, prop_name: str) -> List[Dict[str, Any]]:
        """
        获取特定道具的时间线记录
        
        Args:
            prop_name: 道具名称
            
        Returns:
            道具的时间线记录列表
        """
        return self.prop_records.get(prop_name, [])
    
    def get_character_props(self, character: str) -> Set[str]:
        """
        获取角色当前持有的道具
        
        Args:
            character: 角色名称
            
        Returns:
            角色持有的道具集合
        """
        return self.character_props.get(character, set())
    
    def get_all_props(self) -> List[str]:
        """
        获取所有记录的道具
        
        Returns:
            所有道具的列表
        """
        return list(self.prop_records.keys())


def track_props(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：追踪场景序列中的道具使用
    
    Args:
        scenes: 场景列表
        
    Returns:
        道具追踪结果，包含问题列表和统计信息
    """
    tracker = PropTracker()
    issues = tracker.track_prop_usage(scenes)
    
    # 计算统计信息
    prop_stats = {}
    for prop_name in tracker.get_all_props():
        timeline = tracker.get_prop_timeline(prop_name)
        prop_stats[prop_name] = {
            "appearances": len(timeline),
            "origin": tracker.prop_origins.get(prop_name, "未知"),
            "last_status": timeline[-1].get("status", "present") if timeline else "未知",
            "characters": [record.get("character") for record in timeline if record.get("character")]
        }
    
    return {
        "issues": issues,
        "statistics": {
            "total_props": len(tracker.get_all_props()),
            "props_with_issues": len(set(issue["prop"] for issue in issues if "prop" in issue)),
            "prop_details": prop_stats
        }
    } 