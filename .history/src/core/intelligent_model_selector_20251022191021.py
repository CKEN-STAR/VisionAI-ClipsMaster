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

        # 质量阈值配置
        self.quality_thresholds = {
            "high": 0.95,
            "medium": 0.85,
            "low": 0.75,
            "minimal": 0.65
        }

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

        # 新增：清除跨标签页状态污染源
        if hasattr(self, '_last_tab_context'):
            delattr(self, '_last_tab_context')
        if hasattr(self, '_dialog_context'):
            delattr(self, '_dialog_context')
        if hasattr(self, '_request_context'):
            delattr(self, '_request_context')

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
        hardware_override: Optional[HardwareProfile] = None,
        tab_context: str = None  # 新增：标签页上下文标识
    ) -> ModelRecommendation:
        """推荐模型版本"""

        logger.info(f"🤖 开始推荐模型版本: {model_name}, 标签页上下文: {tab_context}")

        # 重要修复：检查模型名称变化，如果变化则清除缓存
        if self._last_model_name and self._last_model_name != model_name:
            logger.info(f"🔄 检测到模型名称变化: {self._last_model_name} -> {model_name}，清除缓存")
            self.clear_cache()

        # 新增：检查标签页上下文变化
        current_tab_context = tab_context or "unknown"
        if hasattr(self, '_last_tab_context') and self._last_tab_context != current_tab_context:
            logger.info(f"🔄 检测到标签页上下文变化: {self._last_tab_context} -> {current_tab_context}，清除缓存")
            self.clear_cache()

        # 记录当前模型名称和标签页上下文
        self._last_model_name = model_name
        self._last_tab_context = current_tab_context

        # 额外验证：确保请求的模型名称有效（包含新增模型）
        valid_models = [
            "qwen2.5-0.5b", "qwen2.5-1.5b", "qwen2.5-3b", "qwen2.5-7b", "qwen2.5-14b", "qwen2.5-32b",  # Qwen2.5系列
            "mistral-7b", "mistral-12b-nemo", "mistral-24b-small", "mistral-large2"
        ]

        if model_name not in valid_models:
            logger.warning(f"⚠️ 检测到非标准模型名称: {model_name}")
            # 标准化模型名称
            if "mistral" in model_name.lower():
                # 根据硬件配置推荐合适的Mistral模型
                hardware = hardware_override or self._get_hardware_with_cache()
                model_name = self._select_mistral_variant(hardware)
                logger.info(f"🔄 标准化为英文模型: {model_name}")
            elif "qwen" in model_name.lower():
                # 根据硬件配置推荐合适的Qwen模型
                hardware = hardware_override or self._get_hardware_with_cache()
                model_name = self._select_qwen_variant(hardware)
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

        # 计算硬件评分，用于智能推荐
        hardware_score = self.calculate_hardware_score(hardware)
        logger.info(f"💯 硬件综合评分: {hardware_score:.1f}/100")

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

            # 检查Mistral系列模型
            if "mistral" in model_name and "mistral" not in variant_name:
                logger.error(f"❌ 英文模型推荐错误: 请求={model_name}, 推荐变体={recommendation.variant.name}")
                raise ValueError(f"推荐结果与请求模型不匹配: {model_name} vs {recommendation.variant.name}")

            # 检查Qwen系列模型
            elif "qwen" in model_name and "qwen" not in variant_name:
                logger.error(f"❌ 中文模型推荐错误: 请求={model_name}, 推荐变体={recommendation.variant.name}")
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

        # 检查是否需要强制刷新硬件配置
        force_refresh = self._should_force_refresh_hardware()

        # 如果缓存存在且未过期（5分钟内）且不需要强制刷新，使用缓存
        if (not force_refresh and self._hardware_cache and self._cache_timestamp and
            current_time - self._cache_timestamp < 300):  # 5分钟缓存
            logger.debug("🔄 使用缓存的硬件配置")
            return self._hardware_cache

        # 重新检测硬件配置
        if force_refresh:
            logger.info("🔄 强制刷新硬件配置（检测到设备变化）")
        else:
            logger.info("🔍 重新检测硬件配置")

        hardware = self.detector.detect_hardware()

        # 检测硬件配置是否发生重大变化
        if self._hardware_cache:
            self._log_hardware_changes(self._hardware_cache, hardware)

        # 更新缓存
        self._hardware_cache = hardware
        self._cache_timestamp = current_time

        logger.info(f"💾 硬件配置已缓存: GPU={hardware.gpu_memory_gb}GB, RAM={hardware.system_ram_gb}GB")
        return hardware

    def _should_force_refresh_hardware(self) -> bool:
        """检查是否需要强制刷新硬件配置"""
        try:
            # 检查GPU状态变化的快速指标
            import torch

            # 如果之前没有缓存，需要检测
            if not self._hardware_cache:
                return True

            # 检查CUDA可用性是否发生变化
            cuda_available_now = torch.cuda.is_available() if hasattr(torch, 'cuda') else False
            cuda_was_available = self._hardware_cache.gpu_memory_gb > 0

            if cuda_available_now != cuda_was_available:
                logger.info(f"🔄 检测到CUDA状态变化: {cuda_was_available} -> {cuda_available_now}")
                return True

            # 检查GPU数量是否发生变化
            if cuda_available_now:
                current_gpu_count = torch.cuda.device_count()
                cached_gpu_count = getattr(self._hardware_cache, 'gpu_count', 0)
                if current_gpu_count != cached_gpu_count:
                    logger.info(f"🔄 检测到GPU数量变化: {cached_gpu_count} -> {current_gpu_count}")
                    return True

            return False

        except Exception as e:
            logger.debug(f"硬件变化检测失败，强制刷新: {e}")
            return True

    def _log_hardware_changes(self, old_hardware: HardwareProfile, new_hardware: HardwareProfile):
        """记录硬件配置变化"""
        try:
            changes = []

            # 检查GPU变化
            if old_hardware.gpu_memory_gb != new_hardware.gpu_memory_gb:
                changes.append(f"GPU显存: {old_hardware.gpu_memory_gb:.1f}GB -> {new_hardware.gpu_memory_gb:.1f}GB")

            # 检查内存变化
            if abs(old_hardware.system_ram_gb - new_hardware.system_ram_gb) > 0.5:
                changes.append(f"系统内存: {old_hardware.system_ram_gb:.1f}GB -> {new_hardware.system_ram_gb:.1f}GB")

            # 检查性能等级变化
            if hasattr(old_hardware, 'performance_level') and hasattr(new_hardware, 'performance_level'):
                if old_hardware.performance_level != new_hardware.performance_level:
                    changes.append(f"性能等级: {old_hardware.performance_level.value} -> {new_hardware.performance_level.value}")

            if changes:
                logger.info(f"🔄 检测到硬件配置变化: {'; '.join(changes)}")
            else:
                logger.debug("硬件配置无重大变化")

        except Exception as e:
            logger.debug(f"硬件变化记录失败: {e}")

    def force_refresh_hardware(self):
        """强制刷新硬件配置（公共接口）"""
        logger.info("🔄 强制刷新硬件配置")
        self._hardware_cache = None
        self._cache_timestamp = None

    def calculate_hardware_score(self, hardware: HardwareProfile) -> float:
        """计算硬件综合评分（0-100分）

        基于多维硬件参数的连续评分系统，替代原有的5级离散分级。

        评分维度：
        - GPU显存：40%权重
        - 系统内存：30%权重
        - CPU核心数：15%权重
        - 存储空间：15%权重

        Returns:
            float: 硬件综合评分（0-100）
        """
        score = 0.0

        # GPU显存权重：40%
        if hardware.has_gpu:
            # GPU模式：基于显存大小评分
            # 32GB显存 = 满分40分
            vram_score = min(hardware.gpu_memory_gb / 32.0 * 40, 40)
            score += vram_score
        else:
            # CPU模式：使用系统内存的一半权重
            # 32GB内存 = 20分（最高）
            ram_score = min(hardware.system_ram_gb / 32.0 * 20, 20)
            score += ram_score

        # 系统内存权重：30%
        # 64GB内存 = 满分30分
        ram_score = min(hardware.system_ram_gb / 64.0 * 30, 30)
        score += ram_score

        # CPU核心数权重：15%
        # 16核心 = 满分15分
        cpu_score = min(hardware.cpu_cores / 16.0 * 15, 15)
        score += cpu_score

        # 存储空间权重：15%
        # 500GB存储 = 满分15分
        storage_score = min(hardware.storage_available_gb / 500.0 * 15, 15)
        score += storage_score

        logger.info(f"💯 硬件评分: {score:.1f}/100 (GPU:{hardware.gpu_memory_gb:.1f}GB, RAM:{hardware.system_ram_gb:.1f}GB, CPU:{hardware.cpu_cores}核)")
        return score

    def _select_qwen_variant(self, hardware: HardwareProfile) -> str:
        """根据硬件配置选择合适的Qwen模型变体（基于连续评分）"""
        score = self.calculate_hardware_score(hardware)

        # 基于硬件评分的连续匹配规则
        if score >= 85:
            return "qwen2.5-32b"      # 85-100分：旗舰级
        elif score >= 75:
            return "qwen2.5-14b"      # 75-85分：高级
        elif score >= 65:
            return "qwen2.5-7b"       # 65-75分：中高级
        elif score >= 55:
            return "qwen2.5-3b"       # 55-65分：中级
        elif score >= 35:
            return "qwen2.5-1.5b"     # 35-55分：进阶级
        else:
            return "qwen2.5-0.5b"     # 0-35分：入门级

    def _select_mistral_variant(self, hardware: HardwareProfile) -> str:
        """根据硬件配置选择合适的Mistral模型变体（基于连续评分）"""
        score = self.calculate_hardware_score(hardware)

        # 基于硬件评分的连续匹配规则
        if score >= 85:
            return "mistral-large2"     # 85-100分：旗舰级
        elif score >= 65:
            return "mistral-24b-small"  # 65-85分：中高级
        elif score >= 45:
            return "mistral-12b-nemo"   # 45-65分：进阶级
        else:
            return "mistral-7b"         # 0-45分：入门级
    
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

        # 检查最佳变体是否满足最低硬件要求
        best_variant = scored_variants[0]

        # 关键检查：如果最佳变体（通常是最小的模型）都不满足硬件要求，则不推荐
        # 检查是否有严重的硬件不足问题（系统内存或GPU内存不足）
        critical_issues = []
        for issue in best_variant["compatibility"]["issues"]:
            if "系统内存不足" in issue or "GPU内存不足" in issue:
                critical_issues.append(issue)

        if critical_issues:
                logger.warning(f"⚠️  设备硬件不足，无法推荐{model_name}模型")
                logger.warning(f"   硬件问题: {', '.join(critical_issues)}")
                logger.warning(f"   最小模型要求: {best_variant['variant'].memory_requirement_gb:.1f}GB内存")
                logger.warning(f"   当前设备: {hardware.system_ram_gb:.1f}GB内存, {hardware.gpu_memory_gb:.1f}GB显存")

                # 返回一个特殊的推荐，表示设备不足
                return ModelRecommendation(
                    model_name=model_name,
                    variant=None,  # 不推荐任何变体
                    reasoning=[
                        f"❌ 设备硬件不足，无法运行{model_name}模型",
                        f"最小模型要求: {best_variant['variant'].memory_requirement_gb:.1f}GB内存",
                        f"当前设备: {hardware.system_ram_gb:.1f}GB内存, {hardware.gpu_memory_gb:.1f}GB显存",
                        "建议: 升级硬件或选择更小的模型"
                    ],
                    alternative_options=[],
                    deployment_notes=[
                        "⚠️  当前设备无法运行此模型",
                        "请考虑以下选项：",
                        "1. 升级内存/显存",
                        "2. 选择更小的模型（如Qwen2.5-0.5B）",
                        "3. 使用云端推理服务"
                    ],
                    confidence_score=0.0
                )
        
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
        """计算变体评分（增强版本，基于连续硬件评分的智能匹配）"""
        score = 0.0

        # 获取硬件信息
        memory_gb = getattr(hardware, 'memory_gb', getattr(hardware, 'system_ram_gb', 0))
        gpu_available = getattr(hardware, 'gpu_available', getattr(hardware, 'has_gpu', False))
        gpu_memory_gb = getattr(hardware, 'gpu_memory_gb', 0)
        cpu_cores = getattr(hardware, 'cpu_cores', getattr(hardware, 'cpu_count', 0))

        # 计算硬件综合评分
        hardware_score = self.calculate_hardware_score(hardware)

        # 1. 内存适配性评分 (0-40分)
        memory_requirement = variant.memory_requirement_gb
        if gpu_available and gpu_memory_gb > 0:
            # GPU模式：检查GPU显存
            if memory_requirement <= gpu_memory_gb * 0.6:  # 使用60%以下显存
                score += 40
            elif memory_requirement <= gpu_memory_gb * 0.8:  # 使用80%以下显存
                score += 30
            elif memory_requirement <= gpu_memory_gb:  # 刚好够用
                score += 20
            else:  # 显存不足
                score += 0
        else:
            # CPU模式：检查系统内存
            if memory_requirement <= memory_gb * 0.6:  # 使用60%以下内存
                score += 40
            elif memory_requirement <= memory_gb * 0.8:  # 使用80%以下内存
                score += 30
            elif memory_requirement <= memory_gb:  # 刚好够用
                score += 20
            else:  # 内存不足
                score += 0

        # 2. 量化配置适配性评分 (0-30分) - 基于硬件评分的连续匹配
        quantization = variant.quantization

        if hardware_score >= 85:  # 旗舰级设备（85-100分）
            # 优先选择高精度GPTQ量化
            if quantization in [QuantizationType.INT8_PERCHANNEL, QuantizationType.INT8]:
                score += 30
            elif quantization in [QuantizationType.INT4_PERCHANNEL, QuantizationType.INT4]:
                score += 20
            else:
                score += 10

        elif hardware_score >= 65:  # 中高级设备（65-85分）
            # 平衡精度和性能
            if quantization in [QuantizationType.INT4_PERCHANNEL, QuantizationType.INT4]:
                score += 30
            elif quantization in [QuantizationType.INT8_PERCHANNEL, QuantizationType.INT8]:
                score += 25
            else:
                score += 15

        elif hardware_score >= 45:  # 进阶级设备（45-65分）
            # 优先选择INT4 GPTQ量化
            if quantization in [QuantizationType.INT4, QuantizationType.INT4_PERCHANNEL]:
                score += 30
            elif quantization == QuantizationType.INT8:
                score += 20
            else:
                score += 10

        else:  # 入门级设备（0-45分）
            # 优先选择最轻量的GPTQ量化
            if quantization == QuantizationType.INT4:
                score += 30
            elif quantization == QuantizationType.INT4_PERCHANNEL:
                score += 25
            else:
                score += 10
        # 3. 质量要求匹配评分 (0-20分)
        quality_threshold = self.quality_thresholds.get(quality_requirement, 0.85)
        if variant.quality_retention >= quality_threshold:
            score += 20
        elif variant.quality_retention >= quality_threshold - 0.1:
            score += 15
        else:
            score += 5

        # 4. 部署目标适配性评分 (0-10分)
        if deployment_target:
            if deployment_target.value == 'production' and variant.quality_retention >= 0.9:
                score += 10
            elif deployment_target.value == 'development' and variant.quantization in [QuantizationType.INT4, QuantizationType.INT4_PERCHANNEL]:
                score += 10
            elif deployment_target.value == 'demo' and variant.size_gb <= 5:
                score += 10
            else:
                score += 5

        # 兼容性评分 (25%)
        compatibility = self.detector.assess_compatibility(hardware, variant)
        score += compatibility["compatibility_score"] * 0.25

        # 质量要求评分 (15%)
        required_quality = self.selection_rules["quality_requirements"].get(quality_requirement, 0.90)
        if variant.quality_retention >= required_quality:
            quality_score = variant.quality_retention
        else:
            quality_score = variant.quality_retention * 0.7  # 轻微惩罚
        score += quality_score * 0.15

        # 资源效率评分 (10%)
        # 优先选择资源占用合理的版本
        system_memory = getattr(hardware, 'system_ram_gb', getattr(hardware, 'total_memory_gb', memory_gb))
        memory_efficiency = max(0, 1 - variant.memory_requirement_gb / max(system_memory * 0.6, 4.0))
        score += memory_efficiency * 0.1

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
        """根据硬件推断部署目标（与硬件检测器保持一致）"""
        memory_thresholds = self.selection_rules["memory_thresholds"]

        # 获取GPU信息
        gpu_memory = hardware.gpu_memory_gb if hasattr(hardware, 'gpu_memory_gb') else 0
        gpu_type = getattr(hardware, 'gpu_type', None)
        system_memory = hardware.system_ram_gb if hasattr(hardware, 'system_ram_gb') else hardware.total_memory_gb

        # 与硬件检测器保持一致的推断逻辑
        if gpu_type and hasattr(gpu_type, 'value') and gpu_type.value == 'nvidia':
            # NVIDIA独显设备
            if gpu_memory >= 16:
                return DeploymentTarget.HIGH_PERFORMANCE
            elif gpu_memory >= 8:
                return DeploymentTarget.BALANCED
            else:
                return DeploymentTarget.LIGHTWEIGHT
        elif gpu_type and hasattr(gpu_type, 'value') and gpu_type.value == 'intel':
            # 集成显卡设备：最高只能是LIGHTWEIGHT
            if system_memory >= 16:
                return DeploymentTarget.LIGHTWEIGHT
            else:
                return DeploymentTarget.ULTRA_LIGHT
        else:
            # 无GPU设备：根据系统内存决定
            if system_memory >= 16:
                return DeploymentTarget.LIGHTWEIGHT
            elif system_memory >= 8:
                return DeploymentTarget.ULTRA_LIGHT
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
    """
    创建多层级下载配置（支持LoRA微调）

    重要说明：
    - 只下载原始FP16模型，不下载预量化模型（GPTQ/INT8/INT4）
    - 原因：预量化模型无法正确转换为GGUF格式
    - 正确流程：FP16模型 + LoRA训练 → 保存HF格式 → 转换为GGUF（此时进行量化）
    - 量化在GGUF转换阶段进行，而不是在下载阶段
    """
    return {
        "qwen3-4b": {
            "fp16": {
                "name": "Qwen3-4B-Instruct-FP16",
                "size_gb": 8.0,
                "urls": ["https://modelscope.cn/models/qwen/Qwen3-4B-Instruct"],
                "target_dir": "models/qwen/qwen3-4b/base"
            }
        },
        "qwen3-8b": {
            "fp16": {
                "name": "Qwen3-8B-Instruct-FP16",
                "size_gb": 16.0,
                "urls": ["https://modelscope.cn/models/qwen/Qwen3-8B-Instruct"],
                "target_dir": "models/qwen/qwen3-8b/base"
            }
        },
        "mistral-7b": {
            "fp16": {
                "name": "Mistral-7B-Instruct-FP16",
                "size_gb": 13.5,
                "urls": ["https://hf-mirror.com/mistralai/Mistral-7B-Instruct-v0.3"],
                "target_dir": "models/mistral/mistral-7b/base"
            }
        }
    }
