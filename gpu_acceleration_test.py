#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster GPU加速功能专项测试
详细测试GPU环境、CUDA支持、内存管理等
"""

import os
import sys
import time
import psutil
import logging
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPUAccelerationTest:
    """GPU加速功能专项测试"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_cuda_environment(self):
        """测试CUDA环境"""
        logger.info("=== CUDA环境测试 ===")
        
        try:
            import torch
            
            # 基本CUDA信息
            cuda_available = torch.cuda.is_available()
            logger.info(f"CUDA可用: {cuda_available}")
            
            if cuda_available:
                gpu_count = torch.cuda.device_count()
                logger.info(f"GPU数量: {gpu_count}")
                
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    logger.info(f"GPU {i}: {gpu_name}, 显存: {gpu_memory:.1f}GB")
                
                # 测试CUDA操作
                try:
                    device = torch.device("cuda:0")
                    test_tensor = torch.randn(1000, 1000).to(device)
                    result = torch.matmul(test_tensor, test_tensor)
                    logger.info("CUDA张量操作测试: 成功")
                    
                    # 显存使用情况
                    memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                    memory_reserved = torch.cuda.memory_reserved(0) / 1024**3
                    logger.info(f"显存使用: 已分配 {memory_allocated:.2f}GB, 已保留 {memory_reserved:.2f}GB")
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"CUDA操作测试失败: {e}")
                    return False
            else:
                logger.info("CUDA不可用，检查驱动和PyTorch安装")
                return False
                
        except ImportError:
            logger.error("PyTorch未安装")
            return False
        except Exception as e:
            logger.error(f"CUDA环境测试失败: {e}")
            return False
    
    def test_opencl_environment(self):
        """测试OpenCL环境"""
        logger.info("=== OpenCL环境测试 ===")
        
        try:
            import pyopencl as cl
            
            platforms = cl.get_platforms()
            logger.info(f"OpenCL平台数量: {len(platforms)}")
            
            for i, platform in enumerate(platforms):
                logger.info(f"平台 {i}: {platform.name}")
                
                devices = platform.get_devices()
                for j, device in enumerate(devices):
                    logger.info(f"  设备 {j}: {device.name}")
                    logger.info(f"    类型: {cl.device_type.to_string(device.type)}")
                    logger.info(f"    全局内存: {device.global_mem_size / 1024**3:.1f}GB")
                    logger.info(f"    最大工作组大小: {device.max_work_group_size}")
            
            # 测试OpenCL操作
            if platforms:
                context = cl.Context([platforms[0].get_devices()[0]])
                queue = cl.CommandQueue(context)
                logger.info("OpenCL上下文创建: 成功")
                return True
            else:
                logger.info("没有可用的OpenCL设备")
                return False
                
        except ImportError:
            logger.info("PyOpenCL未安装")
            return False
        except Exception as e:
            logger.error(f"OpenCL环境测试失败: {e}")
            return False
    
    def test_cpu_vs_gpu_performance(self):
        """测试CPU vs GPU性能对比"""
        logger.info("=== CPU vs GPU性能对比测试 ===")
        
        try:
            import torch
            
            # 测试数据
            size = 2048
            iterations = 10
            
            # CPU测试
            logger.info("开始CPU性能测试...")
            cpu_device = torch.device("cpu")
            cpu_times = []
            
            for i in range(iterations):
                start_time = time.time()
                a = torch.randn(size, size, device=cpu_device)
                b = torch.randn(size, size, device=cpu_device)
                c = torch.matmul(a, b)
                cpu_times.append(time.time() - start_time)
            
            avg_cpu_time = sum(cpu_times) / len(cpu_times)
            logger.info(f"CPU平均时间: {avg_cpu_time:.3f}秒")
            
            # GPU测试（如果可用）
            if torch.cuda.is_available():
                logger.info("开始GPU性能测试...")
                gpu_device = torch.device("cuda:0")
                gpu_times = []
                
                # 预热GPU
                for _ in range(3):
                    a = torch.randn(size, size, device=gpu_device)
                    b = torch.randn(size, size, device=gpu_device)
                    c = torch.matmul(a, b)
                    torch.cuda.synchronize()
                
                for i in range(iterations):
                    start_time = time.time()
                    a = torch.randn(size, size, device=gpu_device)
                    b = torch.randn(size, size, device=gpu_device)
                    c = torch.matmul(a, b)
                    torch.cuda.synchronize()
                    gpu_times.append(time.time() - start_time)
                
                avg_gpu_time = sum(gpu_times) / len(gpu_times)
                logger.info(f"GPU平均时间: {avg_gpu_time:.3f}秒")
                
                speedup = avg_cpu_time / avg_gpu_time
                logger.info(f"GPU加速比: {speedup:.1f}x")
                
                return {
                    "cpu_time": avg_cpu_time,
                    "gpu_time": avg_gpu_time,
                    "speedup": speedup
                }
            else:
                logger.info("GPU不可用，无法进行性能对比")
                return {
                    "cpu_time": avg_cpu_time,
                    "gpu_time": None,
                    "speedup": None
                }
                
        except Exception as e:
            logger.error(f"性能对比测试失败: {e}")
            return None
    
    def test_memory_management(self):
        """测试内存管理"""
        logger.info("=== 内存管理测试 ===")
        
        try:
            import torch
            
            initial_memory = psutil.virtual_memory().percent
            logger.info(f"初始系统内存使用: {initial_memory:.1f}%")
            
            if torch.cuda.is_available():
                initial_gpu_memory = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"初始GPU内存使用: {initial_gpu_memory:.2f}GB")
            
            # 创建大量张量测试内存管理
            tensors = []
            for i in range(100):
                if torch.cuda.is_available():
                    tensor = torch.randn(1000, 1000).cuda()
                else:
                    tensor = torch.randn(1000, 1000)
                tensors.append(tensor)
                
                if i % 20 == 0:
                    current_memory = psutil.virtual_memory().percent
                    logger.info(f"创建 {i+1} 个张量后，系统内存: {current_memory:.1f}%")
                    
                    if torch.cuda.is_available():
                        gpu_memory = torch.cuda.memory_allocated(0) / 1024**3
                        logger.info(f"GPU内存使用: {gpu_memory:.2f}GB")
            
            # 清理内存
            del tensors
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            final_memory = psutil.virtual_memory().percent
            logger.info(f"清理后系统内存使用: {final_memory:.1f}%")
            
            if torch.cuda.is_available():
                final_gpu_memory = torch.cuda.memory_allocated(0) / 1024**3
                logger.info(f"清理后GPU内存使用: {final_gpu_memory:.2f}GB")
            
            # 检查内存是否在合理范围内
            memory_ok = final_memory < 90.0  # 系统内存使用不超过90%
            
            return memory_ok
            
        except Exception as e:
            logger.error(f"内存管理测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有GPU测试"""
        logger.info("开始GPU加速功能完整测试")
        
        # 测试1: CUDA环境
        cuda_result = self.test_cuda_environment()
        self.test_results["CUDA环境"] = cuda_result
        
        # 测试2: OpenCL环境
        opencl_result = self.test_opencl_environment()
        self.test_results["OpenCL环境"] = opencl_result
        
        # 测试3: 性能对比
        performance_result = self.test_cpu_vs_gpu_performance()
        self.test_results["性能对比"] = performance_result
        
        # 测试4: 内存管理
        memory_result = self.test_memory_management()
        self.test_results["内存管理"] = memory_result
        
        # 生成总结
        logger.info("=== GPU测试总结 ===")
        for test_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            logger.info(f"{status}: {test_name}")
        
        return self.test_results

if __name__ == "__main__":
    test = GPUAccelerationTest()
    results = test.run_all_tests()
    
    # 输出最终结果
    print("\n" + "="*60)
    print("GPU加速功能测试完成")
    print("="*60)
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {test_name}: {result}")
