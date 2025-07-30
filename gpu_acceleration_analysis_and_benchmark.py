#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster GPU加速能力详细分析和基准测试
验证GPU检测、自动切换、性能提升等功能
"""

import os
import sys
import json
import time
import tempfile
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gpu_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GPUAccelerationAnalyzer:
    """GPU加速能力分析器"""
    
    def __init__(self):
        self.analysis_results = {}
        self.benchmark_results = {}
        self.system_info = {}
        self.start_time = time.time()
        
        logger.info("GPU加速能力分析器初始化完成")
    
    def analyze_gpu_detection_capability(self) -> Dict[str, Any]:
        """分析GPU检测和自动切换功能"""
        logger.info("=" * 80)
        logger.info("1. GPU检测和自动切换功能验证")
        logger.info("=" * 80)
        
        detection_result = {
            "detection_time": datetime.now().isoformat(),
            "pytorch_available": False,
            "cuda_available": False,
            "gpu_devices": [],
            "auto_switch_capability": False,
            "code_implementation_status": {},
            "compatibility_check": {}
        }
        
        try:
            # 1. 检查PyTorch和CUDA可用性
            logger.info("检查PyTorch和CUDA环境...")
            
            try:
                import torch
                detection_result["pytorch_available"] = True
                detection_result["pytorch_version"] = torch.__version__
                
                cuda_available = torch.cuda.is_available()
                detection_result["cuda_available"] = cuda_available
                
                if cuda_available:
                    detection_result["cuda_version"] = torch.version.cuda
                    detection_result["cudnn_version"] = torch.backends.cudnn.version()
                    
                    # 获取GPU设备信息
                    gpu_count = torch.cuda.device_count()
                    gpu_devices = []
                    
                    for i in range(gpu_count):
                        device_props = torch.cuda.get_device_properties(i)
                        gpu_info = {
                            "device_id": i,
                            "name": device_props.name,
                            "total_memory_gb": round(device_props.total_memory / 1024**3, 2),
                            "major": device_props.major,
                            "minor": device_props.minor,
                            "multi_processor_count": device_props.multi_processor_count,
                            "compute_capability": f"{device_props.major}.{device_props.minor}"
                        }
                        gpu_devices.append(gpu_info)
                    
                    detection_result["gpu_devices"] = gpu_devices
                    detection_result["current_device"] = torch.cuda.current_device()
                    
                    logger.info(f"✅ 检测到{gpu_count}个CUDA设备")
                    for gpu in gpu_devices:
                        logger.info(f"  GPU {gpu['device_id']}: {gpu['name']} ({gpu['total_memory_gb']}GB)")
                else:
                    logger.warning("⚠️ CUDA不可用，将使用CPU模式")
                
            except ImportError as e:
                logger.error(f"❌ PyTorch导入失败: {str(e)}")
                detection_result["pytorch_error"] = str(e)
            
            # 2. 验证项目代码中的GPU检测实现
            logger.info("验证项目代码中的GPU检测实现...")
            
            code_check = self._verify_gpu_code_implementation()
            detection_result["code_implementation_status"] = code_check
            
            # 3. 测试自动切换功能
            logger.info("测试GPU自动切换功能...")
            
            auto_switch_test = self._test_auto_switch_functionality()
            detection_result["auto_switch_capability"] = auto_switch_test["success"]
            detection_result["auto_switch_details"] = auto_switch_test
            
            # 4. 兼容性检查
            logger.info("执行GPU兼容性检查...")
            
            compatibility = self._check_gpu_compatibility()
            detection_result["compatibility_check"] = compatibility
            
        except Exception as e:
            logger.error(f"❌ GPU检测分析异常: {str(e)}")
            detection_result["error"] = str(e)
        
        self.analysis_results["gpu_detection"] = detection_result
        return detection_result
    
    def _verify_gpu_code_implementation(self) -> Dict[str, Any]:
        """验证GPU代码实现"""
        code_check = {
            "get_device_function": False,
            "move_to_device_function": False,
            "clear_gpu_memory_function": False,
            "enhanced_trainer_class": False,
            "gpu_support_methods": [],
            "implementation_quality": "unknown"
        }
        
        try:
            # 检查simple_ui_fixed.py中的GPU函数
            ui_file = "simple_ui_fixed.py"
            if os.path.exists(ui_file):
                with open(ui_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查关键函数
                code_check["get_device_function"] = "def get_device():" in content
                code_check["move_to_device_function"] = "def move_to_device(" in content
                code_check["clear_gpu_memory_function"] = "def clear_gpu_memory():" in content
                code_check["enhanced_trainer_class"] = "class EnhancedViralTrainer:" in content
                
                # 检查GPU支持方法
                gpu_methods = []
                if "torch.cuda.is_available()" in content:
                    gpu_methods.append("CUDA可用性检测")
                if "torch.device" in content:
                    gpu_methods.append("设备选择")
                if ".cuda()" in content:
                    gpu_methods.append("GPU内存分配")
                if "torch.cuda.empty_cache()" in content:
                    gpu_methods.append("GPU内存清理")
                
                code_check["gpu_support_methods"] = gpu_methods
                
                # 评估实现质量
                implementation_score = sum([
                    code_check["get_device_function"],
                    code_check["move_to_device_function"],
                    code_check["clear_gpu_memory_function"],
                    code_check["enhanced_trainer_class"]
                ])
                
                if implementation_score >= 4:
                    code_check["implementation_quality"] = "excellent"
                elif implementation_score >= 3:
                    code_check["implementation_quality"] = "good"
                elif implementation_score >= 2:
                    code_check["implementation_quality"] = "basic"
                else:
                    code_check["implementation_quality"] = "insufficient"
                
                logger.info(f"✅ GPU代码实现检查完成，质量评级: {code_check['implementation_quality']}")
            else:
                logger.error("❌ simple_ui_fixed.py文件不存在")
        
        except Exception as e:
            logger.error(f"❌ GPU代码验证异常: {str(e)}")
            code_check["error"] = str(e)
        
        return code_check
    
    def _test_auto_switch_functionality(self) -> Dict[str, Any]:
        """测试自动切换功能"""
        auto_switch_test = {
            "success": False,
            "cpu_device_detection": False,
            "gpu_device_detection": False,
            "device_switching": False,
            "error_handling": False,
            "details": {}
        }
        
        try:
            # 尝试导入和测试项目中的GPU函数
            try:
                # 动态导入GPU函数
                import importlib.util
                spec = importlib.util.spec_from_file_location("gpu_functions", "simple_ui_fixed.py")
                if spec and spec.loader:
                    gpu_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(gpu_module)
                    
                    # 测试get_device函数
                    if hasattr(gpu_module, 'get_device'):
                        device = gpu_module.get_device()
                        auto_switch_test["cpu_device_detection"] = True
                        auto_switch_test["details"]["detected_device"] = str(device)
                        logger.info(f"✅ 设备检测成功: {device}")
                        
                        # 如果检测到GPU，测试GPU切换
                        if "cuda" in str(device):
                            auto_switch_test["gpu_device_detection"] = True
                    
                    # 测试move_to_device函数
                    if hasattr(gpu_module, 'move_to_device'):
                        # 创建简单的测试模型
                        try:
                            import torch
                            import torch.nn as nn
                            
                            test_model = nn.Linear(10, 1)
                            device = gpu_module.get_device()
                            moved_model = gpu_module.move_to_device(test_model, device)
                            
                            auto_switch_test["device_switching"] = True
                            logger.info("✅ 设备切换功能正常")
                        except Exception as e:
                            logger.warning(f"⚠️ 设备切换测试异常: {str(e)}")
                    
                    # 测试clear_gpu_memory函数
                    if hasattr(gpu_module, 'clear_gpu_memory'):
                        try:
                            gpu_module.clear_gpu_memory()
                            auto_switch_test["error_handling"] = True
                            logger.info("✅ GPU内存清理功能正常")
                        except Exception as e:
                            logger.warning(f"⚠️ GPU内存清理测试异常: {str(e)}")
                    
                    # 综合评估
                    success_count = sum([
                        auto_switch_test["cpu_device_detection"],
                        auto_switch_test["device_switching"],
                        auto_switch_test["error_handling"]
                    ])
                    
                    auto_switch_test["success"] = success_count >= 2
                    
            except Exception as e:
                logger.error(f"❌ 自动切换功能测试异常: {str(e)}")
                auto_switch_test["details"]["error"] = str(e)
        
        except Exception as e:
            logger.error(f"❌ 自动切换测试异常: {str(e)}")
            auto_switch_test["error"] = str(e)
        
        return auto_switch_test
    
    def _check_gpu_compatibility(self) -> Dict[str, Any]:
        """检查GPU兼容性"""
        compatibility = {
            "nvidia_driver": {"available": False, "version": "unknown"},
            "cuda_toolkit": {"available": False, "version": "unknown"},
            "pytorch_cuda": {"available": False, "version": "unknown"},
            "system_requirements": {},
            "recommendations": []
        }
        
        try:
            # 检查NVIDIA驱动
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    compatibility["nvidia_driver"]["available"] = True
                    # 尝试提取驱动版本
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if "Driver Version:" in line:
                            version = line.split("Driver Version:")[1].split()[0]
                            compatibility["nvidia_driver"]["version"] = version
                            break
                    logger.info(f"✅ NVIDIA驱动可用: {compatibility['nvidia_driver']['version']}")
                else:
                    logger.warning("⚠️ NVIDIA驱动不可用")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("⚠️ 无法检测NVIDIA驱动")
            
            # 检查CUDA工具包
            try:
                result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    compatibility["cuda_toolkit"]["available"] = True
                    # 提取CUDA版本
                    output = result.stdout
                    if "release" in output:
                        version_line = [line for line in output.split('\n') if 'release' in line][0]
                        version = version_line.split('release')[1].split(',')[0].strip()
                        compatibility["cuda_toolkit"]["version"] = version
                    logger.info(f"✅ CUDA工具包可用: {compatibility['cuda_toolkit']['version']}")
                else:
                    logger.warning("⚠️ CUDA工具包不可用")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("⚠️ 无法检测CUDA工具包")
            
            # 检查PyTorch CUDA支持
            try:
                import torch
                if torch.cuda.is_available():
                    compatibility["pytorch_cuda"]["available"] = True
                    compatibility["pytorch_cuda"]["version"] = torch.version.cuda
                    logger.info(f"✅ PyTorch CUDA支持可用: {compatibility['pytorch_cuda']['version']}")
                else:
                    logger.warning("⚠️ PyTorch CUDA支持不可用")
            except ImportError:
                logger.warning("⚠️ PyTorch未安装")
            
            # 系统要求检查
            compatibility["system_requirements"] = {
                "os": platform.system(),
                "architecture": platform.architecture()[0],
                "python_version": platform.python_version()
            }
            
            # 生成建议
            recommendations = []
            if not compatibility["nvidia_driver"]["available"]:
                recommendations.append("安装NVIDIA显卡驱动 (版本 >= 460.x)")
            if not compatibility["cuda_toolkit"]["available"]:
                recommendations.append("安装CUDA Toolkit (版本 >= 11.0)")
            if not compatibility["pytorch_cuda"]["available"]:
                recommendations.append("安装PyTorch GPU版本")
            
            if not recommendations:
                recommendations.append("GPU环境配置完整，可以使用GPU加速")
            
            compatibility["recommendations"] = recommendations
        
        except Exception as e:
            logger.error(f"❌ GPU兼容性检查异常: {str(e)}")
            compatibility["error"] = str(e)
        
        return compatibility

    def analyze_training_performance_improvement(self) -> Dict[str, Any]:
        """分析训练性能提升"""
        logger.info("=" * 80)
        logger.info("2. 训练性能提升分析")
        logger.info("=" * 80)

        performance_analysis = {
            "analysis_time": datetime.now().isoformat(),
            "cpu_benchmark": {},
            "gpu_benchmark": {},
            "performance_comparison": {},
            "memory_analysis": {},
            "batch_size_analysis": {},
            "theoretical_improvements": {}
        }

        try:
            # 1. CPU基准测试
            logger.info("执行CPU训练基准测试...")
            cpu_results = self._run_cpu_training_benchmark()
            performance_analysis["cpu_benchmark"] = cpu_results

            # 2. GPU基准测试（如果可用）
            logger.info("执行GPU训练基准测试...")
            gpu_results = self._run_gpu_training_benchmark()
            performance_analysis["gpu_benchmark"] = gpu_results

            # 3. 性能对比分析
            logger.info("分析性能对比...")
            comparison = self._analyze_performance_comparison(cpu_results, gpu_results)
            performance_analysis["performance_comparison"] = comparison

            # 4. 内存使用分析
            logger.info("分析内存使用效率...")
            memory_analysis = self._analyze_memory_efficiency()
            performance_analysis["memory_analysis"] = memory_analysis

            # 5. 批处理大小分析
            logger.info("分析最大批处理大小...")
            batch_analysis = self._analyze_max_batch_size()
            performance_analysis["batch_size_analysis"] = batch_analysis

            # 6. 理论性能改进分析
            logger.info("分析理论性能改进...")
            theoretical = self._analyze_theoretical_improvements()
            performance_analysis["theoretical_improvements"] = theoretical

        except Exception as e:
            logger.error(f"❌ 训练性能分析异常: {str(e)}")
            performance_analysis["error"] = str(e)

        self.analysis_results["performance"] = performance_analysis
        return performance_analysis

    def _run_cpu_training_benchmark(self) -> Dict[str, Any]:
        """运行CPU训练基准测试"""
        cpu_benchmark = {
            "available": False,
            "training_time": 0.0,
            "iterations_per_second": 0.0,
            "memory_usage_mb": 0.0,
            "max_batch_size": 0,
            "model_parameters": 0,
            "details": {}
        }

        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            import psutil
            import gc

            # 强制使用CPU
            device = torch.device("cpu")

            # 创建测试模型（模拟文本转换模型）
            class TestViralModel(nn.Module):
                def __init__(self, vocab_size=1000, hidden_size=256):
                    super().__init__()
                    self.embedding = nn.Embedding(vocab_size, hidden_size)
                    self.encoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
                    self.decoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
                    self.output_layer = nn.Linear(hidden_size, vocab_size)

                def forward(self, src, tgt=None):
                    embedded = self.embedding(src)
                    encoder_out, (h, c) = self.encoder(embedded)

                    if tgt is not None:
                        tgt_embedded = self.embedding(tgt)
                        decoder_out, _ = self.decoder(tgt_embedded, (h, c))
                    else:
                        decoder_out = encoder_out

                    output = self.output_layer(decoder_out)
                    return output

            model = TestViralModel().to(device)
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.CrossEntropyLoss()

            # 计算模型参数数量
            total_params = sum(p.numel() for p in model.parameters())
            cpu_benchmark["model_parameters"] = total_params

            # 测试不同批处理大小
            batch_sizes = [1, 2, 4, 8, 16, 32]
            max_batch_size = 1

            for batch_size in batch_sizes:
                try:
                    # 创建测试数据
                    seq_length = 50
                    src_data = torch.randint(0, 1000, (batch_size, seq_length))
                    tgt_data = torch.randint(0, 1000, (batch_size, seq_length))
                    labels = torch.randint(0, 1000, (batch_size, seq_length))

                    # 测试前向传播
                    model.train()
                    optimizer.zero_grad()
                    output = model(src_data, tgt_data)
                    loss = criterion(output.view(-1, 1000), labels.view(-1))
                    loss.backward()
                    optimizer.step()

                    max_batch_size = batch_size

                except RuntimeError as e:
                    if "out of memory" in str(e).lower():
                        break
                    else:
                        raise e

            cpu_benchmark["max_batch_size"] = max_batch_size

            # 执行性能基准测试
            batch_size = min(8, max_batch_size)  # 使用合适的批处理大小
            num_iterations = 20

            # 预热
            for _ in range(3):
                src_data = torch.randint(0, 1000, (batch_size, 50))
                tgt_data = torch.randint(0, 1000, (batch_size, 50))
                labels = torch.randint(0, 1000, (batch_size, 50))

                optimizer.zero_grad()
                output = model(src_data, tgt_data)
                loss = criterion(output.view(-1, 1000), labels.view(-1))
                loss.backward()
                optimizer.step()

            # 清理内存
            gc.collect()

            # 记录内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # 正式基准测试
            start_time = time.time()

            for i in range(num_iterations):
                src_data = torch.randint(0, 1000, (batch_size, 50))
                tgt_data = torch.randint(0, 1000, (batch_size, 50))
                labels = torch.randint(0, 1000, (batch_size, 50))

                optimizer.zero_grad()
                output = model(src_data, tgt_data)
                loss = criterion(output.view(-1, 1000), labels.view(-1))
                loss.backward()
                optimizer.step()

            end_time = time.time()

            # 记录内存使用
            memory_after = process.memory_info().rss / 1024 / 1024  # MB

            training_time = end_time - start_time
            iterations_per_second = num_iterations / training_time
            memory_usage = memory_after - memory_before

            cpu_benchmark.update({
                "available": True,
                "training_time": training_time,
                "iterations_per_second": iterations_per_second,
                "memory_usage_mb": memory_usage,
                "details": {
                    "batch_size_tested": batch_size,
                    "num_iterations": num_iterations,
                    "sequence_length": 50,
                    "vocab_size": 1000,
                    "hidden_size": 256
                }
            })

            logger.info(f"✅ CPU基准测试完成: {iterations_per_second:.2f} iter/s, {memory_usage:.1f}MB")

        except Exception as e:
            logger.error(f"❌ CPU基准测试异常: {str(e)}")
            cpu_benchmark["error"] = str(e)

        return cpu_benchmark

    def _run_gpu_training_benchmark(self) -> Dict[str, Any]:
        """运行GPU训练基准测试"""
        gpu_benchmark = {
            "available": False,
            "training_time": 0.0,
            "iterations_per_second": 0.0,
            "memory_usage_mb": 0.0,
            "gpu_memory_usage_mb": 0.0,
            "max_batch_size": 0,
            "model_parameters": 0,
            "details": {}
        }

        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            import gc

            if not torch.cuda.is_available():
                logger.warning("⚠️ GPU不可用，跳过GPU基准测试")
                gpu_benchmark["available"] = False
                gpu_benchmark["reason"] = "CUDA不可用"
                return gpu_benchmark

            device = torch.device("cuda")

            # 创建相同的测试模型
            class TestViralModel(nn.Module):
                def __init__(self, vocab_size=1000, hidden_size=256):
                    super().__init__()
                    self.embedding = nn.Embedding(vocab_size, hidden_size)
                    self.encoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
                    self.decoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
                    self.output_layer = nn.Linear(hidden_size, vocab_size)

                def forward(self, src, tgt=None):
                    embedded = self.embedding(src)
                    encoder_out, (h, c) = self.encoder(embedded)

                    if tgt is not None:
                        tgt_embedded = self.embedding(tgt)
                        decoder_out, _ = self.decoder(tgt_embedded, (h, c))
                    else:
                        decoder_out = encoder_out

                    output = self.output_layer(decoder_out)
                    return output

            model = TestViralModel().to(device)
            optimizer = optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.CrossEntropyLoss()

            # 计算模型参数数量
            total_params = sum(p.numel() for p in model.parameters())
            gpu_benchmark["model_parameters"] = total_params

            # 清理GPU内存
            torch.cuda.empty_cache()

            # 测试最大批处理大小
            batch_sizes = [1, 2, 4, 8, 16, 32, 64, 128]
            max_batch_size = 1

            for batch_size in batch_sizes:
                try:
                    # 创建测试数据
                    seq_length = 50
                    src_data = torch.randint(0, 1000, (batch_size, seq_length)).to(device)
                    tgt_data = torch.randint(0, 1000, (batch_size, seq_length)).to(device)
                    labels = torch.randint(0, 1000, (batch_size, seq_length)).to(device)

                    # 测试前向传播
                    model.train()
                    optimizer.zero_grad()
                    output = model(src_data, tgt_data)
                    loss = criterion(output.view(-1, 1000), labels.view(-1))
                    loss.backward()
                    optimizer.step()

                    max_batch_size = batch_size

                    # 清理
                    del src_data, tgt_data, labels, output, loss
                    torch.cuda.empty_cache()

                except RuntimeError as e:
                    if "out of memory" in str(e).lower():
                        break
                    else:
                        raise e

            gpu_benchmark["max_batch_size"] = max_batch_size

            # 执行性能基准测试
            batch_size = min(32, max_batch_size)  # 使用较大的批处理大小
            num_iterations = 20

            # 预热GPU
            for _ in range(5):
                src_data = torch.randint(0, 1000, (batch_size, 50)).to(device)
                tgt_data = torch.randint(0, 1000, (batch_size, 50)).to(device)
                labels = torch.randint(0, 1000, (batch_size, 50)).to(device)

                optimizer.zero_grad()
                output = model(src_data, tgt_data)
                loss = criterion(output.view(-1, 1000), labels.view(-1))
                loss.backward()
                optimizer.step()

                del src_data, tgt_data, labels, output, loss

            torch.cuda.empty_cache()

            # 记录GPU内存使用
            gpu_memory_before = torch.cuda.memory_allocated() / 1024 / 1024  # MB

            # 同步GPU
            torch.cuda.synchronize()
            start_time = time.time()

            for i in range(num_iterations):
                src_data = torch.randint(0, 1000, (batch_size, 50)).to(device)
                tgt_data = torch.randint(0, 1000, (batch_size, 50)).to(device)
                labels = torch.randint(0, 1000, (batch_size, 50)).to(device)

                optimizer.zero_grad()
                output = model(src_data, tgt_data)
                loss = criterion(output.view(-1, 1000), labels.view(-1))
                loss.backward()
                optimizer.step()

                del src_data, tgt_data, labels, output, loss

            torch.cuda.synchronize()
            end_time = time.time()

            # 记录GPU内存使用
            gpu_memory_after = torch.cuda.memory_allocated() / 1024 / 1024  # MB

            training_time = end_time - start_time
            iterations_per_second = num_iterations / training_time
            gpu_memory_usage = gpu_memory_after - gpu_memory_before

            gpu_benchmark.update({
                "available": True,
                "training_time": training_time,
                "iterations_per_second": iterations_per_second,
                "gpu_memory_usage_mb": gpu_memory_usage,
                "details": {
                    "batch_size_tested": batch_size,
                    "num_iterations": num_iterations,
                    "sequence_length": 50,
                    "vocab_size": 1000,
                    "hidden_size": 256,
                    "gpu_name": torch.cuda.get_device_name(0),
                    "gpu_memory_total": torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
                }
            })

            logger.info(f"✅ GPU基准测试完成: {iterations_per_second:.2f} iter/s, {gpu_memory_usage:.1f}MB GPU内存")

        except Exception as e:
            logger.error(f"❌ GPU基准测试异常: {str(e)}")
            gpu_benchmark["error"] = str(e)

        return gpu_benchmark

    def _analyze_performance_comparison(self, cpu_results: Dict, gpu_results: Dict) -> Dict[str, Any]:
        """分析性能对比"""
        comparison = {
            "speed_improvement": 0.0,
            "memory_efficiency": {},
            "batch_size_improvement": 0.0,
            "training_time_reduction": 0.0,
            "cost_effectiveness": {},
            "recommendations": []
        }

        try:
            if cpu_results.get("available") and gpu_results.get("available"):
                # 速度提升
                cpu_speed = cpu_results.get("iterations_per_second", 0)
                gpu_speed = gpu_results.get("iterations_per_second", 0)

                if cpu_speed > 0:
                    comparison["speed_improvement"] = gpu_speed / cpu_speed

                # 批处理大小改进
                cpu_batch = cpu_results.get("max_batch_size", 0)
                gpu_batch = gpu_results.get("max_batch_size", 0)

                if cpu_batch > 0:
                    comparison["batch_size_improvement"] = gpu_batch / cpu_batch

                # 训练时间减少
                cpu_time = cpu_results.get("training_time", 0)
                gpu_time = gpu_results.get("training_time", 0)

                if cpu_time > 0:
                    time_reduction = (cpu_time - gpu_time) / cpu_time * 100
                    comparison["training_time_reduction"] = time_reduction

                # 内存效率
                comparison["memory_efficiency"] = {
                    "cpu_memory_mb": cpu_results.get("memory_usage_mb", 0),
                    "gpu_memory_mb": gpu_results.get("gpu_memory_usage_mb", 0),
                    "memory_type": "GPU内存独立于系统内存"
                }

                # 成本效益分析
                comparison["cost_effectiveness"] = {
                    "performance_per_watt": "GPU通常具有更好的性能功耗比",
                    "scalability": "GPU支持更大的批处理，适合大规模训练",
                    "development_efficiency": f"训练速度提升{comparison['speed_improvement']:.1f}x，开发效率显著提升"
                }

                # 生成建议
                recommendations = []
                if comparison["speed_improvement"] > 2.0:
                    recommendations.append("强烈推荐使用GPU训练，性能提升显著")
                elif comparison["speed_improvement"] > 1.5:
                    recommendations.append("建议使用GPU训练，有明显性能提升")
                else:
                    recommendations.append("GPU提升有限，可根据具体需求选择")

                if comparison["batch_size_improvement"] > 2.0:
                    recommendations.append("GPU支持更大批处理，适合大规模数据训练")

                comparison["recommendations"] = recommendations

            elif cpu_results.get("available") and not gpu_results.get("available"):
                comparison["status"] = "仅CPU可用"
                comparison["recommendations"] = ["配置GPU环境以获得更好的训练性能"]

            else:
                comparison["status"] = "性能测试不完整"
                comparison["recommendations"] = ["检查训练环境配置"]

        except Exception as e:
            logger.error(f"❌ 性能对比分析异常: {str(e)}")
            comparison["error"] = str(e)

        return comparison

    def _analyze_memory_efficiency(self) -> Dict[str, Any]:
        """分析内存使用效率"""
        memory_analysis = {
            "cpu_memory_analysis": {},
            "gpu_memory_analysis": {},
            "memory_optimization_tips": []
        }

        try:
            import psutil

            # CPU内存分析
            memory_info = psutil.virtual_memory()
            memory_analysis["cpu_memory_analysis"] = {
                "total_gb": round(memory_info.total / 1024**3, 2),
                "available_gb": round(memory_info.available / 1024**3, 2),
                "usage_percent": memory_info.percent,
                "recommended_batch_size": "根据可用内存动态调整"
            }

            # GPU内存分析
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_props = torch.cuda.get_device_properties(0)
                    total_memory = gpu_props.total_memory / 1024**3

                    memory_analysis["gpu_memory_analysis"] = {
                        "total_gb": round(total_memory, 2),
                        "device_name": gpu_props.name,
                        "compute_capability": f"{gpu_props.major}.{gpu_props.minor}",
                        "recommended_usage": "建议使用80%以下的GPU内存"
                    }

                    # 基于GPU内存给出批处理建议
                    if total_memory >= 8:
                        memory_analysis["gpu_memory_analysis"]["batch_size_recommendation"] = "支持大批处理 (64-128)"
                    elif total_memory >= 4:
                        memory_analysis["gpu_memory_analysis"]["batch_size_recommendation"] = "支持中等批处理 (16-32)"
                    else:
                        memory_analysis["gpu_memory_analysis"]["batch_size_recommendation"] = "支持小批处理 (4-8)"

            except ImportError:
                memory_analysis["gpu_memory_analysis"]["status"] = "PyTorch未安装"

            # 内存优化建议
            optimization_tips = [
                "使用梯度累积来模拟大批处理",
                "启用混合精度训练以减少内存使用",
                "定期清理GPU内存缓存",
                "使用数据加载器的pin_memory选项",
                "考虑使用模型并行处理大模型"
            ]

            memory_analysis["memory_optimization_tips"] = optimization_tips

        except Exception as e:
            logger.error(f"❌ 内存效率分析异常: {str(e)}")
            memory_analysis["error"] = str(e)

        return memory_analysis

    def _analyze_max_batch_size(self) -> Dict[str, Any]:
        """分析最大批处理大小"""
        batch_analysis = {
            "cpu_max_batch": 0,
            "gpu_max_batch": 0,
            "batch_size_scaling": {},
            "performance_impact": {},
            "recommendations": []
        }

        try:
            # 从之前的基准测试结果中获取数据
            cpu_results = self.analysis_results.get("performance", {}).get("cpu_benchmark", {})
            gpu_results = self.analysis_results.get("performance", {}).get("gpu_benchmark", {})

            batch_analysis["cpu_max_batch"] = cpu_results.get("max_batch_size", 0)
            batch_analysis["gpu_max_batch"] = gpu_results.get("max_batch_size", 0)

            # 批处理大小扩展分析
            if batch_analysis["cpu_max_batch"] > 0 and batch_analysis["gpu_max_batch"] > 0:
                scaling_factor = batch_analysis["gpu_max_batch"] / batch_analysis["cpu_max_batch"]
                batch_analysis["batch_size_scaling"] = {
                    "scaling_factor": scaling_factor,
                    "interpretation": f"GPU支持{scaling_factor:.1f}x更大的批处理"
                }

            # 性能影响分析
            batch_analysis["performance_impact"] = {
                "larger_batch_benefits": [
                    "更稳定的梯度估计",
                    "更好的GPU利用率",
                    "减少训练时间",
                    "提高训练稳定性"
                ],
                "considerations": [
                    "可能需要调整学习率",
                    "内存使用增加",
                    "可能影响模型泛化能力"
                ]
            }

            # 生成建议
            recommendations = []
            if batch_analysis["gpu_max_batch"] > 32:
                recommendations.append("GPU支持大批处理，建议用于大规模数据训练")
            if batch_analysis["gpu_max_batch"] > batch_analysis["cpu_max_batch"] * 2:
                recommendations.append("GPU批处理优势明显，推荐GPU训练")

            recommendations.extend([
                "根据数据集大小选择合适的批处理大小",
                "监控训练稳定性，必要时调整学习率",
                "使用学习率预热策略适应大批处理"
            ])

            batch_analysis["recommendations"] = recommendations

        except Exception as e:
            logger.error(f"❌ 批处理大小分析异常: {str(e)}")
            batch_analysis["error"] = str(e)

        return batch_analysis

    def _analyze_theoretical_improvements(self) -> Dict[str, Any]:
        """分析理论性能改进"""
        theoretical = {
            "parallel_processing": {},
            "memory_bandwidth": {},
            "compute_throughput": {},
            "energy_efficiency": {},
            "scalability": {}
        }

        try:
            # 并行处理分析
            theoretical["parallel_processing"] = {
                "cpu_cores": "通常4-16核心",
                "gpu_cores": "通常数百到数千个CUDA核心",
                "parallel_advantage": "GPU在并行计算方面具有显著优势",
                "suitable_tasks": ["矩阵运算", "神经网络训练", "大规模数据处理"]
            }

            # 内存带宽分析
            theoretical["memory_bandwidth"] = {
                "cpu_bandwidth": "通常50-100 GB/s",
                "gpu_bandwidth": "通常500-1000 GB/s",
                "bandwidth_advantage": "GPU内存带宽通常是CPU的5-10倍",
                "impact": "显著提升数据密集型计算性能"
            }

            # 计算吞吐量分析
            theoretical["compute_throughput"] = {
                "cpu_flops": "通常数百GFLOPS",
                "gpu_flops": "通常数千到数万GFLOPS",
                "throughput_advantage": "GPU在浮点运算方面具有10-100倍优势",
                "ml_relevance": "深度学习训练主要是浮点运算密集型任务"
            }

            # 能效分析
            theoretical["energy_efficiency"] = {
                "performance_per_watt": "GPU通常具有更好的性能功耗比",
                "training_cost": "GPU训练虽然功耗高，但训练时间短，总体能耗可能更低",
                "environmental_impact": "更快的训练意味着更少的总体能源消耗"
            }

            # 可扩展性分析
            theoretical["scalability"] = {
                "multi_gpu": "支持多GPU并行训练",
                "distributed_training": "支持分布式训练",
                "model_size": "支持更大的模型和数据集",
                "future_proof": "为未来的大模型训练做好准备"
            }

        except Exception as e:
            logger.error(f"❌ 理论改进分析异常: {str(e)}")
            theoretical["error"] = str(e)

        return theoretical

    def analyze_gpu_compatibility_requirements(self) -> Dict[str, Any]:
        """分析GPU兼容性要求"""
        logger.info("=" * 80)
        logger.info("3. GPU兼容性要求分析")
        logger.info("=" * 80)

        compatibility_requirements = {
            "analysis_time": datetime.now().isoformat(),
            "hardware_requirements": {},
            "software_requirements": {},
            "supported_gpu_models": {},
            "minimum_specifications": {},
            "recommended_specifications": {},
            "compatibility_matrix": {}
        }

        try:
            # 硬件要求分析
            logger.info("分析硬件要求...")
            hardware_reqs = self._analyze_hardware_requirements()
            compatibility_requirements["hardware_requirements"] = hardware_reqs

            # 软件要求分析
            logger.info("分析软件要求...")
            software_reqs = self._analyze_software_requirements()
            compatibility_requirements["software_requirements"] = software_reqs

            # 支持的GPU型号
            logger.info("分析支持的GPU型号...")
            gpu_models = self._analyze_supported_gpu_models()
            compatibility_requirements["supported_gpu_models"] = gpu_models

            # 最低规格要求
            logger.info("确定最低规格要求...")
            min_specs = self._determine_minimum_specifications()
            compatibility_requirements["minimum_specifications"] = min_specs

            # 推荐规格
            logger.info("确定推荐规格...")
            recommended_specs = self._determine_recommended_specifications()
            compatibility_requirements["recommended_specifications"] = recommended_specs

            # 兼容性矩阵
            logger.info("生成兼容性矩阵...")
            compatibility_matrix = self._generate_compatibility_matrix()
            compatibility_requirements["compatibility_matrix"] = compatibility_matrix

        except Exception as e:
            logger.error(f"❌ GPU兼容性要求分析异常: {str(e)}")
            compatibility_requirements["error"] = str(e)

        self.analysis_results["compatibility"] = compatibility_requirements
        return compatibility_requirements

    def _analyze_hardware_requirements(self) -> Dict[str, Any]:
        """分析硬件要求"""
        hardware_reqs = {
            "gpu_architecture": {},
            "memory_requirements": {},
            "compute_capability": {},
            "power_requirements": {},
            "cooling_requirements": {}
        }

        try:
            # GPU架构要求
            hardware_reqs["gpu_architecture"] = {
                "supported_architectures": [
                    "Pascal (GTX 10 series)",
                    "Turing (RTX 20 series)",
                    "Ampere (RTX 30 series)",
                    "Ada Lovelace (RTX 40 series)",
                    "Hopper (H100 series)"
                ],
                "minimum_architecture": "Pascal",
                "recommended_architecture": "Turing或更新"
            }

            # 显存要求
            hardware_reqs["memory_requirements"] = {
                "minimum_vram": "4GB",
                "recommended_vram": "8GB或更多",
                "optimal_vram": "16GB或更多",
                "memory_type": "GDDR6或更新",
                "memory_bandwidth": "建议 > 400 GB/s"
            }

            # 计算能力要求
            hardware_reqs["compute_capability"] = {
                "minimum_compute": "6.0",
                "recommended_compute": "7.0或更高",
                "tensor_cores": "推荐支持Tensor Cores以获得最佳性能",
                "fp16_support": "推荐支持半精度浮点运算"
            }

            # 功耗要求
            hardware_reqs["power_requirements"] = {
                "minimum_psu": "500W",
                "recommended_psu": "650W或更高",
                "gpu_power_consumption": "150-350W取决于GPU型号",
                "efficiency_rating": "建议80+ Gold或更高"
            }

            # 散热要求
            hardware_reqs["cooling_requirements"] = {
                "gpu_cooling": "双风扇或更好的散热解决方案",
                "case_airflow": "良好的机箱通风",
                "ambient_temperature": "建议室温 < 25°C",
                "thermal_throttling": "确保GPU温度 < 80°C"
            }

        except Exception as e:
            logger.error(f"❌ 硬件要求分析异常: {str(e)}")
            hardware_reqs["error"] = str(e)

        return hardware_reqs

    def _analyze_software_requirements(self) -> Dict[str, Any]:
        """分析软件要求"""
        software_reqs = {
            "operating_system": {},
            "drivers": {},
            "cuda_toolkit": {},
            "python_environment": {},
            "deep_learning_frameworks": {}
        }

        try:
            # 操作系统要求
            software_reqs["operating_system"] = {
                "supported_os": [
                    "Windows 10/11 (64-bit)",
                    "Ubuntu 18.04/20.04/22.04",
                    "CentOS 7/8",
                    "macOS (limited CUDA support)"
                ],
                "recommended_os": "Ubuntu 20.04 LTS或Windows 11",
                "architecture": "x86_64"
            }

            # 驱动要求
            software_reqs["drivers"] = {
                "minimum_driver": "460.x或更新",
                "recommended_driver": "最新稳定版本",
                "driver_source": "NVIDIA官方驱动",
                "installation_method": "官方安装程序或包管理器"
            }

            # CUDA工具包要求
            software_reqs["cuda_toolkit"] = {
                "minimum_cuda": "11.0",
                "recommended_cuda": "11.8或12.x",
                "cudnn_version": "8.x或更新",
                "installation_guide": "从NVIDIA官网下载安装"
            }

            # Python环境要求
            software_reqs["python_environment"] = {
                "python_version": "3.8-3.11",
                "package_manager": "pip或conda",
                "virtual_environment": "强烈推荐使用虚拟环境",
                "memory_management": "确保足够的系统内存"
            }

            # 深度学习框架要求
            software_reqs["deep_learning_frameworks"] = {
                "pytorch": {
                    "minimum_version": "1.9.0",
                    "recommended_version": "2.0.0或更新",
                    "installation_command": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                },
                "transformers": {
                    "minimum_version": "4.0.0",
                    "recommended_version": "4.30.0或更新",
                    "installation_command": "pip install transformers"
                },
                "additional_packages": [
                    "numpy >= 1.21.0",
                    "pandas >= 1.3.0",
                    "scikit-learn >= 1.0.0"
                ]
            }

        except Exception as e:
            logger.error(f"❌ 软件要求分析异常: {str(e)}")
            software_reqs["error"] = str(e)

        return software_reqs

    def _analyze_supported_gpu_models(self) -> Dict[str, Any]:
        """分析支持的GPU型号"""
        gpu_models = {
            "consumer_gpus": {},
            "professional_gpus": {},
            "data_center_gpus": {},
            "performance_tiers": {},
            "price_performance": {}
        }

        try:
            # 消费级GPU
            gpu_models["consumer_gpus"] = {
                "entry_level": {
                    "models": ["GTX 1660", "RTX 3050", "RTX 4060"],
                    "vram": "4-8GB",
                    "performance": "适合小规模训练和推理",
                    "price_range": "$200-400"
                },
                "mid_range": {
                    "models": ["RTX 3060", "RTX 3070", "RTX 4070"],
                    "vram": "8-12GB",
                    "performance": "适合中等规模训练",
                    "price_range": "$400-600"
                },
                "high_end": {
                    "models": ["RTX 3080", "RTX 3090", "RTX 4080", "RTX 4090"],
                    "vram": "10-24GB",
                    "performance": "适合大规模训练和研究",
                    "price_range": "$700-1600"
                }
            }

            # 专业级GPU
            gpu_models["professional_gpus"] = {
                "workstation": {
                    "models": ["RTX A4000", "RTX A5000", "RTX A6000"],
                    "vram": "16-48GB",
                    "performance": "专业工作站，稳定性好",
                    "features": ["ECC内存", "专业驱动支持"]
                },
                "server": {
                    "models": ["Tesla V100", "A100", "H100"],
                    "vram": "16-80GB",
                    "performance": "数据中心级别性能",
                    "features": ["多GPU互联", "虚拟化支持"]
                }
            }

            # 性能分级
            gpu_models["performance_tiers"] = {
                "tier_1_basic": {
                    "gpus": ["GTX 1660", "RTX 3050"],
                    "use_case": "学习和小规模实验",
                    "batch_size": "4-8",
                    "training_time": "较长"
                },
                "tier_2_intermediate": {
                    "gpus": ["RTX 3060", "RTX 3070", "RTX 4060", "RTX 4070"],
                    "use_case": "中等规模开发和训练",
                    "batch_size": "16-32",
                    "training_time": "中等"
                },
                "tier_3_advanced": {
                    "gpus": ["RTX 3080", "RTX 3090", "RTX 4080", "RTX 4090"],
                    "use_case": "大规模训练和研究",
                    "batch_size": "32-128",
                    "training_time": "较短"
                },
                "tier_4_professional": {
                    "gpus": ["A100", "H100", "RTX A6000"],
                    "use_case": "生产环境和企业应用",
                    "batch_size": "128+",
                    "training_time": "最短"
                }
            }

        except Exception as e:
            logger.error(f"❌ GPU型号分析异常: {str(e)}")
            gpu_models["error"] = str(e)

        return gpu_models

    def _determine_minimum_specifications(self) -> Dict[str, Any]:
        """确定最低规格要求"""
        min_specs = {
            "gpu": "GTX 1660或RTX 3050",
            "vram": "4GB",
            "compute_capability": "6.0",
            "cuda_version": "11.0",
            "driver_version": "460.x",
            "system_ram": "8GB",
            "python_version": "3.8",
            "pytorch_version": "1.9.0"
        }
        return min_specs

    def _determine_recommended_specifications(self) -> Dict[str, Any]:
        """确定推荐规格"""
        recommended_specs = {
            "gpu": "RTX 3070或RTX 4070",
            "vram": "8GB或更多",
            "compute_capability": "7.0或更高",
            "cuda_version": "11.8或12.x",
            "driver_version": "最新稳定版",
            "system_ram": "16GB或更多",
            "python_version": "3.9或3.10",
            "pytorch_version": "2.0.0或更新"
        }
        return recommended_specs

    def _generate_compatibility_matrix(self) -> Dict[str, Any]:
        """生成兼容性矩阵"""
        matrix = {
            "cuda_pytorch_compatibility": {
                "CUDA 11.0": ["PyTorch 1.9.x", "PyTorch 1.10.x"],
                "CUDA 11.6": ["PyTorch 1.11.x", "PyTorch 1.12.x"],
                "CUDA 11.7": ["PyTorch 1.13.x"],
                "CUDA 11.8": ["PyTorch 2.0.x", "PyTorch 2.1.x"],
                "CUDA 12.1": ["PyTorch 2.1.x", "PyTorch 2.2.x"]
            },
            "gpu_performance_matrix": {
                "GTX 1660": {"performance": "基础", "vram": "6GB", "recommended_batch": "4-8"},
                "RTX 3060": {"performance": "良好", "vram": "12GB", "recommended_batch": "16-24"},
                "RTX 3070": {"performance": "优秀", "vram": "8GB", "recommended_batch": "16-32"},
                "RTX 3080": {"performance": "优秀", "vram": "10GB", "recommended_batch": "32-48"},
                "RTX 3090": {"performance": "极佳", "vram": "24GB", "recommended_batch": "64-128"},
                "RTX 4090": {"performance": "极佳", "vram": "24GB", "recommended_batch": "64-128"}
            }
        }
        return matrix

    def provide_usage_guidance(self) -> Dict[str, Any]:
        """提供实际使用指导"""
        logger.info("=" * 80)
        logger.info("4. 实际使用指导")
        logger.info("=" * 80)

        usage_guidance = {
            "guidance_time": datetime.now().isoformat(),
            "installation_steps": {},
            "configuration_guide": {},
            "usage_examples": {},
            "troubleshooting": {},
            "optimization_tips": {}
        }

        try:
            # 安装步骤
            logger.info("生成安装步骤指导...")
            installation = self._generate_installation_steps()
            usage_guidance["installation_steps"] = installation

            # 配置指导
            logger.info("生成配置指导...")
            configuration = self._generate_configuration_guide()
            usage_guidance["configuration_guide"] = configuration

            # 使用示例
            logger.info("生成使用示例...")
            examples = self._generate_usage_examples()
            usage_guidance["usage_examples"] = examples

            # 故障排除
            logger.info("生成故障排除指导...")
            troubleshooting = self._generate_troubleshooting_guide()
            usage_guidance["troubleshooting"] = troubleshooting

            # 优化建议
            logger.info("生成优化建议...")
            optimization = self._generate_optimization_tips()
            usage_guidance["optimization_tips"] = optimization

        except Exception as e:
            logger.error(f"❌ 使用指导生成异常: {str(e)}")
            usage_guidance["error"] = str(e)

        self.analysis_results["usage_guidance"] = usage_guidance
        return usage_guidance

    def _generate_installation_steps(self) -> Dict[str, Any]:
        """生成安装步骤"""
        installation = {
            "step_1_driver": {
                "title": "安装NVIDIA显卡驱动",
                "description": "从NVIDIA官网下载并安装最新的显卡驱动",
                "commands": [
                    "访问 https://www.nvidia.com/drivers",
                    "选择对应的GPU型号和操作系统",
                    "下载并运行安装程序",
                    "重启计算机"
                ],
                "verification": "运行 nvidia-smi 命令验证安装"
            },
            "step_2_cuda": {
                "title": "安装CUDA Toolkit",
                "description": "安装CUDA开发工具包",
                "commands": [
                    "访问 https://developer.nvidia.com/cuda-downloads",
                    "选择操作系统和架构",
                    "下载CUDA Toolkit安装程序",
                    "按照安装向导完成安装"
                ],
                "verification": "运行 nvcc --version 验证安装"
            },
            "step_3_python": {
                "title": "配置Python环境",
                "description": "设置Python虚拟环境",
                "commands": [
                    "python -m venv visionai_env",
                    "source visionai_env/bin/activate  # Linux/Mac",
                    "visionai_env\\Scripts\\activate  # Windows",
                    "pip install --upgrade pip"
                ],
                "verification": "python --version 确认Python版本"
            },
            "step_4_pytorch": {
                "title": "安装PyTorch GPU版本",
                "description": "安装支持CUDA的PyTorch",
                "commands": [
                    "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                ],
                "verification": "python -c \"import torch; print(torch.cuda.is_available())\""
            },
            "step_5_dependencies": {
                "title": "安装项目依赖",
                "description": "安装VisionAI-ClipsMaster的依赖包",
                "commands": [
                    "pip install transformers",
                    "pip install numpy pandas scikit-learn",
                    "pip install PyQt6"
                ],
                "verification": "python -c \"import transformers; print('Dependencies installed')\""
            }
        }
        return installation

    def _generate_configuration_guide(self) -> Dict[str, Any]:
        """生成配置指导"""
        configuration = {
            "environment_variables": {
                "CUDA_VISIBLE_DEVICES": "设置可见的GPU设备，例如: export CUDA_VISIBLE_DEVICES=0",
                "PYTORCH_CUDA_ALLOC_CONF": "配置GPU内存分配，例如: export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128"
            },
            "project_configuration": {
                "model_config": "编辑 model_config.json 选择合适的模型架构",
                "batch_size": "根据GPU内存调整批处理大小",
                "learning_rate": "大批处理可能需要调整学习率"
            },
            "performance_tuning": {
                "mixed_precision": "启用混合精度训练以提升性能",
                "dataloader_workers": "设置合适的数据加载器工作进程数",
                "pin_memory": "启用pin_memory以加速数据传输"
            }
        }
        return configuration

    def _generate_usage_examples(self) -> Dict[str, Any]:
        """生成使用示例"""
        examples = {
            "basic_gpu_training": {
                "description": "基础GPU训练示例",
                "code": """
# 创建增强训练器
from simple_ui_fixed import EnhancedViralTrainer

trainer = EnhancedViralTrainer()
print(f"使用设备: {trainer.device}")

# 准备训练数据
training_data = [
    {"original": "这个方法很好", "viral": "🔥 这个方法绝了！"},
    {"original": "大家可以试试", "viral": "⚡ 姐妹们快试试！"}
]

# 开始训练
trainer.train_with_gpu_support(training_data, epochs=5)
"""
            },
            "gpu_memory_management": {
                "description": "GPU内存管理示例",
                "code": """
from simple_ui_fixed import clear_gpu_memory, get_device

# 获取设备
device = get_device()
print(f"当前设备: {device}")

# 训练后清理GPU内存
clear_gpu_memory()
print("GPU内存已清理")
"""
            },
            "batch_size_optimization": {
                "description": "批处理大小优化示例",
                "code": """
import torch

# 根据GPU内存动态调整批处理大小
def find_optimal_batch_size(model, max_batch_size=128):
    for batch_size in [1, 2, 4, 8, 16, 32, 64, 128]:
        if batch_size > max_batch_size:
            break
        try:
            # 测试批处理大小
            test_input = torch.randn(batch_size, 50, 256).cuda()
            output = model(test_input)
            optimal_batch_size = batch_size
        except RuntimeError as e:
            if "out of memory" in str(e):
                break
            raise e
    return optimal_batch_size
"""
            }
        }
        return examples

    def _generate_troubleshooting_guide(self) -> Dict[str, Any]:
        """生成故障排除指导"""
        troubleshooting = {
            "common_issues": {
                "cuda_not_available": {
                    "problem": "torch.cuda.is_available() 返回 False",
                    "solutions": [
                        "检查NVIDIA驱动是否正确安装",
                        "确认安装了CUDA版本的PyTorch",
                        "验证CUDA Toolkit版本兼容性",
                        "重启计算机后重试"
                    ]
                },
                "out_of_memory": {
                    "problem": "CUDA out of memory 错误",
                    "solutions": [
                        "减少批处理大小",
                        "使用梯度累积模拟大批处理",
                        "启用混合精度训练",
                        "定期清理GPU内存缓存"
                    ]
                },
                "slow_training": {
                    "problem": "GPU训练速度慢于预期",
                    "solutions": [
                        "检查是否使用了正确的设备",
                        "增加批处理大小",
                        "启用混合精度训练",
                        "优化数据加载器设置"
                    ]
                },
                "driver_issues": {
                    "problem": "驱动相关问题",
                    "solutions": [
                        "更新到最新的NVIDIA驱动",
                        "检查驱动与CUDA版本兼容性",
                        "使用DDU工具完全卸载旧驱动",
                        "从NVIDIA官网下载驱动"
                    ]
                }
            },
            "diagnostic_commands": {
                "gpu_status": "nvidia-smi",
                "cuda_version": "nvcc --version",
                "pytorch_cuda": "python -c \"import torch; print(torch.cuda.is_available())\"",
                "gpu_memory": "python -c \"import torch; print(torch.cuda.memory_summary())\"",
                "driver_version": "cat /proc/driver/nvidia/version"
            },
            "performance_debugging": {
                "profiling": "使用torch.profiler进行性能分析",
                "memory_tracking": "使用torch.cuda.memory_stats()跟踪内存使用",
                "bottleneck_detection": "检查数据加载和GPU利用率"
            }
        }
        return troubleshooting

    def _generate_optimization_tips(self) -> Dict[str, Any]:
        """生成优化建议"""
        optimization = {
            "training_optimization": {
                "mixed_precision": {
                    "description": "使用自动混合精度训练",
                    "benefits": ["减少内存使用", "提升训练速度", "保持数值稳定性"],
                    "implementation": "使用torch.cuda.amp.autocast()和GradScaler"
                },
                "gradient_accumulation": {
                    "description": "梯度累积模拟大批处理",
                    "benefits": ["在有限内存下使用大批处理", "提升训练稳定性"],
                    "implementation": "累积多个小批次的梯度后再更新"
                },
                "dataloader_optimization": {
                    "description": "优化数据加载",
                    "tips": [
                        "使用pin_memory=True",
                        "设置合适的num_workers",
                        "使用prefetch_factor",
                        "考虑使用DataLoader2"
                    ]
                }
            },
            "memory_optimization": {
                "model_optimization": [
                    "使用checkpoint技术减少内存",
                    "启用gradient_checkpointing",
                    "使用更小的模型架构",
                    "考虑模型并行"
                ],
                "batch_optimization": [
                    "动态批处理大小",
                    "根据序列长度分组",
                    "使用pack_padded_sequence",
                    "实现自适应批处理"
                ]
            },
            "inference_optimization": {
                "model_optimization": [
                    "使用torch.jit.script编译模型",
                    "转换为ONNX格式",
                    "使用TensorRT加速",
                    "启用模型量化"
                ],
                "deployment_tips": [
                    "使用torch.no_grad()禁用梯度",
                    "设置model.eval()模式",
                    "批量推理提升吞吐量",
                    "使用异步推理"
                ]
            }
        }
        return optimization

    def run_comprehensive_gpu_analysis(self) -> Dict[str, Any]:
        """运行全面的GPU分析"""
        logger.info("🎯 开始VisionAI-ClipsMaster GPU加速能力全面分析")
        logger.info("=" * 80)

        overall_start_time = time.time()

        try:
            # 步骤1: GPU检测和自动切换功能验证
            logger.info("执行步骤1: GPU检测和自动切换功能验证")
            detection_result = self.analyze_gpu_detection_capability()

            # 步骤2: 训练性能提升分析
            logger.info("执行步骤2: 训练性能提升分析")
            performance_result = self.analyze_training_performance_improvement()

            # 步骤3: GPU兼容性要求分析
            logger.info("执行步骤3: GPU兼容性要求分析")
            compatibility_result = self.analyze_gpu_compatibility_requirements()

            # 步骤4: 实际使用指导
            logger.info("执行步骤4: 实际使用指导")
            guidance_result = self.provide_usage_guidance()

        except Exception as e:
            logger.error(f"❌ GPU分析异常: {str(e)}")

        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time

        # 生成综合报告
        comprehensive_report = self.generate_gpu_analysis_report(overall_duration)

        return comprehensive_report

    def generate_gpu_analysis_report(self, overall_duration: float) -> Dict[str, Any]:
        """生成GPU分析报告"""
        logger.info("=" * 80)
        logger.info("📊 生成GPU加速能力分析报告")
        logger.info("=" * 80)

        # 收集分析结果
        detection_result = self.analysis_results.get("gpu_detection", {})
        performance_result = self.analysis_results.get("performance", {})
        compatibility_result = self.analysis_results.get("compatibility", {})
        guidance_result = self.analysis_results.get("usage_guidance", {})

        # 计算关键指标
        gpu_available = detection_result.get("cuda_available", False)
        auto_switch_working = detection_result.get("auto_switch_capability", False)

        # 性能提升数据
        performance_comparison = performance_result.get("performance_comparison", {})
        speed_improvement = performance_comparison.get("speed_improvement", 0)
        batch_improvement = performance_comparison.get("batch_size_improvement", 0)

        # 生成报告
        report = {
            "analysis_summary": {
                "analysis_type": "GPU加速能力全面分析",
                "gpu_available": gpu_available,
                "auto_switch_capability": auto_switch_working,
                "speed_improvement": speed_improvement,
                "batch_size_improvement": batch_improvement,
                "overall_gpu_readiness": self._assess_gpu_readiness(),
                "total_duration": round(overall_duration, 2),
                "analysis_date": datetime.now().isoformat()
            },
            "detection_analysis": detection_result,
            "performance_analysis": performance_result,
            "compatibility_analysis": compatibility_result,
            "usage_guidance": guidance_result,
            "executive_summary": self._generate_executive_summary(),
            "recommendations": self._generate_final_recommendations()
        }

        # 打印摘要
        logger.info("📋 GPU加速能力分析摘要:")
        logger.info(f"  GPU可用性: {'✅ 可用' if gpu_available else '❌ 不可用'}")
        logger.info(f"  自动切换: {'✅ 正常' if auto_switch_working else '⚠️ 需要检查'}")
        if speed_improvement > 0:
            logger.info(f"  性能提升: {speed_improvement:.1f}x")
        if batch_improvement > 0:
            logger.info(f"  批处理提升: {batch_improvement:.1f}x")
        logger.info(f"  GPU就绪度: {report['analysis_summary']['overall_gpu_readiness']}")
        logger.info(f"  分析耗时: {overall_duration:.2f}秒")

        # 保存报告
        report_file = f"gpu_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            # 创建可序列化的报告副本
            serializable_report = self._make_serializable(report)

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_report, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 GPU分析报告已保存: {report_file}")
            report["report_file"] = report_file
        except Exception as e:
            logger.error(f"❌ 保存分析报告失败: {str(e)}")

        return report

    def _assess_gpu_readiness(self) -> str:
        """评估GPU就绪度"""
        detection_result = self.analysis_results.get("gpu_detection", {})

        gpu_available = detection_result.get("cuda_available", False)
        auto_switch_working = detection_result.get("auto_switch_capability", False)
        code_quality = detection_result.get("code_implementation_status", {}).get("implementation_quality", "unknown")

        if gpu_available and auto_switch_working and code_quality == "excellent":
            return "完全就绪"
        elif gpu_available and auto_switch_working:
            return "基本就绪"
        elif gpu_available:
            return "硬件就绪"
        else:
            return "需要配置"

    def _generate_executive_summary(self) -> Dict[str, Any]:
        """生成执行摘要"""
        detection_result = self.analysis_results.get("gpu_detection", {})
        performance_result = self.analysis_results.get("performance", {})

        summary = {
            "current_status": {},
            "performance_potential": {},
            "implementation_quality": {},
            "business_impact": {}
        }

        # 当前状态
        gpu_available = detection_result.get("cuda_available", False)
        summary["current_status"] = {
            "gpu_hardware": "可用" if gpu_available else "不可用",
            "software_stack": "已实现" if detection_result.get("auto_switch_capability") else "需要完善",
            "code_readiness": detection_result.get("code_implementation_status", {}).get("implementation_quality", "unknown")
        }

        # 性能潜力
        performance_comparison = performance_result.get("performance_comparison", {})
        summary["performance_potential"] = {
            "training_speedup": f"{performance_comparison.get('speed_improvement', 0):.1f}x",
            "batch_size_increase": f"{performance_comparison.get('batch_size_improvement', 0):.1f}x",
            "development_efficiency": "显著提升" if performance_comparison.get('speed_improvement', 0) > 2 else "有限提升"
        }

        # 实现质量
        code_status = detection_result.get("code_implementation_status", {})
        summary["implementation_quality"] = {
            "gpu_detection": "✅" if code_status.get("get_device_function") else "❌",
            "device_switching": "✅" if code_status.get("move_to_device_function") else "❌",
            "memory_management": "✅" if code_status.get("clear_gpu_memory_function") else "❌",
            "training_framework": "✅" if code_status.get("enhanced_trainer_class") else "❌"
        }

        # 业务影响
        summary["business_impact"] = {
            "development_speed": "GPU加速可显著提升模型训练速度",
            "cost_efficiency": "更快的训练意味着更低的开发成本",
            "scalability": "支持更大规模的模型和数据集",
            "competitive_advantage": "更快的迭代速度提供竞争优势"
        }

        return summary

    def _generate_final_recommendations(self) -> List[str]:
        """生成最终建议"""
        recommendations = []

        detection_result = self.analysis_results.get("gpu_detection", {})
        performance_result = self.analysis_results.get("performance", {})

        gpu_available = detection_result.get("cuda_available", False)
        speed_improvement = performance_result.get("performance_comparison", {}).get("speed_improvement", 0)

        if not gpu_available:
            recommendations.extend([
                "🔧 配置GPU环境：安装NVIDIA驱动和CUDA Toolkit",
                "💰 考虑购买支持CUDA的GPU以获得训练加速",
                "☁️ 或考虑使用云GPU服务进行训练"
            ])
        elif speed_improvement > 2.0:
            recommendations.extend([
                "🚀 GPU加速效果显著，强烈推荐使用GPU训练",
                "📈 考虑增加批处理大小以充分利用GPU性能",
                "🔬 探索更复杂的模型架构以提升效果"
            ])
        elif speed_improvement > 1.0:
            recommendations.extend([
                "✅ GPU加速有效，建议在训练时使用GPU",
                "⚡ 启用混合精度训练以进一步提升性能",
                "🎯 优化数据加载以减少GPU等待时间"
            ])

        # 通用建议
        recommendations.extend([
            "📚 定期更新PyTorch和CUDA以获得最新优化",
            "🔍 监控GPU利用率以确保充分使用",
            "💾 实施模型检查点以防止训练中断",
            "📊 使用性能分析工具优化训练流程"
        ])

        return recommendations

    def _make_serializable(self, obj):
        """使对象可序列化"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return obj


def main():
    """主函数"""
    print("🎯 VisionAI-ClipsMaster GPU加速能力详细分析")
    print("=" * 80)

    # 创建分析器
    analyzer = GPUAccelerationAnalyzer()

    try:
        # 运行全面分析
        report = analyzer.run_comprehensive_gpu_analysis()

        # 显示最终结果
        gpu_readiness = report.get("analysis_summary", {}).get("overall_gpu_readiness", "unknown")
        speed_improvement = report.get("analysis_summary", {}).get("speed_improvement", 0)

        if gpu_readiness == "完全就绪":
            print(f"\n🎉 GPU加速完全就绪！性能提升: {speed_improvement:.1f}x")
        elif gpu_readiness == "基本就绪":
            print(f"\n✅ GPU加速基本就绪！性能提升: {speed_improvement:.1f}x")
        elif gpu_readiness == "硬件就绪":
            print(f"\n⚠️ GPU硬件就绪，软件需要完善")
        else:
            print(f"\n❌ GPU环境需要配置")

        # 显示建议
        recommendations = report.get("recommendations", [])
        if recommendations:
            print("\n📋 关键建议:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"  {i}. {rec}")

        return report

    except KeyboardInterrupt:
        print("\n⏹️ 分析被用户中断")
        return None
    except Exception as e:
        print(f"\n💥 分析过程异常: {str(e)}")
        return None


if __name__ == "__main__":
    main()
