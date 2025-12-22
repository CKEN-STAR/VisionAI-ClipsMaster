"""
剧本重构数据增强器
使用7步重构算法生成训练数据变体
"""

import logging
from typing import List, Dict, Any, Optional
import time

# 导入剧本工程师
from src.core.screenplay_engineer import ScreenplayEngineer

logger = logging.getLogger(__name__)


class ReconstructionAugmenter:
    """
    基于7步重构算法的数据增强器
    
    功能:
    - 使用剧本重构算法生成训练样本变体
    - 提升训练数据的多样性和质量
    - 保持语义一致性
    """
    
    def __init__(self):
        """初始化增强器"""
        self.engineer = ScreenplayEngineer()
        self.augmentation_stats = {
            "total_samples": 0,
            "augmented_samples": 0,
            "failed_samples": 0,
            "total_time": 0.0
        }
        logger.info("🔄 剧本重构数据增强器初始化完成")
    
    def augment_sample(self, original: str, viral: str, 
                      language: str = "zh", 
                      num_variants: int = 3) -> List[Dict[str, Any]]:
        """
        使用7步重构算法生成训练样本变体
        
        Args:
            original: 原始剧本文本
            viral: 爆款剧本文本
            language: 语言代码 ("zh" 或 "en")
            num_variants: 生成变体数量
            
        Returns:
            List[Dict]: 包含原始样本和变体的列表
        """
        start_time = time.time()
        variants = []
        
        try:
            # 1. 保留原始样本
            variants.append({
                "original": original,
                "viral": viral,
                "augmented": False,
                "method": "original"
            })
            
            # 2. 生成重构变体
            for i in range(num_variants):
                try:
                    # 使用7步重构算法
                    reconstructed = self.engineer.reconstruct_plot(
                        original, 
                        language=language
                    )
                    
                    # 验证重构质量
                    if self._validate_reconstruction(original, reconstructed, language):
                        variants.append({
                            "original": original,
                            "viral": reconstructed,
                            "augmented": True,
                            "method": "7step_reconstruction",
                            "variant_id": i + 1
                        })
                        self.augmentation_stats["augmented_samples"] += 1
                    else:
                        logger.warning(f"变体 {i+1} 质量不达标，跳过")
                        self.augmentation_stats["failed_samples"] += 1
                        
                except Exception as e:
                    logger.error(f"生成变体 {i+1} 失败: {e}")
                    self.augmentation_stats["failed_samples"] += 1
            
            self.augmentation_stats["total_samples"] += 1
            
        except Exception as e:
            logger.error(f"增强样本失败: {e}")
            # 至少返回原始样本
            if not variants:
                variants.append({
                    "original": original,
                    "viral": viral,
                    "augmented": False,
                    "method": "original"
                })
        
        finally:
            elapsed_time = time.time() - start_time
            self.augmentation_stats["total_time"] += elapsed_time
        
        return variants
    
    def _validate_reconstruction(self, original: str, reconstructed: str, language: str) -> bool:
        """
        验证重构质量
        
        Args:
            original: 原始文本
            reconstructed: 重构后文本
            language: 语言代码
            
        Returns:
            bool: 是否通过质量检查
        """
        # 1. 长度检查：重构后文本不应为空
        if not reconstructed or len(reconstructed.strip()) == 0:
            return False
        
        # 2. 长度合理性：不应过短或过长
        length_ratio = len(reconstructed) / len(original) if len(original) > 0 else 0
        if length_ratio < 0.3 or length_ratio > 3.0:
            return False
        
        # 3. 语义相关性：检查关键词重叠
        if language == "zh":
            # 中文：检查字符重叠
            original_chars = set(original)
            reconstructed_chars = set(reconstructed)
            overlap = len(original_chars & reconstructed_chars) / len(original_chars) if original_chars else 0
        else:
            # 英文：检查单词重叠
            original_words = set(original.lower().split())
            reconstructed_words = set(reconstructed.lower().split())
            overlap = len(original_words & reconstructed_words) / len(original_words) if original_words else 0
        
        # 至少保留20%的关键词
        if overlap < 0.2:
            return False
        
        return True
    
    def augment_batch(self, training_data: List[Dict[str, Any]], 
                     language: str = "zh",
                     num_variants: int = 3,
                     max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量增强训练数据
        
        Args:
            training_data: 原始训练数据列表
            language: 语言代码
            num_variants: 每个样本生成的变体数量
            max_samples: 最大处理样本数（None表示处理全部）
            
        Returns:
            List[Dict]: 增强后的训练数据
        """
        logger.info(f"🔄 开始批量数据增强，原始样本数: {len(training_data)}")
        
        augmented_data = []
        samples_to_process = training_data[:max_samples] if max_samples else training_data
        
        for idx, item in enumerate(samples_to_process):
            original = item.get("original", "")
            viral = item.get("viral", "")
            
            if not original or not viral:
                logger.warning(f"样本 {idx} 缺少必要字段，跳过")
                continue
            
            # 生成变体
            variants = self.augment_sample(original, viral, language, num_variants)
            augmented_data.extend(variants)
            
            # 进度日志
            if (idx + 1) % 10 == 0:
                logger.info(f"已处理 {idx + 1}/{len(samples_to_process)} 个样本")
        
        logger.info(f"✅ 批量增强完成: {len(training_data)} -> {len(augmented_data)} 样本")
        logger.info(f"📊 增强统计: {self.get_stats()}")
        
        return augmented_data
    
    def get_stats(self) -> Dict[str, Any]:
        """获取增强统计信息"""
        stats = self.augmentation_stats.copy()
        
        # 计算平均处理时间
        if stats["total_samples"] > 0:
            stats["avg_time_per_sample"] = stats["total_time"] / stats["total_samples"]
        else:
            stats["avg_time_per_sample"] = 0.0
        
        # 计算成功率
        total_attempts = stats["augmented_samples"] + stats["failed_samples"]
        if total_attempts > 0:
            stats["success_rate"] = stats["augmented_samples"] / total_attempts
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.augmentation_stats = {
            "total_samples": 0,
            "augmented_samples": 0,
            "failed_samples": 0,
            "total_time": 0.0
        }
        logger.info("📊 统计信息已重置")


# 便捷函数
def augment_training_data(training_data: List[Dict[str, Any]], 
                         language: str = "zh",
                         num_variants: int = 3) -> List[Dict[str, Any]]:
    """
    便捷函数：增强训练数据
    
    Args:
        training_data: 原始训练数据
        language: 语言代码
        num_variants: 每个样本生成的变体数量
        
    Returns:
        List[Dict]: 增强后的训练数据
    """
    augmenter = ReconstructionAugmenter()
    return augmenter.augment_batch(training_data, language, num_variants)

