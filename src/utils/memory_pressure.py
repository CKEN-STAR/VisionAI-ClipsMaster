"""
内存压力动态生成器 - 用于测试和优化模型在低内存环境下的性能
提供多种压力模式和内存监控功能，与模型切换系统集成
"""

import gc
import time
import psutil
import numpy as np
import threading
import logging
from typing import List, Dict, Tuple, Optional, Callable

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryPressure")

class MemoryPressurer:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """
    内存压力动态生成器 - 用于测试和优化低配设备(4GB内存)下的模型性能
    支持多种压力模式: 阶梯式增长、突发式分配、锯齿波动
    可与模型管理系统集成，实现根据内存压力动态调整模型量化级别
    """
    
    def __init__(self, 
                safety_margin_mb: int = 500, 
                monitor_interval: float = 0.5,
                threshold_critical: float = 0.9,
                threshold_warning: float = 0.75):
        """
        初始化内存压力生成器
        
        Args:
            safety_margin_mb: 安全边际(MB)，防止系统完全耗尽内存
            monitor_interval: 内存监控间隔(秒)
            threshold_critical: 危险阈值(0-1)，超过此值触发紧急释放
            threshold_warning: 警告阈值(0-1)，超过此值触发警告
        """
        self.safety_margin_mb = safety_margin_mb
        self.monitor_interval = monitor_interval
        self.threshold_critical = threshold_critical
        self.threshold_warning = threshold_warning
        
        # 内存块存储
        self.chunks: List[bytearray] = []
        # 当前分配的总内存(MB)
        self.allocated_mb: int = 0
        # 内存监控线程
        self.monitor_thread: Optional[threading.Thread] = None
        # 停止标志
        self.stop_monitor = threading.Event()
        # 回调函数
        self.warning_callbacks: List[Callable] = []
        self.critical_callbacks: List[Callable] = []
        
    def get_system_memory_info(self) -> Dict[str, float]:
        """获取系统内存信息"""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "used_gb": memory.used / (1024**3),
            "available_gb": memory.available / (1024**3),
            "percent_used": memory.percent / 100,
            "free_mb": memory.available / (1024**2)
        }
        
    def allocate_chunk(self, size_mb: int) -> Optional[bytearray]:
        """
        分配指定大小的内存块
        
        Args:
            size_mb: 分配大小(MB)
            
        Returns:
            成功返回bytearray对象，失败返回None
        """
        try:
            # 1MB = 1024*1024字节
            chunk = bytearray(size_mb * 1024 * 1024)
            return chunk
        except MemoryError:
            logger.warning(f"内存分配失败: 无法分配{size_mb}MB")
            return None
            
    def allocate_until_full(self, chunk_size_mb: int = 128) -> int:
        """
        分配内存直到接近系统极限(用于测试系统最大可用内存)
        
        Args:
            chunk_size_mb: 每次分配的内存块大小(MB)
            
        Returns:
            成功分配的总内存大小(MB)
        """
        logger.info("开始持续分配内存直至耗尽")
        self.release_all()  # 确保开始前清空之前的分配
        
        try:
            while True:
                mem_info = self.get_system_memory_info()
                available_mb = mem_info["free_mb"]
                
                # 如果剩余内存小于安全边际，停止分配
                if available_mb < self.safety_margin_mb:
                    break
                    
                # 确定本次分配大小(不超过可用内存)
                alloc_size = min(chunk_size_mb, int(available_mb - self.safety_margin_mb))
                if alloc_size <= 0:
                    break
                    
                chunk = self.allocate_chunk(alloc_size)
                if chunk is None:
                    break
                    
                self.chunks.append(chunk)
                self.allocated_mb += alloc_size
                logger.debug(f"已分配: {self.allocated_mb}MB, 剩余: {available_mb-alloc_size}MB")
                
        except Exception as e:
            logger.error(f"内存分配异常: {str(e)}")
            
        finally:
            logger.info(f"内存分配完成: 总计{self.allocated_mb}MB")
            return self.allocated_mb
    
    def staircase_pressure(self, 
                          step_size_mb: int = 100, 
                          step_interval_sec: float = 1.0,
                          max_steps: int = 20) -> int:
        """
        阶梯式内存压力(每隔固定时间增加固定内存)
        
        Args:
            step_size_mb: 每步增加的内存(MB)
            step_interval_sec: 每步间隔时间(秒)
            max_steps: 最大步数，防止无限增长
            
        Returns:
            最终分配的内存(MB)
        """
        logger.info(f"开始阶梯式内存压力测试: 每{step_interval_sec}秒增加{step_size_mb}MB")
        self.release_all()
        
        steps = 0
        try:
            while steps < max_steps:
                mem_info = self.get_system_memory_info()
                
                # 检查是否还有足够内存分配
                if mem_info["free_mb"] < step_size_mb + self.safety_margin_mb:
                    logger.warning("可用内存不足，停止阶梯增长")
                    break
                
                # 分配本阶段内存
                chunk = self.allocate_chunk(step_size_mb)
                if chunk is None:
                    break
                    
                self.chunks.append(chunk)
                self.allocated_mb += step_size_mb
                steps += 1
                
                logger.info(f"阶梯 {steps}/{max_steps}: 已分配{self.allocated_mb}MB")
                
                # 等待间隔时间
                time.sleep(step_interval_sec)
                
        except KeyboardInterrupt:
            logger.info("用户中断阶梯式压力测试")
            
        except Exception as e:
            logger.error(f"阶梯式压力测试异常: {str(e)}")
            
        finally:
            logger.info(f"阶梯式压力测试完成: 总计{self.allocated_mb}MB，{steps}个阶梯")
            return self.allocated_mb
    
    def burst_pressure(self, 
                      target_percent: float = 0.8, 
                      burst_duration_sec: float = 5.0) -> int:
        """
        突发式内存压力(快速占用指定比例内存，保持一段时间后释放)
        
        Args:
            target_percent: 目标内存占用比例(0-1)
            burst_duration_sec: 维持高压状态时间(秒)
            
        Returns:
            峰值分配内存(MB)
        """
        logger.info(f"开始突发式内存压力测试: 目标占用{target_percent*100}%系统内存")
        self.release_all()
        
        try:
            mem_info = self.get_system_memory_info()
            total_mb = mem_info["total_gb"] * 1024
            
            # 计算需要分配的内存
            target_mb = int(total_mb * target_percent)
            current_used_mb = int((mem_info["total_gb"] - mem_info["available_gb"]) * 1024)
            allocation_needed_mb = max(0, target_mb - current_used_mb)
            
            if allocation_needed_mb <= 0:
                logger.warning(f"系统已使用内存({current_used_mb}MB)超过目标({target_mb}MB)，无需额外分配")
                return 0
                
            # 确保不会超出安全边际
            safe_allocation_mb = int(mem_info["free_mb"] - self.safety_margin_mb)
            allocation_mb = min(allocation_needed_mb, safe_allocation_mb)
            
            logger.info(f"突发分配{allocation_mb}MB内存...")
            
            # 一次性分配大块内存
            chunk = self.allocate_chunk(allocation_mb)
            if chunk is not None:
                self.chunks.append(chunk)
                self.allocated_mb = allocation_mb
                
                logger.info(f"已突发分配{self.allocated_mb}MB内存，维持{burst_duration_sec}秒")
                time.sleep(burst_duration_sec)
            else:
                logger.error("突发分配失败")
                
        except Exception as e:
            logger.error(f"突发式压力测试异常: {str(e)}")
            
        finally:
            peak_allocated = self.allocated_mb
            logger.info(f"突发式压力测试完成，释放{peak_allocated}MB内存")
            self.release_all()
            return peak_allocated
    
    def sawtooth_pressure(self, 
                         min_percent: float = 0.3,
                         max_percent: float = 0.7, 
                         cycle_duration_sec: float = 10.0,
                         num_cycles: int = 3) -> int:
        """
        锯齿波动内存压力(在最大和最小占用之间循环波动)
        
        Args:
            min_percent: 最小内存占用百分比(0-1)
            max_percent: 最大内存占用百分比(0-1)
            cycle_duration_sec: 每个周期持续时间(秒)
            num_cycles: 周期数量
            
        Returns:
            峰值分配内存(MB)
        """
        logger.info(f"开始锯齿波动压力测试: {min_percent*100}%-{max_percent*100}%, {num_cycles}个周期")
        self.release_all()
        
        peak_allocated = 0
        try:
            mem_info = self.get_system_memory_info()
            total_mb = mem_info["total_gb"] * 1024
            current_used_mb = int((mem_info["total_gb"] - mem_info["available_gb"]) * 1024)
            
            for cycle in range(num_cycles):
                # 增长阶段 - 到达最大值
                target_max_mb = int(total_mb * max_percent)
                max_allocation_mb = max(0, target_max_mb - current_used_mb)
                
                # 确保不超出安全边际
                mem_info = self.get_system_memory_info()
                safe_allocation_mb = int(mem_info["free_mb"] - self.safety_margin_mb)
                max_allocation_mb = min(max_allocation_mb, safe_allocation_mb)
                
                if max_allocation_mb > 0:
                    logger.info(f"周期{cycle+1}/{num_cycles}: 增长到{max_allocation_mb}MB")
                    chunk = self.allocate_chunk(max_allocation_mb)
                    if chunk is not None:
                        self.chunks.append(chunk)
                        self.allocated_mb = max_allocation_mb
                        peak_allocated = max(peak_allocated, self.allocated_mb)
                    
                    # 保持高峰一小段时间
                    time.sleep(cycle_duration_sec / 4)
                
                # 降低到最小值
                target_min_mb = int(total_mb * min_percent)
                min_allocation_mb = max(0, target_min_mb - current_used_mb)
                
                # 释放部分内存，保留最小分配量
                if self.allocated_mb > min_allocation_mb and min_allocation_mb >= 0:
                    to_release = self.allocated_mb - min_allocation_mb
                    logger.info(f"周期{cycle+1}/{num_cycles}: 降低到{min_allocation_mb}MB (释放{to_release}MB)")
                    
                    # 保留初始块
                    keep_chunks = []
                    released = 0
                    for chunk in reversed(self.chunks):
                        if released >= to_release:
                            keep_chunks.insert(0, chunk)
                        else:
                            # 估算当前块大小
                            chunk_size = len(chunk) / (1024 * 1024)
                            released += chunk_size
                    
                    # 更新块列表和分配计数
                    self.chunks = keep_chunks
                    self.allocated_mb = self.allocated_mb - to_release
                
                # 保持低谷一小段时间
                time.sleep(cycle_duration_sec / 4)
                
        except Exception as e:
            logger.error(f"锯齿波动压力测试异常: {str(e)}")
            
        finally:
            logger.info(f"锯齿波动压力测试完成，峰值分配: {peak_allocated}MB")
            self.release_all()
            return peak_allocated
    
    def release_all(self) -> int:
        """
        释放所有已分配的内存
        
        Returns:
            释放的内存大小(MB)
        """
        released = self.allocated_mb
        if released > 0:
            logger.info(f"释放所有已分配内存: {released}MB")
            
        self.chunks.clear()
        self.allocated_mb = 0
        
        # 强制垃圾回收
        gc.collect()
        return released
    
    def start_memory_monitor(self, 
                            callback_warning: Optional[Callable] = None,
                            callback_critical: Optional[Callable] = None) -> None:
        """
        启动内存监控线程，当内存使用超过阈值时触发回调
        
        Args:
            callback_warning: 内存使用超过警告阈值时的回调函数
            callback_critical: 内存使用超过危险阈值时的回调函数
        """
        if callback_warning:
            self.warning_callbacks.append(callback_warning)
        if callback_critical:
            self.critical_callbacks.append(callback_critical)
            
        # 停止现有监控线程(如果有)
        self.stop_monitor.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(1.0)
            
        # 重置停止标志
        self.stop_monitor.clear()
        
        # 创建新监控线程
        self.monitor_thread = threading.Thread(
            target=self._memory_monitor_task,
            daemon=True,
            name="MemoryMonitor"
        )
        self.monitor_thread.start()
        logger.info("内存监控线程已启动")
        
    def stop_memory_monitor(self) -> None:
        """停止内存监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.info("正在停止内存监控线程")
            self.stop_monitor.set()
            self.monitor_thread.join(2.0)
            if not self.monitor_thread.is_alive():
                logger.info("内存监控线程已停止")
            else:
                logger.warning("内存监控线程未能正常停止")
    
    def _memory_monitor_task(self) -> None:
        """内存监控线程任务"""
        logger.info("内存监控任务开始运行")
        warning_triggered = False
        critical_triggered = False
        
        while not self.stop_monitor.is_set():
            try:
                mem_info = self.get_system_memory_info()
                usage_ratio = mem_info["percent_used"]
                
                # 记录当前内存状态
                logger.debug(f"内存使用率: {usage_ratio*100:.1f}%, "
                           f"可用: {mem_info['available_gb']:.2f}GB")
                
                # 检查是否达到危险阈值
                if usage_ratio >= self.threshold_critical and not critical_triggered:
                    logger.warning(f"内存使用率达到危险水平: {usage_ratio*100:.1f}%")
                    critical_triggered = True
                    warning_triggered = True  # 同时设置警告标志
                    
                    # 触发所有危险回调
                    for callback in self.critical_callbacks:
                        try:
                            callback(mem_info)
                        except Exception as e:
                            logger.error(f"危险回调执行异常: {str(e)}")
                
                # 检查是否低于危险阈值(恢复)
                elif usage_ratio < self.threshold_critical and critical_triggered:
                    logger.info(f"内存使用率降至危险水平以下: {usage_ratio*100:.1f}%")
                    critical_triggered = False
                
                # 检查是否达到警告阈值
                if usage_ratio >= self.threshold_warning and not warning_triggered:
                    logger.info(f"内存使用率达到警告水平: {usage_ratio*100:.1f}%")
                    warning_triggered = True
                    
                    # 触发所有警告回调
                    for callback in self.warning_callbacks:
                        try:
                            callback(mem_info)
                        except Exception as e:
                            logger.error(f"警告回调执行异常: {str(e)}")
                
                # 检查是否低于警告阈值(恢复)
                elif usage_ratio < self.threshold_warning and warning_triggered:
                    logger.info(f"内存使用率降至警告水平以下: {usage_ratio*100:.1f}%")
                    warning_triggered = False
                
                # 等待下一次检查
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"内存监控异常: {str(e)}")
                time.sleep(1.0)  # 出错后短暂暂停
        
        logger.info("内存监控任务已退出")
    
    def __del__(self):
        """析构函数，确保释放所有资源"""
        self.stop_memory_monitor()
        self.release_all()


# 集成测试功能
def run_pressure_test(test_mode: str = "staircase", **kwargs):
    """
    运行内存压力测试
    
    Args:
        test_mode: 测试模式 ('staircase', 'burst', 'sawtooth', 'allocate_full')
        **kwargs: 传递给具体测试方法的参数
    """
    pressurer = MemoryPressurer()
    
    # 显示系统初始内存状态
    mem_info = pressurer.get_system_memory_info()
    print(f"\n==== 内存压力测试开始 [{test_mode}] ====")
    print(f"系统总内存: {mem_info['total_gb']:.2f}GB")
    print(f"当前可用内存: {mem_info['available_gb']:.2f}GB")
    print(f"当前内存使用率: {mem_info['percent_used']*100:.1f}%")
    
    # 根据模式执行不同测试
    peak_mb = 0
    try:
        if test_mode == "staircase":
            peak_mb = pressurer.staircase_pressure(**kwargs)
        elif test_mode == "burst":
            peak_mb = pressurer.burst_pressure(**kwargs)
        elif test_mode == "sawtooth":
            peak_mb = pressurer.sawtooth_pressure(**kwargs)
        elif test_mode == "allocate_full":
            peak_mb = pressurer.allocate_until_full(**kwargs)
        else:
            print(f"未知测试模式: {test_mode}")
            return
    
    finally:
        # 确保释放内存
        pressurer.release_all()
        
        # 显示测试结果
        mem_info = pressurer.get_system_memory_info()
        print(f"\n==== 内存压力测试结束 ====")
        print(f"测试模式: {test_mode}")
        print(f"峰值内存分配: {peak_mb}MB")
        print(f"测试后可用内存: {mem_info['available_gb']:.2f}GB")
        print(f"测试后内存使用率: {mem_info['percent_used']*100:.1f}%")


if __name__ == "__main__":
    # 简单的命令行接口，用于独立测试
    import argparse
    
    parser = argparse.ArgumentParser(description="内存压力测试工具")
    parser.add_argument("--mode", choices=["staircase", "burst", "sawtooth", "allocate_full"],
                       default="staircase", help="测试模式")
    parser.add_argument("--step", type=int, default=100, help="阶梯模式下每步增加的内存(MB)")
    parser.add_argument("--interval", type=float, default=1.0, help="阶梯模式下每步间隔时间(秒)")
    parser.add_argument("--target", type=float, default=0.7, help="突发模式下目标内存占用比例(0-1)")
    parser.add_argument("--duration", type=float, default=5.0, 
                       help="突发模式下持续时间或锯齿模式下周期时间(秒)")
    parser.add_argument("--min", type=float, default=0.3, help="锯齿模式下最小内存占用比例(0-1)")
    parser.add_argument("--max", type=float, default=0.7, help="锯齿模式下最大内存占用比例(0-1)")
    parser.add_argument("--cycles", type=int, default=3, help="锯齿模式下周期数")
    
    args = parser.parse_args()
    
    # 根据命令行参数执行测试
    if args.mode == "staircase":
        run_pressure_test(args.mode, step_size_mb=args.step, step_interval_sec=args.interval)
    elif args.mode == "burst":
        run_pressure_test(args.mode, target_percent=args.target, burst_duration_sec=args.duration)
    elif args.mode == "sawtooth":
        run_pressure_test(args.mode, min_percent=args.min, max_percent=args.max, 
                         cycle_duration_sec=args.duration, num_cycles=args.cycles)
    elif args.mode == "allocate_full":
        run_pressure_test(args.mode, chunk_size_mb=args.step) 