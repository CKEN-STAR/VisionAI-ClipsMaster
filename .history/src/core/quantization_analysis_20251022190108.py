#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 量化技术深度分析
提供量化技术原理、性能影响分析和轻量化部署评估
"""

import math
import psutil
import platform
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class QuantizationType(Enum):
    """量化类型枚举（仅GPTQ格式，支持LoRA/QLoRA微调）"""
    FP16 = "fp16"           # 16位浮点 (半精度)
    INT8 = "int8"           # 8位GPTQ量化，group_size=128
    INT4 = "int4"           # 4位GPTQ量化，group_size=128
    INT8_PERCHANNEL = "int8_perchannel"  # 8位GPTQ per-channel量化
    INT4_PERCHANNEL = "int4_perchannel"  # 4位GPTQ per-channel量化

@dataclass
class ModelVariant:
    """模型变体配置"""
    name: str
    quantization: QuantizationType
    size_gb: float
    memory_requirement_gb: float
    inference_speed_factor: float  # 相对于FP16的速度倍数
    quality_retention: float       # 质量保持率 (0.0-1.0)
    cpu_compatible: bool
    gpu_memory_min_gb: float

@dataclass
class HardwareProfile:
    """硬件配置档案"""
    gpu_memory_gb: float
    system_ram_gb: float
    storage_available_gb: float
    cpu_cores: int
    has_gpu: bool
    gpu_compute_capability: Optional[str] = None

    @property
    def total_memory_gb(self) -> float:
        """兼容性属性：总内存大小(GB)"""
        return self.system_ram_gb

    @property
    def cpu_count(self) -> int:
        """兼容性属性：CPU核心数"""
        return self.cpu_cores

class QuantizationAnalyzer:
    """量化技术分析器"""
    
    def __init__(self):
        self.model_variants = self._initialize_model_variants()
        self.performance_benchmarks = self._initialize_benchmarks()
    
    def _initialize_model_variants(self) -> Dict[str, List[ModelVariant]]:
        """
        初始化模型变体配置（仅FP16原始模型）

        重要说明：
        - 只使用FP16原始模型，不使用预量化模型（GPTQ/INT8/INT4）
        - 原因：训练器使用AutoModelForCausalLM.from_pretrained，不支持GPTQ模型加载
        - 正确流程：FP16模型 + LoRA训练 → 保存HF格式 → 转换为GGUF（此时量化）
        - 量化在GGUF转换阶段进行（Q4_K_M, Q5_K, Q8_0等），而不是在下载阶段

        模型选择基于硬件评分：
        - 0-35分（入门级）：Qwen2.5-0.5B / Mistral-7B
        - 35-55分（进阶级）：Qwen2.5-1.5B / Mistral-7B
        - 55-65分（中级）：Qwen2.5-3B / Mistral-7B
        - 65-75分（中高级）：Qwen2.5-7B / Mistral-7B
        - 75-85分（高级）：Qwen2.5-14B / Mistral-7B
        - 85-100分（旗舰级）：Qwen2.5-32B / Mistral-7B
        """
        return {
            # Qwen2.5-0.5B 中文模型（入门级）- 仅FP16
            "qwen2.5-0.5b": [
                ModelVariant(
                    name="Qwen2.5-0.5B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=1.0,  # FP16原始模型大小
                    memory_requirement_gb=4.0,  # 训练时需要的内存
                    inference_speed_factor=1.0,  # FP16基准速度
                    quality_retention=1.0,  # 无量化损失
                    cpu_compatible=True,
                    gpu_memory_min_gb=4.0
                )
            ],

            # Qwen2.5-1.5B 中文模型（进阶级）- 仅FP16
            "qwen2.5-1.5b": [
                ModelVariant(
                    name="Qwen2.5-1.5B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=3.0,
                    memory_requirement_gb=6.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=True,
                    gpu_memory_min_gb=6.0
                )
            ],

            # Qwen2.5-3B 中文模型（中级）- 仅FP16
            "qwen2.5-3b": [
                ModelVariant(
                    name="Qwen2.5-3B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=6.0,
                    memory_requirement_gb=10.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=True,
                    gpu_memory_min_gb=10.0
                )
            ],

            # Qwen2.5-7B 中文模型（中高级）- 仅FP16
            "qwen2.5-7b": [
                ModelVariant(
                    name="Qwen2.5-7B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=14.0,
                    memory_requirement_gb=18.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=18.0
                )
            ],

            # Qwen2.5-14B 中文模型（高级）- 仅FP16
            "qwen2.5-14b": [
                ModelVariant(
                    name="Qwen2.5-14B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=28.0,
                    memory_requirement_gb=32.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=32.0
                )
            ],

            # Qwen2.5-32B 中文模型（旗舰级）- 仅FP16
            "qwen2.5-32b": [
                ModelVariant(
                    name="Qwen2.5-32B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=64.0,
                    memory_requirement_gb=80.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=80.0
                )
            ],

            # Mistral-7B 英文模型（入门级/基础级）- 仅FP16
            "mistral-7b": [
                ModelVariant(
                    name="Mistral-7B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=14.0,
                    memory_requirement_gb=18.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=True,
                    gpu_memory_min_gb=18.0
                )
            ],

            # Mistral-12B-Nemo 英文模型（进阶级）- 仅FP16
            "mistral-12b-nemo": [
                ModelVariant(
                    name="Mistral-Nemo-12B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=24.0,
                    memory_requirement_gb=28.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=28.0
                )
            ],

            # Mistral-24B-Small 英文模型（中高级）- 仅FP16
            "mistral-24b-small": [
                ModelVariant(
                    name="Mistral-Small-24B-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=48.0,
                    memory_requirement_gb=56.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=56.0
                )
            ],

            # Mistral-Large-2 英文模型（旗舰级）- 仅FP16
            "mistral-large2": [
                ModelVariant(
                    name="Mistral-Large-2-Instruct-FP16",
                    quantization=QuantizationType.FP16,
                    size_gb=246.0,  # FP16原始模型大小（约123B参数 × 2字节）
                    memory_requirement_gb=280.0,
                    inference_speed_factor=1.0,
                    quality_retention=1.0,
                    cpu_compatible=False,
                    gpu_memory_min_gb=280.0
                )
            ]
        }
    
    def _initialize_benchmarks(self) -> Dict[str, Dict]:
        """初始化性能基准测试数据（仅GPTQ格式）"""
        return {
            "subtitle_reconstruction": {
                "fp16": {"accuracy": 0.95, "speed_tokens_per_sec": 120},
                "int8": {"accuracy": 0.94, "speed_tokens_per_sec": 102},
                "int8_perchannel": {"accuracy": 0.94, "speed_tokens_per_sec": 100},
                "int4": {"accuracy": 0.89, "speed_tokens_per_sec": 78},
                "int4_perchannel": {"accuracy": 0.90, "speed_tokens_per_sec": 80}
            },
            "plot_analysis": {
                "fp16": {"accuracy": 0.92, "speed_tokens_per_sec": 100},
                "int8": {"accuracy": 0.91, "speed_tokens_per_sec": 85},
                "int8_perchannel": {"accuracy": 0.91, "speed_tokens_per_sec": 83},
                "int4": {"accuracy": 0.86, "speed_tokens_per_sec": 65},
                "int4_perchannel": {"accuracy": 0.87, "speed_tokens_per_sec": 67}
            },
            "emotion_analysis": {
                "fp16": {"accuracy": 0.88, "speed_tokens_per_sec": 110},
                "int8": {"accuracy": 0.87, "speed_tokens_per_sec": 94},
                "int8_perchannel": {"accuracy": 0.87, "speed_tokens_per_sec": 92},
                "int4": {"accuracy": 0.82, "speed_tokens_per_sec": 72},
                "int4_perchannel": {"accuracy": 0.83, "speed_tokens_per_sec": 74}
            }
        }
    
    def analyze_quantization_impact(self, task: str, quantization: QuantizationType) -> Dict:
        """分析量化对特定任务的影响"""
        if task not in self.performance_benchmarks:
            raise ValueError(f"未知任务类型: {task}")
        
        benchmark = self.performance_benchmarks[task]
        quant_key = quantization.value
        
        if quant_key not in benchmark:
            # 使用最接近的量化类型
            quant_key = "int4"  # 默认使用INT4 GPTQ
        
        fp16_data = benchmark["fp16"]
        quant_data = benchmark[quant_key]
        
        return {
            "task": task,
            "quantization": quantization.value,
            "accuracy_loss": fp16_data["accuracy"] - quant_data["accuracy"],
            "accuracy_retention": quant_data["accuracy"] / fp16_data["accuracy"],
            "speed_ratio": quant_data["speed_tokens_per_sec"] / fp16_data["speed_tokens_per_sec"],
            "performance_score": self._calculate_performance_score(quant_data, fp16_data)
        }
    
    def _calculate_performance_score(self, quant_data: Dict, fp16_data: Dict) -> float:
        """计算综合性能评分"""
        accuracy_weight = 0.7
        speed_weight = 0.3
        
        accuracy_ratio = quant_data["accuracy"] / fp16_data["accuracy"]
        speed_ratio = quant_data["speed_tokens_per_sec"] / fp16_data["speed_tokens_per_sec"]
        
        return accuracy_weight * accuracy_ratio + speed_weight * speed_ratio
    
    def get_quantization_explanation(self, from_type: QuantizationType, to_type: QuantizationType) -> str:
        """获取量化转换过程的技术解释（仅GPTQ格式）"""
        explanations = {
            (QuantizationType.FP16, QuantizationType.INT8):
                "FP16→INT8 GPTQ量化：将16位浮点数转换为8位整数，通过校准数据集确定量化参数，"
                "保持较高精度的同时减少50%内存占用。支持LoRA/QLoRA微调。",

            (QuantizationType.FP16, QuantizationType.INT8_PERCHANNEL):
                "FP16→INT8-PerChannel GPTQ量化：per-channel量化策略，每个通道独立量化，"
                "提供更高精度，减少50%存储空间。支持LoRA/QLoRA微调。",

            (QuantizationType.FP16, QuantizationType.INT4):
                "FP16→INT4 GPTQ量化：激进量化策略，大部分权重使用4位表示，"
                "通过group-wise量化优化，减少75%存储空间。支持LoRA/QLoRA微调。",

            (QuantizationType.FP16, QuantizationType.INT4_PERCHANNEL):
                "FP16→INT4-PerChannel GPTQ量化：4位per-channel量化，平衡精度和压缩比，"
                "减少75%存储空间同时保持较高质量。支持LoRA/QLoRA微调。",

            (QuantizationType.INT8, QuantizationType.INT4):
                "INT8→INT4 GPTQ量化：进一步压缩，使用4位量化，"
                "在保持可接受质量的前提下最大化压缩比。支持LoRA/QLoRA微调。"
        }

        return explanations.get((from_type, to_type),
                              f"从{from_type.value}量化到{to_type.value}的GPTQ转换过程")

class HardwareDetector:
    """硬件检测器"""
    
    @staticmethod
    def detect_hardware() -> HardwareProfile:
        """检测当前硬件配置"""
        # 检测系统RAM
        memory = psutil.virtual_memory()
        system_ram_gb = memory.total / (1024**3)
        
        # 检测存储空间
        disk = psutil.disk_usage('.')
        storage_available_gb = disk.free / (1024**3)
        
        # 检测CPU核心数
        cpu_cores = psutil.cpu_count(logical=False)
        
        # 检测GPU (简化版本，实际应使用nvidia-ml-py等)
        gpu_memory_gb = 0.0
        has_gpu = False
        gpu_compute_capability = None
        
        try:
            import torch
            # 安全检查torch.cuda是否可用
            if hasattr(torch, 'cuda') and hasattr(torch.cuda, 'is_available'):
                if callable(torch.cuda.is_available) and torch.cuda.is_available():
                    # 🔧 修复：添加额外的设备可用性检查
                    try:
                        # 尝试获取设备数量，确保至少有一个可用设备
                        if hasattr(torch.cuda, 'device_count') and torch.cuda.device_count() > 0:
                            has_gpu = True
                            if hasattr(torch.cuda, 'get_device_properties'):
                                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                            # 简化的计算能力检测
                            if hasattr(torch.cuda, 'get_device_capability'):
                                major, minor = torch.cuda.get_device_capability(0)
                                gpu_compute_capability = f"{major}.{minor}"
                    except (AssertionError, RuntimeError) as e:
                        # CUDA可用但设备不可访问，回退到CPU模式
                        logger.warning(f"CUDA报告可用但设备不可访问: {e}")
                        has_gpu = False
        except ImportError:
            pass
        
        return HardwareProfile(
            gpu_memory_gb=gpu_memory_gb,
            system_ram_gb=system_ram_gb,
            storage_available_gb=storage_available_gb,
            cpu_cores=cpu_cores,
            has_gpu=has_gpu,
            gpu_compute_capability=gpu_compute_capability
        )
    
    @staticmethod
    def assess_compatibility(hardware: HardwareProfile, variant: ModelVariant) -> Dict:
        """评估硬件与模型变体的兼容性"""
        compatibility_score = 0.0
        issues = []
        recommendations = []
        
        # 检查存储空间
        if hardware.storage_available_gb < variant.size_gb:
            issues.append(f"存储空间不足：需要{variant.size_gb:.1f}GB，可用{hardware.storage_available_gb:.1f}GB")
        else:
            compatibility_score += 0.3
        
        # 检查GPU内存
        if hardware.has_gpu:
            if hardware.gpu_memory_gb >= variant.gpu_memory_min_gb:
                compatibility_score += 0.5
                recommendations.append("GPU内存充足，推荐GPU推理")
            else:
                issues.append(f"GPU内存不足：需要{variant.gpu_memory_min_gb:.1f}GB，可用{hardware.gpu_memory_gb:.1f}GB")
                if variant.cpu_compatible:
                    recommendations.append("建议使用CPU推理")
        else:
            if variant.cpu_compatible:
                compatibility_score += 0.3
                recommendations.append("无GPU，将使用CPU推理")
            else:
                issues.append("需要GPU支持，但未检测到GPU")
        
        # 检查系统RAM
        if hardware.system_ram_gb >= variant.memory_requirement_gb:
            compatibility_score += 0.2
        else:
            issues.append(f"系统内存不足：需要{variant.memory_requirement_gb:.1f}GB，可用{hardware.system_ram_gb:.1f}GB")
        
        return {
            "compatibility_score": compatibility_score,
            "is_compatible": compatibility_score >= 0.7,
            "issues": issues,
            "recommendations": recommendations,
            "performance_expectation": HardwareDetector._estimate_performance(hardware, variant)
        }
    
    @staticmethod
    def _estimate_performance(hardware: HardwareProfile, variant: ModelVariant) -> Dict:
        """估算性能表现"""
        if hardware.has_gpu and hardware.gpu_memory_gb >= variant.gpu_memory_min_gb:
            # GPU推理
            base_speed = 100 * variant.inference_speed_factor
            memory_factor = min(hardware.gpu_memory_gb / variant.gpu_memory_min_gb, 2.0)
            estimated_speed = base_speed * memory_factor
            mode = "GPU"
        else:
            # CPU推理
            base_speed = 20 * variant.inference_speed_factor
            cpu_factor = min(hardware.cpu_cores / 4.0, 2.0)
            estimated_speed = base_speed * cpu_factor
            mode = "CPU"
        
        return {
            "inference_mode": mode,
            "estimated_tokens_per_second": estimated_speed,
            "quality_retention": variant.quality_retention,
            "memory_usage_gb": variant.memory_requirement_gb
        }

def analyze_visionai_quantization_impact():
    """分析量化对VisionAI-ClipsMaster核心功能的影响（仅GPTQ格式）"""
    analyzer = QuantizationAnalyzer()

    # 分析各个核心任务
    tasks = ["subtitle_reconstruction", "plot_analysis", "emotion_analysis"]
    quantizations = [QuantizationType.INT8, QuantizationType.INT8_PERCHANNEL,
                    QuantizationType.INT4, QuantizationType.INT4_PERCHANNEL]
    
    results = {}
    for task in tasks:
        results[task] = {}
        for quant in quantizations:
            results[task][quant.value] = analyzer.analyze_quantization_impact(task, quant)
    
    return results

if __name__ == "__main__":
    # 示例使用
    detector = HardwareDetector()
    hardware = detector.detect_hardware()
    
    print(f"检测到的硬件配置:")
    print(f"  GPU内存: {hardware.gpu_memory_gb:.1f}GB")
    print(f"  系统RAM: {hardware.system_ram_gb:.1f}GB")
    print(f"  存储空间: {hardware.storage_available_gb:.1f}GB")
    print(f"  CPU核心: {hardware.cpu_cores}")
    print(f"  有GPU: {hardware.has_gpu}")
    
    # 分析量化影响
    impact_results = analyze_visionai_quantization_impact()
    print("\n量化影响分析:")
    for task, quant_results in impact_results.items():
        print(f"\n{task}:")
        for quant_type, result in quant_results.items():
            print(f"  {quant_type}: 准确率保持{result['accuracy_retention']:.1%}, "
                  f"速度比{result['speed_ratio']:.1%}, "
                  f"综合评分{result['performance_score']:.3f}")
