#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分层压缩策略管理器

管理不同资源类型的压缩策略，支持从YAML配置文件加载策略
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml

# 导入压缩模块
from src.compression.compressors import (
    get_compressor, 
    get_available_compressors
)
from src.compression.integration import get_compression_manager

# 日志配置
logger = logging.getLogger("LayeredPolicy")

class CompressionPolicyManager:
    """压缩策略管理器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化压缩策略管理器
        
        Args:
            config_path: 配置文件路径，默认为 configs/compression_layers.yaml
        """
        # 默认配置
        self.default_config = {
            "algorithm": "gzip",
            "level": 6,
            "chunk_size": "4MB",
            "auto_compress": False,
            "threshold_mb": 10,
            "priority": "low"
        }
        
        # 策略配置
        self.policies = {
            "default": self.default_config
        }
        
        # 加载配置
        if config_path:
            self.load_config(config_path)
        else:
            # 尝试加载默认配置
            default_config = os.path.join("configs", "compression_layers.yaml")
            if os.path.exists(default_config):
                self.load_config(default_config)
            else:
                logger.warning(f"默认配置文件 {default_config} 不存在，使用内置默认策略")
        
        # 初始化压缩管理器
        self.compression_manager = get_compression_manager()
        
        # 应用策略到压缩管理器
        self.apply_policies_to_manager()
    
    def load_config(self, config_path: str) -> bool:
        """
        从YAML文件加载压缩策略配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查配置结构
            if not config or not isinstance(config, dict):
                logger.error(f"配置文件 {config_path} 格式错误")
                return False
            
            # 获取压缩策略
            compression_policy = config.get("compression_policy", {})
            if not compression_policy:
                logger.error(f"配置文件 {config_path} 中没有找到 compression_policy 节点")
                return False
            
            # 更新策略
            self.policies = compression_policy
            
            # 确保有默认策略
            if "default" not in self.policies:
                self.policies["default"] = self.default_config
            
            logger.info(f"成功从 {config_path} 加载了 {len(self.policies)} 个压缩策略")
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件 {config_path} 失败: {e}")
            return False
    
    def save_config(self, config_path: str) -> bool:
        """
        保存当前压缩策略配置到YAML文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 创建配置目录(如果不存在)
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 构建配置
            config = {
                "compression_policy": self.policies
            }
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"成功将压缩策略保存到 {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件 {config_path} 失败: {e}")
            return False
    
    def get_policy(self, resource_type: str) -> Dict[str, Any]:
        """
        获取指定资源类型的压缩策略
        
        Args:
            resource_type: 资源类型
            
        Returns:
            Dict: 压缩策略配置
        """
        # 如果策略存在，返回指定类型的策略
        if resource_type in self.policies:
            return self.policies[resource_type]
        
        # 否则返回默认策略
        return self.policies["default"]
    
    def set_policy(self, resource_type: str, policy: Dict[str, Any]) -> None:
        """
        设置指定资源类型的压缩策略
        
        Args:
            resource_type: 资源类型
            policy: 压缩策略配置
        """
        self.policies[resource_type] = policy
        
        # 应用到压缩管理器
        self._apply_policy_to_manager(resource_type, policy)
        
        logger.info(f"已更新 {resource_type} 的压缩策略")
    
    def apply_policies_to_manager(self) -> None:
        """将所有策略应用到压缩管理器"""
        for res_type, policy in self.policies.items():
            self._apply_policy_to_manager(res_type, policy)
    
    def _apply_policy_to_manager(self, resource_type: str, policy: Dict[str, Any]) -> None:
        """
        将单个策略应用到压缩管理器
        
        Args:
            resource_type: 资源类型
            policy: 压缩策略
        """
        if not self.compression_manager:
            logger.warning("压缩管理器不可用，无法应用策略")
            return
        
        # 转换策略为压缩管理器配置
        config = self._convert_policy_to_config(policy)
        
        # 更新压缩管理器配置
        self.compression_manager.update_compression_config(resource_type, config)
    
    def _convert_policy_to_config(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        将策略转换为压缩管理器配置
        
        Args:
            policy: 压缩策略
            
        Returns:
            Dict: 压缩管理器配置
        """
        config = {}
        
        # 算法
        if "algorithm" in policy:
            config["algorithm"] = policy["algorithm"]
        
        # 压缩级别
        if "level" in policy:
            config["compression_level"] = policy["level"]
        
        # 自动压缩
        if "auto_compress" in policy:
            config["auto_compress"] = policy["auto_compress"]
        
        # 压缩阈值
        if "threshold_mb" in policy:
            config["compression_threshold_mb"] = policy["threshold_mb"]
        
        # 平衡模式 (根据优先级映射)
        if "priority" in policy:
            priority = policy["priority"]
            if priority == "high":
                config["balance_mode"] = "speed"  # 高优先级使用速度优先
            elif priority == "medium":
                config["balance_mode"] = "balanced"  # 中等优先级使用平衡模式
            elif priority == "low":
                config["balance_mode"] = "ratio"  # 低优先级使用压缩率优先
        
        return config
    
    def parse_chunk_size(self, chunk_size_str: str) -> int:
        """
        解析分块大小字符串，如 '1MB', '512KB' 等
        
        Args:
            chunk_size_str: 分块大小字符串
            
        Returns:
            int: 字节数
        """
        if isinstance(chunk_size_str, (int, float)):
            return int(chunk_size_str)
            
        chunk_size_str = str(chunk_size_str).upper()
        
        # 尝试解析单位
        if chunk_size_str.endswith('KB'):
            return int(float(chunk_size_str[:-2]) * 1024)
        elif chunk_size_str.endswith('MB'):
            return int(float(chunk_size_str[:-2]) * 1024 * 1024)
        elif chunk_size_str.endswith('GB'):
            return int(float(chunk_size_str[:-2]) * 1024 * 1024 * 1024)
        elif chunk_size_str.endswith('B'):
            return int(chunk_size_str[:-1])
        else:
            # 默认假设为字节
            try:
                return int(chunk_size_str)
            except ValueError:
                logger.warning(f"无法解析分块大小 '{chunk_size_str}'，使用默认值 4MB")
                return 4 * 1024 * 1024
    
    def compress_resource(self, resource_id: str, resource_type: Optional[str] = None) -> bool:
        """
        使用分层策略压缩资源
        
        Args:
            resource_id: 资源ID
            resource_type: 资源类型，如果为None，将尝试从资源元数据获取
            
        Returns:
            bool: 是否成功压缩
        """
        if not self.compression_manager:
            logger.error("压缩管理器不可用")
            return False
        
        # 尝试获取资源类型
        if not resource_type:
            # 从资源跟踪器获取资源类型
            if hasattr(self.compression_manager, "resource_tracker") and self.compression_manager.resource_tracker:
                resource_info = self.compression_manager.resource_tracker.get_resource_info(resource_id)
                if resource_info:
                    resource_type = resource_info.get("res_type", "default")
                else:
                    resource_type = "default"
            else:
                resource_type = "default"
        
        # 获取压缩策略
        policy = self.get_policy(resource_type)
        
        # 设置临时配置
        self._apply_policy_to_manager(resource_type, policy)
        
        # 压缩资源
        return self.compression_manager.compress_resource(resource_id)
    
    def get_available_policies(self) -> List[str]:
        """
        获取所有可用的策略类型
        
        Returns:
            List[str]: 策略类型列表
        """
        return list(self.policies.keys())
    
    def get_all_policies(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有策略配置
        
        Returns:
            Dict: 所有策略配置
        """
        return self.policies
    
    def get_policy_summary(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有策略的摘要信息
        
        Returns:
            Dict: 策略摘要
        """
        summary = {}
        
        for res_type, policy in self.policies.items():
            summary[res_type] = {
                "algorithm": policy.get("algorithm", "unknown"),
                "level": str(policy.get("level", "N/A")),
                "auto_compress": "是" if policy.get("auto_compress", False) else "否",
                "threshold": f"{policy.get('threshold_mb', 'N/A')}MB",
                "priority": policy.get("priority", "medium")
            }
        
        return summary

# 单例模式
_policy_manager = None

def get_policy_manager(config_path: Optional[str] = None) -> CompressionPolicyManager:
    """
    获取压缩策略管理器实例
    
    Args:
        config_path: 配置文件路径，默认为None表示使用默认路径
        
    Returns:
        CompressionPolicyManager: 策略管理器实例
    """
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = CompressionPolicyManager(config_path)
    elif config_path:
        # 如果提供了配置路径，重新加载配置
        _policy_manager.load_config(config_path)
    return _policy_manager

# 便捷函数
def compress_with_policy(resource_id: str, resource_type: Optional[str] = None) -> bool:
    """
    使用策略压缩资源的便捷函数
    
    Args:
        resource_id: 资源ID
        resource_type: 资源类型，可选
        
    Returns:
        bool: 是否成功
    """
    manager = get_policy_manager()
    return manager.compress_resource(resource_id, resource_type)

def get_resource_policy(resource_type: str) -> Dict[str, Any]:
    """
    获取资源类型的压缩策略的便捷函数
    
    Args:
        resource_type: 资源类型
        
    Returns:
        Dict: 策略配置
    """
    manager = get_policy_manager()
    return manager.get_policy(resource_type)

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取策略管理器
    manager = get_policy_manager()
    
    # 打印所有策略
    policies = manager.get_all_policies()
    print("\n所有压缩策略:")
    for res_type, policy in policies.items():
        print(f"\n{res_type}:")
        for key, value in policy.items():
            print(f"  {key}: {value}")
    
    # 获取策略摘要
    summary = manager.get_policy_summary()
    print("\n策略摘要:")
    for res_type, info in summary.items():
        print(f"{res_type}: {info['algorithm']} (级别{info['level']}), "
              f"自动压缩: {info['auto_compress']}, 阈值: {info['threshold']}") 