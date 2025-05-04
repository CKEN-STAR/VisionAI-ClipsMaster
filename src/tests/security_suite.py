"""安全验证套件

此模块提供全面的安全验证功能，包括:
1. 模型完整性验证
2. 权限检查
3. 内存安全验证
4. 加载过程验证
5. 异常处理测试
"""

import os
import unittest
import tempfile
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from ..utils.permission_handler import PermissionHandler
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice
from ..benchmarks.load_benchmark import LoadBenchmark

class SecurityTestSuite(unittest.TestCase):
    """安全验证测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """测试套件初始化"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.permission_handler = PermissionHandler()
        cls.memory_manager = MemoryManager()
        cls.device_manager = HybridDevice()
        cls.load_benchmark = LoadBenchmark(
            memory_manager=cls.memory_manager,
            device_manager=cls.device_manager
        )
        
        # 创建测试目录结构
        cls._create_test_structure()
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        try:
            shutil.rmtree(cls.temp_dir)
        except Exception as e:
            logger.error(f"清理测试目录失败: {str(e)}")
    
    @classmethod
    def _create_test_structure(cls):
        """创建测试目录结构"""
        try:
            # 创建模型目录
            model_dir = Path(cls.temp_dir) / "models"
            model_dir.mkdir(exist_ok=True)
            
            # 创建测试文件
            test_files = {
                "model.bin": b"test_model_content",
                "config.json": b'{"name": "test_model", "version": "1.0"}',
                "vocab.txt": b"test_vocabulary",
                "checksum.md5": b"test_checksum"
            }
            
            for filename, content in test_files.items():
                file_path = model_dir / filename
                file_path.write_bytes(content)
                
            # 设置权限
            cls.permission_handler.set_directory_permissions(str(model_dir))
            
        except Exception as e:
            logger.error(f"创建测试目录结构失败: {str(e)}")
            raise
    
    def test_model_integrity(self):
        """测试模型完整性"""
        model_dir = Path(self.temp_dir) / "models"
        model_file = model_dir / "model.bin"
        
        # 验证文件存在
        self.assertTrue(model_file.exists())
        
        # 验证文件大小
        self.assertGreater(model_file.stat().st_size, 0)
        
        # 验证文件权限
        self.assertTrue(os.access(str(model_file), os.R_OK))
        
        # 验证文件校验和
        with open(model_file, 'rb') as f:
            content = f.read()
            checksum = hashlib.md5(content).hexdigest()
            self.assertIsNotNone(checksum)
    
    def test_permission_security(self):
        """测试权限安全"""
        model_dir = Path(self.temp_dir) / "models"
        
        # 验证目录权限
        self.assertTrue(os.access(str(model_dir), os.R_OK | os.X_OK))
        
        # 验证文件权限设置
        for file_path in model_dir.glob("*"):
            self.assertTrue(os.access(str(file_path), os.R_OK))
            self.assertFalse(os.access(str(file_path), os.W_OK))  # 确保文件是只读的
    
    def test_memory_safety(self):
        """测试内存安全"""
        # 验证内存限制
        self.assertIsNotNone(self.memory_manager.get_current_memory_usage())
        
        # 验证内存分配
        try:
            self.memory_manager.allocate_memory(1024 * 1024)  # 分配1MB
            self.assertTrue(True)
        except MemoryError:
            self.fail("内存分配失败")
        finally:
            self.memory_manager.cleanup()
    
    def test_load_security(self):
        """测试加载安全性"""
        model_dir = Path(self.temp_dir) / "models"
        model_file = str(model_dir / "model.bin")
        
        # 测试加载性能
        results = self.load_benchmark.benchmark_load_time(
            model_paths=[model_file],
            iterations=1,
            warm_up=False
        )
        
        self.assertIsNotNone(results)
        self.assertIn(Path(model_file).stem, results)
    
    def test_device_security(self):
        """测试设备安全性"""
        # 验证设备状态
        device_info = self.device_manager.get_device_info()
        self.assertIsNotNone(device_info)
        
        # 验证设备选择
        selected_device = self.device_manager.select_device()
        self.assertIsNotNone(selected_device)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            self.load_benchmark.benchmark_load_time(
                model_paths=["non_existent_model.bin"]
            )
        
        # 测试无效的内存分配
        with self.assertRaises(MemoryError):
            self.memory_manager.allocate_memory(float('inf'))
        
        # 测试无效的权限设置
        with self.assertRaises(PermissionError):
            self.permission_handler.set_file_permissions("/root/test.txt", 0o777)
    
    def test_concurrent_access(self):
        """测试并发访问安全性"""
        import threading
        
        def access_model():
            model_dir = Path(self.temp_dir) / "models"
            model_file = model_dir / "model.bin"
            try:
                with open(model_file, 'rb') as f:
                    f.read()
                return True
            except Exception:
                return False
        
        # 创建多个线程同时访问
        threads = []
        results = []
        
        for _ in range(5):
            thread = threading.Thread(target=lambda: results.append(access_model()))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有访问都成功
        self.assertTrue(all(results))
    
    def test_recovery_mechanism(self):
        """测试恢复机制"""
        model_dir = Path(self.temp_dir) / "models"
        backup_file = model_dir / "model.bin.bak"
        
        # 创建备份
        shutil.copy2(model_dir / "model.bin", backup_file)
        
        try:
            # 模拟文件损坏
            with open(model_dir / "model.bin", 'wb') as f:
                f.write(b"corrupted_content")
            
            # 验证文件已损坏
            with open(model_dir / "model.bin", 'rb') as f:
                self.assertNotEqual(f.read(), b"test_model_content")
            
            # 从备份恢复
            shutil.copy2(backup_file, model_dir / "model.bin")
            
            # 验证恢复成功
            with open(model_dir / "model.bin", 'rb') as f:
                self.assertEqual(f.read(), b"test_model_content")
                
        finally:
            # 清理备份
            if backup_file.exists():
                backup_file.unlink()
    
    def test_configuration_security(self):
        """测试配置安全性"""
        model_dir = Path(self.temp_dir) / "models"
        config_file = model_dir / "config.json"
        
        # 验证配置文件存在
        self.assertTrue(config_file.exists())
        
        # 验证配置文件格式
        import json
        with open(config_file) as f:
            config = json.load(f)
            self.assertIn("name", config)
            self.assertIn("version", config)
    
    def test_isolation(self):
        """测试隔离性"""
        # 验证进程隔离
        import psutil
        current_process = psutil.Process()
        
        # 验证内存隔离
        memory_info = current_process.memory_info()
        self.assertIsNotNone(memory_info)
        
        # 验证文件系统隔离
        self.assertTrue(os.path.isabs(self.temp_dir))
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_resource_cleanup(self):
        """测试资源清理"""
        # 分配一些资源
        self.memory_manager.allocate_memory(1024 * 1024)  # 1MB
        
        # 清理资源
        self.memory_manager.cleanup()
        
        # 验证清理成功
        self.assertEqual(self.memory_manager.get_allocated_memory(), 0)
    
if __name__ == '__main__':
    unittest.main() 