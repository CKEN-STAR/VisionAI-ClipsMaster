#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应模型配置管理器
根据硬件配置自动调整AI模型的量化等级、加载策略和内存使用
"""

import os
import gc
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .hardware_detector import HardwareDetector, HardwareInfo, PerformanceLevel


class ModelMode(Enum):
    """模型运行模式"""
    AUTO = "auto"                    # 自动模式
    PERFORMANCE = "performance"      # 性能优先
    MEMORY = "memory"               # 内存优先
    CUSTOM = "custom"               # 自定义


class QuantizationLevel(Enum):
    """量化等级"""
    Q2_K = "Q2_K"       # 2-bit量化，最小内存
    Q4_K_M = "Q4_K_M"   # 4-bit量化，平衡
    Q5_K = "Q5_K"       # 5-bit量化，高质量
    FP16 = "FP16"       # 半精度浮点
    FP32 = "FP32"       # 全精度浮点


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    quantization: QuantizationLevel
    max_memory_gb: float
    context_length: int
    batch_size: int
    num_threads: int
    use_gpu: bool
    gpu_layers: int


@dataclass
class AdaptiveConfig:
    """自适应配置"""
    mode: ModelMode
    hardware_info: HardwareInfo
    
    # 模型配置
    mistral_config: ModelConfig
    qwen_config: ModelConfig
    
    # 运行策略
    concurrent_models: bool
    dynamic_loading: bool
    memory_threshold: float
    
    # 监控设置
    monitor_interval: int
    auto_cleanup: bool
    
    # 性能预期
    expected_bleu_score: float
    max_startup_time: int
    max_switch_time: int


class AdaptiveModelConfigManager:
    """自适应模型配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化配置管理器"""
        self.logger = logging.getLogger(__name__)
        self.config_dir = config_dir or Path("configs")
        
        # 硬件检测器
        self.hardware_detector = HardwareDetector()
        self.hardware_info = None
        
        # 当前配置
        self.current_config = None
        self.current_mode = ModelMode.AUTO
        
        # 监控线程
        self.monitor_thread = None
        self.monitor_running = False
        
        # 配置历史
        self.config_history = []
        
        self.logger.info("自适应模型配置管理器初始化完成")
    
    def initialize(self) -> AdaptiveConfig:
        """初始化配置系统"""
        try:
            self.logger.info("开始初始化自适应配置系统...")
            
            # 检测硬件
            self.hardware_info = self.hardware_detector.detect_hardware()
            
            # 生成初始配置
            self.current_config = self._generate_adaptive_config(self.current_mode)
            
            # 保存配置
            self._save_config()
            
            # 启动监控
            self._start_monitoring()
            
            self.logger.info(f"自适应配置系统初始化完成 - 模式: {self.current_mode.value}")
            return self.current_config
            
        except Exception as e:
            self.logger.error(f"配置系统初始化失败: {e}")
            return self._get_fallback_config()
    
    def set_mode(self, mode: ModelMode) -> AdaptiveConfig:
        """设置运行模式"""
        try:
            self.logger.info(f"切换运行模式: {self.current_mode.value} -> {mode.value}")
            
            old_mode = self.current_mode
            self.current_mode = mode
            
            # 重新生成配置
            new_config = self._generate_adaptive_config(mode)
            
            # 验证配置
            if self._validate_config(new_config):
                self.current_config = new_config
                self._save_config()
                self.logger.info(f"模式切换成功: {mode.value}")
                return new_config
            else:
                # 回退到原模式
                self.current_mode = old_mode
                self.logger.warning(f"配置验证失败，回退到原模式: {old_mode.value}")
                return self.current_config
                
        except Exception as e:
            self.logger.error(f"模式切换失败: {e}")
            return self.current_config
    
    def get_model_config(self, model_type: str) -> ModelConfig:
        """获取指定模型的配置"""
        if model_type.lower() in ["mistral", "english", "en"]:
            return self.current_config.mistral_config
        elif model_type.lower() in ["qwen", "chinese", "zh"]:
            return self.current_config.qwen_config
        else:
            raise ValueError(f"未知的模型类型: {model_type}")
    
    def update_hardware_info(self) -> HardwareInfo:
        """更新硬件信息"""
        try:
            self.hardware_info = self.hardware_detector.detect_hardware()
            
            # 检查是否需要调整配置
            if self._should_adjust_config():
                self.logger.info("检测到硬件变化，重新生成配置")
                self.current_config = self._generate_adaptive_config(self.current_mode)
                self._save_config()
            
            return self.hardware_info
            
        except Exception as e:
            self.logger.error(f"硬件信息更新失败: {e}")
            return self.hardware_info
    
    def _generate_adaptive_config(self, mode: ModelMode) -> AdaptiveConfig:
        """生成自适应配置"""
        try:
            if not self.hardware_info:
                self.hardware_info = self.hardware_detector.detect_hardware()
            
            # 根据模式和硬件生成配置
            if mode == ModelMode.AUTO:
                return self._generate_auto_config()
            elif mode == ModelMode.PERFORMANCE:
                return self._generate_performance_config()
            elif mode == ModelMode.MEMORY:
                return self._generate_memory_config()
            else:  # CUSTOM
                return self._load_custom_config()
                
        except Exception as e:
            self.logger.error(f"配置生成失败: {e}")
            return self._get_fallback_config()
    
    def _generate_auto_config(self) -> AdaptiveConfig:
        """生成自动模式配置"""
        perf_level = self.hardware_info.performance_level
        total_memory = self.hardware_info.total_memory_gb
        
        if perf_level == PerformanceLevel.LOW:
            # 4GB RAM设备配置 - 优化内存分配
            max_model_memory = min(total_memory * 0.35, 1.5)  # 使用35%的总内存，最多1.5GB

            mistral_config = ModelConfig(
                model_name="mistral-7b",
                quantization=QuantizationLevel.Q2_K,
                max_memory_gb=max_model_memory,
                context_length=1024,  # 减少上下文长度节省内存
                batch_size=1,
                num_threads=min(4, self.hardware_info.cpu_count),
                use_gpu=False,
                gpu_layers=0
            )

            qwen_config = ModelConfig(
                model_name="qwen2.5-7b",
                quantization=QuantizationLevel.Q2_K,
                max_memory_gb=max_model_memory,
                context_length=1024,  # 减少上下文长度节省内存
                batch_size=1,
                num_threads=min(4, self.hardware_info.cpu_count),
                use_gpu=False,
                gpu_layers=0
            )
            
            return AdaptiveConfig(
                mode=ModelMode.AUTO,
                hardware_info=self.hardware_info,
                mistral_config=mistral_config,
                qwen_config=qwen_config,
                concurrent_models=False,  # 单模型动态加载
                dynamic_loading=True,
                memory_threshold=0.85,
                monitor_interval=30,
                auto_cleanup=True,
                expected_bleu_score=0.70,
                max_startup_time=10,
                max_switch_time=3
            )
            
        elif perf_level == PerformanceLevel.MEDIUM:
            # 8GB RAM设备配置 - 优化内存分配
            max_model_memory = min(total_memory * 0.3, 2.5)  # 使用30%的总内存，最多2.5GB

            mistral_config = ModelConfig(
                model_name="mistral-7b",
                quantization=QuantizationLevel.Q4_K_M,
                max_memory_gb=max_model_memory,
                context_length=2048,  # 适中的上下文长度
                batch_size=1,  # 减少批处理大小节省内存
                num_threads=min(6, self.hardware_info.cpu_count),
                use_gpu=self.hardware_info.gpu_type.value != "none",
                gpu_layers=20 if self.hardware_info.gpu_type.value != "none" else 0
            )

            qwen_config = ModelConfig(
                model_name="qwen2.5-7b",
                quantization=QuantizationLevel.Q4_K_M,
                max_memory_gb=max_model_memory,
                context_length=2048,  # 适中的上下文长度
                batch_size=1,  # 减少批处理大小节省内存
                num_threads=min(6, self.hardware_info.cpu_count),
                use_gpu=self.hardware_info.gpu_type.value != "none",
                gpu_layers=20 if self.hardware_info.gpu_type.value != "none" else 0
            )
            
            return AdaptiveConfig(
                mode=ModelMode.AUTO,
                hardware_info=self.hardware_info,
                mistral_config=mistral_config,
                qwen_config=qwen_config,
                concurrent_models=False,
                dynamic_loading=True,
                memory_threshold=0.80,
                monitor_interval=30,
                auto_cleanup=True,
                expected_bleu_score=0.75,
                max_startup_time=8,
                max_switch_time=2
            )
            
        else:  # HIGH or ULTRA
            # 16GB+ RAM设备配置 - 优化内存分配
            if perf_level == PerformanceLevel.HIGH:
                quantization = QuantizationLevel.Q4_K_M  # 使用更保守的量化
                max_memory = min(total_memory * 0.25, 3.0)  # 使用25%的总内存，最多3.0GB
                concurrent_models = False  # 高配设备也使用单模型模式确保稳定性
            else:  # ULTRA
                quantization = QuantizationLevel.Q5_K
                max_memory = min(total_memory * 0.2, 4.0)  # 使用20%的总内存，最多4.0GB
                concurrent_models = True

            mistral_config = ModelConfig(
                model_name="mistral-7b",
                quantization=quantization,
                max_memory_gb=max_memory,
                context_length=4096,  # 适中的上下文长度
                batch_size=2,  # 适中的批处理大小
                num_threads=min(8, self.hardware_info.cpu_count),
                use_gpu=self.hardware_info.gpu_type.value != "none",
                gpu_layers=35 if self.hardware_info.gpu_type.value != "none" else 0
            )

            qwen_config = ModelConfig(
                model_name="qwen2.5-7b",
                quantization=quantization,
                max_memory_gb=max_memory,
                context_length=4096,  # 适中的上下文长度
                batch_size=2,  # 适中的批处理大小
                num_threads=min(8, self.hardware_info.cpu_count),
                use_gpu=self.hardware_info.gpu_type.value != "none",
                gpu_layers=35 if self.hardware_info.gpu_type.value != "none" else 0
            )

            # 设置并发模型标志
            concurrent_models_flag = concurrent_models if perf_level == PerformanceLevel.ULTRA else False
            
            return AdaptiveConfig(
                mode=ModelMode.AUTO,
                hardware_info=self.hardware_info,
                mistral_config=mistral_config,
                qwen_config=qwen_config,
                concurrent_models=concurrent_models_flag,  # 根据性能等级决定
                dynamic_loading=not concurrent_models_flag,  # 与并发模型相反
                memory_threshold=0.75,
                monitor_interval=60,
                auto_cleanup=True,  # 启用自动清理
                expected_bleu_score=0.78 if perf_level == PerformanceLevel.ULTRA else 0.75,
                max_startup_time=5,
                max_switch_time=1
            )

    def _generate_performance_config(self) -> AdaptiveConfig:
        """生成性能优先配置"""
        total_memory = self.hardware_info.total_memory_gb

        # 根据内存大小选择合适的量化等级
        if total_memory >= 32:
            quantization = QuantizationLevel.Q5_K
            max_memory = min(total_memory * 0.15, 4.0)  # 保守的内存使用
        elif total_memory >= 16:
            quantization = QuantizationLevel.Q4_K_M
            max_memory = min(total_memory * 0.2, 3.0)
        else:
            quantization = QuantizationLevel.Q4_K_M
            max_memory = min(total_memory * 0.25, 2.0)

        mistral_config = ModelConfig(
            model_name="mistral-7b",
            quantization=quantization,
            max_memory_gb=max_memory,
            context_length=4096,  # 适中的上下文长度
            batch_size=2,  # 适中的批处理大小
            num_threads=min(8, self.hardware_info.cpu_count),
            use_gpu=self.hardware_info.gpu_type.value != "none",
            gpu_layers=35 if self.hardware_info.gpu_type.value != "none" else 0
        )

        qwen_config = ModelConfig(
            model_name="qwen2.5-7b",
            quantization=quantization,
            max_memory_gb=max_memory,
            context_length=4096,  # 适中的上下文长度
            batch_size=2,  # 适中的批处理大小
            num_threads=min(8, self.hardware_info.cpu_count),
            use_gpu=self.hardware_info.gpu_type.value != "none",
            gpu_layers=35 if self.hardware_info.gpu_type.value != "none" else 0
        )

        return AdaptiveConfig(
            mode=ModelMode.PERFORMANCE,
            hardware_info=self.hardware_info,
            mistral_config=mistral_config,
            qwen_config=qwen_config,
            concurrent_models=False,  # 性能模式也使用单模型确保稳定性
            dynamic_loading=True,
            memory_threshold=0.70,
            monitor_interval=60,
            auto_cleanup=True,
            expected_bleu_score=0.78,
            max_startup_time=8,
            max_switch_time=2
        )

    def _generate_memory_config(self) -> AdaptiveConfig:
        """生成内存优先配置"""
        total_memory = self.hardware_info.total_memory_gb

        # 内存优先：使用最激进的量化和最小的内存分配
        max_memory = min(total_memory * 0.1, 1.2)  # 使用10%的总内存，最多1.2GB

        mistral_config = ModelConfig(
            model_name="mistral-7b",
            quantization=QuantizationLevel.Q2_K,
            max_memory_gb=max_memory,
            context_length=512,  # 最小上下文长度
            batch_size=1,
            num_threads=min(4, self.hardware_info.cpu_count),
            use_gpu=False,  # 强制CPU模式节省显存
            gpu_layers=0
        )

        qwen_config = ModelConfig(
            model_name="qwen2.5-7b",
            quantization=QuantizationLevel.Q2_K,
            max_memory_gb=max_memory,
            context_length=512,  # 最小上下文长度
            batch_size=1,
            num_threads=min(4, self.hardware_info.cpu_count),
            use_gpu=False,
            gpu_layers=0
        )

        return AdaptiveConfig(
            mode=ModelMode.MEMORY,
            hardware_info=self.hardware_info,
            mistral_config=mistral_config,
            qwen_config=qwen_config,
            concurrent_models=False,
            dynamic_loading=True,
            memory_threshold=0.95,  # 更高的内存阈值
            monitor_interval=15,  # 更频繁的监控
            auto_cleanup=True,
            expected_bleu_score=0.68,
            max_startup_time=12,
            max_switch_time=4
        )

    def _load_custom_config(self) -> AdaptiveConfig:
        """加载自定义配置"""
        try:
            config_file = self.config_dir / "custom_model_config.yaml"
            if config_file.exists():
                # 这里应该实现YAML配置文件的加载
                # 为简化，返回默认配置
                self.logger.info("加载自定义配置（当前返回默认配置）")
                return self._generate_auto_config()
            else:
                self.logger.warning("自定义配置文件不存在，使用自动配置")
                return self._generate_auto_config()
        except Exception as e:
            self.logger.error(f"加载自定义配置失败: {e}")
            return self._generate_auto_config()

    def _validate_config(self, config: AdaptiveConfig) -> bool:
        """验证配置的有效性"""
        try:
            # 检查内存限制 - 修复验证逻辑
            if config.concurrent_models:
                # 并发模式：两个模型同时加载
                total_model_memory = config.mistral_config.max_memory_gb + config.qwen_config.max_memory_gb
            else:
                # 单模型模式：只需要较大的那个模型的内存
                total_model_memory = max(config.mistral_config.max_memory_gb, config.qwen_config.max_memory_gb)

            # 使用总内存而不是可用内存进行验证，并留出系统开销
            total_memory = self.hardware_info.total_memory_gb
            memory_limit = total_memory * 0.8  # 使用80%的总内存作为限制

            # 对于低配设备，使用更宽松的验证标准
            if self.hardware_info.performance_level.value == "low":
                memory_limit = min(total_memory * 0.9, 3.8)  # 4GB设备最多使用3.8GB

            if total_model_memory > memory_limit:
                self.logger.warning(f"配置内存需求: {total_model_memory}GB，内存限制: {memory_limit}GB")
                # 对于内存模式，允许更宽松的验证
                if config.mode == ModelMode.MEMORY and total_model_memory <= 2.0:
                    self.logger.info("内存模式下使用宽松验证标准")
                    return True
                return False

            # 检查其他约束
            if config.mistral_config.batch_size < 1 or config.qwen_config.batch_size < 1:
                self.logger.warning("批处理大小不能小于1")
                return False

            # 检查量化等级是否合理
            valid_quantizations = ["Q2_K", "Q4_K_M", "Q5_K", "FP16", "FP32"]
            if (config.mistral_config.quantization.value not in valid_quantizations or
                config.qwen_config.quantization.value not in valid_quantizations):
                self.logger.warning("无效的量化等级")
                return False

            return True

        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False

    def _should_adjust_config(self) -> bool:
        """检查是否需要调整配置"""
        try:
            if not self.current_config:
                return True

            # 检查内存使用变化
            current_memory_usage = self.hardware_info.memory_usage_percent
            if current_memory_usage > 85:
                self.logger.info(f"内存使用率过高: {current_memory_usage}%")
                return True

            # 检查可用内存变化
            available_memory = self.hardware_info.available_memory_gb
            required_memory = self.current_config.mistral_config.max_memory_gb
            if not self.current_config.concurrent_models:
                required_memory = max(
                    self.current_config.mistral_config.max_memory_gb,
                    self.current_config.qwen_config.max_memory_gb
                )
            else:
                required_memory += self.current_config.qwen_config.max_memory_gb

            if available_memory < required_memory * 1.2:  # 需要20%的缓冲
                self.logger.info(f"可用内存不足: {available_memory}GB < {required_memory * 1.2}GB")
                return True

            return False

        except Exception as e:
            self.logger.error(f"配置调整检查失败: {e}")
            return False

    def _start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("监控线程已启动")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitor_running:
            try:
                time.sleep(self.current_config.monitor_interval)

                # 更新硬件信息
                self.update_hardware_info()

                # 检查内存压力
                self._check_memory_pressure()

                # 自动清理
                if self.current_config.auto_cleanup:
                    self._auto_cleanup()

            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")

    def _check_memory_pressure(self):
        """检查内存压力"""
        try:
            memory_usage = self.hardware_info.memory_usage_percent / 100
            threshold = self.current_config.memory_threshold

            if memory_usage > threshold:
                self.logger.warning(f"内存压力警告: {memory_usage:.1%} > {threshold:.1%}")

                # 触发降级
                if memory_usage > 0.90:
                    self._emergency_downgrade()
                elif memory_usage > 0.85:
                    self._gradual_downgrade()

        except Exception as e:
            self.logger.error(f"内存压力检查失败: {e}")

    def _emergency_downgrade(self):
        """紧急降级"""
        self.logger.warning("触发紧急内存降级")

        # 强制切换到内存优先模式
        if self.current_mode != ModelMode.MEMORY:
            self.set_mode(ModelMode.MEMORY)

        # 强制垃圾回收
        gc.collect()

    def _gradual_downgrade(self):
        """渐进式降级"""
        self.logger.info("执行渐进式内存降级")

        # 如果当前是并发模式，切换到单模型模式
        if self.current_config.concurrent_models:
            self.current_config.concurrent_models = False
            self.current_config.dynamic_loading = True
            self.logger.info("切换到单模型动态加载模式")

    def _auto_cleanup(self):
        """自动清理"""
        try:
            # 执行垃圾回收
            gc.collect()

            # 清理缓存（如果有的话）
            # 这里可以添加更多的清理逻辑

        except Exception as e:
            self.logger.error(f"自动清理失败: {e}")

    def _save_config(self):
        """保存配置"""
        try:
            # 这里应该实现配置的持久化
            # 为简化，只记录到历史
            self.config_history.append({
                "timestamp": time.time(),
                "mode": self.current_mode.value,
                "config": self.current_config
            })

            # 只保留最近10个配置
            if len(self.config_history) > 10:
                self.config_history = self.config_history[-10:]

        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")

    def _get_fallback_config(self) -> AdaptiveConfig:
        """获取回退配置"""
        # 最保守的配置，确保在任何设备上都能运行
        mistral_config = ModelConfig(
            model_name="mistral-7b",
            quantization=QuantizationLevel.Q2_K,
            max_memory_gb=1.5,
            context_length=1024,
            batch_size=1,
            num_threads=2,
            use_gpu=False,
            gpu_layers=0
        )

        qwen_config = ModelConfig(
            model_name="qwen2.5-7b",
            quantization=QuantizationLevel.Q2_K,
            max_memory_gb=1.5,
            context_length=1024,
            batch_size=1,
            num_threads=2,
            use_gpu=False,
            gpu_layers=0
        )

        return AdaptiveConfig(
            mode=ModelMode.MEMORY,
            hardware_info=self.hardware_info or self.hardware_detector._get_default_low_config(),
            mistral_config=mistral_config,
            qwen_config=qwen_config,
            concurrent_models=False,
            dynamic_loading=True,
            memory_threshold=0.95,
            monitor_interval=30,
            auto_cleanup=True,
            expected_bleu_score=0.65,
            max_startup_time=15,
            max_switch_time=5
        )

    def stop_monitoring(self):
        """停止监控"""
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("监控线程已停止")


if __name__ == "__main__":
    # 测试自适应配置管理器
    manager = AdaptiveModelConfigManager()
    config = manager.initialize()
    print(f"生成的自适应配置: {config}")
