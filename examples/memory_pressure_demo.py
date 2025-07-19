#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存压力生成器演示
-----------------
展示如何使用内存压力生成器测试应用在不同内存压力下的表现
"""

import os
import sys
import time
import argparse
import threading
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("memory_pressure_demo")

# 添加父目录到导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入内存压力生成器
try:
    from tests.memory_pressurer import get_memory_pressurer
except ImportError:
    logger.error("无法导入内存压力生成器，请确保tests/memory_pressurer.py存在")
    sys.exit(1)

# 导入内存安全框架组件
try:
    from core.safe_executor import SafeExecutor, MemoryThresholdExceeded
    from core.recovery_manager import RecoveryManager
    from core.effect_validator import EffectValidator
    from core.event_tracer import EventTracer
except ImportError:
    logger.error("无法导入内存安全框架组件，请确保它们存在")
    sys.exit(1)


class PressureDemoApp:
    """内存压力生成器演示应用"""
    
    def __init__(self):
        """初始化演示应用"""
        # 初始化内存压力生成器
        self.pressurer = get_memory_pressurer()
        
        # 初始化内存安全框架组件
        self.recovery_manager = RecoveryManager()
        self.effect_validator = EffectValidator()
        self.event_tracer = EventTracer()
        
        # 使用4GB限制的安全执行器
        self.safe_executor = SafeExecutor(
            memory_threshold_mb=3500,  # 警告阈值: 3.5GB
            critical_threshold_mb=3800,  # 临界阈值: 3.8GB
            recovery_manager=self.recovery_manager,
            effect_validator=self.effect_validator,
            event_tracer=self.event_tracer
        )
        
        # 监控线程
        self.monitor_thread = None
        self.stop_monitor = threading.Event()
        
        logger.info("演示应用初始化完成")
    
    def run_with_pressure(self,
                       pattern: str,
                       test_func: callable,
                       **kwargs) -> None:
        """
        在内存压力下运行测试函数
        
        Args:
            pattern: 压力模式
            test_func: 要运行的测试函数
            **kwargs: 传递给压力生成器的参数
        """
        logger.info(f"开始在'{pattern}'内存压力模式下运行测试")
        
        # 启动监控线程
        self.stop_monitor.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitor_memory,
            daemon=True
        )
        self.monitor_thread.start()
        
        # 启动内存压力生成器
        pressure_thread = threading.Thread(
            target=lambda: self.pressurer.start_pressure_pattern(pattern, **kwargs),
            daemon=True
        )
        pressure_thread.start()
        
        try:
            # 等待压力开始生效
            time.sleep(2)
            
            # 在安全执行器中运行测试函数
            logger.info("开始运行测试函数")
            try:
                self.safe_executor.safe_execute(test_func)
                logger.info("测试函数执行成功完成")
            except MemoryThresholdExceeded:
                logger.warning("测试函数被内存安全框架中断")
            
        except KeyboardInterrupt:
            logger.info("用户中断测试")
        finally:
            # 停止内存压力
            logger.info("停止内存压力")
            self.pressurer.stop_pressure()
            
            # 停止监控
            self.stop_monitor.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=3)
                
            # 释放所有内存
            self.pressurer.release_all_memory()
            
            # 等待系统内存恢复
            time.sleep(1)
            
            # 显示测试结果摘要
            self._print_test_summary()
    
    def _monitor_memory(self) -> None:
        """内存使用监控线程"""
        import psutil

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        
        logger.info("内存监控线程启动")
        
        # 记录历史数据
        history = []
        
        while not self.stop_monitor.is_set():
            # 获取当前内存使用情况
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # 记录数据
            history.append(memory_mb)
            
            # 输出当前内存使用
            logger.debug(f"当前内存使用: {memory_mb:.1f}MB")
            
            # 每秒采样一次
            time.sleep(1)
            
        # 计算统计数据
        if history:
            avg_memory = sum(history) / len(history)
            max_memory = max(history)
            min_memory = min(history)
            logger.info(f"内存监控结束: 平均={avg_memory:.1f}MB, 最大={max_memory:.1f}MB, 最小={min_memory:.1f}MB")
    
    def _print_test_summary(self) -> None:
        """打印测试结果摘要"""
        # 获取事件追踪器的摘要
        summary = self.event_tracer.get_summary()
        
        print("\n======= 测试结果摘要 =======")
        print(f"总事件数: {summary['total_events']}")
        print(f"熔断次数: {summary['circuit_breaks']}")
        print(f"熔断重置次数: {summary['circuit_resets']}")
        print(f"恢复尝试次数: {summary['recovery_attempts']}")
        print(f"成功恢复次数: {summary['successful_recoveries']}")
        
        if summary['recovery_attempts'] > 0:
            success_rate = summary['successful_recoveries'] / summary['recovery_attempts'] * 100
            print(f"恢复成功率: {success_rate:.1f}%")
            
        print(f"1小时内熔断频率: {summary['circuit_break_frequency_1h']:.2f}次/小时")
        print("============================\n")
        
        # 检查内存泄漏
        leak_report = self.effect_validator.get_leak_report()
        if leak_report:
            print("潜在的内存泄漏:")
            for func_name, stats in leak_report.items():
                print(f"  - {func_name}: 平均增加={stats['average_increase_mb']:.1f}MB, 最大增加={stats['max_increase_mb']:.1f}MB")


# 测试函数示例
def memory_intensive_task() -> None:
    """模拟内存密集型任务"""
    logger.info("开始执行内存密集型任务")
    
    # 分配一些内存
    data_blocks = []
    
    try:
        # 模拟处理大量数据
        for i in range(10):
            logger.info(f"处理数据块 {i+1}/10")
            
            # 分配200MB内存
            data = bytearray(200 * 1024 * 1024)
            
            # 处理数据(简单示例)
            for j in range(0, len(data), 1024*1024):
                data[j] = 1
                
            # 保存结果
            data_blocks.append(data)
            
            # 等待一下
            time.sleep(0.5)
            
        logger.info("内存密集型任务完成")
        
    except MemoryError:
        logger.error("内存不足，任务失败")
    finally:
        # 释放内存
        data_blocks.clear()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内存压力生成器演示")
    parser.add_argument("pattern", choices=["stepped", "spike", "sawtooth"],
                      help="压力模式: 阶梯式增长(stepped)、突发尖峰(spike)或锯齿波动(sawtooth)")
    
    parser.add_argument("--duration", type=int, default=60,
                      help="测试持续时间(秒)")
    parser.add_argument("--step-size", type=float, default=100,
                      help="阶梯模式: 每步内存增加量(MB)")
    parser.add_argument("--target-percent", type=float, default=80,
                      help="尖峰模式: 目标内存使用百分比(0-100)")
    
    args = parser.parse_args()
    
    # 创建演示应用
    app = PressureDemoApp()
    
    # 准备压力生成器参数
    kwargs = {}
    
    if args.pattern == "stepped":
        kwargs = {
            "step_size_mb": args.step_size,
            "step_interval_sec": 2.0,
            "duration_sec": args.duration
        }
    elif args.pattern == "spike":
        kwargs = {
            "target_percent": args.target_percent,
            "hold_sec": args.duration // 2
        }
    elif args.pattern == "sawtooth":
        kwargs = {
            "cycles": max(2, args.duration // 20),
            "period_sec": 20.0
        }
    
    # 运行测试
    app.run_with_pressure(args.pattern, memory_intensive_task, **kwargs)


if __name__ == "__main__":
    main() 