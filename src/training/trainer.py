#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用训练器 - 集成中英文训练器和内存管理
提供统一的训练接口和优化的内存管理机制
"""

import os
import sys
import gc
import json
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class MemoryManager:
    """内存管理器 - 优化内存使用和清理"""

    def __init__(self, memory_limit_gb: float = 3.8):
        """
        初始化内存管理器

        Args:
            memory_limit_gb: 内存限制(GB)
        """
        self.memory_limit = memory_limit_gb * (1024**3)  # 转换为字节
        self.initial_memory = psutil.virtual_memory().used
        self.peak_memory = self.initial_memory
        self.cleanup_threshold = 0.8  # 80%时触发清理

        print(f"💾 内存管理器初始化")
        print(f"📊 内存限制: {memory_limit_gb:.1f}GB")
        print(f"📊 初始内存: {self.initial_memory / (1024**3):.2f}GB")

    def get_current_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        current = psutil.virtual_memory().used
        increase = current - self.initial_memory

        if current > self.peak_memory:
            self.peak_memory = current

        return {
            "current_gb": current / (1024**3),
            "increase_gb": increase / (1024**3),
            "peak_gb": self.peak_memory / (1024**3),
            "limit_gb": self.memory_limit / (1024**3),
            "usage_ratio": increase / self.memory_limit
        }

    def check_memory_limit(self) -> bool:
        """检查是否超过内存限制"""
        memory_info = self.get_current_memory_usage()
        return memory_info["usage_ratio"] < 1.0

    def force_garbage_collection(self) -> Dict[str, Any]:
        """强制垃圾回收"""
        before_memory = psutil.virtual_memory().used

        # 执行垃圾回收
        collected = gc.collect()

        # 强制清理未引用对象
        for i in range(3):
            gc.collect()
            time.sleep(0.01)

        after_memory = psutil.virtual_memory().used
        freed_memory = before_memory - after_memory

        cleanup_result = {
            "objects_collected": collected,
            "memory_freed_mb": freed_memory / (1024**2),
            "before_memory_gb": before_memory / (1024**3),
            "after_memory_gb": after_memory / (1024**3)
        }

        return cleanup_result

    def auto_cleanup_if_needed(self) -> bool:
        """如果需要则自动清理内存"""
        memory_info = self.get_current_memory_usage()

        if memory_info["usage_ratio"] > self.cleanup_threshold:
            print(f"⚠️ 内存使用率 {memory_info['usage_ratio']:.1%}，开始自动清理...")
            cleanup_result = self.force_garbage_collection()
            print(f"🧹 清理完成: 释放 {cleanup_result['memory_freed_mb']:.1f}MB")
            return True

        return False

class ModelTrainer:
    """通用模型训练器 - 集成内存管理和错误处理"""

    def __init__(self, training_data: Optional[List[Dict[str, Any]]] = None,
                 use_gpu: bool = False, memory_limit_gb: float = 3.8):
        """
        初始化训练器

        Args:
            training_data: 训练数据
            use_gpu: 是否使用GPU
            memory_limit_gb: 内存限制
        """
        self.training_data = training_data or []
        self.use_gpu = use_gpu
        self.memory_manager = MemoryManager(memory_limit_gb)

        # 训练状态
        self.is_training = False
        self.current_epoch = 0
        self.training_interrupted = False

        # 错误处理
        self.error_log = []
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

        # 设置日志
        self.logger = logging.getLogger("ModelTrainer")

        print(f"🤖 通用训练器初始化完成")
        print(f"📊 训练数据: {len(self.training_data)} 个样本")
        print(f"🔧 GPU模式: {'启用' if use_gpu else '禁用'}")

    def validate_training_data(self) -> Dict[str, Any]:
        """验证训练数据"""
        validation_result = {
            "is_valid": False,
            "total_samples": len(self.training_data),
            "valid_samples": 0,
            "invalid_samples": 0,
            "issues": []
        }

        if not self.training_data:
            validation_result["issues"].append("训练数据为空")
            return validation_result

        valid_count = 0
        for i, sample in enumerate(self.training_data):
            if isinstance(sample, dict) and "original" in sample and "viral" in sample:
                if sample["original"] and sample["viral"]:
                    valid_count += 1
                else:
                    validation_result["issues"].append(f"样本 {i}: 内容为空")
            else:
                validation_result["issues"].append(f"样本 {i}: 格式错误")

        validation_result["valid_samples"] = valid_count
        validation_result["invalid_samples"] = len(self.training_data) - valid_count
        validation_result["is_valid"] = valid_count > 0

        return validation_result

    def handle_training_error(self, error: Exception, context: str) -> bool:
        """
        处理训练错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            是否可以恢复
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "recovery_attempt": self.recovery_attempts
        }

        self.error_log.append(error_info)
        self.recovery_attempts += 1

        print(f"❌ 训练错误 [{context}]: {error}")

        # 尝试恢复
        if self.recovery_attempts <= self.max_recovery_attempts:
            print(f"🔄 尝试恢复 (第 {self.recovery_attempts}/{self.max_recovery_attempts} 次)...")

            # 清理内存
            self.memory_manager.force_garbage_collection()

            # 等待一段时间
            time.sleep(1)

            return True
        else:
            print(f"💥 超过最大恢复次数，训练终止")
            return False
    
    def train(self, training_data: Optional[List[Dict[str, Any]]] = None,
              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行训练

        Args:
            training_data: 训练数据
            progress_callback: 进度回调函数，接收(进度百分比,状态消息)，返回bool表示是否继续

        Returns:
            Dict: 训练结果
        """
        start_time = time.time()

        # 使用传入的训练数据或实例数据
        if training_data:
            self.training_data = training_data

        try:
            # 验证训练数据
            validation_result = self.validate_training_data()
            if not validation_result["is_valid"]:
                return {
                    "success": False,
                    "error": "训练数据验证失败",
                    "validation_issues": validation_result["issues"]
                }

            # 开始训练
            self.is_training = True
            self.training_interrupted = False

            if progress_callback:
                progress_callback(0.1, "初始化训练环境...")

            # 内存检查
            if not self.memory_manager.check_memory_limit():
                return {"success": False, "error": "内存不足，无法开始训练"}

            # 执行训练
            result = self._execute_training(progress_callback)

            # 训练完成后清理内存
            self.memory_manager.force_garbage_collection()

            end_time = time.time()
            result["training_duration"] = end_time - start_time

            return result

        except Exception as e:
            # 错误处理
            if self.handle_training_error(e, "主训练流程"):
                # 尝试恢复训练
                return self.train(training_data, progress_callback)
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "error_log": self.error_log
                }
        finally:
            self.is_training = False

    def _execute_training(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行训练过程

        Args:
            progress_callback: 进度回调函数

        Returns:
            训练结果
        """
        try:
            # 准备训练数据
            if progress_callback:
                progress_callback(0.2, "准备训练数据...")

            # 检测语言并选择合适的训练器
            language = self._detect_primary_language()

            if progress_callback:
                progress_callback(0.3, f"检测到主要语言: {'中文' if language == 'zh' else '英文'}")

            # 导入对应的训练器
            if language == "zh":
                from .zh_trainer import ZhTrainer
                trainer = ZhTrainer(use_gpu=self.use_gpu)
            else:
                from .en_trainer import EnTrainer
                trainer = EnTrainer(use_gpu=self.use_gpu)

            if progress_callback:
                progress_callback(0.4, f"初始化{language}训练器...")

            # 执行训练
            def training_progress_callback(progress, message):
                # 将训练器进度映射到总体进度 (40%-95%)
                overall_progress = 0.4 + progress * 0.55
                if progress_callback:
                    return progress_callback(overall_progress, message)
                return True

            # 内存监控
            self.memory_manager.auto_cleanup_if_needed()

            # 执行实际训练
            training_result = trainer.train(
                training_data=self.training_data,
                progress_callback=training_progress_callback
            )

            if progress_callback:
                progress_callback(0.95, "保存训练结果...")

            # 最终内存清理
            self.memory_manager.force_garbage_collection()

            if progress_callback:
                progress_callback(1.0, "训练完成！")

            return training_result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _detect_primary_language(self) -> str:
        """检测训练数据的主要语言"""
        chinese_count = 0
        english_count = 0

        for sample in self.training_data[:10]:  # 只检查前10个样本
            text = sample.get("original", "") + sample.get("viral", "")

            # 检测中文字符
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            # 检测英文字符
            english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)

            if chinese_chars > english_chars:
                chinese_count += 1
            else:
                english_count += 1

        return "zh" if chinese_count > english_count else "en"

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        return {
            "memory_usage": self.memory_manager.get_current_memory_usage(),
            "error_count": len(self.error_log),
            "recovery_attempts": self.recovery_attempts,
            "is_training": self.is_training
        }

    def interrupt_training(self) -> bool:
        """中断训练"""
        if self.is_training:
            self.training_interrupted = True
            print("⚠️ 训练中断请求已发送")
            return True
        return False

    def resume_training(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """恢复训练"""
        if self.training_interrupted:
            print("🔄 恢复训练...")
            self.training_interrupted = False
            self.recovery_attempts = 0  # 重置恢复计数
            return self.train(progress_callback=progress_callback)
        else:
            return {"success": False, "error": "没有中断的训练可以恢复"}

    def export_training_log(self, output_path: Optional[str] = None) -> str:
        """导出训练日志"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"training_log_{timestamp}.json"

        log_data = {
            "training_data_count": len(self.training_data),
            "memory_stats": self.get_memory_stats(),
            "error_log": self.error_log,
            "created_at": datetime.now().isoformat()
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            print(f"📋 训练日志已导出: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 日志导出失败: {e}")
            return ""
