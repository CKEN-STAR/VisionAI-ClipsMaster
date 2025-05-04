"""模型预加载机制模块

此模块实现了智能的模型预加载策略，包括：
1. 使用模式分析
2. 资源预测
3. 优先级调度
4. 后台预加载
5. 自适应策略
"""

import os
import time
import json
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from src.utils.memory_manager import MemoryManager
from src.utils.device_manager import HybridDevice
from src.core.on_demand_loader import OnDemandLoader

class PreloadStrategy:
    """预加载策略类"""
    FREQUENCY = "frequency"      # 基于使用频率
    SEQUENCE = "sequence"        # 基于使用顺序
    SCHEDULE = "schedule"        # 基于时间计划
    ADAPTIVE = "adaptive"        # 自适应策略

class ModelPreloader:
    """模型预加载器"""
    
    def __init__(self,
                 loader: OnDemandLoader,
                 strategy: str = PreloadStrategy.ADAPTIVE,
                 history_file: str = "preload_history.json",
                 min_memory_available: float = 0.3):  # 最小可用内存比例
        """初始化预加载器
        
        Args:
            loader: 按需加载器实例
            strategy: 预加载策略
            history_file: 历史记录文件
            min_memory_available: 最小可用内存比例
        """
        self.loader = loader
        self.strategy = strategy
        self.history_file = Path(history_file)
        self.min_memory_available = min_memory_available
        
        # 初始化组件
        self.memory_manager = MemoryManager()
        self.device_manager = HybridDevice()
        
        # 使用统计
        self.usage_history = defaultdict(list)  # 模型使用历史
        self.usage_patterns = defaultdict(int)  # 使用模式统计
        self.model_sequences = []               # 模型使用序列
        self.scheduled_loads = {}               # 计划加载时间
        
        # 预加载状态
        self.preloading = set()                # 正在预加载的模型
        self.preloaded = set()                 # 已预加载的模型
        
        # 加载历史记录
        self._load_history()
        
        # 启动预加载线程
        self._start_preload_thread()
    
    def record_usage(self, model_name: str):
        """记录模型使用
        
        Args:
            model_name: 模型名称
        """
        current_time = time.time()
        
        # 更新使用历史
        self.usage_history[model_name].append(current_time)
        
        # 更新使用频率
        self.usage_patterns[model_name] += 1
        
        # 更新使用序列
        self.model_sequences.append((model_name, current_time))
        
        # 清理旧记录
        self._cleanup_old_records()
        
        # 保存历史记录
        self._save_history()
        
        # 触发预加载分析
        self._analyze_and_preload()
    
    def schedule_preload(self,
                        model_name: str,
                        schedule_time: datetime):
        """计划预加载
        
        Args:
            model_name: 模型名称
            schedule_time: 计划加载时间
        """
        self.scheduled_loads[model_name] = schedule_time
    
    async def preload_models(self, model_names: List[str]):
        """主动预加载模型
        
        Args:
            model_names: 模型名称列表
        """
        # 检查资源
        if not self._check_resources():
            logger.warning("资源不足，跳过预加载")
            return
        
        # 按优先级排序
        prioritized_models = self._prioritize_models(model_names)
        
        # 异步预加载
        tasks = []
        for model_name in prioritized_models:
            if model_name not in self.preloading and model_name not in self.preloaded:
                self.preloading.add(model_name)
                task = asyncio.create_task(self._preload_model(model_name))
                tasks.append(task)
        
        # 等待完成
        if tasks:
            await asyncio.gather(*tasks)
    
    async def _preload_model(self, model_name: str):
        """预加载单个模型
        
        Args:
            model_name: 模型名称
        """
        try:
            await self.loader.preload_model(model_name)
            self.preloaded.add(model_name)
            logger.info(f"预加载模型成功: {model_name}")
            
        except Exception as e:
            logger.error(f"预加载模型失败: {model_name}, 错误: {str(e)}")
            
        finally:
            self.preloading.remove(model_name)
    
    def _analyze_and_preload(self):
        """分析使用模式并触发预加载"""
        if self.strategy == PreloadStrategy.FREQUENCY:
            # 基于使用频率预测
            next_models = self._predict_by_frequency()
        elif self.strategy == PreloadStrategy.SEQUENCE:
            # 基于使用序列预测
            next_models = self._predict_by_sequence()
        elif self.strategy == PreloadStrategy.SCHEDULE:
            # 基于时间计划预测
            next_models = self._predict_by_schedule()
        else:  # ADAPTIVE
            # 综合多种策略
            next_models = self._predict_adaptive()
        
        # 触发预加载
        if next_models:
            asyncio.create_task(self.preload_models(next_models))
    
    def _predict_by_frequency(self) -> List[str]:
        """基于使用频率预测下一个模型"""
        # 获取使用频率最高的模型
        sorted_models = sorted(
            self.usage_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回前N个未加载的模型
        return [
            model for model, _ in sorted_models
            if model not in self.preloaded and model not in self.preloading
        ][:3]
    
    def _predict_by_sequence(self) -> List[str]:
        """基于使用序列预测下一个模型"""
        if not self.model_sequences:
            return []
        
        # 分析最近的使用序列
        recent_sequence = [model for model, _ in self.model_sequences[-5:]]
        
        # 查找相似序列
        next_models = set()
        for i in range(len(self.model_sequences) - 5):
            sequence = [model for model, _ in self.model_sequences[i:i+5]]
            if sequence == recent_sequence:
                if i + 5 < len(self.model_sequences):
                    next_model = self.model_sequences[i+5][0]
                    if (next_model not in self.preloaded and 
                        next_model not in self.preloading):
                        next_models.add(next_model)
        
        return list(next_models)
    
    def _predict_by_schedule(self) -> List[str]:
        """基于时间计划预测下一个模型"""
        current_time = datetime.now()
        next_models = []
        
        # 检查计划加载时间
        for model_name, schedule_time in self.scheduled_loads.items():
            if (schedule_time - current_time).total_seconds() <= 300:  # 5分钟内
                if (model_name not in self.preloaded and 
                    model_name not in self.preloading):
                    next_models.append(model_name)
        
        return next_models
    
    def _predict_adaptive(self) -> List[str]:
        """自适应预测策略"""
        next_models = set()
        
        # 综合多种预测结果
        frequency_models = set(self._predict_by_frequency())
        sequence_models = set(self._predict_by_sequence())
        schedule_models = set(self._predict_by_schedule())
        
        # 优先级：计划 > 序列 > 频率
        next_models.update(schedule_models)
        next_models.update(sequence_models)
        next_models.update(frequency_models)
        
        return list(next_models)
    
    def _prioritize_models(self, model_names: List[str]) -> List[str]:
        """对模型进行优先级排序
        
        Args:
            model_names: 模型名称列表
            
        Returns:
            List[str]: 排序后的模型列表
        """
        # 计算每个模型的优先级分数
        scores = {}
        for model_name in model_names:
            score = 0
            
            # 基于使用频率
            score += self.usage_patterns.get(model_name, 0) * 0.5
            
            # 基于最近使用时间
            if model_name in self.usage_history:
                last_use = max(self.usage_history[model_name])
                time_diff = time.time() - last_use
                score += max(0, 1 - time_diff / 86400)  # 24小时内递减
            
            # 基于计划时间
            if model_name in self.scheduled_loads:
                schedule_time = self.scheduled_loads[model_name]
                if schedule_time > datetime.now():
                    time_diff = (schedule_time - datetime.now()).total_seconds()
                    if time_diff <= 300:  # 5分钟内
                        score += 2
            
            scores[model_name] = score
        
        # 按分数排序
        return sorted(model_names, key=lambda x: scores[x], reverse=True)
    
    def _check_resources(self) -> bool:
        """检查是否有足够资源进行预加载"""
        # 检查内存使用情况
        memory_info = self.memory_manager.get_memory_stats()
        available_ratio = memory_info["available"] / memory_info["total"]
        
        return available_ratio >= self.min_memory_available
    
    def _cleanup_old_records(self):
        """清理旧记录"""
        current_time = time.time()
        cutoff_time = current_time - 7 * 24 * 3600  # 7天前
        
        # 清理使用历史
        for model_name in list(self.usage_history.keys()):
            self.usage_history[model_name] = [
                t for t in self.usage_history[model_name]
                if t > cutoff_time
            ]
            if not self.usage_history[model_name]:
                del self.usage_history[model_name]
        
        # 清理使用序列
        self.model_sequences = [
            (model, t) for model, t in self.model_sequences
            if t > cutoff_time
        ]
        
        # 清理计划加载
        current_datetime = datetime.now()
        self.scheduled_loads = {
            model: time for model, time in self.scheduled_loads.items()
            if time > current_datetime
        }
    
    def _load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.usage_history = defaultdict(list, data.get("usage_history", {}))
                    self.usage_patterns = defaultdict(int, data.get("usage_patterns", {}))
                    self.model_sequences = data.get("model_sequences", [])
                    self.scheduled_loads = {
                        k: datetime.fromisoformat(v)
                        for k, v in data.get("scheduled_loads", {}).items()
                    }
            except Exception as e:
                logger.error(f"加载历史记录失败: {str(e)}")
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    "usage_history": dict(self.usage_history),
                    "usage_patterns": dict(self.usage_patterns),
                    "model_sequences": self.model_sequences,
                    "scheduled_loads": {
                        k: v.isoformat()
                        for k, v in self.scheduled_loads.items()
                    }
                }, f, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")
    
    def _start_preload_thread(self):
        """启动预加载监控线程"""
        def monitor_routine():
            while True:
                try:
                    # 分析并触发预加载
                    self._analyze_and_preload()
                    
                    # 清理过期记录
                    self._cleanup_old_records()
                    
                    # 每5分钟运行一次
                    time.sleep(300)
                    
                except Exception as e:
                    logger.error(f"预加载监控异常: {str(e)}")
                    time.sleep(300)
        
        # 启动监控线程
        threading.Thread(target=monitor_routine, daemon=True).start()
    
    def get_preload_stats(self) -> Dict:
        """获取预加载统计信息
        
        Returns:
            Dict: 预加载统计
        """
        return {
            "strategy": self.strategy,
            "preloading_models": list(self.preloading),
            "preloaded_models": list(self.preloaded),
            "usage_patterns": dict(self.usage_patterns),
            "scheduled_loads": {
                k: v.isoformat()
                for k, v in self.scheduled_loads.items()
            }
        }
    
    def __del__(self):
        """保存历史记录"""
        self._save_history() 