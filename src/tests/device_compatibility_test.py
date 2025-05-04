"""设备兼容性矩阵测试套件

此模块实现全面的设备兼容性测试，包括：
1. CPU兼容性测试
2. 内存配置测试
3. 存储性能测试
4. 操作系统兼容性测试
5. 模型运行性能测试
"""

import os
import sys
import platform
import psutil
import unittest
import time
from typing import Dict, List, Optional, Tuple
from loguru import logger
from ..utils.device_manager import HybridDevice
from ..utils.memory_manager import MemoryManager
from ..utils.metrics import PerformanceMetrics

class DeviceCompatibilityTest(unittest.TestCase):
    """设备兼容性测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        cls.device_manager = HybridDevice()
        cls.memory_manager = MemoryManager()
        cls.metrics = PerformanceMetrics()
        
        # 测试配置
        cls.test_config = {
            'min_cpu_cores': 2,          # 最小CPU核心数
            'min_memory_gb': 4,          # 最小内存(GB)
            'min_disk_space_gb': 10,     # 最小磁盘空间(GB)
            'min_disk_speed_mbps': 100,  # 最小磁盘速度(MB/s)
            'max_model_load_time': 30,   # 最大模型加载时间(秒)
            'min_inference_speed': 1.0,  # 最小推理速度(次/秒)
        }
        
        # 设备信息
        cls.device_info = cls._collect_device_info()
        
        # 兼容性矩阵
        cls.compatibility_matrix = {
            'cpu': {},
            'memory': {},
            'storage': {},
            'os': {},
            'model_performance': {}
        }
    
    def setUp(self):
        """准备测试环境"""
        # 记录测试开始时间
        self.start_time = time.time()
    
    def test_cpu_compatibility(self):
        """测试CPU兼容性"""
        logger.info("开始CPU兼容性测试")
        
        try:
            cpu_info = self.device_info['cpu']
            
            # 验证CPU核心数
            self.assertGreaterEqual(
                cpu_info['cores'],
                self.test_config['min_cpu_cores'],
                f"CPU核心数不足: {cpu_info['cores']} < {self.test_config['min_cpu_cores']}"
            )
            
            # 记录CPU性能
            cpu_performance = self._measure_cpu_performance()
            
            # 更新兼容性矩阵
            self.compatibility_matrix['cpu'] = {
                'cores': cpu_info['cores'],
                'model': cpu_info['model'],
                'frequency': cpu_info['frequency'],
                'performance_score': cpu_performance,
                'compatible': cpu_info['cores'] >= self.test_config['min_cpu_cores']
            }
            
        except Exception as e:
            logger.error(f"CPU兼容性测试失败: {str(e)}")
            raise
    
    def test_memory_compatibility(self):
        """测试内存兼容性"""
        logger.info("开始内存兼容性测试")
        
        try:
            memory_info = self.device_info['memory']
            
            # 验证内存大小
            self.assertGreaterEqual(
                memory_info['total_gb'],
                self.test_config['min_memory_gb'],
                f"内存不足: {memory_info['total_gb']}GB < {self.test_config['min_memory_gb']}GB"
            )
            
            # 测试内存性能
            memory_performance = self._measure_memory_performance()
            
            # 更新兼容性矩阵
            self.compatibility_matrix['memory'] = {
                'total_gb': memory_info['total_gb'],
                'available_gb': memory_info['available_gb'],
                'performance_score': memory_performance,
                'compatible': memory_info['total_gb'] >= self.test_config['min_memory_gb']
            }
            
        except Exception as e:
            logger.error(f"内存兼容性测试失败: {str(e)}")
            raise
    
    def test_storage_compatibility(self):
        """测试存储兼容性"""
        logger.info("开始存储兼容性测试")
        
        try:
            storage_info = self.device_info['storage']
            
            # 验证磁盘空间
            self.assertGreaterEqual(
                storage_info['free_gb'],
                self.test_config['min_disk_space_gb'],
                f"磁盘空间不足: {storage_info['free_gb']}GB < {self.test_config['min_disk_space_gb']}GB"
            )
            
            # 测试磁盘性能
            disk_speed = self._measure_disk_speed()
            
            # 更新兼容性矩阵
            self.compatibility_matrix['storage'] = {
                'total_gb': storage_info['total_gb'],
                'free_gb': storage_info['free_gb'],
                'speed_mbps': disk_speed,
                'compatible': (storage_info['free_gb'] >= self.test_config['min_disk_space_gb'] and
                             disk_speed >= self.test_config['min_disk_speed_mbps'])
            }
            
        except Exception as e:
            logger.error(f"存储兼容性测试失败: {str(e)}")
            raise
    
    def test_os_compatibility(self):
        """测试操作系统兼容性"""
        logger.info("开始操作系统兼容性测试")
        
        try:
            os_info = self.device_info['os']
            
            # 验证操作系统版本
            self.assertTrue(
                self._is_os_supported(os_info),
                f"不支持的操作系统: {os_info['name']} {os_info['version']}"
            )
            
            # 更新兼容性矩阵
            self.compatibility_matrix['os'] = {
                'name': os_info['name'],
                'version': os_info['version'],
                'architecture': os_info['architecture'],
                'compatible': self._is_os_supported(os_info)
            }
            
        except Exception as e:
            logger.error(f"操作系统兼容性测试失败: {str(e)}")
            raise
    
    def test_model_performance(self):
        """测试模型性能"""
        logger.info("开始模型性能测试")
        
        try:
            # 模拟模型加载和推理
            load_time = self._measure_model_load_time()
            inference_speed = self._measure_inference_speed()
            
            # 更新兼容性矩阵
            self.compatibility_matrix['model_performance'] = {
                'load_time_seconds': load_time,
                'inference_speed': inference_speed,
                'compatible': (load_time <= self.test_config['max_model_load_time'] and
                             inference_speed >= self.test_config['min_inference_speed'])
            }
            
        except Exception as e:
            logger.error(f"模型性能测试失败: {str(e)}")
            raise
    
    @classmethod
    def _collect_device_info(cls) -> Dict:
        """收集设备信息
        
        Returns:
            Dict: 设备信息
        """
        return {
            'cpu': {
                'cores': psutil.cpu_count(logical=False),
                'model': platform.processor(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None
            },
            'memory': {
                'total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'available_gb': round(psutil.virtual_memory().available / (1024**3), 2)
            },
            'storage': {
                'total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                'free_gb': round(psutil.disk_usage('/').free / (1024**3), 2)
            },
            'os': {
                'name': platform.system(),
                'version': platform.version(),
                'architecture': platform.machine()
            }
        }
    
    def _measure_cpu_performance(self) -> float:
        """测量CPU性能
        
        Returns:
            float: CPU性能得分
        """
        # 执行简单的CPU密集型计算
        start_time = time.time()
        result = 0
        for i in range(1000000):
            result += i * i
        end_time = time.time()
        
        # 计算性能得分（越高越好）
        return 1.0 / (end_time - start_time)
    
    def _measure_memory_performance(self) -> float:
        """测量内存性能
        
        Returns:
            float: 内存性能得分
        """
        # 分配和释放内存来测试性能
        size = 1024 * 1024  # 1MB
        start_time = time.time()
        
        for _ in range(100):
            memory = self.memory_manager.allocate_memory(size)
            self.memory_manager.free_memory(memory)
        
        end_time = time.time()
        
        # 计算性能得分（越高越好）
        return 100.0 / (end_time - start_time)
    
    def _measure_disk_speed(self) -> float:
        """测量磁盘速度
        
        Returns:
            float: 磁盘速度(MB/s)
        """
        # 创建临时文件测试写入速度
        import tempfile
        size = 100 * 1024 * 1024  # 100MB
        
        with tempfile.NamedTemporaryFile() as temp_file:
            start_time = time.time()
            
            # 写入测试数据
            with open(temp_file.name, 'wb') as f:
                f.write(os.urandom(size))
            
            end_time = time.time()
            
            # 计算写入速度(MB/s)
            return size / (1024 * 1024) / (end_time - start_time)
    
    def _is_os_supported(self, os_info: Dict) -> bool:
        """检查操作系统是否支持
        
        Args:
            os_info: 操作系统信息
            
        Returns:
            bool: 是否支持
        """
        supported_os = {
            'Windows': ['10', '11'],
            'Linux': ['Ubuntu', 'CentOS', 'Debian'],
            'Darwin': ['macOS']
        }
        
        return (os_info['name'] in supported_os and
                any(os_info['version'].startswith(v) for v in supported_os[os_info['name']]))
    
    def _measure_model_load_time(self) -> float:
        """测量模型加载时间
        
        Returns:
            float: 加载时间(秒)
        """
        # 模拟模型加载
        start_time = time.time()
        time.sleep(1)  # 模拟加载过程
        return time.time() - start_time
    
    def _measure_inference_speed(self) -> float:
        """测量推理速度
        
        Returns:
            float: 推理速度(次/秒)
        """
        # 模拟推理过程
        iterations = 10
        start_time = time.time()
        
        for _ in range(iterations):
            time.sleep(0.1)  # 模拟推理时间
        
        end_time = time.time()
        
        # 计算推理速度
        return iterations / (end_time - start_time)
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境并生成报告"""
        # 生成兼容性报告
        cls._generate_compatibility_report()
    
    @classmethod
    def _generate_compatibility_report(cls):
        """生成兼容性报告"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'device_info': cls.device_info,
            'compatibility_matrix': cls.compatibility_matrix,
            'overall_compatibility': all(
                matrix['compatible']
                for matrix in cls.compatibility_matrix.values()
                if 'compatible' in matrix
            )
        }
        
        # 保存报告
        import json
        report_path = 'compatibility_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        logger.info(f"兼容性报告已生成: {report_path}") 