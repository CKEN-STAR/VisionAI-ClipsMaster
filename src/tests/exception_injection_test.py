"""异常注入测试套件

此模块实现全面的异常注入测试，包括：
1. 文件操作异常测试
2. 内存异常测试
3. 模型加载异常测试
4. 视频处理异常测试
5. 字幕处理异常测试
6. 并发操作异常测试
"""

import os
import sys
import time
import random
import unittest
import threading
from typing import Dict, List, Optional
from loguru import logger
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice
from ..utils.file_handler import FileHandler
from ..core.model_switcher import ModelSwitcher
from ..core.srt_parser import SRTParser
from ..core.clip_generator import ClipGenerator

class ExceptionInjectionTest(unittest.TestCase):
    """异常注入测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.memory_manager = MemoryManager()
        cls.device_manager = HybridDevice()
        cls.file_handler = FileHandler()
        cls.model_switcher = ModelSwitcher()
        cls.srt_parser = SRTParser()
        cls.clip_generator = ClipGenerator()
        
        # 测试配置
        cls.test_config = {
            'max_retries': 3,           # 最大重试次数
            'timeout_seconds': 30,      # 超时时间（秒）
            'corruption_rate': 0.1,     # 文件损坏率
            'memory_limit_mb': 100,     # 内存限制（MB）
            'concurrent_tasks': 5        # 并发任务数
        }
        
        # 创建测试目录
        cls.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(cls.test_dir, exist_ok=True)
    
    def setUp(self):
        """准备测试环境"""
        # 清理之前的测试文件
        self._cleanup_test_files()
        
        # 创建测试文件
        self._create_test_files()
    
    def tearDown(self):
        """清理测试环境"""
        self._cleanup_test_files()
    
    def test_file_operation_exceptions(self):
        """测试文件操作异常"""
        logger.info("开始文件操作异常测试")
        
        try:
            # 测试不存在的文件
            with self.assertRaises(FileNotFoundError):
                self.file_handler.read_file("non_existent.srt")
            
            # 测试权限不足
            test_file = os.path.join(self.test_dir, "permission_test.srt")
            with open(test_file, 'w') as f:
                f.write("test content")
            os.chmod(test_file, 0o000)  # 移除所有权限
            
            with self.assertRaises(PermissionError):
                self.file_handler.read_file(test_file)
            
            # 测试文件损坏
            corrupted_file = self._create_corrupted_file("corrupted.srt")
            with self.assertRaises(Exception):
                self.srt_parser.parse(corrupted_file)
            
        except Exception as e:
            logger.error(f"文件操作异常测试失败: {str(e)}")
            raise
    
    def test_memory_exceptions(self):
        """测试内存异常"""
        logger.info("开始内存异常测试")
        
        try:
            # 测试内存不足
            with self.assertRaises(MemoryError):
                self.memory_manager.allocate_memory(
                    self.test_config['memory_limit_mb'] * 1024 * 1024 * 2
                )
            
            # 测试内存泄露
            allocated_memory = []
            try:
                for _ in range(100):
                    memory = self.memory_manager.allocate_memory(1024 * 1024)  # 1MB
                    allocated_memory.append(memory)
                    if len(allocated_memory) % 10 == 0:
                        raise MemoryError("模拟内存不足")
            except MemoryError:
                # 确保异常时内存被释放
                for memory in allocated_memory:
                    self.memory_manager.free_memory(memory)
                raise
            
        except Exception as e:
            logger.error(f"内存异常测试失败: {str(e)}")
            raise
    
    def test_model_loading_exceptions(self):
        """测试模型加载异常"""
        logger.info("开始模型加载异常测试")
        
        try:
            # 测试模型文件损坏
            corrupted_model = self._create_corrupted_file("corrupted_model.bin")
            with self.assertRaises(Exception):
                self.model_switcher.load_model(corrupted_model)
            
            # 测试模型版本不匹配
            with self.assertRaises(ValueError):
                self.model_switcher.load_model("wrong_version_model.bin")
            
            # 测试模型加载超时
            with self.assertRaises(TimeoutError):
                self.model_switcher.load_model(
                    "timeout_model.bin",
                    timeout=self.test_config['timeout_seconds']
                )
            
        except Exception as e:
            logger.error(f"模型加载异常测试失败: {str(e)}")
            raise
    
    def test_video_processing_exceptions(self):
        """测试视频处理异常"""
        logger.info("开始视频处理异常测试")
        
        try:
            # 测试视频文件损坏
            corrupted_video = self._create_corrupted_file("corrupted.mp4")
            with self.assertRaises(Exception):
                self.clip_generator.process_video(corrupted_video)
            
            # 测试视频格式不支持
            with self.assertRaises(ValueError):
                self.clip_generator.process_video("unsupported.avi")
            
            # 测试视频分辨率异常
            with self.assertRaises(Exception):
                self.clip_generator.process_video("invalid_resolution.mp4")
            
        except Exception as e:
            logger.error(f"视频处理异常测试失败: {str(e)}")
            raise
    
    def test_subtitle_processing_exceptions(self):
        """测试字幕处理异常"""
        logger.info("开始字幕处理异常测试")
        
        try:
            # 测试字幕格式错误
            invalid_srt = os.path.join(self.test_dir, "invalid.srt")
            with open(invalid_srt, 'w') as f:
                f.write("Invalid SRT format")
            
            with self.assertRaises(ValueError):
                self.srt_parser.parse(invalid_srt)
            
            # 测试时间轴错误
            wrong_timeline = os.path.join(self.test_dir, "wrong_timeline.srt")
            with open(wrong_timeline, 'w') as f:
                f.write("1\n00:00:10,000 --> 00:00:05,000\nInvalid timeline")
            
            with self.assertRaises(ValueError):
                self.srt_parser.parse(wrong_timeline)
            
            # 测试编码错误
            wrong_encoding = os.path.join(self.test_dir, "wrong_encoding.srt")
            with open(wrong_encoding, 'wb') as f:
                f.write(b"Invalid encoding \xff\xfe")
            
            with self.assertRaises(UnicodeDecodeError):
                self.srt_parser.parse(wrong_encoding)
            
        except Exception as e:
            logger.error(f"字幕处理异常测试失败: {str(e)}")
            raise
    
    def test_concurrent_operation_exceptions(self):
        """测试并发操作异常"""
        logger.info("开始并发操作异常测试")
        
        try:
            def concurrent_task():
                """并发任务"""
                try:
                    # 随机选择操作类型
                    operations = [
                        lambda: self.memory_manager.allocate_memory(1024 * 1024),
                        lambda: self.file_handler.read_file("test.srt"),
                        lambda: self.model_switcher.load_model("test_model.bin")
                    ]
                    operation = random.choice(operations)
                    operation()
                except Exception:
                    pass
            
            # 创建多个并发任务
            threads = []
            for _ in range(self.test_config['concurrent_tasks']):
                thread = threading.Thread(target=concurrent_task)
                threads.append(thread)
                thread.start()
            
            # 等待所有任务完成
            for thread in threads:
                thread.join()
            
            # 验证系统状态
            self.assertTrue(self.memory_manager.is_healthy())
            self.assertTrue(self.file_handler.is_healthy())
            
        except Exception as e:
            logger.error(f"并发操作异常测试失败: {str(e)}")
            raise
    
    def _create_test_files(self):
        """创建测试文件"""
        # 创建正常的测试文件
        test_srt = os.path.join(self.test_dir, "test.srt")
        with open(test_srt, 'w', encoding='utf-8') as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nTest subtitle")
    
    def _cleanup_test_files(self):
        """清理测试文件"""
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
    
    def _create_corrupted_file(self, filename: str) -> str:
        """创建损坏的测试文件
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        file_path = os.path.join(self.test_dir, filename)
        with open(file_path, 'wb') as f:
            # 写入随机损坏的数据
            f.write(os.urandom(1024))
        return file_path 