"""分层卸载管理器模块

此模块实现了智能的模型组件分层卸载策略，包括:
1. 组件依赖分析
2. 使用频率跟踪
3. 内存压力监控
4. 分层卸载决策
5. 状态恢复管理
"""

import time
import torch
import psutil
import os
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class ComponentType(Enum):
    """组件类型"""
    ATTENTION = "attention"      # 注意力层
    EMBEDDING = "embeddings"     # 嵌入层
    FEEDFORWARD = "feedforward"  # 前馈层
    NORMALIZATION = "norm"       # 归一化层
    HEAD = "head"               # 输出头
    OTHER = "other"             # 其他组件

@dataclass
class ComponentInfo:
    """组件信息"""
    name: str                    # 组件名称
    type: ComponentType          # 组件类型
    size: int                    # 内存占用(字节)
    dependencies: Set[str]       # 依赖组件
    last_access: float          # 最后访问时间
    access_count: int           # 访问计数
    is_loaded: bool             # 是否已加载
    checkpoint_path: str        # 检查点路径

class UnloadManager:
    """分层卸载管理器"""
    
    def __init__(self,
                 memory_threshold: float = 0.8,    # 内存阈值(占总内存比例)
                 min_access_interval: int = 300,   # 最小访问间隔(秒)
                 enable_auto_unload: bool = True): # 是否启用自动卸载
        """初始化卸载管理器
        
        Args:
            memory_threshold: 内存使用阈值
            min_access_interval: 最小访问间隔
            enable_auto_unload: 是否启用自动卸载
        """
        self.memory_threshold = memory_threshold
        self.min_access_interval = min_access_interval
        self.enable_auto_unload = enable_auto_unload
        
        # 组件注册表
        self._components: Dict[str, ComponentInfo] = {}
        
        # 组件优先级
        self._priority_scores: Dict[str, float] = {}
        
        # 卸载历史
        self._unload_history: List[Tuple[str, float]] = []
        
        # 性能统计
        self._stats = {
            "total_unloads": 0,
            "emergency_unloads": 0,
            "memory_saved": 0
        }
    
    def register_component(self,
                         name: str,
                         component_type: ComponentType,
                         size: int,
                         dependencies: Optional[Set[str]] = None,
                         checkpoint_path: Optional[str] = None):
        """注册组件
        
        Args:
            name: 组件名称
            component_type: 组件类型
            size: 内存占用
            dependencies: 依赖组件
            checkpoint_path: 检查点路径
        """
        if name in self._components:
            logger.warning(f"组件已存在: {name}")
            return
            
        self._components[name] = ComponentInfo(
            name=name,
            type=component_type,
            size=size,
            dependencies=dependencies or set(),
            last_access=time.time(),
            access_count=0,
            is_loaded=True,
            checkpoint_path=checkpoint_path or ""
        )
        
        # 初始化优先级分数
        self._update_priority(name)
    
    def access_component(self, name: str):
        """记录组件访问
        
        Args:
            name: 组件名称
        """
        if name not in self._components:
            logger.error(f"未注册的组件: {name}")
            return
            
        component = self._components[name]
        component.last_access = time.time()
        component.access_count += 1
        
        # 更新优先级
        self._update_priority(name)
        
        # 检查内存压力
        if self.enable_auto_unload:
            self._check_memory_pressure()
    
    def unload_component(self, name: str) -> bool:
        """卸载组件
        
        Args:
            name: 组件名称
            
        Returns:
            bool: 是否成功卸载
        """
        if name not in self._components:
            logger.error(f"未注册的组件: {name}")
            return False
            
        component = self._components[name]
        
        # 检查依赖
        for comp_name, comp in self._components.items():
            if name in comp.dependencies and comp.is_loaded:
                logger.warning(f"组件{name}仍被{comp_name}依赖")
                return False
        
        # 保存检查点
        if component.checkpoint_path:
            try:
                self._save_checkpoint(component)
            except Exception as e:
                logger.error(f"保存检查点失败: {str(e)}")
                return False
        
        # 执行卸载
        component.is_loaded = False
        self._stats["total_unloads"] += 1
        self._stats["memory_saved"] += component.size
        self._unload_history.append((name, time.time()))
        
        logger.info(f"已卸载组件: {name}")
        return True
    
    def reload_component(self, name: str) -> bool:
        """重新加载组件
        
        Args:
            name: 组件名称
            
        Returns:
            bool: 是否成功加载
        """
        if name not in self._components:
            logger.error(f"未注册的组件: {name}")
            return False
            
        component = self._components[name]
        
        if component.is_loaded:
            return True
            
        # 检查依赖
        for dep_name in component.dependencies:
            if dep_name not in self._components:
                logger.error(f"依赖组件不存在: {dep_name}")
                return False
            if not self._components[dep_name].is_loaded:
                if not self.reload_component(dep_name):
                    return False
        
        # 从检查点加载
        if component.checkpoint_path:
            try:
                self._load_checkpoint(component)
            except Exception as e:
                logger.error(f"加载检查点失败: {str(e)}")
                return False
        
        component.is_loaded = True
        logger.info(f"已重新加载组件: {name}")
        return True
    
    def get_unload_candidates(self, count: int = 1) -> List[str]:
        """获取卸载候选组件
        
        Args:
            count: 需要的候选数量
            
        Returns:
            List[str]: 候选组件名称列表
        """
        # 按优先级排序
        sorted_components = sorted(
            [
                (name, self._priority_scores[name])
                for name, comp in self._components.items()
                if comp.is_loaded
            ],
            key=lambda x: x[1]
        )
        
        return [name for name, _ in sorted_components[:count]]
    
    def get_component_status(self, name: str) -> Dict:
        """获取组件状态
        
        Args:
            name: 组件名称
            
        Returns:
            Dict: 组件状态信息
        """
        if name not in self._components:
            return {}
            
        component = self._components[name]
        return {
            "name": component.name,
            "type": component.type.value,
            "size": component.size,
            "is_loaded": component.is_loaded,
            "last_access": component.last_access,
            "access_count": component.access_count,
            "priority_score": self._priority_scores.get(name, 0)
        }
    
    def get_stats(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            **self._stats,
            "registered_components": len(self._components),
            "loaded_components": sum(
                1 for c in self._components.values()
                if c.is_loaded
            ),
            "total_size": sum(
                c.size for c in self._components.values()
                if c.is_loaded
            )
        }
    
    def _update_priority(self, name: str):
        """更新组件优先级
        
        Args:
            name: 组件名称
        """
        if name not in self._components:
            return
            
        component = self._components[name]
        current_time = time.time()
        
        # 计算优先级分数
        time_factor = 1.0 / (current_time - component.last_access + 1)
        freq_factor = 1.0 / (component.access_count + 1)
        type_weight = self._get_type_weight(component.type)
        dep_weight = len(component.dependencies) * 0.1
        
        # 优先级分数 = 时间因子 * 0.4 + 频率因子 * 0.3 + 类型权重 * 0.2 + 依赖权重 * 0.1
        priority = (
            time_factor * 0.4 +
            freq_factor * 0.3 +
            type_weight * 0.2 +
            dep_weight * 0.1
        )
        
        self._priority_scores[name] = priority
    
    def _get_type_weight(self, component_type: ComponentType) -> float:
        """获取组件类型权重
        
        Args:
            component_type: 组件类型
            
        Returns:
            float: 权重值
        """
        weights = {
            ComponentType.ATTENTION: 0.8,
            ComponentType.EMBEDDING: 0.7,
            ComponentType.FEEDFORWARD: 0.6,
            ComponentType.NORMALIZATION: 0.4,
            ComponentType.HEAD: 0.3,
            ComponentType.OTHER: 0.2
        }
        return weights.get(component_type, 0.1)
    
    def _check_memory_pressure(self):
        """检查内存压力"""
        memory = psutil.virtual_memory()
        if memory.percent >= self.memory_threshold * 100:
            # 触发紧急卸载
            candidates = self.get_unload_candidates(count=3)
            for name in candidates:
                if self.unload_component(name):
                    self._stats["emergency_unloads"] += 1
    
    def _save_checkpoint(self, component: ComponentInfo):
        """保存组件检查点
        
        Args:
            component: 组件信息
        """
        if not component.checkpoint_path:
            return
            
        try:
            # 确保检查点目录存在
            checkpoint_dir = os.path.dirname(component.checkpoint_path)
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            # 获取组件状态
            state_dict = {
                'name': component.name,
                'type': component.type.value,
                'size': component.size,
                'dependencies': list(component.dependencies),
                'last_access': component.last_access,
                'access_count': component.access_count,
                'model_state': None  # 将在实际使用时由外部设置
            }
            
            # 保存检查点
            torch.save(state_dict, component.checkpoint_path)
            logger.info(f"已保存组件检查点: {component.name}")
            
        except Exception as e:
            logger.error(f"保存检查点失败 {component.name}: {str(e)}")
            raise
    
    def _load_checkpoint(self, component: ComponentInfo):
        """加载组件检查点
        
        Args:
            component: 组件信息
        """
        if not component.checkpoint_path:
            return
            
        try:
            # 检查检查点文件是否存在
            if not os.path.exists(component.checkpoint_path):
                raise FileNotFoundError(f"检查点文件不存在: {component.checkpoint_path}")
            
            # 加载检查点
            state_dict = torch.load(component.checkpoint_path, map_location='cpu')
            
            # 验证检查点
            if state_dict['name'] != component.name:
                raise ValueError(f"检查点名称不匹配: {state_dict['name']} != {component.name}")
            
            # 恢复组件状态
            component.last_access = state_dict['last_access']
            component.access_count = state_dict['access_count']
            component.dependencies = set(state_dict['dependencies'])
            
            # model_state将在实际使用时由外部处理
            logger.info(f"已加载组件检查点: {component.name}")
            
            return state_dict.get('model_state')
            
        except Exception as e:
            logger.error(f"加载检查点失败 {component.name}: {str(e)}")
            raise
    
    def __del__(self):
        """清理资源"""
        # 保存所有未卸载组件的检查点
        for component in self._components.values():
            if component.is_loaded and component.checkpoint_path:
                try:
                    self._save_checkpoint(component)
                except Exception as e:
                    logger.error(f"保存检查点失败: {str(e)}") 