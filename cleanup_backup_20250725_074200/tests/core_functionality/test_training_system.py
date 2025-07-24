#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 投喂训练系统测试

测试范围:
1. "原片-爆款"学习逻辑验证
2. 双语言训练管道分离
3. 训练时间和内存控制 (≤30分钟/轮, ≤3.8GB)
4. 损失收敛验证 (>50%/10轮)
5. 训练数据增强功能
"""

import pytest
import time
import json
import tempfile
import os
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from src.training.en_trainer import EnglishTrainer
from src.training.zh_trainer import ChineseTrainer
from src.training.data_splitter import DataSplitter
from src.training.data_augment import DataAugmenter
from src.training.plot_augment import PlotAugmenter


class TestTrainingSystem:
    """投喂训练系统测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.en_trainer = EnglishTrainer()
        self.zh_trainer = ChineseTrainer()
        self.data_splitter = DataSplitter()
        self.data_augmenter = DataAugmenter()
        self.plot_augmenter = PlotAugmenter()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 模拟训练数据
        self.sample_training_data = {
            "zh": {
                "original_subtitles": [
                    {"text": "今天天气很好", "start_time": "00:00:01,000", "end_time": "00:00:03,000"},
                    {"text": "我们去公园散步", "start_time": "00:00:04,000", "end_time": "00:00:06,000"},
                    {"text": "突然下起了雨", "start_time": "00:00:07,000", "end_time": "00:00:09,000"}
                ],
                "viral_subtitles": [
                    {"text": "完美的一天开始了！", "start_time": "00:00:01,000", "end_time": "00:00:03,000"},
                    {"text": "浪漫的公园约会", "start_time": "00:00:04,000", "end_time": "00:00:06,000"},
                    {"text": "意外的惊喜来了！", "start_time": "00:00:07,000", "end_time": "00:00:09,000"}
                ]
            },
            "en": {
                "original_subtitles": [
                    {"text": "The weather is nice today", "start_time": "00:00:01,000", "end_time": "00:00:03,000"},
                    {"text": "Let's go to the park", "start_time": "00:00:04,000", "end_time": "00:00:06,000"},
                    {"text": "It started raining", "start_time": "00:00:07,000", "end_time": "00:00:09,000"}
                ],
                "viral_subtitles": [
                    {"text": "Perfect day begins!", "start_time": "00:00:01,000", "end_time": "00:00:03,000"},
                    {"text": "Romantic park date", "start_time": "00:00:04,000", "end_time": "00:00:06,000"},
                    {"text": "Unexpected surprise!", "start_time": "00:00:07,000", "end_time": "00:00:09,000"}
                ]
            }
        }

    def test_original_to_viral_learning_logic(self):
        """测试"原片→爆款"学习逻辑"""
        # 测试中文训练逻辑
        zh_data = self.sample_training_data["zh"]
        zh_training_config = {
            "epochs": 2,
            "batch_size": 1,
            "learning_rate": 0.001,
            "language": "zh"
        }
        
        # 执行训练
        zh_result = self.zh_trainer.train(
            original_data=zh_data["original_subtitles"],
            viral_data=zh_data["viral_subtitles"],
            config=zh_training_config
        )
        
        # 验证训练结果
        assert zh_result["status"] == "success", "中文训练失败"
        assert "loss_history" in zh_result, "缺少损失历史"
        assert len(zh_result["loss_history"]) > 0, "损失历史为空"
        
        # 测试英文训练逻辑
        en_data = self.sample_training_data["en"]
        en_training_config = {
            "epochs": 2,
            "batch_size": 1,
            "learning_rate": 0.001,
            "language": "en"
        }
        
        en_result = self.en_trainer.train(
            original_data=en_data["original_subtitles"],
            viral_data=en_data["viral_subtitles"],
            config=en_training_config
        )
        
        assert en_result["status"] == "success", "英文训练失败"

    def test_bilingual_training_pipeline_separation(self):
        """测试双语言训练管道分离"""
        # 创建混合语言数据
        mixed_data = {
            "samples": [
                {"text": "Hello world", "language": "en", "type": "original"},
                {"text": "Amazing discovery!", "language": "en", "type": "viral"},
                {"text": "你好世界", "language": "zh", "type": "original"},
                {"text": "惊人的发现！", "language": "zh", "type": "viral"}
            ]
        }
        
        # 数据分离
        separated_data = self.data_splitter.split_by_language(mixed_data)
        
        # 验证分离结果
        assert "zh" in separated_data, "缺少中文数据"
        assert "en" in separated_data, "缺少英文数据"
        
        zh_samples = separated_data["zh"]
        en_samples = separated_data["en"]
        
        assert len(zh_samples) == 2, f"中文样本数量错误: {len(zh_samples)}"
        assert len(en_samples) == 2, f"英文样本数量错误: {len(en_samples)}"
        
        # 验证语言纯度
        for sample in zh_samples:
            assert sample["language"] == "zh", "中文数据混入其他语言"
        
        for sample in en_samples:
            assert sample["language"] == "en", "英文数据混入其他语言"

    def test_training_time_constraint(self):
        """测试训练时间约束 (≤30分钟/轮)"""
        training_config = {
            "epochs": 1,
            "batch_size": 2,
            "learning_rate": 0.01,
            "language": "zh",
            "max_time_per_epoch": 1800  # 30分钟
        }
        
        start_time = time.time()
        
        # 执行训练
        result = self.zh_trainer.train(
            original_data=self.sample_training_data["zh"]["original_subtitles"],
            viral_data=self.sample_training_data["zh"]["viral_subtitles"],
            config=training_config
        )
        
        training_time = time.time() - start_time
        
        # 验证时间约束
        assert training_time <= 1800, f"训练时间超限: {training_time:.2f}s (限制: 1800s)"
        assert result["status"] == "success", "训练未成功完成"

    def test_memory_usage_during_training(self):
        """测试训练过程内存使用 (≤3.8GB)"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建较大的训练数据集
        large_training_data = {
            "original_subtitles": self.sample_training_data["zh"]["original_subtitles"] * 100,
            "viral_subtitles": self.sample_training_data["zh"]["viral_subtitles"] * 100
        }
        
        training_config = {
            "epochs": 1,
            "batch_size": 10,
            "learning_rate": 0.001,
            "language": "zh"
        }
        
        # 监控内存使用
        peak_memory = initial_memory
        
        def memory_monitor():
            nonlocal peak_memory
            current_memory = process.memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, current_memory)
        
        # 执行训练并监控内存
        result = self.zh_trainer.train(
            original_data=large_training_data["original_subtitles"],
            viral_data=large_training_data["viral_subtitles"],
            config=training_config
        )
        
        memory_monitor()
        memory_usage = peak_memory - initial_memory
        
        # 验证内存约束 (3.8GB = 3891.2MB)
        assert memory_usage <= 3891.2, f"内存使用超限: {memory_usage:.2f}MB (限制: 3891.2MB)"

    def test_loss_convergence(self):
        """测试损失收敛 (>50%/10轮)"""
        training_config = {
            "epochs": 10,
            "batch_size": 2,
            "learning_rate": 0.01,
            "language": "zh"
        }
        
        result = self.zh_trainer.train(
            original_data=self.sample_training_data["zh"]["original_subtitles"],
            viral_data=self.sample_training_data["zh"]["viral_subtitles"],
            config=training_config
        )
        
        # 验证损失收敛
        loss_history = result.get("loss_history", [])
        assert len(loss_history) >= 10, f"损失历史不足: {len(loss_history)}"
        
        initial_loss = loss_history[0]
        final_loss = loss_history[-1]
        
        # 计算损失下降比例
        loss_reduction = (initial_loss - final_loss) / initial_loss
        assert loss_reduction >= 0.5, f"损失收敛不足: {loss_reduction:.2%} (目标: >50%)"

    def test_data_augmentation_functionality(self):
        """测试数据增强功能"""
        original_data = self.sample_training_data["zh"]["original_subtitles"]
        
        # 文本增强
        text_augmented = self.data_augmenter.augment_text(original_data, language="zh")
        assert len(text_augmented) > len(original_data), "文本增强未生成新数据"
        
        # 剧情增强
        plot_augmented = self.plot_augmenter.augment_plot_structure(original_data, language="zh")
        assert len(plot_augmented) > len(original_data), "剧情增强未生成新数据"
        
        # 验证增强数据质量
        for augmented_item in text_augmented:
            assert "text" in augmented_item, "增强数据缺少文本字段"
            assert "start_time" in augmented_item, "增强数据缺少时间信息"
            assert len(augmented_item["text"]) > 0, "增强数据文本为空"

    def test_training_checkpoint_and_resume(self):
        """测试训练检查点和恢复"""
        checkpoint_path = os.path.join(self.temp_dir, "training_checkpoint.json")
        
        training_config = {
            "epochs": 5,
            "batch_size": 1,
            "learning_rate": 0.001,
            "language": "zh",
            "checkpoint_path": checkpoint_path,
            "save_checkpoint_every": 2
        }
        
        # 开始训练
        result = self.zh_trainer.train(
            original_data=self.sample_training_data["zh"]["original_subtitles"],
            viral_data=self.sample_training_data["zh"]["viral_subtitles"],
            config=training_config
        )
        
        # 验证检查点文件存在
        assert os.path.exists(checkpoint_path), "检查点文件未创建"
        
        # 验证检查点内容
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        
        assert "epoch" in checkpoint_data, "检查点缺少epoch信息"
        assert "loss_history" in checkpoint_data, "检查点缺少损失历史"

    def test_training_error_handling(self):
        """测试训练错误处理"""
        # 测试空数据
        empty_result = self.zh_trainer.train(
            original_data=[],
            viral_data=[],
            config={"epochs": 1, "language": "zh"}
        )
        assert "error" in empty_result or empty_result["status"] == "failed", "空数据错误处理失败"
        
        # 测试不匹配数据
        mismatched_result = self.zh_trainer.train(
            original_data=self.sample_training_data["zh"]["original_subtitles"],
            viral_data=self.sample_training_data["zh"]["viral_subtitles"][:1],  # 数量不匹配
            config={"epochs": 1, "language": "zh"}
        )
        # 应该有适当的错误处理或数据对齐

    def test_curriculum_learning_strategy(self):
        """测试课程学习策略"""
        from src.training.curriculum import CurriculumLearning
        
        curriculum = CurriculumLearning()
        
        # 创建不同难度的训练数据
        easy_data = self.sample_training_data["zh"]["original_subtitles"][:1]
        hard_data = self.sample_training_data["zh"]["original_subtitles"]
        
        # 获取课程学习计划
        learning_plan = curriculum.create_learning_plan(
            easy_samples=easy_data,
            hard_samples=hard_data,
            total_epochs=10
        )
        
        assert len(learning_plan) > 0, "课程学习计划为空"
        assert learning_plan[0]["difficulty"] == "easy", "课程学习应该从简单开始"

    @pytest.mark.performance
    def test_parallel_training_capability(self):
        """测试并行训练能力"""
        import threading
        
        results = []
        errors = []
        
        def train_worker(language: str, worker_id: int):
            try:
                trainer = self.zh_trainer if language == "zh" else self.en_trainer
                data = self.sample_training_data[language]
                
                config = {
                    "epochs": 2,
                    "batch_size": 1,
                    "learning_rate": 0.001,
                    "language": language,
                    "worker_id": worker_id
                }
                
                result = trainer.train(
                    original_data=data["original_subtitles"],
                    viral_data=data["viral_subtitles"],
                    config=config
                )
                
                results.append((worker_id, language, result))
                
            except Exception as e:
                errors.append((worker_id, language, str(e)))
        
        # 创建并行训练线程
        threads = []
        for i in range(4):
            lang = "zh" if i % 2 == 0 else "en"
            thread = threading.Thread(target=train_worker, args=(lang, i))
            threads.append(thread)
        
        # 启动并等待完成
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=60)
        
        # 验证并行训练结果
        assert len(errors) == 0, f"并行训练出现错误: {errors}"
        assert len(results) == 4, f"并行训练结果不完整: {len(results)}/4"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
