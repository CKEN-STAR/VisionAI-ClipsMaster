"""内存泄露检测测试套件

此模块实现全面的内存泄露检测，包括：
1. 基础内存分配/释放测试
2. 长时间运行测试
3. 模型加载/卸载测试
4. 并发操作测试
5. 异常情况测试
"""

import os
import time
import gc
import psutil
import unittest
from typing import Dict, List, Optional
from loguru import logger
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice

class MemoryLeakTest(unittest.TestCase):
    """内存泄露测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.memory_manager = MemoryManager()
        cls.device_manager = HybridDevice()
        cls.process = psutil.Process()
        
        # 测试配置
        cls.test_config = {
            'test_duration': 60,        # 测试持续时间（秒）
            'memory_threshold': 0.1,    # 内存增长阈值（10%）
            'check_interval': 5,        # 检查间隔（秒）
            'max_iterations': 1000      # 最大迭代次数
        }
    
    def setUp(self):
        """准备测试环境"""
        # 清理内存
        gc.collect()
        if hasattr(self.memory_manager, 'cleanup'):
            self.memory_manager.cleanup()
        
        # 记录初始内存使用
        self.initial_memory = self._get_memory_usage()
    
    def tearDown(self):
        """清理测试环境"""
        # 确保所有资源都被释放
        gc.collect()
        if hasattr(self.memory_manager, 'cleanup'):
            self.memory_manager.cleanup()
    
    def test_basic_memory_operations(self):
        """测试基础内存操作"""
        logger.info("开始基础内存操作测试")
        
        try:
            # 分配内存
            allocated_memory = []
            for size in [1024, 2048, 4096]:  # 1KB, 2KB, 4KB
                memory = self.memory_manager.allocate_memory(size)
                allocated_memory.append(memory)
                self.assertIsNotNone(memory)
            
            # 释放内存
            for memory in allocated_memory:
                self.memory_manager.free_memory(memory)
            
            # 验证内存已释放
            final_memory = self._get_memory_usage()
            self.assertLessEqual(
                abs(final_memory - self.initial_memory),
                self.test_config['memory_threshold'] * self.initial_memory,
                "内存未完全释放"
            )
            
        except Exception as e:
            logger.error(f"基础内存操作测试失败: {str(e)}")
            raise
    
    def test_long_running_memory(self):
        """测试长时间运行内存使用"""
        logger.info("开始长时间运行内存测试")
        
        try:
            start_time = time.time()
            memory_history = []
            
            while time.time() - start_time < self.test_config['test_duration']:
                # 分配和释放内存
                memory = self.memory_manager.allocate_memory(1024)
                self.memory_manager.free_memory(memory)
                
                # 记录内存使用
                memory_history.append(self._get_memory_usage())
                
                # 检查内存增长
                if len(memory_history) > 1:
                    growth = (memory_history[-1] - memory_history[0]) / memory_history[0]
                    self.assertLessEqual(
                        growth,
                        self.test_config['memory_threshold'],
                        f"内存持续增长: {growth:.2%}"
                    )
                
                time.sleep(self.test_config['check_interval'])
            
        except Exception as e:
            logger.error(f"长时间运行内存测试失败: {str(e)}")
            raise
    
    def test_model_memory_management(self):
        """测试模型内存管理"""
        logger.info("开始模型内存管理测试")
        
        try:
            # 模拟模型加载
            model_size = 1024 * 1024  # 1MB
            model_memory = self.memory_manager.allocate_memory(model_size)
            
            # 记录加载后内存
            loaded_memory = self._get_memory_usage()
            
            # 模拟模型卸载
            self.memory_manager.free_memory(model_memory)
            gc.collect()
            
            # 记录卸载后内存
            unloaded_memory = self._get_memory_usage()
            
            # 验证内存释放
            memory_diff = abs(unloaded_memory - self.initial_memory)
            self.assertLessEqual(
                memory_diff,
                self.test_config['memory_threshold'] * self.initial_memory,
                f"模型内存未完全释放: {memory_diff} bytes"
            )
            
        except Exception as e:
            logger.error(f"模型内存管理测试失败: {str(e)}")
            raise
    
    def test_concurrent_memory_operations(self):
        """测试并发内存操作"""
        logger.info("开始并发内存操作测试")
        
        try:
            import threading
            
            def memory_worker():
                """内存操作工作线程"""
                for _ in range(100):
                    memory = self.memory_manager.allocate_memory(1024)
                    time.sleep(0.01)
                    self.memory_manager.free_memory(memory)
            
            # 创建多个工作线程
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=memory_worker)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证内存使用
            final_memory = self._get_memory_usage()
            self.assertLessEqual(
                abs(final_memory - self.initial_memory),
                self.test_config['memory_threshold'] * self.initial_memory,
                "并发操作导致内存泄露"
            )
            
        except Exception as e:
            logger.error(f"并发内存操作测试失败: {str(e)}")
            raise
    
    def test_exception_handling(self):
        """测试异常情况下的内存管理"""
        logger.info("开始异常处理内存测试")
        
        try:
            # 模拟异常情况
            allocated_memory = []
            for _ in range(10):
                try:
                    memory = self.memory_manager.allocate_memory(1024)
                    allocated_memory.append(memory)
                    if len(allocated_memory) == 5:
                        raise Exception("模拟异常")
                except Exception:
                    # 确保异常情况下内存也被释放
                    for mem in allocated_memory:
                        self.memory_manager.free_memory(mem)
                    allocated_memory = []
                    raise
            
        except Exception:
            # 验证异常处理后内存已释放
            final_memory = self._get_memory_usage()
            self.assertLessEqual(
                abs(final_memory - self.initial_memory),
                self.test_config['memory_threshold'] * self.initial_memory,
                "异常处理导致内存泄露"
            )
    
    def test_video_processing_memory(self):
        """测试视频处理过程中的内存管理"""
        logger.info("开始视频处理内存测试")
        
        try:
            # 模拟视频帧处理
            frame_sizes = [1920 * 1080 * 3, 1280 * 720 * 3]  # 1080p和720p的RGB帧
            processed_frames = []
            
            for size in frame_sizes:
                # 模拟帧处理
                frame = self.memory_manager.allocate_memory(size)
                processed_frames.append(frame)
                
                # 模拟处理后的帧缓存
                processed_frame = self.memory_manager.allocate_memory(size)
                processed_frames.append(processed_frame)
                
                # 释放原始帧
                self.memory_manager.free_memory(frame)
                processed_frames.remove(frame)
            
            # 释放所有处理后的帧
            for frame in processed_frames:
                self.memory_manager.free_memory(frame)
            
            # 验证内存使用
            final_memory = self._get_memory_usage()
            self.assertLessEqual(
                abs(final_memory - self.initial_memory),
                self.test_config['memory_threshold'] * self.initial_memory,
                "视频处理导致内存泄露"
            )
            
        except Exception as e:
            logger.error(f"视频处理内存测试失败: {str(e)}")
            raise
    
    def _get_memory_usage(self) -> int:
        """获取当前内存使用量
        
        Returns:
            int: 内存使用量（字节）
        """
        return self.process.memory_info().rss 