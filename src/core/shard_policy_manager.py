"""模型分片策略管理模块

此模块负责管理模型分片策略的配置、加载和应用：
1. 加载和解析分片策略配置
2. 根据系统资源和模型选择合适的分片策略
3. 提供分片策略应用接口
4. 支持动态调整分片策略
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

from src.utils.device_manager import HybridDevice
from src.utils.memory_manager import MemoryManager
from src.core.model_sharding import ModelSharding


class ShardPolicyManager:
    """模型分片策略管理类"""
    
    def __init__(self, 
                 config_path: str = "configs/shard_policy.yaml",
                 enable_dynamic: bool = True):
        """初始化分片策略管理器
        
        Args:
            config_path: 分片策略配置文件路径
            enable_dynamic: 是否启用动态调整
        """
        self.config_path = Path(config_path)
        self.enable_dynamic = enable_dynamic
        self.device_manager = HybridDevice()
        self.memory_manager = MemoryManager()
        self.model_sharding = ModelSharding()
        
        # 加载配置
        self.config = self._load_config()
        self.current_strategy = self.config["sharding"]["default_strategy"]
        self.strategy_history = []
        
        # 记录当前策略
        self._record_strategy_change("初始化", self.current_strategy)
    
    def _load_config(self) -> Dict:
        """加载分片策略配置
        
        Returns:
            Dict: 配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"分片策略配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"成功加载分片策略配置: {len(config['shard_strategies'])} 个策略")
        return config
    
    def save_config(self) -> bool:
        """保存当前配置到配置文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"成功保存分片策略配置到: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_current_strategy(self) -> Dict:
        """获取当前使用的分片策略
        
        Returns:
            Dict: 当前分片策略信息
        """
        return self._get_strategy_by_name(self.current_strategy)
    
    def _get_strategy_by_name(self, strategy_name: str) -> Dict:
        """通过名称获取策略配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            Dict: 策略配置信息
        """
        for strategy in self.config["shard_strategies"]:
            if strategy["name"] == strategy_name:
                return strategy
        
        # 如果找不到，返回默认策略
        logger.warning(f"未找到策略 '{strategy_name}'，使用默认策略")
        default_strategy = self.config["sharding"]["default_strategy"]
        return self._get_strategy_by_name(default_strategy)
    
    def get_all_strategies(self) -> List[Dict]:
        """获取所有可用的分片策略
        
        Returns:
            List[Dict]: 所有分片策略列表
        """
        return self.config["shard_strategies"]
    
    def get_strategy_history(self) -> List[Dict]:
        """获取分片策略变更历史
        
        Returns:
            List[Dict]: 策略变更历史记录
        """
        return self.strategy_history
    
    def _record_strategy_change(self, reason: str, new_strategy: str):
        """记录策略变更
        
        Args:
            reason: 变更原因
            new_strategy: 新策略名称
        """
        import time

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        
        record = {
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prev_strategy": self.current_strategy if hasattr(self, 'current_strategy') else None,
            "new_strategy": new_strategy,
            "reason": reason,
            "memory_available": self.memory_manager.get_available_memory()
        }
        
        self.strategy_history.append(record)
        # 只保留最近50条记录
        if len(self.strategy_history) > 50:
            self.strategy_history.pop(0)
    
    def select_strategy_for_model(self, model_name: str) -> str:
        """为特定模型选择合适的分片策略
        
        Args:
            model_name: 模型名称
            
        Returns:
            str: 选择的策略名称
        """
        # 检查是否有特定模型的配置
        if model_name in self.config["model_specific"]:
            model_config = self.config["model_specific"][model_name]
            return model_config["default_strategy"]
        
        # 如果没有特定配置，根据系统资源自动选择
        if self.config["sharding"]["auto_select"]:
            return self._auto_select_strategy()
        
        # 返回默认策略
        return self.config["sharding"]["default_strategy"]
    
    def _auto_select_strategy(self) -> str:
        """根据系统资源自动选择分片策略
        
        Returns:
            str: 自动选择的策略名称
        """
        available_memory = self.memory_manager.get_available_memory()
        thresholds = self.config["auto_select_thresholds"]
        
        # 根据内存阈值选择策略
        if available_memory <= thresholds["critical"]:
            return "minimum"
        elif available_memory <= thresholds["low"]:
            return "conservative"
        elif available_memory <= thresholds["normal"]:
            return "balanced"
        else:
            return "performance"
    
    def apply_strategy(self, strategy_name: str, reason: str = "手动切换") -> bool:
        """应用指定的分片策略
        
        Args:
            strategy_name: 策略名称
            reason: a应用原因
            
        Returns:
            bool: 是否应用成功
        """
        # 验证策略是否存在
        strategy = self._get_strategy_by_name(strategy_name)
        if not strategy:
            logger.error(f"策略 '{strategy_name}' 不存在")
            return False
        
        # 更新当前策略
        prev_strategy = self.current_strategy
        self.current_strategy = strategy_name
        
        # 更新模型分片器的配置
        strategy_config = self._get_strategy_by_name(strategy_name)
        self.model_sharding.default_shard_size = strategy_config["max_shard_size"] * 1024 * 1024  # 转换为字节
        
        # 记录变更
        self._record_strategy_change(reason, strategy_name)
        
        logger.info(f"已切换分片策略: {prev_strategy} -> {strategy_name}, 原因: {reason}")
        return True
    
    def evaluate_current_conditions(self) -> Tuple[bool, Optional[str], str]:
        """评估当前系统条件，决定是否需要调整分片策略
        
        Returns:
            Tuple[bool, Optional[str], str]: 
                - 是否需要调整
                - 如果需要调整，建议的策略名称
                - 调整原因
        """
        # 如果不启用动态调整，直接返回不需要调整
        if not self.enable_dynamic:
            return False, None, "动态调整已禁用"
        
        # 获取当前系统条件
        available_memory = self.memory_manager.get_available_memory()
        current_strategy = self._get_strategy_by_name(self.current_strategy)
        
        # 检查内存是否不足，需要降级策略
        if available_memory < current_strategy["memory_threshold"] * 0.9:  # 预留10%缓冲区
            suggested_strategy = self._auto_select_strategy()
            if suggested_strategy != self.current_strategy:
                return True, suggested_strategy, f"内存不足 ({available_memory}MB < {current_strategy['memory_threshold']}MB)"
        
        # 检查内存是否充足，可以升级策略
        elif available_memory > current_strategy["memory_threshold"] * 1.5:  # 内存充足50%以上
            suggested_strategy = self._auto_select_strategy()
            if suggested_strategy != self.current_strategy:
                # 只有当建议的策略比当前策略"性能"更高时才升级
                strategies_order = ["minimum", "conservative", "balanced", "performance"]
                current_idx = strategies_order.index(self.current_strategy)
                suggested_idx = strategies_order.index(suggested_strategy)
                
                if suggested_idx > current_idx:
                    return True, suggested_strategy, f"内存充足 ({available_memory}MB > {current_strategy['memory_threshold'] * 1.5}MB)"
        
        # 不需要调整
        return False, None, "当前策略适合系统条件"
    
    def adjust_if_needed(self) -> bool:
        """如有必要，自动调整分片策略
        
        Returns:
            bool: 是否进行了调整
        """
        needs_adjustment, suggested_strategy, reason = self.evaluate_current_conditions()
        
        if needs_adjustment and suggested_strategy:
            return self.apply_strategy(suggested_strategy, f"自动调整: {reason}")
        
        return False
    
    def get_model_specific_settings(self, model_name: str) -> Dict:
        """获取特定模型的分片设置
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict: 模型特定的分片设置
        """
        if model_name in self.config["model_specific"]:
            return self.config["model_specific"][model_name]
        return {}
    
    def update_model_settings(self, model_name: str, settings: Dict) -> bool:
        """更新特定模型的分片设置
        
        Args:
            model_name: 模型名称
            settings: 新的设置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if model_name not in self.config["model_specific"]:
                self.config["model_specific"][model_name] = {}
            
            # 更新设置
            self.config["model_specific"][model_name].update(settings)
            
            # 保存配置
            self.save_config()
            logger.info(f"已更新模型 {model_name} 的分片设置")
            return True
            
        except Exception as e:
            logger.error(f"更新模型设置失败: {e}")
            return False
    
    def get_layer_dependencies(self) -> List[Dict]:
        """获取模型层依赖关系配置
        
        Returns:
            List[Dict]: 层依赖关系列表
        """
        return self.config["sharding"]["layer_dependencies"]
    
    def update_layer_dependencies(self, dependencies: List[Dict]) -> bool:
        """更新模型层依赖关系
        
        Args:
            dependencies: 新的层依赖关系
            
        Returns:
            bool: 是否更新成功
        """
        try:
            self.config["sharding"]["layer_dependencies"] = dependencies
            self.save_config()
            logger.info(f"已更新模型层依赖关系")
            return True
        except Exception as e:
            logger.error(f"更新层依赖关系失败: {e}")
            return False
    
    def generate_sharding_plan(self, model_name: str, model_size: int) -> Dict:
        """生成模型分片计划
        
        Args:
            model_name: 模型名称
            model_size: 模型大小(字节)
            
        Returns:
            Dict: 分片计划
        """
        # 选择合适的策略
        strategy_name = self.select_strategy_for_model(model_name)
        strategy = self._get_strategy_by_name(strategy_name)
        
        # 获取模型特定设置（如果有）
        model_settings = self.get_model_specific_settings(model_name)
        
        # 确定分片大小
        shard_size_mb = strategy["max_shard_size"]
        if model_settings and "custom_settings" in model_settings:
            if "max_shard_size" in model_settings["custom_settings"]:
                shard_size_mb = model_settings["custom_settings"]["max_shard_size"]
        
        # 确保至少有最小分片数
        min_shards = strategy.get("min_shards", 1)
        model_size_mb = model_size / (1024 * 1024)
        
        # 计算分片数和每个分片大小
        num_shards = max(min_shards, round(model_size_mb / shard_size_mb))
        actual_shard_size_mb = model_size_mb / num_shards
        
        # 获取层分组信息
        layer_grouping = []
        if model_settings and "custom_settings" in model_settings:
            if "layer_grouping_override" in model_settings["custom_settings"]:
                layer_grouping = model_settings["custom_settings"]["layer_grouping_override"]
        
        # 生成分片计划
        return {
            "model_name": model_name,
            "model_size_mb": model_size_mb,
            "strategy": strategy_name,
            "num_shards": num_shards,
            "shard_size_mb": actual_shard_size_mb,
            "layer_grouping": layer_grouping,
            "loading_mode": strategy["loading_mode"],
            "verification_level": self.config["sharding"]["verification_level"],
            "compression": self.config["advanced"]["compression"]
        }
    
    def get_configuration_summary(self) -> Dict:
        """获取配置摘要
        
        Returns:
            Dict: 配置摘要
        """
        return {
            "version": self.config["version"],
            "default_strategy": self.config["sharding"]["default_strategy"],
            "current_strategy": self.current_strategy,
            "auto_select": self.config["sharding"]["auto_select"],
            "available_strategies": [s["name"] for s in self.config["shard_strategies"]],
            "supported_models": list(self.config["model_specific"].keys()),
            "enable_dynamic": self.enable_dynamic,
            "memory_available": self.memory_manager.get_available_memory(),
            "layer_dependencies_count": len(self.config["sharding"]["layer_dependencies"]),
            "strategy_history_count": len(self.strategy_history)
        } 