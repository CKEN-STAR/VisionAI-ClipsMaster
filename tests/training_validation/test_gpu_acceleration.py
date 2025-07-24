#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速效果测试模块
对比CPU训练与GPU训练的实际时间差异
"""

import os
import sys
import json
import time
import logging
import unittest
import torch
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.training.en_trainer import EnTrainer
from src.training.zh_trainer import ZhTrainer
from src.utils.memory_guard import get_memory_manager
from src.utils.device_manager import DeviceManager

class GPUAccelerationTest(unittest.TestCase):
    """GPU加速效果测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.memory_manager = get_memory_manager()
        self.device_manager = DeviceManager()
        self.test_results = {}
        
        # 检测GPU可用性
        self.gpu_available = torch.cuda.is_available()
        self.device_info = self.device_manager.get_device_info()
        
        # 创建标准测试数据
        self.test_data_en = self._create_test_data("en", 500)
        self.test_data_zh = self._create_test_data("zh", 500)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"GPU可用性: {self.gpu_available}")
        if self.gpu_available:
            self.logger.info(f"GPU设备: {torch.cuda.get_device_name()}")
            self.logger.info(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    def _create_test_data(self, language: str, count: int) -> List[Dict[str, Any]]:
        """创建测试数据"""
        if language == "en":
            base_data = [
                {
                    "original": "The story begins with a young man walking through the city streets.",
                    "viral": "SHOCKING: Young man's city walk reveals INCREDIBLE secrets that will BLOW YOUR MIND!"
                },
                {
                    "original": "She discovered an old book in the library that changed her life forever.",
                    "viral": "UNBELIEVABLE: Library book discovery will CHANGE EVERYTHING you thought you knew!"
                }
            ]
        else:  # zh
            base_data = [
                {
                    "original": "故事开始于一个年轻人走过城市街道。他发现了一些不寻常的事情。",
                    "viral": "震撼！年轻人城市漫步发现史上最惊人秘密！这个发现改变一切！"
                },
                {
                    "original": "她在图书馆发现了一本改变她一生的旧书。从此她的世界完全不同了。",
                    "viral": "不敢相信！图书馆发现的这本书太精彩了！她的人生从此改变一切！"
                }
            ]
        
        # 扩展到指定数量
        extended_data = []
        for i in range(count):
            base_item = base_data[i % len(base_data)]
            extended_data.append({
                "original": f"{base_item['original']} (Sample {i+1})",
                "viral": f"{base_item['viral']} (Enhanced {i+1})"
            })
        
        return extended_data
    
    def test_cpu_vs_gpu_english_training(self):
        """测试CPU vs GPU英文训练性能对比"""
        self.logger.info("开始CPU vs GPU英文训练性能对比测试...")
        
        results = {}
        
        # CPU训练测试
        self.logger.info("执行CPU英文训练...")
        cpu_result = self._run_training_test(
            trainer_class=EnTrainer,
            training_data=self.test_data_en,
            use_gpu=False,
            test_name="CPU_English"
        )
        results["cpu"] = cpu_result
        
        # GPU训练测试（如果可用）
        if self.gpu_available:
            self.logger.info("执行GPU英文训练...")
            gpu_result = self._run_training_test(
                trainer_class=EnTrainer,
                training_data=self.test_data_en,
                use_gpu=True,
                test_name="GPU_English"
            )
            results["gpu"] = gpu_result
            
            # 计算加速比
            if cpu_result["success"] and gpu_result["success"]:
                speedup = cpu_result["training_time"] / gpu_result["training_time"]
                results["speedup_ratio"] = speedup
                
                self.logger.info(f"GPU加速比: {speedup:.2f}x")
                
                # 验证GPU加速效果（至少30%提升）
                self.assertGreater(speedup, 1.3, 
                                 "GPU加速效果不足30%")
        else:
            self.logger.warning("GPU不可用，跳过GPU测试")
            results["gpu"] = {"success": False, "error": "GPU不可用"}
            results["speedup_ratio"] = 0
        
        self.test_results["english_cpu_vs_gpu"] = results
    
    def test_cpu_vs_gpu_chinese_training(self):
        """测试CPU vs GPU中文训练性能对比"""
        self.logger.info("开始CPU vs GPU中文训练性能对比测试...")
        
        results = {}
        
        # CPU训练测试
        self.logger.info("执行CPU中文训练...")
        cpu_result = self._run_training_test(
            trainer_class=ZhTrainer,
            training_data=self.test_data_zh,
            use_gpu=False,
            test_name="CPU_Chinese"
        )
        results["cpu"] = cpu_result
        
        # GPU训练测试（如果可用）
        if self.gpu_available:
            self.logger.info("执行GPU中文训练...")
            gpu_result = self._run_training_test(
                trainer_class=ZhTrainer,
                training_data=self.test_data_zh,
                use_gpu=True,
                test_name="GPU_Chinese"
            )
            results["gpu"] = gpu_result
            
            # 计算加速比
            if cpu_result["success"] and gpu_result["success"]:
                speedup = cpu_result["training_time"] / gpu_result["training_time"]
                results["speedup_ratio"] = speedup
                
                self.logger.info(f"GPU加速比: {speedup:.2f}x")
                
                # 验证GPU加速效果（至少30%提升）
                self.assertGreater(speedup, 1.3, 
                                 "GPU加速效果不足30%")
        else:
            self.logger.warning("GPU不可用，跳过GPU测试")
            results["gpu"] = {"success": False, "error": "GPU不可用"}
            results["speedup_ratio"] = 0
        
        self.test_results["chinese_cpu_vs_gpu"] = results
    
    def test_device_manager_gpu_allocation(self):
        """测试设备管理器的GPU动态分配功能"""
        self.logger.info("测试设备管理器GPU动态分配...")
        
        # 测试设备选择
        selected_device = self.device_manager.select_device()
        self.logger.info(f"自动选择的设备: {selected_device}")
        
        # 测试设备信息获取
        device_info = self.device_manager.get_device_info()
        self.assertIsInstance(device_info, dict)
        self.assertIn("current_device", device_info)
        
        # 测试GPU检测
        gpu_devices = self.device_manager.detect_gpus()
        self.assertIsInstance(gpu_devices, list)
        
        # 测试CPU回退
        cpu_fallback = self.device_manager.test_cpu_fallback()
        self.assertTrue(cpu_fallback, "CPU回退功能不可用")
        
        self.test_results["device_manager"] = {
            "selected_device": str(selected_device),
            "device_info": device_info,
            "gpu_devices": gpu_devices,
            "cpu_fallback": cpu_fallback
        }
    
    def test_memory_usage_under_4gb_limit(self):
        """测试4GB内存限制下的训练稳定性"""
        self.logger.info("测试4GB内存限制下的训练稳定性...")
        
        # 监控内存使用
        self.memory_manager.start_monitoring()
        
        try:
            # 执行较大规模的训练测试
            large_test_data = self._create_test_data("zh", 1000)
            
            zh_trainer = ZhTrainer(use_gpu=self.gpu_available)
            
            memory_before = self.memory_manager.get_memory_usage()
            
            training_result = zh_trainer.train(
                training_data=large_test_data,
                progress_callback=self._memory_progress_callback
            )
            
            memory_after = self.memory_manager.get_memory_usage()
            memory_peak = max(memory_before, memory_after)
            
            # 验证内存使用不超过4GB
            self.assertLess(memory_peak, 4000, 
                          f"内存使用超过4GB限制: {memory_peak:.1f}MB")
            
            # 验证训练成功
            self.assertTrue(training_result.get("success", False), 
                          "大规模训练失败")
            
            self.test_results["memory_limit_test"] = {
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_peak": memory_peak,
                "training_success": training_result.get("success", False),
                "sample_count": len(large_test_data)
            }
            
        finally:
            self.memory_manager.stop_monitoring()
    
    def _run_training_test(self, trainer_class, training_data: List[Dict[str, Any]], 
                          use_gpu: bool, test_name: str) -> Dict[str, Any]:
        """运行训练测试"""
        try:
            trainer = trainer_class(use_gpu=use_gpu)
            
            # 记录开始状态
            memory_before = self.memory_manager.get_memory_usage()
            start_time = time.time()
            
            # 执行训练
            training_result = trainer.train(
                training_data=training_data,
                progress_callback=lambda p, m: self.logger.debug(f"{test_name}: {p:.1%} - {m}")
            )
            
            # 记录结束状态
            end_time = time.time()
            memory_after = self.memory_manager.get_memory_usage()
            
            return {
                "success": training_result.get("success", False),
                "training_time": end_time - start_time,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_delta": memory_after - memory_before,
                "training_result": training_result,
                "device": "gpu" if use_gpu else "cpu"
            }
            
        except Exception as e:
            self.logger.error(f"{test_name}训练测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "device": "gpu" if use_gpu else "cpu"
            }
    
    def _memory_progress_callback(self, progress: float, message: str):
        """内存监控进度回调"""
        current_memory = self.memory_manager.get_memory_usage()
        self.logger.info(f"进度: {progress:.1%} - {message} (内存: {current_memory:.1f}MB)")
        
        # 如果内存使用过高，触发清理
        if current_memory > 3500:  # 3.5GB阈值
            self.memory_manager.force_cleanup()
    
    def tearDown(self):
        """测试清理"""
        # 强制内存清理
        self.memory_manager.force_cleanup()
        
        # 清理GPU缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"gpu_acceleration_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"GPU加速测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
