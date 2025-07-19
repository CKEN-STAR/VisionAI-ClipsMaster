"""分片预加载系统

此模块提供智能的模型分片预加载功能，包括：
1. 后台异步预加载
2. 基于使用模式的预测
3. 资源感知加载
4. 依赖关系处理
5. 多策略预加载
"""

import os
import gc
import time
import threading
import asyncio
import psutil
import queue
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Callable
from collections import defaultdict, deque
from pathlib import Path
from loguru import logger

import torch

from src.sharding.cache_manager import ShardManager, ShardCache
from src.sharding.metadata_manager import MetadataManager


class PreloadStrategy(Enum):
    """预加载策略枚举"""
    SEQUENTIAL = "sequential"    # 按顺序预加载下一个分片
    DEPENDENCY = "dependency"    # 基于依赖关系预加载
    FREQUENCY = "frequency"      # 基于使用频率预加载
    HYBRID = "hybrid"            # 混合策略


class PreloaderState(Enum):
    """预加载器状态枚举"""
    IDLE = "idle"                # 空闲状态
    RUNNING = "running"          # 运行中
    PAUSED = "paused"            # 暂停
    STOPPED = "stopped"          # 已停止


class ShardPreloader:
    """分片预加载器
    
    在系统资源允许的情况下，智能预加载可能需要的模型分片。
    """
    
    def __init__(
        self,
        shard_manager: ShardManager,
        strategy: PreloadStrategy = PreloadStrategy.HYBRID,
        max_cpu_usage: float = 30.0,      # 最大CPU使用率（百分比）
        max_memory_usage: float = 75.0,   # 最大内存使用率（百分比）
        max_preload_shards: int = 3,      # 最大同时预加载分片数
        check_interval: float = 2.0,      # 资源检查间隔（秒）
        history_file: Optional[str] = None # 使用历史记录文件
    ):
        """初始化分片预加载器
        
        Args:
            shard_manager: 分片管理器实例
            strategy: 预加载策略
            max_cpu_usage: 最大CPU使用率，超过此值将暂停预加载
            max_memory_usage: 最大内存使用率，超过此值将暂停预加载
            max_preload_shards: 最大同时预加载分片数
            check_interval: 资源检查间隔（秒）
            history_file: 使用历史记录文件，用于频率预测
        """
        self.shard_manager = shard_manager
        self.strategy = strategy
        self.max_cpu_usage = max_cpu_usage
        self.max_memory_usage = max_memory_usage
        self.max_preload_shards = max_preload_shards
        self.check_interval = check_interval
        
        # 历史记录文件
        if history_file is None:
            history_file = f".{self.shard_manager.model_name}_preload_history.json"
        self.history_file = Path(history_file)
        
        # 预加载队列和状态
        self.preload_queue = queue.PriorityQueue()  # 优先级队列
        self.preloading = set()  # 正在预加载的分片IDs
        self.preloaded = set()   # 已预加载的分片IDs
        self.state = PreloaderState.IDLE
        
        # 使用历史和频率
        self.access_history = deque(maxlen=100)  # 最近100次访问记录
        self.access_frequency = defaultdict(int)  # 分片访问频率
        self.sequential_patterns = []  # 顺序访问模式
        
        # 后台线程
        self._preload_thread = None
        self._thread_running = False
        self._lock = threading.RLock()
        
        # 加载历史记录
        self._load_history()
        
        logger.info(f"分片预加载器初始化完成，策略: {strategy.value}")
    
    def start(self):
        """启动预加载线程"""
        if self._preload_thread is not None and self._thread_running:
            logger.warning("预加载线程已经在运行中")
            return
        
        self._thread_running = True
        self._preload_thread = threading.Thread(
            target=self._preload_worker,
            daemon=True  # 设为守护线程，主线程结束时自动结束
        )
        self._preload_thread.start()
        
        self.state = PreloaderState.RUNNING
        logger.info("预加载线程已启动")
    
    def stop(self):
        """停止预加载线程"""
        self._thread_running = False
        if self._preload_thread is not None:
            # 等待线程结束
            if self._preload_thread.is_alive():
                self._preload_thread.join(timeout=2.0)
            self._preload_thread = None
        
        self.state = PreloaderState.STOPPED
        logger.info("预加载线程已停止")
    
    def pause(self):
        """暂停预加载"""
        self.state = PreloaderState.PAUSED
        logger.info("预加载已暂停")
    
    def resume(self):
        """恢复预加载"""
        if self.state == PreloaderState.PAUSED:
            self.state = PreloaderState.RUNNING
            logger.info("预加载已恢复")
    
    def record_access(self, shard_id: str):
        """记录分片访问
        
        用于跟踪分片使用模式，改进预测
        
        Args:
            shard_id: 分片ID
        """
        with self._lock:
            current_time = time.time()
            
            # 记录访问历史
            self.access_history.append((shard_id, current_time))
            
            # 更新访问频率
            self.access_frequency[shard_id] += 1
            
            # 更新顺序模式
            self._update_sequential_patterns(shard_id)
            
            # 保存历史记录
            self._save_history()
    
    def _update_sequential_patterns(self, current_shard_id: str):
        """更新顺序访问模式
        
        Args:
            current_shard_id: 当前访问的分片ID
        """
        if len(self.access_history) < 2:
            return
        
        # 获取前一个访问的分片
        prev_shard_id = self.access_history[-2][0]
        
        # 更新顺序模式
        pattern_found = False
        for i, (shard1, shard2, count) in enumerate(self.sequential_patterns):
            if shard1 == prev_shard_id and shard2 == current_shard_id:
                # 更新已有模式的计数
                self.sequential_patterns[i] = (shard1, shard2, count + 1)
                pattern_found = True
                break
        
        if not pattern_found:
            # 添加新的顺序模式
            self.sequential_patterns.append((prev_shard_id, current_shard_id, 1))
        
        # 按计数排序模式
        self.sequential_patterns.sort(key=lambda x: x[2], reverse=True)
    
    def _check_resources(self) -> bool:
        """检查系统资源是否允许预加载
        
        Returns:
            bool: 是否可以预加载
        """
        # 检查CPU使用率
        cpu_usage = psutil.cpu_percent()
        if cpu_usage > self.max_cpu_usage:
            logger.debug(f"CPU使用率过高: {cpu_usage}%，暂停预加载")
            return False
        
        # 检查内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        if memory_usage > self.max_memory_usage:
            logger.debug(f"内存使用率过高: {memory_usage}%，暂停预加载")
            return False
        
        # 检查GPU内存（如果有）
        if torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_memory_allocated = torch.cuda.memory_allocated(device) / (1024**3)  # GB
            gpu_memory_total = torch.cuda.get_device_properties(device).total_memory / (1024**3)  # GB
            gpu_usage = (gpu_memory_allocated / gpu_memory_total) * 100
            
            if gpu_usage > self.max_memory_usage:
                logger.debug(f"GPU内存使用率过高: {gpu_usage:.2f}%，暂停预加载")
                return False
        
        return True
    
    def predict_next_shard(self, current_shard_id: Optional[str] = None) -> List[str]:
        """预测下一个需要加载的分片
        
        Args:
            current_shard_id: 当前分片ID，如果为None，则基于历史预测
            
        Returns:
            List[str]: 预测的下一个分片ID列表，按优先级排序
        """
        predicted_shards = []
        
        # 如果当前没有分片信息，使用最近访问的分片
        if current_shard_id is None and self.access_history:
            current_shard_id = self.access_history[-1][0]
        
        # 如果没有任何访问历史，返回空列表
        if current_shard_id is None:
            return []
        
        # 根据策略预测
        if self.strategy == PreloadStrategy.SEQUENTIAL:
            # 基于顺序关系预测
            predicted_shards = self._predict_sequential(current_shard_id)
        elif self.strategy == PreloadStrategy.DEPENDENCY:
            # 基于依赖关系预测
            predicted_shards = self._predict_dependency(current_shard_id)
        elif self.strategy == PreloadStrategy.FREQUENCY:
            # 基于使用频率预测
            predicted_shards = self._predict_frequency()
        else:  # HYBRID
            # 混合策略，结合上述方法
            seq_predictions = self._predict_sequential(current_shard_id)
            dep_predictions = self._predict_dependency(current_shard_id)
            freq_predictions = self._predict_frequency()
            
            # 合并预测结果，去重
            seen = set()
            for pred_list in [seq_predictions, dep_predictions, freq_predictions]:
                for shard_id in pred_list:
                    if shard_id not in seen:
                        predicted_shards.append(shard_id)
                        seen.add(shard_id)
        
        # 过滤掉已加载和正在加载的分片
        filtered_shards = [
            shard_id for shard_id in predicted_shards
            if (shard_id not in self.preloaded and 
                shard_id not in self.preloading and
                not self.shard_manager.shard_cache.contains(shard_id))
        ]
        
        return filtered_shards
    
    def _predict_sequential(self, current_shard_id: str) -> List[str]:
        """基于顺序关系预测下一个分片
        
        Args:
            current_shard_id: 当前分片ID
            
        Returns:
            List[str]: 预测的下一个分片ID列表
        """
        next_shards = []
        
        # 从顺序模式中查找
        for shard1, shard2, count in self.sequential_patterns:
            if shard1 == current_shard_id:
                next_shards.append(shard2)
        
        # 如果没有找到顺序模式，尝试基于索引预测
        if not next_shards:
            # 从分片ID提取数字部分（假设格式为"shard_X"）
            try:
                current_index = int(current_shard_id.split('_')[-1])
                next_index = current_index + 1
                next_shard_id = f"shard_{next_index}"
                
                # 检查下一个分片是否存在
                if self.shard_manager.metadata.get_shard(next_shard_id) is not None:
                    next_shards.append(next_shard_id)
            except (ValueError, IndexError):
                # 如果分片ID格式不匹配，忽略
                pass
        
        return next_shards
    
    def _predict_dependency(self, current_shard_id: str) -> List[str]:
        """基于依赖关系预测下一个分片
        
        Args:
            current_shard_id: 当前分片ID
            
        Returns:
            List[str]: 预测的下一个分片ID列表
        """
        next_shards = []
        
        # 查找依赖于当前分片的其他分片
        metadata = self.shard_manager.metadata
        if metadata:
            for shard_id, shard_info in metadata.get_shards().items():
                depends_on = shard_info.get("depends_on", [])
                if current_shard_id in depends_on:
                    next_shards.append(shard_id)
        
        return next_shards
    
    def _predict_frequency(self) -> List[str]:
        """基于使用频率预测下一个分片
        
        Returns:
            List[str]: 预测的下一个分片ID列表
        """
        # 按访问频率排序分片
        sorted_shards = sorted(
            self.access_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回频率最高的分片
        return [shard_id for shard_id, _ in sorted_shards[:self.max_preload_shards]]
    
    def background_preload(self):
        """执行后台预加载
        
        根据当前状态和系统资源，预加载预测的分片
        """
        # 检查是否有分片需要预加载
        if self.preload_queue.empty():
            # 预测下一批需要预加载的分片
            next_shards = self.predict_next_shard()
            
            # 将预测的分片加入预加载队列
            for i, shard_id in enumerate(next_shards):
                # 优先级为索引（越小优先级越高）
                self.preload_queue.put((i, shard_id))
        
        # 检查是否可以进行预加载
        if (self.state != PreloaderState.RUNNING or
            len(self.preloading) >= self.max_preload_shards or
            not self._check_resources()):
            return
        
        # 从队列获取下一个要预加载的分片
        try:
            _, shard_id = self.preload_queue.get_nowait()
            
            # 标记为正在预加载
            self.preloading.add(shard_id)
            
            # 开始预加载
            try:
                # 注意：这是同步操作，但在后台线程中执行
                logger.debug(f"开始预加载分片: {shard_id}")
                self.shard_manager.load_shard(shard_id, recursive=False)
                
                # 预加载成功
                self.preloaded.add(shard_id)
                logger.info(f"分片预加载成功: {shard_id}")
                
            except Exception as e:
                logger.error(f"分片预加载失败: {shard_id}, 错误: {str(e)}")
                
            finally:
                # 标记预加载完成
                self.preloading.remove(shard_id)
                self.preload_queue.task_done()
                
        except queue.Empty:
            # 队列为空，没有要预加载的分片
            pass
    
    def _preload_worker(self):
        """预加载工作线程
        
        在后台持续执行预加载任务
        """
        logger.info("预加载工作线程已启动")
        
        while self._thread_running:
            try:
                # 如果状态为运行中，执行预加载
                if self.state == PreloaderState.RUNNING:
                    self.background_preload()
                
                # 等待一段时间再检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"预加载线程出错: {str(e)}")
                # 出错后等待更长时间后重试
                time.sleep(self.check_interval * 2)
        
        logger.info("预加载工作线程已停止")
    
    def _load_history(self):
        """加载历史记录"""
        if not self.history_file.exists():
            return
        
        try:
            import json
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                
                # 加载访问频率
                self.access_frequency = defaultdict(int, data.get('frequency', {}))
                
                # 加载顺序模式
                self.sequential_patterns = data.get('sequential_patterns', [])
                
                # 加载访问历史
                history = data.get('history', [])
                self.access_history = deque(history, maxlen=100)
                
                logger.info(f"已加载预加载历史记录: {self.history_file}")
                
        except Exception as e:
            logger.error(f"加载历史记录失败: {str(e)}")
    
    def _save_history(self):
        """保存历史记录"""
        try:
            import json
            
            data = {
                'frequency': dict(self.access_frequency),
                'sequential_patterns': self.sequential_patterns,
                'history': list(self.access_history)
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f)
                
            logger.debug(f"已保存预加载历史记录: {self.history_file}")
            
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")
    
    def get_preload_stats(self) -> Dict[str, Any]:
        """获取预加载统计信息
        
        Returns:
            Dict[str, Any]: 预加载统计信息
        """
        return {
            'state': self.state.value,
            'preloading': list(self.preloading),
            'preloaded': list(self.preloaded),
            'queue_size': self.preload_queue.qsize(),
            'access_history_size': len(self.access_history),
            'unique_shards_accessed': len(self.access_frequency),
            'sequential_patterns': len(self.sequential_patterns)
        }
    
    def __del__(self):
        """析构函数"""
        self.stop()
        

def get_cpu_usage() -> float:
    """获取CPU使用率
    
    Returns:
        float: CPU使用率（百分比）
    """
    return psutil.cpu_percent()


def predict_next_shard(current_shard: str, metadata_manager: MetadataManager, model_name: str) -> str:
    """预测下一个分片
    
    基于当前处理进度预测下个分片
    
    Args:
        current_shard: 当前分片ID
        metadata_manager: 元数据管理器
        model_name: 模型名称
        
    Returns:
        str: 预测的下一个分片ID
    """
    # 获取模型元数据
    metadata = metadata_manager.get_metadata(model_name)
    if not metadata:
        return ""
    
    # 获取所有分片ID
    all_shards = list(metadata.get_shards().keys())
    if not all_shards:
        return ""
    
    # 寻找当前分片的索引
    try:
        current_index = all_shards.index(current_shard)
        # 获取下一个分片（如果存在）
        if current_index + 1 < len(all_shards):
            return all_shards[current_index + 1]
    except ValueError:
        # 当前分片不在列表中
        pass
    
    # 没有找到下一个分片，尝试通过依赖关系查找
    if metadata:
        for shard_id, shard_info in metadata.get_shards().items():
            depends_on = shard_info.get("depends_on", [])
            if current_shard in depends_on:
                return shard_id
    
    # 无法预测下一个分片
    return ""


def background_preload():
    """空闲时预加载可能需要的分片
    
    当CPU使用率低时，预测并异步加载下一个可能需要的分片。
    """
    # 检查CPU使用率
    if get_cpu_usage() < 30:  # CPU使用率<30%时认为空闲
        # 这里通常会从全局上下文获取当前处理的分片和模型信息
        # 在实际应用中，需要适当修改以获取正确的上下文
        try:
            from src.sharding.context import get_current_context
            context = get_current_context()
            
            if context and context.current_shard:
                # 预测下一个分片
                next_shard = predict_next_shard(
                    context.current_shard,
                    context.metadata_manager,
                    context.model_name
                )
                
                if next_shard:
                    # 异步加载预测的分片
                    logger.info(f"后台预加载分片: {next_shard}")
                    context.shard_manager.load_shard(next_shard, recursive=False)
        except (ImportError, AttributeError) as e:
            logger.debug(f"获取上下文失败: {str(e)}")
            # 当上下文管理器不可用时，无法执行预加载 