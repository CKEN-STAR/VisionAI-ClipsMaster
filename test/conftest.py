"""测试配置初始化模块

本模块为所有测试提供基础配置和公共夹具(fixtures)，主要功能包括：
1. 配置测试环境
2. 提供公共夹具
3. 设置全局资源限制
4. 提供通用模拟数据
"""

import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator

import pytest
from unittest.mock import MagicMock

# 模拟nvidia_smi模块
sys.modules['nvidia_smi'] = MagicMock()

# 确保src包在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.exceptions import ClipMasterError, ErrorCode, MemoryOverflowError
from src.core.degradation import DegradationManager, DegradationLevel
from src.core.qos_manager import QoSManager, QoSPriority
from src.utils.memory_guard import MemoryGuard
from src.utils.config_loader import ConfigLoader

# 全局测试配置
@pytest.fixture(scope="session")
def base_config() -> Dict[str, Any]:
    """提供测试基础配置参数
    
    Returns:
        Dict: 测试基础配置字典
    """
    return {
        "max_memory": 4096,  # 最大内存限制（MB）
        "timeout": 30,       # 操作超时时间（秒）
        "golden_samples": "test/golden_samples/",  # 标准样本目录
        "test_models": "test/models/",             # 测试模型目录
        "temp_dir": tempfile.gettempdir(),         # 临时文件目录
        "retry_count": 3,                          # 重试次数
        "parallel_tests": 4,                        # 并行测试数
    }

# 创建临时目录夹具
@pytest.fixture(scope="function")
def temp_dir() -> Generator[str, None, None]:
    """提供测试临时目录
    
    Yields:
        str: 临时目录路径
    """
    temp_path = tempfile.mkdtemp(prefix="visionai_test_")
    yield temp_path
    # 测试后清理
    shutil.rmtree(temp_path, ignore_errors=True)

# 创建临时配置文件夹具
@pytest.fixture(scope="function")
def temp_config_file() -> Generator[str, None, None]:
    """创建临时配置文件
    
    Yields:
        str: 临时配置文件路径
    """
    config = {
        "resource_limits": {
            "memory_limits": {
                "per_process": 1024,
                "total": 4096
            },
            "cpu_limits": {
                "max_usage": 90
            }
        },
        "security": {
            "max_memory_percent": 80,
            "max_cpu_percent": 90,
            "allowed_file_types": [".mp4", ".srt", ".txt"],
            "max_file_size_mb": 1000
        },
        "processing": {
            "max_workers": 4,
            "timeout_seconds": 30,
            "retry_count": 3
        }
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False)
    json.dump(config, temp_file)
    temp_file.close()
    
    yield temp_file.name
    
    # 测试后删除
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

# 模拟降级管理器夹具
@pytest.fixture(scope="function")
def mock_degradation_manager() -> MagicMock:
    """提供模拟的降级管理器
    
    Returns:
        MagicMock: 模拟的降级管理器
    """
    mock_dm = MagicMock(spec=DegradationManager)
    mock_dm.current_level = DegradationLevel.NORMAL
    mock_dm.register_callback = MagicMock()
    return mock_dm

# 模拟QoS管理器夹具
@pytest.fixture(scope="function")
def mock_qos_manager(mock_degradation_manager) -> MagicMock:
    """提供模拟的QoS管理器
    
    Args:
        mock_degradation_manager: 模拟的降级管理器
        
    Returns:
        MagicMock: 模拟的QoS管理器
    """
    mock_qm = MagicMock(spec=QoSManager)
    mock_qm.degradation_manager = mock_degradation_manager
    mock_qm.current_priority = QoSPriority.BALANCED
    return mock_qm

# 模拟内存监控夹具
@pytest.fixture(scope="function")
def mock_memory_guard() -> MagicMock:
    """提供模拟的内存监控
    
    Returns:
        MagicMock: 模拟的内存监控
    """
    mock_mg = MagicMock(spec=MemoryGuard)
    mock_mg.register_callback = MagicMock()
    return mock_mg

# 异常模拟测试夹具
@pytest.fixture(scope="function")
def error_maker():
    """提供异常制造函数
    
    Returns:
        函数: 根据错误类型制造异常的函数
    """
    def _make_error(error_type, **kwargs):
        """根据错误类型制造异常
        
        Args:
            error_type: 错误类型
            **kwargs: 异常构造参数
            
        Raises:
            指定类型的异常
        """
        if error_type == "memory":
            raise MemoryOverflowError(**kwargs)
        elif error_type == "timeout":
            raise ClipMasterError(code=ErrorCode.TIMEOUT_ERROR, **kwargs)
        else:
            raise ClipMasterError(code=ErrorCode.UNKNOWN_ERROR, **kwargs)
    
    return _make_error

# 模型切换器测试夹具
@pytest.fixture(scope="function")
def model_switcher_test_dir(temp_dir) -> Generator[str, None, None]:
    """为模型切换器测试创建测试目录结构
    
    Args:
        temp_dir: 测试临时目录
        
    Yields:
        str: 模型测试目录路径
    """
    # 创建模型目录结构
    model_dir = os.path.join(temp_dir, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建配置目录
    config_dir = os.path.join(model_dir, "configs")
    os.makedirs(config_dir, exist_ok=True)
    
    # 创建两种测试模型的配置
    model_configs = {
        "en": {
            "path": "en/model.bin",
            "memory_required": 1024,
            "device_requirements": {
                "min_ram": 512,
                "gpu_preferred": True
            },
            "type": "TRANSFORMER",
            "checkpoint_path": "en/checkpoint"
        },
        "zh": {
            "path": "zh/model.bin",
            "memory_required": 768,
            "device_requirements": {
                "min_ram": 384,
                "gpu_preferred": False
            },
            "type": "TRANSFORMER",
            "checkpoint_path": "zh/checkpoint"
        }
    }
    
    # 创建模型目录和文件
    for model_name, config in model_configs.items():
        model_path = os.path.join(model_dir, model_name)
        os.makedirs(model_path, exist_ok=True)
        
        # 创建模型文件
        with open(os.path.join(model_path, "model.bin"), "w") as f:
            f.write(f"Simulated {model_name} model data")
            
        # 创建检查点目录
        os.makedirs(os.path.join(model_path, "checkpoint"), exist_ok=True)
        
        # 保存配置文件
        with open(os.path.join(config_dir, f"{model_name}.yaml"), "w") as f:
            import yaml
            yaml.dump(config, f)
    
    yield model_dir

# 性能测试夹具
@pytest.fixture(scope="function")
def performance_monitor():
    """提供性能监控工具
    
    Returns:
        Dict: 性能监测函数字典
    """
    class PerfMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.results = {}
            
        def start(self):
            """开始计时"""
            self.start_time = time.time()
            return self
            
        def stop(self):
            """停止计时"""
            self.end_time = time.time()
            self.results['elapsed'] = self.end_time - self.start_time
            return self.results
            
        def add_metric(self, name, value):
            """添加指标"""
            self.results[name] = value
            
    return PerfMonitor() 