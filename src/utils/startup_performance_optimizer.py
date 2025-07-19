#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动性能优化器

专门优化VisionAI-ClipsMaster的启动性能，目标从4.74秒优化到≤3秒。
"""

import time
import threading
import logging
from typing import Dict, Any, List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc

logger = logging.getLogger(__name__)

class StartupPerformanceOptimizer:
    """启动性能优化器
    
    通过以下策略优化启动性能：
    1. 延迟加载非关键模块
    2. 并行初始化独立组件
    3. 智能预加载关键资源
    4. 内存预分配优化
    """
    
    def __init__(self):
        """初始化启动性能优化器"""
        self.start_time = time.time()
        self.critical_components = []
        self.deferred_components = []
        self.parallel_components = []
        self.preload_cache = {}
        self.initialization_times = {}
        
    def register_critical_component(self, name: str, init_func: Callable, *args, **kwargs):
        """注册关键组件（必须在启动时加载）
        
        Args:
            name: 组件名称
            init_func: 初始化函数
            *args, **kwargs: 初始化参数
        """
        self.critical_components.append({
            'name': name,
            'init_func': init_func,
            'args': args,
            'kwargs': kwargs
        })
        
    def register_deferred_component(self, name: str, init_func: Callable, *args, **kwargs):
        """注册延迟组件（可以在启动后加载）
        
        Args:
            name: 组件名称
            init_func: 初始化函数
            *args, **kwargs: 初始化参数
        """
        self.deferred_components.append({
            'name': name,
            'init_func': init_func,
            'args': args,
            'kwargs': kwargs
        })
        
    def register_parallel_component(self, name: str, init_func: Callable, *args, **kwargs):
        """注册并行组件（可以并行初始化）
        
        Args:
            name: 组件名称
            init_func: 初始化函数
            *args, **kwargs: 初始化参数
        """
        self.parallel_components.append({
            'name': name,
            'init_func': init_func,
            'args': args,
            'kwargs': kwargs
        })
    
    def optimize_imports(self):
        """优化导入性能"""
        # 预编译正则表达式
        import re
        common_patterns = [
            r'\d+',
            r'[a-zA-Z_][a-zA-Z0-9_]*',
            r'\s+',
            r'[^\w\s]'
        ]
        for pattern in common_patterns:
            re.compile(pattern)
        
        # 预加载常用模块
        import json
        import yaml
        import threading
        import queue
        
        logger.debug("导入优化完成")
    
    def initialize_critical_components(self) -> Dict[str, Any]:
        """初始化关键组件"""
        results = {}
        
        for component in self.critical_components:
            start_time = time.time()
            try:
                result = component['init_func'](*component['args'], **component['kwargs'])
                results[component['name']] = result
                
                init_time = time.time() - start_time
                self.initialization_times[component['name']] = init_time
                logger.debug(f"关键组件 {component['name']} 初始化完成，耗时: {init_time:.3f}秒")
                
            except Exception as e:
                logger.error(f"关键组件 {component['name']} 初始化失败: {e}")
                results[component['name']] = None
        
        return results
    
    def initialize_parallel_components(self) -> Dict[str, Any]:
        """并行初始化组件"""
        results = {}
        
        if not self.parallel_components:
            return results
        
        with ThreadPoolExecutor(max_workers=min(4, len(self.parallel_components))) as executor:
            # 提交所有并行任务
            future_to_component = {}
            for component in self.parallel_components:
                future = executor.submit(
                    self._initialize_component_with_timing,
                    component
                )
                future_to_component[future] = component['name']
            
            # 收集结果
            for future in as_completed(future_to_component):
                component_name = future_to_component[future]
                try:
                    result, init_time = future.result()
                    results[component_name] = result
                    self.initialization_times[component_name] = init_time
                    logger.debug(f"并行组件 {component_name} 初始化完成，耗时: {init_time:.3f}秒")
                except Exception as e:
                    logger.error(f"并行组件 {component_name} 初始化失败: {e}")
                    results[component_name] = None
        
        return results
    
    def _initialize_component_with_timing(self, component: Dict[str, Any]) -> tuple:
        """带计时的组件初始化"""
        start_time = time.time()
        try:
            result = component['init_func'](*component['args'], **component['kwargs'])
            init_time = time.time() - start_time
            return result, init_time
        except Exception as e:
            init_time = time.time() - start_time
            raise e
    
    def start_deferred_initialization(self):
        """启动延迟初始化（在后台线程中）"""
        if not self.deferred_components:
            return
        
        def deferred_init():
            for component in self.deferred_components:
                try:
                    start_time = time.time()
                    component['init_func'](*component['args'], **component['kwargs'])
                    init_time = time.time() - start_time
                    self.initialization_times[f"{component['name']}_deferred"] = init_time
                    logger.debug(f"延迟组件 {component['name']} 初始化完成，耗时: {init_time:.3f}秒")
                except Exception as e:
                    logger.error(f"延迟组件 {component['name']} 初始化失败: {e}")
        
        thread = threading.Thread(target=deferred_init, daemon=True)
        thread.start()
    
    def optimize_memory(self):
        """优化内存使用"""
        # 强制垃圾回收
        gc.collect()
        
        # 设置垃圾回收阈值
        gc.set_threshold(700, 10, 10)
        
        logger.debug("内存优化完成")
    
    def get_startup_report(self) -> Dict[str, Any]:
        """获取启动性能报告"""
        total_time = time.time() - self.start_time
        
        return {
            "total_startup_time": total_time,
            "target_achieved": total_time <= 3.0,
            "component_times": self.initialization_times,
            "critical_components": len(self.critical_components),
            "parallel_components": len(self.parallel_components),
            "deferred_components": len(self.deferred_components),
            "performance_grade": "优秀" if total_time <= 3.0 else "良好" if total_time <= 4.0 else "需改进"
        }

# 全局优化器实例
_optimizer = None

def get_startup_optimizer() -> StartupPerformanceOptimizer:
    """获取启动优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = StartupPerformanceOptimizer()
    return _optimizer

def optimize_startup_performance():
    """执行启动性能优化"""
    optimizer = get_startup_optimizer()
    
    # 优化导入
    optimizer.optimize_imports()
    
    # 优化内存
    optimizer.optimize_memory()
    
    return optimizer

# 装饰器：用于标记组件初始化函数
def critical_component(name: str):
    """标记关键组件的装饰器"""
    def decorator(func):
        optimizer = get_startup_optimizer()
        optimizer.register_critical_component(name, func)
        return func
    return decorator

def parallel_component(name: str):
    """标记并行组件的装饰器"""
    def decorator(func):
        optimizer = get_startup_optimizer()
        optimizer.register_parallel_component(name, func)
        return func
    return decorator

def deferred_component(name: str):
    """标记延迟组件的装饰器"""
    def decorator(func):
        optimizer = get_startup_optimizer()
        optimizer.register_deferred_component(name, func)
        return func
    return decorator

if __name__ == "__main__":
    # 测试启动性能优化器
    optimizer = optimize_startup_performance()
    
    # 模拟组件初始化
    def mock_critical_init():
        time.sleep(0.1)
        return "critical_ok"
    
    def mock_parallel_init():
        time.sleep(0.2)
        return "parallel_ok"
    
    def mock_deferred_init():
        time.sleep(0.3)
        return "deferred_ok"
    
    optimizer.register_critical_component("test_critical", mock_critical_init)
    optimizer.register_parallel_component("test_parallel", mock_parallel_init)
    optimizer.register_deferred_component("test_deferred", mock_deferred_init)
    
    # 执行初始化
    critical_results = optimizer.initialize_critical_components()
    parallel_results = optimizer.initialize_parallel_components()
    optimizer.start_deferred_initialization()
    
    # 等待一段时间让延迟组件完成
    time.sleep(0.5)
    
    # 获取报告
    report = optimizer.get_startup_report()
    print(f"启动性能报告: {report}")
