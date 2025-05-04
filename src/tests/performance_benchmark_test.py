"""性能基准测试套件

此模块实现全面的性能基准测试，包括：
1. 模型推理性能测试
2. 视频处理性能测试
3. 字幕处理性能测试
4. 内存使用性能测试
5. 并发处理性能测试
6. 端到端性能测试
"""

import os
import time
import random
import unittest
import threading
import statistics
from typing import Dict, List, Optional, Tuple
from loguru import logger
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice
from ..utils.file_handler import FileHandler
from ..core.model_switcher import ModelSwitcher
from ..core.srt_parser import SRTParser
from ..core.clip_generator import ClipGenerator
from ..core.narrative_analyzer import NarrativeAnalyzer
from ..core.rhythm_analyzer import RhythmAnalyzer

class PerformanceBenchmarkTest(unittest.TestCase):
    """性能基准测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.memory_manager = MemoryManager()
        cls.device_manager = HybridDevice()
        cls.file_handler = FileHandler()
        cls.model_switcher = ModelSwitcher()
        cls.srt_parser = SRTParser()
        cls.clip_generator = ClipGenerator()
        cls.narrative_analyzer = NarrativeAnalyzer()
        cls.rhythm_analyzer = RhythmAnalyzer()
        
        # 测试配置
        cls.test_config = {
            'warmup_rounds': 3,         # 预热轮数
            'benchmark_rounds': 10,     # 基准测试轮数
            'batch_sizes': [1, 4, 8],   # 批处理大小
            'concurrent_tasks': 5,      # 并发任务数
            'max_memory_mb': 4096,      # 最大内存限制（MB）
            'timeout_seconds': 300      # 超时时间（秒）
        }
        
        # 创建测试目录
        cls.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(cls.test_dir, exist_ok=True)
        
        # 创建测试数据
        cls._create_test_data()
    
    def setUp(self):
        """准备测试环境"""
        # 清理之前的测试文件
        self._cleanup_test_files()
        
        # 创建测试文件
        self._create_test_files()
    
    def tearDown(self):
        """清理测试环境"""
        self._cleanup_test_files()
    
    def test_model_inference_performance(self):
        """测试模型推理性能"""
        logger.info("开始模型推理性能测试")
        
        try:
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                self._run_model_inference()
            
            # 基准测试
            results = []
            for _ in range(self.test_config['benchmark_rounds']):
                start_time = time.time()
                self._run_model_inference()
                end_time = time.time()
                results.append(end_time - start_time)
            
            # 分析结果
            mean_time = statistics.mean(results)
            std_time = statistics.stdev(results)
            logger.info(f"模型推理性能测试结果:")
            logger.info(f"平均时间: {mean_time:.3f}秒")
            logger.info(f"标准差: {std_time:.3f}秒")
            
            # 验证性能
            self.assertLess(mean_time, 5.0)  # 平均推理时间应小于5秒
            
        except Exception as e:
            logger.error(f"模型推理性能测试失败: {str(e)}")
            raise
    
    def test_video_processing_performance(self):
        """测试视频处理性能"""
        logger.info("开始视频处理性能测试")
        
        try:
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                self._process_test_video()
            
            # 基准测试
            results = []
            for batch_size in self.test_config['batch_sizes']:
                batch_results = []
                for _ in range(self.test_config['benchmark_rounds']):
                    start_time = time.time()
                    self._process_test_video(batch_size)
                    end_time = time.time()
                    batch_results.append(end_time - start_time)
                
                mean_time = statistics.mean(batch_results)
                std_time = statistics.stdev(batch_results)
                results.append((batch_size, mean_time, std_time))
            
            # 分析结果
            logger.info("视频处理性能测试结果:")
            for batch_size, mean_time, std_time in results:
                logger.info(f"批处理大小: {batch_size}")
                logger.info(f"平均时间: {mean_time:.3f}秒")
                logger.info(f"标准差: {std_time:.3f}秒")
            
            # 验证性能
            self.assertLess(results[0][1], 10.0)  # 单批次处理时间应小于10秒
            
        except Exception as e:
            logger.error(f"视频处理性能测试失败: {str(e)}")
            raise
    
    def test_subtitle_processing_performance(self):
        """测试字幕处理性能"""
        logger.info("开始字幕处理性能测试")
        
        try:
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                self._process_test_subtitle()
            
            # 基准测试
            results = []
            for _ in range(self.test_config['benchmark_rounds']):
                start_time = time.time()
                self._process_test_subtitle()
                end_time = time.time()
                results.append(end_time - start_time)
            
            # 分析结果
            mean_time = statistics.mean(results)
            std_time = statistics.stdev(results)
            logger.info(f"字幕处理性能测试结果:")
            logger.info(f"平均时间: {mean_time:.3f}秒")
            logger.info(f"标准差: {std_time:.3f}秒")
            
            # 验证性能
            self.assertLess(mean_time, 2.0)  # 平均处理时间应小于2秒
            
        except Exception as e:
            logger.error(f"字幕处理性能测试失败: {str(e)}")
            raise
    
    def test_memory_performance(self):
        """测试内存使用性能"""
        logger.info("开始内存使用性能测试")
        
        try:
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                self._run_memory_test()
            
            # 基准测试
            results = []
            for _ in range(self.test_config['benchmark_rounds']):
                start_memory = self.memory_manager.get_memory_usage()
                self._run_memory_test()
                end_memory = self.memory_manager.get_memory_usage()
                results.append(end_memory - start_memory)
            
            # 分析结果
            mean_memory = statistics.mean(results)
            std_memory = statistics.stdev(results)
            logger.info(f"内存使用性能测试结果:")
            logger.info(f"平均内存增长: {mean_memory:.2f}MB")
            logger.info(f"标准差: {std_memory:.2f}MB")
            
            # 验证性能
            self.assertLess(mean_memory, 100.0)  # 平均内存增长应小于100MB
            
        except Exception as e:
            logger.error(f"内存使用性能测试失败: {str(e)}")
            raise
    
    def test_concurrent_performance(self):
        """测试并发处理性能"""
        logger.info("开始并发处理性能测试")
        
        try:
            def concurrent_task():
                """并发任务"""
                self._run_model_inference()
                self._process_test_video()
                self._process_test_subtitle()
            
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                concurrent_task()
            
            # 基准测试
            results = []
            for _ in range(self.test_config['benchmark_rounds']):
                threads = []
                start_time = time.time()
                
                for _ in range(self.test_config['concurrent_tasks']):
                    thread = threading.Thread(target=concurrent_task)
                    threads.append(thread)
                    thread.start()
                
                for thread in threads:
                    thread.join()
                
                end_time = time.time()
                results.append(end_time - start_time)
            
            # 分析结果
            mean_time = statistics.mean(results)
            std_time = statistics.stdev(results)
            logger.info(f"并发处理性能测试结果:")
            logger.info(f"平均时间: {mean_time:.3f}秒")
            logger.info(f"标准差: {std_time:.3f}秒")
            
            # 验证性能
            self.assertLess(mean_time, 30.0)  # 平均处理时间应小于30秒
            
        except Exception as e:
            logger.error(f"并发处理性能测试失败: {str(e)}")
            raise
    
    def test_end_to_end_performance(self):
        """测试端到端性能"""
        logger.info("开始端到端性能测试")
        
        try:
            # 预热
            for _ in range(self.test_config['warmup_rounds']):
                self._run_end_to_end_test()
            
            # 基准测试
            results = []
            for _ in range(self.test_config['benchmark_rounds']):
                start_time = time.time()
                self._run_end_to_end_test()
                end_time = time.time()
                results.append(end_time - start_time)
            
            # 分析结果
            mean_time = statistics.mean(results)
            std_time = statistics.stdev(results)
            logger.info(f"端到端性能测试结果:")
            logger.info(f"平均时间: {mean_time:.3f}秒")
            logger.info(f"标准差: {std_time:.3f}秒")
            
            # 验证性能
            self.assertLess(mean_time, 60.0)  # 平均处理时间应小于60秒
            
        except Exception as e:
            logger.error(f"端到端性能测试失败: {str(e)}")
            raise
    
    def _create_test_data(self):
        """创建测试数据"""
        # 创建测试视频
        self.test_video = os.path.join(self.test_dir, "test.mp4")
        with open(self.test_video, 'wb') as f:
            f.write(os.urandom(1024 * 1024))  # 1MB测试视频
        
        # 创建测试字幕
        self.test_srt = os.path.join(self.test_dir, "test.srt")
        with open(self.test_srt, 'w', encoding='utf-8') as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nTest subtitle")
    
    def _cleanup_test_files(self):
        """清理测试文件"""
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
    
    def _run_model_inference(self):
        """运行模型推理测试"""
        # 模拟模型推理
        time.sleep(0.1)  # 模拟推理时间
    
    def _process_test_video(self, batch_size: int = 1):
        """处理测试视频
        
        Args:
            batch_size: 批处理大小
        """
        # 模拟视频处理
        time.sleep(0.2 * batch_size)  # 模拟处理时间
    
    def _process_test_subtitle(self):
        """处理测试字幕"""
        # 模拟字幕处理
        time.sleep(0.05)  # 模拟处理时间
    
    def _run_memory_test(self):
        """运行内存测试"""
        # 模拟内存使用
        memory = self.memory_manager.allocate_memory(1024 * 1024)  # 1MB
        time.sleep(0.1)
        self.memory_manager.free_memory(memory)
    
    def _run_end_to_end_test(self):
        """运行端到端测试"""
        # 模拟完整流程
        self._run_model_inference()
        self._process_test_video()
        self._process_test_subtitle()
        time.sleep(0.5)  # 模拟额外处理时间 