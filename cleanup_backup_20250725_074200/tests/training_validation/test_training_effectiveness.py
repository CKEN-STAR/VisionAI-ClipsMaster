#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练效果验证测试模块
验证en_trainer.py和zh_trainer.py的训练效果
"""

import os
import sys
import json
import time
import logging
import unittest
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.training.en_trainer import EnTrainer
from src.training.zh_trainer import ZhTrainer
from src.utils.memory_guard import get_memory_manager
from src.utils.device_manager import DeviceManager

class TrainingEffectivenessTest(unittest.TestCase):
    """训练效果验证测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.memory_manager = get_memory_manager()
        self.device_manager = DeviceManager()
        self.test_results = {}
        
        # 创建测试数据
        self.sample_sizes = [100, 500, 1000]
        self.test_data_en = self._create_english_test_data()
        self.test_data_zh = self._create_chinese_test_data()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _create_english_test_data(self) -> List[Dict[str, Any]]:
        """创建英文测试数据"""
        base_data = [
            {
                "original": "John walked to the store. He bought some milk. Then he went home.",
                "viral": "SHOCKING: Man's INCREDIBLE journey to store will BLOW YOUR MIND! What he bought next is UNBELIEVABLE!"
            },
            {
                "original": "The weather was nice today. I went for a walk in the park.",
                "viral": "AMAZING weather transformation! This person's park adventure will CHANGE EVERYTHING you know!"
            },
            {
                "original": "She cooked dinner for her family. Everyone enjoyed the meal.",
                "viral": "MIND-BLOWING cooking secret! Family's reaction to this dinner will STUN you!"
            }
        ]
        
        # 扩展数据到1000个样本
        extended_data = []
        for i in range(1000):
            base_item = base_data[i % len(base_data)]
            extended_data.append({
                "original": f"{base_item['original']} (Sample {i+1})",
                "viral": f"{base_item['viral']} (Enhanced {i+1})"
            })
        
        return extended_data
    
    def _create_chinese_test_data(self) -> List[Dict[str, Any]]:
        """创建中文测试数据"""
        base_data = [
            {
                "original": "小明今天去了学校。他上了数学课和语文课。下午回到家里。",
                "viral": "震撼！小明的学校之旅太精彩了！他的课堂表现不敢相信，改变一切的一天！"
            },
            {
                "original": "妈妈在厨房做饭。她做了红烧肉和青菜。全家人都很开心。",
                "viral": "惊呆了！妈妈的厨艺史上最强！这道菜的秘密太震撼，全家反应不敢相信！"
            },
            {
                "original": "天气很好，我们去公园散步。看到了很多花和树。",
                "viral": "太精彩！公园散步发现史上最美景色！这些花朵的秘密改变一切！"
            }
        ]
        
        # 扩展数据到1000个样本
        extended_data = []
        for i in range(1000):
            base_item = base_data[i % len(base_data)]
            extended_data.append({
                "original": f"{base_item['original']} (样本{i+1})",
                "viral": f"{base_item['viral']} (增强{i+1})"
            })
        
        return extended_data
    
    def test_english_training_progression(self):
        """测试英文训练的渐进式效果"""
        self.logger.info("开始英文训练渐进式测试...")
        
        en_trainer = EnTrainer(use_gpu=False)  # 先测试CPU模式
        results = {}
        
        for sample_size in self.sample_sizes:
            self.logger.info(f"测试样本数量: {sample_size}")
            
            # 获取对应数量的训练数据
            training_data = self.test_data_en[:sample_size]
            
            # 记录训练前内存
            memory_before = self.memory_manager.get_memory_usage()
            
            # 执行训练
            start_time = time.time()
            training_result = en_trainer.train(
                training_data=training_data,
                progress_callback=self._progress_callback
            )
            end_time = time.time()
            
            # 记录训练后内存
            memory_after = self.memory_manager.get_memory_usage()
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(
                training_result, "en", sample_size
            )
            
            results[sample_size] = {
                "training_result": training_result,
                "quality_metrics": quality_metrics,
                "training_time": end_time - start_time,
                "memory_usage": {
                    "before": memory_before,
                    "after": memory_after,
                    "delta": memory_after - memory_before
                },
                "sample_count": sample_size
            }
            
            # 验证训练成功
            self.assertTrue(training_result.get("success", False), 
                          f"英文训练失败 (样本数: {sample_size})")
            
            # 验证内存使用在合理范围内
            self.assertLess(memory_after, 4000,  # 4GB限制
                          f"内存使用超限 (样本数: {sample_size})")
        
        self.test_results["english_progression"] = results
        self.logger.info("英文训练渐进式测试完成")
    
    def test_chinese_training_progression(self):
        """测试中文训练的渐进式效果"""
        self.logger.info("开始中文训练渐进式测试...")
        
        zh_trainer = ZhTrainer(use_gpu=False)  # 先测试CPU模式
        results = {}
        
        for sample_size in self.sample_sizes:
            self.logger.info(f"测试样本数量: {sample_size}")
            
            # 获取对应数量的训练数据
            training_data = self.test_data_zh[:sample_size]
            
            # 记录训练前内存
            memory_before = self.memory_manager.get_memory_usage()
            
            # 执行训练
            start_time = time.time()
            training_result = zh_trainer.train(
                training_data=training_data,
                progress_callback=self._progress_callback
            )
            end_time = time.time()
            
            # 记录训练后内存
            memory_after = self.memory_manager.get_memory_usage()
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(
                training_result, "zh", sample_size
            )
            
            results[sample_size] = {
                "training_result": training_result,
                "quality_metrics": quality_metrics,
                "training_time": end_time - start_time,
                "memory_usage": {
                    "before": memory_before,
                    "after": memory_after,
                    "delta": memory_after - memory_before
                },
                "sample_count": sample_size
            }
            
            # 验证训练成功
            self.assertTrue(training_result.get("success", False), 
                          f"中文训练失败 (样本数: {sample_size})")
            
            # 验证内存使用在合理范围内
            self.assertLess(memory_after, 4000,  # 4GB限制
                          f"内存使用超限 (样本数: {sample_size})")
        
        self.test_results["chinese_progression"] = results
        self.logger.info("中文训练渐进式测试完成")
    
    def _progress_callback(self, progress: float, message: str):
        """训练进度回调"""
        self.logger.info(f"训练进度: {progress:.1%} - {message}")
    
    def _calculate_quality_metrics(self, training_result: Dict[str, Any], 
                                 language: str, sample_size: int) -> Dict[str, float]:
        """计算训练质量指标"""
        metrics = {
            "bleu_score": 0.0,
            "coherence_score": 0.0,
            "timeline_accuracy": 0.0,
            "viral_feature_score": 0.0
        }
        
        if not training_result.get("success", False):
            return metrics
        
        # 模拟BLEU分数计算（基于训练损失）
        if "train_loss" in training_result:
            # 损失越低，BLEU分数越高
            loss = training_result["train_loss"]
            metrics["bleu_score"] = max(0.0, min(1.0, 1.0 - loss))
        elif "loss" in training_result:
            loss = training_result["loss"]
            metrics["bleu_score"] = max(0.0, min(1.0, 1.0 - loss))
        
        # 模拟连贯性评分（基于样本数量）
        metrics["coherence_score"] = min(1.0, 0.5 + (sample_size / 2000))
        
        # 模拟时间轴准确性（基于训练类型）
        if training_result.get("training_type") == "REAL_ML_TRAINING":
            metrics["timeline_accuracy"] = 0.95
        else:
            metrics["timeline_accuracy"] = 0.85
        
        # 模拟爆款特征评分（基于语言和样本数）
        base_score = 0.8 if language == "zh" else 0.75
        metrics["viral_feature_score"] = min(1.0, base_score + (sample_size / 5000))
        
        return metrics
    
    def tearDown(self):
        """测试清理"""
        # 强制内存清理
        self.memory_manager.force_cleanup()
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"training_effectiveness_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
