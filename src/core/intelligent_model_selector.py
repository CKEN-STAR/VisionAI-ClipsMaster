#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 智能模型版本选择器
基于硬件配置自动推荐最适合的模型版本
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .quantization_analysis import (
    QuantizationAnalyzer, HardwareDetector, ModelVariant, 
    HardwareProfile, QuantizationType
)

logger = logging.getLogger(__name__)

class SelectionStrategy(Enum):
    """选择策略枚举"""
    AUTO_RECOMMEND = "auto_recommend"    # 自动推荐
    MANUAL_SELECT = "manual_select"      # 手动选择
    HYBRID_MODE = "hybrid_mode"          # 混合模式

class DeploymentTarget(Enum):
    """部署目标枚举"""
    HIGH_PERFORMANCE = "high_performance"    # 高性能
    BALANCED = "balanced"                    # 平衡
    LIGHTWEIGHT = "lightweight"             # 轻量化
    ULTRA_LIGHT = "ultra_light"             # 超轻量

@dataclass
class ModelRecommendation:
    """模型推荐结果"""
    model_name: str
    variant: ModelVariant
    confidence_score: float
    reasoning: List[str]
    compatibility_assessment: Dict
    alternative_options: List[Dict]
    deployment_notes: List[str]

class IntelligentModelSelector:
    """智能模型选择器"""

    def __init__(self):
        self.analyzer = QuantizationAnalyzer()
        self.detector = HardwareDetector()
        self.selection_rules = self._initialize_selection_rules()
        self._last_recommendation = None  # 缓存上次推荐结果
        self._last_model_name = None      # 缓存上次请求的模型名称
        self._hardware_cache = None       # 缓存硬件检测结果
        self._cache_timestamp = None      # 缓存时间戳

    def clear_cache(self):
        """清除所有缓存状态，确保状态隔离"""
        logger.info("🔧 清除智能选择器缓存状态")
        self._last_recommendation = None
        self._last_model_name = None
        self._hardware_cache = None
        self._cache_timestamp = None

        # 强化清除：删除所有可能的状态污染源
        if hasattr(self, '_cached_variants'):
            delattr(self, '_cached_variants')
        if hasattr(self, '_last_strategy'):
            delattr(self, '_last_strategy')
        if hasattr(self, '_recommendation_cache'):
            delattr(self, '_recommendation_cache')

        logger.info("✅ 智能选择器状态已清除")
    
    def _initialize_selection_rules(self) -> Dict:
        """初始化选择规则"""
        return {
            "memory_thresholds": {
                "ultra_light": 4.0,      # 4GB以下
                "lightweight": 8.0,      # 4-8GB
                "balanced": 16.0,        # 8-16GB
                "high_performance": 32.0  # 16GB+
            },
            "storage_thresholds": {
                "ultra_light": 10.0,     # 10GB以下
                "lightweight": 20.0,     # 10-20GB
                "balanced": 50.0,        # 20-50GB
                "high_performance": 100.0 # 50GB+
            },
            "quality_requirements": {
                "research": 0.95,        # 研究用途
                "production": 0.90,      # 生产环境
                "development": 0.85,     # 开发测试
                "demo": 0.80            # 演示用途
            }
        }
    
    def recommend_model_version(
        self,
        model_name: str,
        strategy: SelectionStrategy = SelectionStrategy.AUTO_RECOMMEND,
        deployment_target: Optional[DeploymentTarget] = None,
        quality_requirement: str = "production",
        hardware_override: Optional[HardwareProfile] = None
    ) -> ModelRecommendation:
        """推荐模型版本"""

        logger.info(f"🤖 开始推荐模型版本: {model_name}")

        # 重要修复：检查模型名称变化，如果变化则清除缓存
        if self._last_model_name and self._last_model_name != model_name:
            logger.info(f"🔄 检测到模型名称变化: {self._last_model_name} -> {model_name}，清除缓存")
            self.clear_cache()

        # 记录当前模型名称
        self._last_model_name = model_name

        # 额外验证：确保请求的模型名称有效
        if model_name not in ["mistral-7b", "qwen2.5-7b"]:
            logger.warning(f"⚠️ 检测到非标准模型名称: {model_name}")
            # 标准化模型名称
            if "mistral" in model_name.lower():
                model_name = "mistral-7b"
                logger.info(f"🔄 标准化为英文模型: {model_name}")
            elif "qwen" in model_name.lower():
                model_name = "qwen2.5-7b"
                logger.info(f"🔄 标准化为中文模型: {model_name}")
            else:
                logger.error(f"❌ 无法识别的模型名称: {model_name}")
                raise ValueError(f"不支持的模型: {model_name}")

        # 更新标准化后的模型名称
        self._last_model_name = model_name

        # 检测硬件配置（使用缓存机制优化性能）
        hardware = hardware_override or self._get_hardware_with_cache()

        # 验证模型名称有效性
        if model_name not in self.analyzer.model_variants:
            logger.error(f"❌ 不支持的模型: {model_name}")
            raise ValueError(f"不支持的模型: {model_name}")

        variants = self.analyzer.model_variants[model_name]
        logger.info(f"📋 找到 {len(variants)} 个模型变体: {[v.name for v in variants]}")

        # 根据策略选择
        recommendation = None
        if strategy == SelectionStrategy.AUTO_RECOMMEND:
            recommendation = self._auto_recommend(model_name, variants, hardware, deployment_target, quality_requirement)
        elif strategy == SelectionStrategy.MANUAL_SELECT:
            recommendation = self._manual_select_options(model_name, variants, hardware)
        else:  # HYBRID_MODE
            recommendation = self._hybrid_recommend(model_name, variants, hardware, deployment_target, quality_requirement)

        # 验证推荐结果的一致性
        if recommendation and recommendation.model_name != model_name:
            logger.error(f"❌ 推荐结果模型名称不一致: 请求={model_name}, 推荐={recommendation.model_name}")
            # 强制重新生成正确的推荐
            self.clear_cache()
            recommendation = self._auto_recommend(model_name, variants, hardware, deployment_target, quality_requirement)

        # 最终验证：确保推荐内容与模型名称严格匹配
        if recommendation:
            variant_name = recommendation.variant.name.lower()
            if model_name == "mistral-7b" and "mistral" not in variant_name:
                logger.error(f"❌ 英文模型推荐错误: 请求=mistral-7b, 推荐变体={recommendation.variant.name}")
                raise ValueError(f"推荐结果与请求模型不匹配: {model_name} vs {recommendation.variant.name}")
            elif model_name == "qwen2.5-7b" and "qwen" not in variant_name:
                logger.error(f"❌ 中文模型推荐错误: 请求=qwen2.5-7b, 推荐变体={recommendation.variant.name}")
                raise ValueError(f"推荐结果与请求模型不匹配: {model_name} vs {recommendation.variant.name}")

            logger.info(f"✅ 推荐结果验证通过: {model_name} -> {recommendation.variant.name}")

        # 缓存推荐结果
        self._last_recommendation = recommendation

        logger.info(f"✅ 推荐完成: {recommendation.variant.name if recommendation else 'None'}")
        return recommendation

    def _get_hardware_with_cache(self) -> HardwareProfile:
        """获取硬件配置（带缓存机制）"""
        import time
        current_time = time.time()

        # 如果缓存存在且未过期（5分钟内），使用缓存
        if (self._hardware_cache and self._cache_timestamp and
            current_time - self._cache_timestamp < 300):  # 5分钟缓存
            logger.debug("🔄 使用缓存的硬件配置")
            return self._hardware_cache

        # 重新检测硬件配置
        logger.info("🔍 重新检测硬件配置")
        hardware = self.detector.detect_hardware()

        # 更新缓存
        self._hardware_cache = hardware
        self._cache_timestamp = current_time

        logger.info(f"💾 硬件配置已缓存: GPU={hardware.gpu_memory_gb}GB, RAM={hardware.system_ram_gb}GB")
        return hardware
    
    def _auto_recommend(
        self, 
        model_name: str, 
        variants: List[ModelVariant], 
        hardware: HardwareProfile,
        deployment_target: Optional[DeploymentTarget],
        quality_requirement: str
    ) -> ModelRecommendation:
        """自动推荐最佳版本"""
        
        # 确定部署目标
        if deployment_target is None:
            deployment_target = self._infer_deployment_target(hardware)
        
        # 评估所有变体
        scored_variants = []
        for variant in variants:
            score = self._calculate_variant_score(variant, hardware, deployment_target, quality_requirement)
            compatibility = self.detector.assess_compatibility(hardware, variant)
            
            scored_variants.append({
                "variant": variant,
                "score": score,
                "compatibility": compatibility
            })
        
        # 按评分排序
        scored_variants.sort(key=lambda x: x["score"], reverse=True)
        best_variant = scored_variants[0]
        
        # 生成推荐理由
        reasoning = self._generate_reasoning(
            best_variant["variant"], 
            hardware, 
            deployment_target, 
            quality_requirement,
            best_variant["compatibility"]
        )
        
        # 生成替代选项
        alternatives = [
            {
                "variant": sv["variant"],
                "score": sv["score"],
                "reason": self._get_alternative_reason(sv["variant"], best_variant["variant"])
            }
            for sv in scored_variants[1:3]  # 取前2个替代选项
        ]
        
        # 生成部署说明
        deployment_notes = self._generate_deployment_notes(best_variant["variant"], hardware)
        
        return ModelRecommendation(
            model_name=model_name,
            variant=best_variant["variant"],
            confidence_score=best_variant["score"],
            reasoning=reasoning,
            compatibility_assessment=best_variant["compatibility"],
            alternative_options=alternatives,
            deployment_notes=deployment_notes
        )
    
    def _calculate_variant_score(
        self, 
        variant: ModelVariant, 
        hardware: HardwareProfile,
        deployment_target: DeploymentTarget,
        quality_requirement: str
    ) -> float:
        """计算变体评分"""
        score = 0.0
        
        # 兼容性评分 (40%)
        compatibility = self.detector.assess_compatibility(hardware, variant)
        score += compatibility["compatibility_score"] * 0.4
        
        # 质量要求评分 (30%)
        required_quality = self.selection_rules["quality_requirements"].get(quality_requirement, 0.90)
        if variant.quality_retention >= required_quality:
            quality_score = variant.quality_retention
        else:
            quality_score = variant.quality_retention * 0.5  # 惩罚不满足要求的版本
        score += quality_score * 0.3
        
        # 部署目标适配评分 (20%)
        target_score = self._calculate_target_alignment_score(variant, hardware, deployment_target)
        score += target_score * 0.2
        
        # 性能效率评分 (10%)
        efficiency_score = variant.inference_speed_factor * variant.quality_retention
        score += efficiency_score * 0.1
        
        return score
    
    def _calculate_target_alignment_score(
        self, 
        variant: ModelVariant, 
        hardware: HardwareProfile,
        deployment_target: DeploymentTarget
    ) -> float:
        """计算与部署目标的对齐评分"""
        if deployment_target == DeploymentTarget.HIGH_PERFORMANCE:
            # 高性能：优先考虑质量和速度
            return variant.quality_retention * 0.6 + variant.inference_speed_factor * 0.4
        
        elif deployment_target == DeploymentTarget.BALANCED:
            # 平衡：质量、速度、大小均衡
            size_score = max(0, 1 - variant.size_gb / 20.0)  # 20GB为基准
            return (variant.quality_retention * 0.4 + 
                   variant.inference_speed_factor * 0.3 + 
                   size_score * 0.3)
        
        elif deployment_target == DeploymentTarget.LIGHTWEIGHT:
            # 轻量化：优先考虑大小和内存
            size_score = max(0, 1 - variant.size_gb / 15.0)
            memory_score = max(0, 1 - variant.memory_requirement_gb / 10.0)
            return size_score * 0.5 + memory_score * 0.3 + variant.quality_retention * 0.2
        
        else:  # ULTRA_LIGHT
            # 超轻量：最小化资源占用
            size_score = max(0, 1 - variant.size_gb / 10.0)
            memory_score = max(0, 1 - variant.memory_requirement_gb / 8.0)
            cpu_compat_score = 1.0 if variant.cpu_compatible else 0.0
            return size_score * 0.4 + memory_score * 0.4 + cpu_compat_score * 0.2
    
    def _infer_deployment_target(self, hardware: HardwareProfile) -> DeploymentTarget:
        """根据硬件推断部署目标"""
        memory_thresholds = self.selection_rules["memory_thresholds"]
        
        total_memory = hardware.gpu_memory_gb if hardware.has_gpu else hardware.system_ram_gb
        
        if total_memory >= memory_thresholds["high_performance"]:
            return DeploymentTarget.HIGH_PERFORMANCE
        elif total_memory >= memory_thresholds["balanced"]:
            return DeploymentTarget.BALANCED
        elif total_memory >= memory_thresholds["lightweight"]:
            return DeploymentTarget.LIGHTWEIGHT
        else:
            return DeploymentTarget.ULTRA_LIGHT
    
    def _generate_reasoning(
        self, 
        variant: ModelVariant, 
        hardware: HardwareProfile,
        deployment_target: DeploymentTarget,
        quality_requirement: str,
        compatibility: Dict
    ) -> List[str]:
        """生成推荐理由"""
        reasons = []
        
        # 硬件适配理由
        if compatibility["is_compatible"]:
            reasons.append(f"✅ 与当前硬件完全兼容 (兼容性评分: {compatibility['compatibility_score']:.1%})")
        else:
            reasons.append(f"⚠️ 硬件兼容性有限，但可运行 (评分: {compatibility['compatibility_score']:.1%})")
        
        # 部署目标理由
        target_reasons = {
            DeploymentTarget.HIGH_PERFORMANCE: "追求最佳性能和质量",
            DeploymentTarget.BALANCED: "在性能、质量和资源占用间取得平衡",
            DeploymentTarget.LIGHTWEIGHT: "优化资源占用，适合轻量化部署",
            DeploymentTarget.ULTRA_LIGHT: "最小化资源需求，适合低配置设备"
        }
        reasons.append(f"🎯 {target_reasons[deployment_target]}")
        
        # 质量保证理由
        required_quality = self.selection_rules["quality_requirements"].get(quality_requirement, 0.90)
        if variant.quality_retention >= required_quality:
            reasons.append(f"✅ 满足{quality_requirement}质量要求 (保持{variant.quality_retention:.1%}质量)")
        else:
            reasons.append(f"⚠️ 质量略低于{quality_requirement}要求，但仍可接受")
        
        # 资源优化理由
        if variant.size_gb < 10:
            reasons.append(f"💾 存储占用较小 ({variant.size_gb:.1f}GB)")
        if variant.cpu_compatible:
            reasons.append("🖥️ 支持CPU推理，无需GPU")
        
        return reasons
    
    def _get_alternative_reason(self, alternative: ModelVariant, recommended: ModelVariant) -> str:
        """获取替代选项的理由"""
        if alternative.quality_retention > recommended.quality_retention:
            return f"更高质量 ({alternative.quality_retention:.1%} vs {recommended.quality_retention:.1%})"
        elif alternative.size_gb < recommended.size_gb:
            return f"更小体积 ({alternative.size_gb:.1f}GB vs {recommended.size_gb:.1f}GB)"
        elif alternative.inference_speed_factor > recommended.inference_speed_factor:
            return f"更快推理 ({alternative.inference_speed_factor:.1%} vs {recommended.inference_speed_factor:.1%})"
        else:
            return "不同的性能权衡"
    
    def _generate_deployment_notes(self, variant: ModelVariant, hardware: HardwareProfile) -> List[str]:
        """生成部署说明"""
        notes = []
        
        # 推理模式说明
        if hardware.has_gpu and hardware.gpu_memory_gb >= variant.gpu_memory_min_gb:
            notes.append("🚀 推荐使用GPU推理以获得最佳性能")
        elif variant.cpu_compatible:
            notes.append("🖥️ 将使用CPU推理，速度较慢但兼容性好")
        else:
            notes.append("⚠️ 需要GPU支持，请确保有足够的GPU内存")
        
        # 内存使用说明
        notes.append(f"💾 预计内存使用: {variant.memory_requirement_gb:.1f}GB")
        
        # 性能预期说明
        performance = hardware.gpu_memory_gb if hardware.has_gpu else hardware.system_ram_gb
        if performance >= variant.memory_requirement_gb * 1.5:
            notes.append("⚡ 预期性能: 优秀")
        elif performance >= variant.memory_requirement_gb:
            notes.append("⚡ 预期性能: 良好")
        else:
            notes.append("⚡ 预期性能: 一般，可能较慢")
        
        # VisionAI特定说明
        notes.append("📝 字幕重构准确率: " + self._get_accuracy_description(variant.quality_retention))
        notes.append("🎭 剧本分析质量: " + self._get_quality_description(variant.quality_retention))
        
        return notes
    
    def _get_accuracy_description(self, quality_retention: float) -> str:
        """获取准确率描述"""
        if quality_retention >= 0.95:
            return "优秀 (>95%)"
        elif quality_retention >= 0.90:
            return "良好 (90-95%)"
        elif quality_retention >= 0.85:
            return "可接受 (85-90%)"
        else:
            return "一般 (<85%)"
    
    def _get_quality_description(self, quality_retention: float) -> str:
        """获取质量描述"""
        if quality_retention >= 0.95:
            return "接近原始质量"
        elif quality_retention >= 0.90:
            return "高质量输出"
        elif quality_retention >= 0.85:
            return "中等质量输出"
        else:
            return "基础质量输出"
    
    def _manual_select_options(self, model_name: str, variants: List[ModelVariant], hardware: HardwareProfile) -> ModelRecommendation:
        """提供手动选择选项"""
        # 为手动选择模式，返回所有选项的详细信息
        options = []
        for variant in variants:
            compatibility = self.detector.assess_compatibility(hardware, variant)
            options.append({
                "variant": variant,
                "compatibility": compatibility,
                "description": self._get_variant_description(variant)
            })
        
        # 返回第一个作为默认选择，但提供所有选项
        return ModelRecommendation(
            model_name=model_name,
            variant=variants[0],
            confidence_score=0.0,  # 手动选择不提供置信度
            reasoning=["用户手动选择模式"],
            compatibility_assessment={},
            alternative_options=options,
            deployment_notes=["请根据需求手动选择合适的版本"]
        )
    
    def _get_variant_description(self, variant: ModelVariant) -> str:
        """获取变体描述"""
        return (f"{variant.name} - {variant.size_gb:.1f}GB, "
                f"质量保持{variant.quality_retention:.1%}, "
                f"速度{variant.inference_speed_factor:.1%}, "
                f"{'支持CPU' if variant.cpu_compatible else '需要GPU'}")
    
    def _hybrid_recommend(self, model_name: str, variants: List[ModelVariant], hardware: HardwareProfile, deployment_target: Optional[DeploymentTarget], quality_requirement: str) -> ModelRecommendation:
        """混合模式推荐"""
        # 先自动推荐
        auto_recommendation = self._auto_recommend(model_name, variants, hardware, deployment_target, quality_requirement)
        
        # 然后提供手动选择选项
        manual_options = self._manual_select_options(model_name, variants, hardware)
        
        # 合并结果
        auto_recommendation.alternative_options.extend(manual_options.alternative_options)
        auto_recommendation.reasoning.append("💡 提供自动推荐和手动选择选项")
        
        return auto_recommendation

def create_multi_tier_download_config() -> Dict:
    """创建多层级下载配置"""
    return {
        "qwen2.5-7b": {
            "fp16": {
                "name": "Qwen2.5-7B-Instruct-FP16",
                "size_gb": 14.4,
                "urls": ["https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct"],
                "target_dir": "models/models/qwen/fp16"
            },
            "q8": {
                "name": "Qwen2.5-7B-Instruct-Q8",
                "size_gb": 7.6,
                "urls": ["https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF"],
                "target_dir": "models/models/qwen/q8",
                "filename": "qwen2.5-7b-instruct-q8_0.gguf"
            },
            "q5": {
                "name": "Qwen2.5-7B-Instruct-Q5",
                "size_gb": 5.1,
                "urls": ["https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF"],
                "target_dir": "models/models/qwen/q5",
                "filename": "qwen2.5-7b-instruct-q5_k_m.gguf"
            },
            "q4": {
                "name": "Qwen2.5-7B-Instruct-Q4",
                "size_gb": 4.1,
                "urls": ["https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF"],
                "target_dir": "models/models/qwen/q4",
                "filename": "qwen2.5-7b-instruct-q4_k_m.gguf"
            }
        },
        "mistral-7b": {
            "fp16": {
                "name": "Mistral-7B-Instruct-FP16",
                "size_gb": 13.5,
                "urls": ["https://hf-mirror.com/mistralai/Mistral-7B-Instruct-v0.1"],
                "target_dir": "models/mistral/fp16"
            },
            "q8": {
                "name": "Mistral-7B-Instruct-Q8",
                "size_gb": 7.2,
                "urls": ["https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"],
                "target_dir": "models/mistral/q8",
                "filename": "mistral-7b-instruct-v0.1.q8_0.gguf"
            },
            "q5": {
                "name": "Mistral-7B-Instruct-Q5",
                "size_gb": 4.8,
                "urls": ["https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"],
                "target_dir": "models/mistral/q5",
                "filename": "mistral-7b-instruct-v0.1.q5_k_m.gguf"
            },
            "q4": {
                "name": "Mistral-7B-Instruct-Q4",
                "size_gb": 4.1,
                "urls": ["https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"],
                "target_dir": "models/mistral/q4",
                "filename": "mistral-7b-instruct-v0.1.q4_k_m.gguf"
            }
        }
    }
