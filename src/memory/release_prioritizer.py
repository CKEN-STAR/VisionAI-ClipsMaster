#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源释放优先级决策树

该模块负责在内存压力下，决定资源释放的优先级顺序。
主要功能：
1. 按配置的优先级排序资源
2. 同优先级资源按最后访问时间排序
3. 支持多条件排序和自定义规则
4. 提供释放建议和决策依据
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logger = logging.getLogger("ReleasePrioritizer")

class ReleasePrioritizer:
    """资源释放优先级决策器，负责确定资源释放的最佳顺序"""
    
    def __init__(self):
        """初始化释放优先级决策器"""
        # 定义默认权重因子
        self.weight_factors = {
            "priority": 1.0,           # 资源类型优先级权重
            "last_access": 0.7,         # 最后访问时间权重
            "size": 0.3,               # 资源大小权重
            "usage_frequency": 0.5,     # 使用频率权重
            "is_compressed": 0.1        # 压缩状态权重
        }
        logger.info("资源释放优先级决策器初始化完成")
    
    def decide_release_order(self, expired_resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        计算最佳释放顺序
        
        主要逻辑：
        1. 按配置的优先级排序（优先级数字越小越先释放）
        2. 同优先级资源按最后访问时间排序（越久未访问越先释放）
        
        Args:
            expired_resources: 过期资源列表，每个资源应包含优先级和最后访问时间
            
        Returns:
            List[Dict]: 按释放优先级排序的资源列表
        """
        if not expired_resources:
            return []
            
        # 排序资源：优先按优先级，同优先级则按最后访问时间
        sorted_resources = sorted(
            expired_resources,
            key=lambda x: (
                x.get('priority', 999),                # 优先级（低数字优先）
                -x.get('last_access', 0)               # 最后访问时间（更早的优先）
            ),
            reverse=False
        )
        
        return sorted_resources
    
    def calculate_release_priority(self, resources: Dict[str, Dict[str, Any]],
                                  resource_types: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        计算资源释放优先级列表
        
        Args:
            resources: 资源字典 {resource_id: resource_info}
            resource_types: 资源类型配置 {resource_type: type_config}
            
        Returns:
            List[str]: 按释放优先级排序的资源ID列表
        """
        # 准备资源评分
        resource_scores = []
        
        for res_id, res_info in resources.items():
            # 资源类型
            resource_type = res_id.split(":", 1)[0] if ":" in res_id else "unknown"
            
            # 获取资源类型配置
            type_config = resource_types.get(resource_type, {"priority": 999})
            
            # 资源元数据
            metadata = res_info.get("metadata", {})
            
            # 计算基础评分
            priority = type_config.get("priority", 999)
            last_access = res_info.get("last_access", 0)
            current_time = time.time()
            access_age = current_time - last_access
            
            # 是否已过期
            max_retain_time = metadata.get("max_retain_time", 300)
            is_expired = access_age > max_retain_time
            
            # 计算综合评分 (低分优先释放)
            score = priority * 100  # 优先级作为基础分
            
            # 访问时间因子：越久未访问，评分越低（越先释放）
            access_factor = min(1.0, access_age / (max_retain_time * 2))  # 归一化到0-1之间
            score -= access_factor * 50  # 最多降低50分
            
            # 资源大小因子：越大的资源越优先释放
            size_mb = metadata.get("size_mb", 0)
            if size_mb > 0:
                size_factor = min(1.0, size_mb / 1000)  # 归一化，最大1000MB
                score -= size_factor * 30  # 最多降低30分
            
            # 是否是活动模型
            is_active = metadata.get("is_active", False)
            if is_active:
                score += 200  # 活动模型加200分，降低释放优先级
            
            # 是否支持压缩而非释放
            if metadata.get("compression_enabled", False):
                score += 20  # 可压缩资源略微降低释放优先级
            
            # 已过期资源优先释放
            if is_expired:
                score -= 100  # 已过期资源减100分
            
            # 添加到评分列表
            resource_scores.append((res_id, score, priority, last_access))
        
        # 按评分排序（低分优先释放）
        sorted_resources = sorted(resource_scores, key=lambda x: x[1])
        
        # 返回排序后的资源ID列表
        return [item[0] for item in sorted_resources]
    
    def get_release_candidates(self, resources: Dict[str, Dict[str, Any]], 
                              resource_types: Dict[str, Dict[str, Any]],
                              required_memory_mb: float = 0,
                              max_candidates: int = 10) -> List[str]:
        """
        获取释放候选资源
        
        Args:
            resources: 资源字典 {resource_id: resource_info}
            resource_types: 资源类型配置 {resource_type: type_config}
            required_memory_mb: 需要释放的内存大小(MB)
            max_candidates: 最大候选数量
            
        Returns:
            List[str]: 释放候选资源ID列表
        """
        # 获取完整优先级列表
        priority_list = self.calculate_release_priority(resources, resource_types)
        
        # 如果不需要考虑内存大小，直接返回前N个
        if required_memory_mb <= 0:
            return priority_list[:max_candidates]
        
        # 否则累计选择直到满足内存需求
        candidates = []
        accumulated_mb = 0
        
        for res_id in priority_list:
            if len(candidates) >= max_candidates:
                break
                
            res_info = resources.get(res_id, {})
            metadata = res_info.get("metadata", {})
            size_mb = metadata.get("size_mb", 0)
            
            candidates.append(res_id)
            accumulated_mb += size_mb
            
            if accumulated_mb >= required_memory_mb:
                break
        
        return candidates
    
    def explain_decision(self, resource_id: str, resources: Dict[str, Dict[str, Any]],
                       resource_types: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        解释为什么某资源被选择释放
        
        Args:
            resource_id: 资源ID
            resources: 资源字典
            resource_types: 资源类型配置
            
        Returns:
            Dict: 决策解释
        """
        if resource_id not in resources:
            return {"explanation": "资源不存在"}
            
        res_info = resources[resource_id]
        resource_type = resource_id.split(":", 1)[0] if ":" in resource_id else "unknown"
        type_config = resource_types.get(resource_type, {})
        
        # 提取关键信息
        priority = type_config.get("priority", 999)
        max_retain_time = type_config.get("max_retain_time", 300)
        last_access = res_info.get("last_access", 0)
        current_time = time.time()
        access_age = current_time - last_access
        
        # 生成解释
        explanation = {
            "resource_id": resource_id,
            "resource_type": resource_type,
            "priority": priority,
            "last_accessed": f"{access_age:.1f}秒前",
            "max_retain_time": f"{max_retain_time}秒",
            "is_expired": access_age > max_retain_time,
            "release_reason": []
        }
        
        # 添加释放原因
        if access_age > max_retain_time:
            explanation["release_reason"].append(f"资源已过期 ({access_age:.1f}秒 > {max_retain_time}秒)")
        
        if priority < 3:
            explanation["release_reason"].append(f"资源优先级较高 (优先级 {priority})")
        
        if res_info.get("metadata", {}).get("size_mb", 0) > 500:
            explanation["release_reason"].append("资源占用内存较大")
        
        # 如果没有具体原因，添加默认原因
        if not explanation["release_reason"]:
            explanation["release_reason"].append("根据综合评分被选择释放")
        
        return explanation
    
    def adjust_weights(self, new_weights: Dict[str, float]) -> None:
        """
        调整决策权重
        
        Args:
            new_weights: 新的权重设置
        """
        for key, value in new_weights.items():
            if key in self.weight_factors:
                self.weight_factors[key] = value


# 单例模式
_release_prioritizer = None

def get_release_prioritizer() -> ReleasePrioritizer:
    """获取释放优先级决策器单例"""
    global _release_prioritizer
    if _release_prioritizer is None:
        _release_prioritizer = ReleasePrioritizer()
    return _release_prioritizer


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试释放优先级决策器
    prioritizer = get_release_prioritizer()
    
    # 模拟资源和资源类型
    resources = {
        "temp_buffers:buffer1": {
            "last_access": time.time() - 40,
            "metadata": {"size_mb": 100, "max_retain_time": 30}
        },
        "model_shards:layer1": {
            "last_access": time.time() - 200,
            "metadata": {"size_mb": 200, "max_retain_time": 300}
        },
        "model_weights_cache:qwen": {
            "last_access": time.time() - 500,
            "metadata": {"size_mb": 4000, "max_retain_time": 600, "is_active": True}
        },
        "render_cache:frame1": {
            "last_access": time.time() - 190,
            "metadata": {"size_mb": 50, "max_retain_time": 180, "compression_enabled": True}
        }
    }
    
    resource_types = {
        "temp_buffers": {"priority": 3, "max_retain_time": 30},
        "model_shards": {"priority": 1, "max_retain_time": 300},
        "model_weights_cache": {"priority": 5, "max_retain_time": 600},
        "render_cache": {"priority": 2, "max_retain_time": 180}
    }
    
    # 计算释放优先级
    priority_list = prioritizer.calculate_release_priority(resources, resource_types)
    print("资源释放优先级:")
    for i, res_id in enumerate(priority_list):
        print(f"{i+1}. {res_id}")
    
    # 解释决策
    for res_id in priority_list[:2]:
        explanation = prioritizer.explain_decision(res_id, resources, resource_types)
        print(f"\n释放决策解释 - {res_id}:")
        for key, value in explanation.items():
            if key != "release_reason":
                print(f"  {key}: {value}")
        print("  释放原因:")
        for reason in explanation["release_reason"]:
            print(f"    - {reason}") 