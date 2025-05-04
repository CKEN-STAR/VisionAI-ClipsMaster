#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时冲突解决器

使用操作转换（Operational Transformation, OT）算法解决并发编辑冲突。
当多个用户同时编辑同一内容时，确保所有客户端最终达到一致的状态。
"""

import copy
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

# 配置日志记录器
logger = logging.getLogger(__name__)

class OTResolver:
    """操作转换冲突解决器
    
    使用操作转换（Operational Transformation）算法解决并发编辑冲突。
    主要处理短剧混剪过程中的多用户协作场景，确保所有用户视图的一致性。
    """
    
    def __init__(self):
        """初始化操作转换解决器"""
        self.lock = threading.RLock()
        self.transform_functions = {
            "insert": self._transform_insert,
            "delete": self._transform_delete,
            "update": self._transform_update,
            "move": self._transform_move,
            "split": self._transform_split,
            "merge": self._transform_merge,
            "apply_effect": self._transform_effect,
            "adjust_timing": self._transform_timing,
        }
    
    def resolve(self, current_state: Dict[str, Any], incoming_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解决冲突并转换操作
        
        使用Operational Transformation解决编辑冲突，确保所有操作能够
        正确应用，无论它们的到达顺序如何。
        
        Args:
            current_state: 当前编辑状态，包含版本号和操作历史
            incoming_ops: 待处理的传入操作列表
            
        Returns:
            List[Dict[str, Any]]: 转换后的操作列表
        """
        with self.lock:
            transformed_ops = []
            
            for op in incoming_ops:
                # 检查操作时间戳是否早于当前版本
                if op["timestamp"] < current_state["version"]:
                    # 需要转换以适应已经应用的操作
                    op = self._transform_op(op, current_state["ops"])
                
                transformed_ops.append(op)
            
            return transformed_ops
    
    def merge_ops(self, current_state: Dict[str, Any], transformed_ops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并转换后的操作到当前状态
        
        Args:
            current_state: 当前编辑状态
            transformed_ops: 转换后的操作列表
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        # 创建状态的深拷贝以避免直接修改原始对象
        new_state = copy.deepcopy(current_state)
        
        # 将新操作添加到历史中
        new_state["ops"].extend(transformed_ops)
        
        # 更新版本号为最新操作的时间戳
        if transformed_ops:
            latest_timestamp = max(op["timestamp"] for op in transformed_ops)
            new_state["version"] = latest_timestamp
        
        return new_state
    
    def _transform_op(self, op: Dict[str, Any], existing_ops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """转换单个操作，使其适应已有操作的上下文
        
        Args:
            op: 待转换的操作
            existing_ops: 已经应用的操作列表
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        transformed_op = copy.deepcopy(op)
        
        # 应用转换函数
        for existing_op in existing_ops:
            if existing_op["timestamp"] > op["timestamp"]:
                # 只需要转换针对在此操作之后应用的操作
                continue
            
            # 根据操作类型选择合适的转换函数
            op_type = transformed_op.get("type")
            transform_func = self.transform_functions.get(op_type)
            
            if transform_func:
                transformed_op = transform_func(transformed_op, existing_op)
            else:
                logger.warning(f"未找到操作类型的转换函数: {op_type}")
        
        return transformed_op
    
    # 针对不同操作类型的转换函数
    def _transform_insert(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换插入操作
        
        Args:
            op: 待转换的插入操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        transformed = copy.deepcopy(op)
        
        # 如果是插入操作需要考虑位置调整
        if existing_op.get("type") == "insert":
            # 如果现有插入发生在当前插入位置之前，需要调整位置
            if existing_op.get("position", 0) <= op.get("position", 0):
                transformed["position"] = op["position"] + len(existing_op.get("content", ""))
        
        # 删除操作的处理
        elif existing_op.get("type") == "delete":
            delete_start = existing_op.get("position", 0)
            delete_end = delete_start + existing_op.get("length", 0)
            
            # 如果插入位置在删除区域之前，不需要调整
            # 如果插入位置在删除区域之内或之后，需要调整位置
            if op.get("position", 0) > delete_start:
                # 如果完全在删除区域之后，减去删除的长度
                if op.get("position", 0) >= delete_end:
                    transformed["position"] = op["position"] - existing_op.get("length", 0)
                # 如果在删除区域内，则移动到删除起始位置
                else:
                    transformed["position"] = delete_start
        
        return transformed
    
    def _transform_delete(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换删除操作
        
        Args:
            op: 待转换的删除操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        transformed = copy.deepcopy(op)
        delete_start = op.get("position", 0)
        delete_end = delete_start + op.get("length", 0)
        
        # 对已有的插入操作进行调整
        if existing_op.get("type") == "insert":
            insert_pos = existing_op.get("position", 0)
            insert_len = len(existing_op.get("content", ""))
            
            # 插入在删除区域之前
            if insert_pos <= delete_start:
                transformed["position"] = delete_start + insert_len
            
            # 插入在删除区域内
            elif insert_pos < delete_end:
                # 增加删除长度
                transformed["length"] = op["length"] + insert_len
            
            # 插入在删除区域之后，不需要调整
        
        # 对已有的删除操作进行调整
        elif existing_op.get("type") == "delete":
            existing_start = existing_op.get("position", 0)
            existing_end = existing_start + existing_op.get("length", 0)
            
            # 情况1: 两个删除区域不重叠
            if delete_end <= existing_start or delete_start >= existing_end:
                # 如果现有删除在当前删除之前，需要调整位置
                if existing_end <= delete_start:
                    transformed["position"] = delete_start - existing_op.get("length", 0)
            
            # 情况2: 有重叠区域
            else:
                # 计算重叠部分
                overlap_start = max(delete_start, existing_start)
                overlap_end = min(delete_end, existing_end)
                overlap_length = overlap_end - overlap_start
                
                # 根据重叠情况调整删除位置和长度
                if delete_start < existing_start:
                    # 当前删除开始于现有删除之前
                    transformed["length"] = op["length"] - overlap_length
                else:
                    # 当前删除开始于现有删除之内或之后
                    transformed["position"] = delete_start - (overlap_start - existing_start)
                    transformed["length"] = op["length"] - overlap_length
                
                # 如果调整后长度为0，标记为无效操作
                if transformed["length"] <= 0:
                    transformed["invalid"] = True
        
        return transformed
    
    def _transform_update(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换更新操作
        
        Args:
            op: 待转换的更新操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        # 基本实现：如果目标相同，后来的操作优先
        transformed = copy.deepcopy(op)
        
        if existing_op.get("type") == "update" and existing_op.get("target_id") == op.get("target_id"):
            # 可以根据具体需求实现更复杂的属性合并逻辑
            # 这里简单地保留当前操作的值
            pass
        
        return transformed
    
    def _transform_move(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换移动操作
        
        Args:
            op: 待转换的移动操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        transformed = copy.deepcopy(op)
        
        # 如果两个操作都是移动同一个元素，以后来的操作为准
        if existing_op.get("type") == "move" and existing_op.get("target_id") == op.get("target_id"):
            # 保持当前操作不变
            pass
        
        # 针对其他移动操作，可能需要调整目标位置
        elif existing_op.get("type") in ["insert", "delete"]:
            # 根据插入和删除对位置的影响进行调整
            # 实际实现中需要考虑具体的数据结构和位置表示方式
            pass
        
        return transformed
    
    def _transform_split(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换分割操作
        
        Args:
            op: 待转换的分割操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        # 这里实现具体的分割片段操作转换逻辑
        # 例如处理同一个片段被多次分割的情况
        return copy.deepcopy(op)
    
    def _transform_merge(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换合并操作
        
        Args:
            op: 待转换的合并操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        # 这里实现具体的合并片段操作转换逻辑
        # 例如处理要合并的片段已被删除的情况
        return copy.deepcopy(op)
    
    def _transform_effect(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换效果应用操作
        
        Args:
            op: 待转换的效果应用操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        # 处理效果应用操作的冲突
        # 如果是同一目标的效果操作，可能需要合并效果或者按特定规则处理
        return copy.deepcopy(op)
    
    def _transform_timing(self, op: Dict[str, Any], existing_op: Dict[str, Any]) -> Dict[str, Any]:
        """转换时间调整操作
        
        Args:
            op: 待转换的时间调整操作
            existing_op: 已存在的操作
            
        Returns:
            Dict[str, Any]: 转换后的操作
        """
        # 处理时间调整操作的冲突
        # 例如处理多个用户同时调整同一片段的开始/结束时间
        return copy.deepcopy(op)


# 单例模式
_ot_resolver_instance = None
_instance_lock = threading.Lock()

def get_ot_resolver() -> OTResolver:
    """获取操作转换解决器单例实例
    
    Returns:
        OTResolver: 操作转换解决器实例
    """
    global _ot_resolver_instance
    
    if _ot_resolver_instance is None:
        with _instance_lock:
            if _ot_resolver_instance is None:
                _ot_resolver_instance = OTResolver()
    
    return _ot_resolver_instance

def initialize_ot_resolver() -> OTResolver:
    """初始化操作转换解决器
    
    Returns:
        OTResolver: 操作转换解决器实例
    """
    global _ot_resolver_instance
    
    with _instance_lock:
        _ot_resolver_instance = OTResolver()
    
    return _ot_resolver_instance 