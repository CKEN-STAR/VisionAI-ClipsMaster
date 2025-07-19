"""分片加载适配器

此模块提供分片加载适配器，连接分片管理器与按需加载引擎，
实现模型分片的高效管理和加载。
"""

import os
from typing import Dict, List, Optional, Any, Set, Union
from loguru import logger

from src.core.on_demand_loader import OnDemandLoader, ModelLoadRequest
from src.sharding.cache_manager import ShardManager
from src.sharding.metadata_manager import MetadataManager


class ShardLoaderAdapter:
    """分片加载适配器
    
    连接分片管理器与按需加载引擎，协调模型分片的加载和管理。
    """
    
    def __init__(
        self,
        on_demand_loader: Optional[OnDemandLoader] = None,
        metadata_manager: Optional[MetadataManager] = None,
        shard_managers: Optional[Dict[str, ShardManager]] = None,
        max_shards_per_model: int = 5,
        models_dir: str = "models",
        cache_dir: str = ".cache"
    ):
        """初始化分片加载适配器
        
        Args:
            on_demand_loader: 按需加载引擎
            metadata_manager: 元数据管理器
            shard_managers: 现有的分片管理器字典 {model_name: ShardManager}
            max_shards_per_model: 每个模型的最大分片缓存数量
            models_dir: 模型目录
            cache_dir: 缓存目录
        """
        self.on_demand_loader = on_demand_loader
        self.metadata_manager = metadata_manager or MetadataManager()
        self.shard_managers = shard_managers or {}
        self.max_shards_per_model = max_shards_per_model
        self.models_dir = models_dir
        self.cache_dir = cache_dir
        
        # 跟踪当前激活的模型
        self.active_model = None
        
        # 初始化
        self._initialize()
        
        logger.info("分片加载适配器初始化完成")
    
    def _initialize(self):
        """初始化适配器
        
        为所有已安装的模型创建分片管理器
        """
        if not self.on_demand_loader:
            logger.warning("未提供按需加载引擎，部分功能将不可用")
            return
            
        # 获取所有可用模型
        available_models = self.on_demand_loader.get_available_models()
        
        # 为每个安装的模型创建分片管理器
        for model_info in available_models:
            model_name = model_info.get("name")
            
            # 跳过未安装的模型
            if not model_info.get("installed", True):
                logger.debug(f"模型 {model_name} 未安装，跳过创建分片管理器")
                continue
                
            # 如果已经有分片管理器，跳过
            if model_name in self.shard_managers:
                continue
                
            # 创建分片管理器
            self._create_shard_manager(model_name)
    
    def _create_shard_manager(self, model_name: str) -> Optional[ShardManager]:
        """为模型创建分片管理器
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[ShardManager]: 创建的分片管理器，如果创建失败则返回None
        """
        # 获取模型配置
        model_config = None
        if self.on_demand_loader:
            model_config = self.on_demand_loader.model_configs.get(model_name, {})
            
        # 获取分片目录
        shard_dir = os.path.join(self.models_dir, model_name, "shards")
        if model_config and "shard_dir" in model_config:
            shard_dir = model_config["shard_dir"]
            
        # 检查分片目录是否存在
        if not os.path.exists(shard_dir):
            # 检查是否有预定义的分片元数据
            if not self.metadata_manager.get_metadata(model_name):
                logger.debug(f"模型 {model_name} 没有分片目录和元数据，可能不使用分片加载")
                return None
                
        # 创建分片管理器
        try:
            # 模型特定的缓存目录
            model_cache_dir = os.path.join(self.cache_dir, model_name)
            
            # 获取模型建议的分片缓存大小（如果有）
            max_shards = self.max_shards_per_model
            if model_config and "max_shards_in_memory" in model_config:
                max_shards = model_config["max_shards_in_memory"]
                
            # 创建分片管理器
            shard_manager = ShardManager(
                model_name=model_name,
                max_shards_in_memory=max_shards,
                metadata_manager=self.metadata_manager,
                shard_dir=shard_dir,
                cache_dir=model_cache_dir
            )
            
            # 添加到管理器字典
            self.shard_managers[model_name] = shard_manager
            
            logger.info(f"为模型 {model_name} 创建了分片管理器，分片目录: {shard_dir}")
            
            return shard_manager
            
        except Exception as e:
            logger.error(f"为模型 {model_name} 创建分片管理器失败: {str(e)}")
            return None
    
    def get_shard_manager(self, model_name: str) -> Optional[ShardManager]:
        """获取模型的分片管理器
        
        如果管理器不存在，尝试创建
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[ShardManager]: 分片管理器
        """
        if model_name in self.shard_managers:
            return self.shard_managers[model_name]
            
        # 尝试创建
        return self._create_shard_manager(model_name)
    
    def load_model_shard(self, model_name: str, shard_id: str) -> Optional[Any]:
        """加载模型分片
        
        Args:
            model_name: 模型名称
            shard_id: 分片ID
            
        Returns:
            Optional[Any]: 加载的分片数据，如果加载失败则返回None
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            logger.error(f"模型 {model_name} 没有分片管理器")
            return None
            
        # 加载分片
        return shard_manager.load_shard(shard_id)
    
    def load_model_layer(self, model_name: str, layer_name: str) -> Optional[Any]:
        """加载模型层
        
        Args:
            model_name: 模型名称
            layer_name: 层名称
            
        Returns:
            Optional[Any]: 包含该层的分片数据，如果加载失败则返回None
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            logger.error(f"模型 {model_name} 没有分片管理器")
            return None
            
        # 获取包含该层的分片ID
        shard_id = shard_manager.get_shard_for_layer(layer_name)
        if not shard_id:
            logger.warning(f"未找到包含层 {layer_name} 的分片")
            return None
            
        # 加载包含该层的分片
        return shard_manager.load_shard(shard_id)
    
    def load_model_layers(self, model_name: str, layer_names: List[str]) -> Dict[str, Any]:
        """加载多个模型层
        
        Args:
            model_name: 模型名称
            layer_names: 层名称列表
            
        Returns:
            Dict[str, Any]: {层名称: 分片数据}
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            logger.error(f"模型 {model_name} 没有分片管理器")
            return {}
            
        # 加载包含这些层的分片
        return shard_manager.load_layers(layer_names)
    
    def prefetch_model_shards(self, model_name: str, shard_ids: List[str]) -> int:
        """预加载模型分片
        
        Args:
            model_name: 模型名称
            shard_ids: 分片ID列表
            
        Returns:
            int: 成功加载的分片数量
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            logger.error(f"模型 {model_name} 没有分片管理器")
            return 0
            
        # 预加载分片
        return shard_manager.prefetch_shards(shard_ids)
    
    def on_model_activated(self, model_name: str):
        """模型激活时调用
        
        更新当前活动模型，并预加载关键分片
        
        Args:
            model_name: 模型名称
        """
        self.active_model = model_name
        
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            return
            
        # 获取模型配置
        model_config = {}
        if self.on_demand_loader:
            model_config = self.on_demand_loader.model_configs.get(model_name, {})
            
        # 检查是否有预加载分片配置
        prefetch_shards = model_config.get("prefetch_shards", [])
        if prefetch_shards:
            logger.info(f"预加载模型 {model_name} 的关键分片: {prefetch_shards}")
            shard_manager.prefetch_shards(prefetch_shards)
    
    def on_model_deactivated(self, model_name: str):
        """模型停用时调用
        
        清理分片缓存
        
        Args:
            model_name: 模型名称
        """
        if self.active_model == model_name:
            self.active_model = None
            
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            return
            
        # 清理缓存
        shard_manager.clear_cache()
        
    def get_layer_to_shard_mapping(self, model_name: str) -> Dict[str, str]:
        """获取层到分片的映射
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, str]: {层名称: 分片ID}
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            return {}
            
        # 获取映射
        return shard_manager.get_layer_mapping()
    
    def get_model_shard_stats(self, model_name: str) -> Dict[str, Any]:
        """获取模型分片缓存统计
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        # 获取分片管理器
        shard_manager = self.get_shard_manager(model_name)
        if not shard_manager:
            return {}
            
        # 获取统计
        return shard_manager.get_cache_stats()
    
    def clear_all_caches(self):
        """清空所有模型的分片缓存"""
        for model_name, shard_manager in self.shard_managers.items():
            shard_manager.clear_cache()
            logger.info(f"已清空模型 {model_name} 的分片缓存")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，清理资源"""
        self.clear_all_caches() 