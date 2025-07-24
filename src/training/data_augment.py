#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据增强器 - 通用数据增强工具
支持中英文文本增强，提高训练数据多样性和模型泛化能力
"""

import os
import sys
import json
import random
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class DataAugmenter:
    """数据增强器 - 跨语言文本增强工具"""

    def __init__(self, language: str = "zh"):
        """
        初始化数据增强器

        Args:
            language: 目标语言 (zh/en)
        """
        self.language = language

        # 中文增强规则
        self.zh_augmentation_rules = {
            "synonyms": {
                "震撼": ["惊艳", "震惊", "惊人", "令人震撼"],
                "惊呆": ["惊讶", "震惊", "惊愕", "目瞪口呆"],
                "不敢相信": ["难以置信", "无法相信", "简直不敢相信", "太不可思议"],
                "史上最": ["历史最", "前所未有", "空前绝后", "史无前例"],
                "太精彩": ["非常精彩", "极其精彩", "超级精彩", "无比精彩"],
                "改变一切": ["颠覆一切", "改变命运", "扭转乾坤", "彻底改变"]
            },
            "intensifiers": ["超级", "极其", "非常", "特别", "相当", "十分"],
            "exclamations": ["！", "！！", "！！！"],
            "question_words": ["什么", "怎么", "为什么", "哪里", "谁"]
        }

        # 英文增强规则
        self.en_augmentation_rules = {
            "synonyms": {
                "SHOCKING": ["AMAZING", "STUNNING", "INCREDIBLE", "MIND-BLOWING"],
                "AMAZING": ["INCREDIBLE", "FANTASTIC", "WONDERFUL", "SPECTACULAR"],
                "UNBELIEVABLE": ["INCREDIBLE", "ASTONISHING", "MIND-BLOWING", "SHOCKING"],
                "MIND-BLOWING": ["INCREDIBLE", "AMAZING", "STUNNING", "SPECTACULAR"],
                "INCREDIBLE": ["AMAZING", "FANTASTIC", "UNBELIEVABLE", "STUNNING"],
                "STUNNING": ["AMAZING", "INCREDIBLE", "SPECTACULAR", "BREATHTAKING"]
            },
            "intensifiers": ["SUPER", "ULTRA", "EXTREMELY", "INCREDIBLY", "ABSOLUTELY"],
            "exclamations": ["!", "!!", "!!!"],
            "question_words": ["WHAT", "HOW", "WHY", "WHERE", "WHO"]
        }

        print(f"🔄 数据增强器初始化完成")
        print(f"🌍 目标语言: {language}")
        print(f"📊 增强规则: {'中文' if language == 'zh' else '英文'}模式")

    def augment_text_synonyms(self, text: str) -> List[str]:
        """
        同义词替换增强

        Args:
            text: 原始文本

        Returns:
            增强后的文本列表
        """
        augmented_texts = []
        rules = self.zh_augmentation_rules if self.language == "zh" else self.en_augmentation_rules

        # 为每个同义词组生成替换版本
        for original, synonyms in rules["synonyms"].items():
            if original in text:
                for synonym in synonyms:
                    augmented_text = text.replace(original, synonym)
                    if augmented_text != text:
                        augmented_texts.append(augmented_text)

        return augmented_texts

    def augment_text_intensifiers(self, text: str) -> List[str]:
        """
        强化词增强

        Args:
            text: 原始文本

        Returns:
            增强后的文本列表
        """
        augmented_texts = []
        rules = self.zh_augmentation_rules if self.language == "zh" else self.en_augmentation_rules

        # 在关键词前添加强化词
        for intensifier in rules["intensifiers"]:
            if self.language == "zh":
                # 中文强化词插入
                for keyword in ["震撼", "惊呆", "精彩", "厉害"]:
                    if keyword in text and intensifier not in text:
                        augmented_text = text.replace(keyword, f"{intensifier}{keyword}")
                        augmented_texts.append(augmented_text)
            else:
                # 英文强化词插入
                for keyword in ["AMAZING", "INCREDIBLE", "STUNNING"]:
                    if keyword in text and intensifier not in text:
                        augmented_text = text.replace(keyword, f"{intensifier} {keyword}")
                        augmented_texts.append(augmented_text)

        return augmented_texts

    def augment_text_punctuation(self, text: str) -> List[str]:
        """
        标点符号增强

        Args:
            text: 原始文本

        Returns:
            增强后的文本列表
        """
        augmented_texts = []
        rules = self.zh_augmentation_rules if self.language == "zh" else self.en_augmentation_rules

        # 添加不同程度的感叹号
        for exclamation in rules["exclamations"]:
            if not text.endswith(exclamation):
                # 移除原有标点，添加新标点
                clean_text = text.rstrip("!！。.?？")
                augmented_text = clean_text + exclamation
                augmented_texts.append(augmented_text)

        return augmented_texts

    def augment_text_structure(self, text: str) -> List[str]:
        """
        句式结构增强

        Args:
            text: 原始文本

        Returns:
            增强后的文本列表
        """
        augmented_texts = []
        rules = self.zh_augmentation_rules if self.language == "zh" else self.en_augmentation_rules

        if self.language == "zh":
            # 中文句式变换
            if not any(q in text for q in rules["question_words"]):
                # 添加疑问句式
                question_starters = ["你知道吗？", "猜猜看，", "你相信吗？"]
                for starter in question_starters:
                    augmented_text = starter + text
                    augmented_texts.append(augmented_text)
        else:
            # 英文句式变换
            if not any(q in text.upper() for q in rules["question_words"]):
                # 添加疑问句式
                question_starters = ["GUESS WHAT? ", "CAN YOU BELIEVE? ", "DID YOU KNOW? "]
                for starter in question_starters:
                    augmented_text = starter + text
                    augmented_texts.append(augmented_text)

        return augmented_texts

    def augment_single_sample(self, original: str, viral: str,
                            augmentation_factor: int = 3) -> List[Dict[str, Any]]:
        """
        对单个样本进行增强

        Args:
            original: 原始字幕
            viral: 爆款字幕
            augmentation_factor: 增强倍数

        Returns:
            增强后的样本列表
        """
        augmented_samples = []

        # 对爆款字幕进行多种增强
        viral_variants = []

        # 同义词替换
        viral_variants.extend(self.augment_text_synonyms(viral))

        # 强化词增强
        viral_variants.extend(self.augment_text_intensifiers(viral))

        # 标点符号增强
        viral_variants.extend(self.augment_text_punctuation(viral))

        # 句式结构增强
        viral_variants.extend(self.augment_text_structure(viral))

        # 去重并限制数量
        viral_variants = list(set(viral_variants))
        viral_variants = viral_variants[:augmentation_factor]

        # 生成增强样本
        for i, variant in enumerate(viral_variants):
            augmented_sample = {
                "original": original,
                "viral": variant,
                "augmentation_type": f"variant_{i+1}",
                "source_sample": {"original": original, "viral": viral},
                "language": self.language,
                "created_at": datetime.now().isoformat()
            }
            augmented_samples.append(augmented_sample)

        return augmented_samples

    def augment_dataset(self, training_data: List[Dict[str, Any]],
                       augmentation_factor: int = 3) -> Dict[str, Any]:
        """
        对整个数据集进行增强

        Args:
            training_data: 原始训练数据
            augmentation_factor: 增强倍数

        Returns:
            增强后的数据集和统计信息
        """
        augmented_dataset = {
            "original_samples": training_data.copy(),
            "augmented_samples": [],
            "statistics": {
                "original_count": len(training_data),
                "augmented_count": 0,
                "total_count": 0,
                "augmentation_ratio": 0.0,
                "language": self.language
            }
        }

        print(f"🔄 开始数据增强，原始样本数: {len(training_data)}")

        # 对每个样本进行增强
        for i, sample in enumerate(training_data):
            original = sample.get("original", "")
            viral = sample.get("viral", "")

            if original and viral:
                # 生成增强样本
                augmented_samples = self.augment_single_sample(
                    original, viral, augmentation_factor
                )
                augmented_dataset["augmented_samples"].extend(augmented_samples)

                # 显示进度
                if (i + 1) % 10 == 0 or i == len(training_data) - 1:
                    print(f"  📊 已处理 {i + 1}/{len(training_data)} 个样本")

        # 更新统计信息
        augmented_count = len(augmented_dataset["augmented_samples"])
        total_count = len(training_data) + augmented_count

        augmented_dataset["statistics"].update({
            "augmented_count": augmented_count,
            "total_count": total_count,
            "augmentation_ratio": augmented_count / len(training_data) if training_data else 0.0
        })

        print(f"✅ 数据增强完成:")
        print(f"  📊 原始样本: {len(training_data)}")
        print(f"  📊 增强样本: {augmented_count}")
        print(f"  📊 总样本数: {total_count}")
        print(f"  📊 增强比例: {augmented_dataset['statistics']['augmentation_ratio']:.1f}x")

        return augmented_dataset

    def get_quality_score(self, text: str) -> float:
        """
        评估增强文本的质量

        Args:
            text: 待评估文本

        Returns:
            质量分数 (0.0-1.0)
        """
        score = 0.0
        rules = self.zh_augmentation_rules if self.language == "zh" else self.en_augmentation_rules

        # 检查是否包含爆款关键词
        viral_keywords = list(rules["synonyms"].keys())
        has_viral_keywords = any(keyword in text for keyword in viral_keywords)
        if has_viral_keywords:
            score += 0.4

        # 检查是否有强化词
        has_intensifiers = any(intensifier in text for intensifier in rules["intensifiers"])
        if has_intensifiers:
            score += 0.2

        # 检查标点符号
        has_exclamations = any(exc in text for exc in rules["exclamations"])
        if has_exclamations:
            score += 0.2

        # 检查文本长度合理性
        if self.language == "zh":
            if 5 <= len(text) <= 50:
                score += 0.2
        else:
            words = text.split()
            if 3 <= len(words) <= 20:
                score += 0.2

        return min(score, 1.0)

    def filter_high_quality_samples(self, augmented_dataset: Dict[str, Any],
                                   quality_threshold: float = 0.6) -> Dict[str, Any]:
        """
        过滤高质量增强样本

        Args:
            augmented_dataset: 增强后的数据集
            quality_threshold: 质量阈值

        Returns:
            过滤后的高质量数据集
        """
        high_quality_samples = []

        for sample in augmented_dataset["augmented_samples"]:
            viral_text = sample.get("viral", "")
            quality_score = self.get_quality_score(viral_text)

            if quality_score >= quality_threshold:
                sample["quality_score"] = quality_score
                high_quality_samples.append(sample)

        # 更新数据集
        filtered_dataset = augmented_dataset.copy()
        filtered_dataset["augmented_samples"] = high_quality_samples
        filtered_dataset["statistics"]["filtered_count"] = len(high_quality_samples)
        filtered_dataset["statistics"]["quality_threshold"] = quality_threshold

        print(f"🔍 质量过滤完成:")
        print(f"  📊 过滤前: {len(augmented_dataset['augmented_samples'])} 个增强样本")
        print(f"  📊 过滤后: {len(high_quality_samples)} 个高质量样本")
        print(f"  📊 质量阈值: {quality_threshold}")

        return filtered_dataset

    def export_augmented_data(self, augmented_dataset: Dict[str, Any],
                            output_path: Optional[str] = None) -> str:
        """
        导出增强后的数据

        Args:
            augmented_dataset: 增强后的数据集
            output_path: 输出路径

        Returns:
            导出文件路径
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"augmented_data_{self.language}_{timestamp}.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(augmented_dataset, f, ensure_ascii=False, indent=2)

            print(f"💾 增强数据已导出: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""

    def augment_data(self, data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        数据增强主方法 - 为测试兼容性添加

        Args:
            data: 原始数据列表，每个元素包含 'original' 和 'viral' 字段

        Returns:
            增强后的数据列表
        """
        try:
            augmented_data = []

            for item in data:
                # 保留原始数据
                augmented_data.append(item.copy())

                # 生成增强版本
                if 'original' in item and 'viral' in item:
                    # 对原片字幕进行增强
                    original_augmented = self.augment_text(item['original'])

                    # 对爆款字幕进行增强
                    viral_augmented = self.augment_text(item['viral'])

                    # 创建增强样本
                    augmented_item = {
                        'original': original_augmented,
                        'viral': viral_augmented,
                        'augmented': True,
                        'source': 'data_augmenter'
                    }

                    augmented_data.append(augmented_item)

            print(f"🔄 数据增强完成: {len(data)} -> {len(augmented_data)} 样本")
            return augmented_data

        except Exception as e:
            print(f"❌ 数据增强失败: {e}")
            return data  # 返回原始数据作为回退

    def augment_text(self, text: str) -> str:
        """
        文本增强主方法 - 为测试兼容性添加

        Args:
            text: 原始文本

        Returns:
            增强后的文本
        """
        try:
            if not text or not text.strip():
                return text

            # 应用多种增强策略
            augmented_text = text

            # 1. 同义词替换
            if self.language == "zh":
                synonyms = self.zh_augmentation_rules["synonyms"]
                for original, replacements in synonyms.items():
                    if original in augmented_text:
                        import random
                        replacement = random.choice(replacements)
                        augmented_text = augmented_text.replace(original, replacement, 1)
            else:
                synonyms = self.en_augmentation_rules["synonyms"]
                for original, replacements in synonyms.items():
                    if original in augmented_text.upper():
                        import random
                        replacement = random.choice(replacements)
                        augmented_text = augmented_text.replace(original, replacement, 1)

            # 2. 强化词添加
            if self.language == "zh":
                intensifiers = self.zh_augmentation_rules["intensifiers"]
                keywords = ["震撼", "惊呆", "精彩"]
                for keyword in keywords:
                    if keyword in augmented_text:
                        import random
                        intensifier = random.choice(intensifiers)
                        augmented_text = augmented_text.replace(keyword, f"{intensifier}{keyword}", 1)
                        break
            else:
                intensifiers = self.en_augmentation_rules["intensifiers"]
                keywords = ["AMAZING", "INCREDIBLE", "STUNNING"]
                for keyword in keywords:
                    if keyword in augmented_text.upper():
                        import random
                        intensifier = random.choice(intensifiers)
                        augmented_text = augmented_text.replace(keyword, f"{intensifier} {keyword}", 1)
                        break

            # 3. 标点符号增强
            if self.language == "zh":
                if not augmented_text.endswith(("！", "！！", "！！！")):
                    augmented_text = augmented_text.rstrip("。") + "！"
            else:
                if not augmented_text.endswith(("!", "!!", "!!!")):
                    augmented_text = augmented_text.rstrip(".") + "!"

            return augmented_text

        except Exception as e:
            print(f"❌ 文本增强失败: {e}")
            return text  # 返回原始文本作为回退


# 为了保持向后兼容性，添加别名
DataAugment = DataAugmenter


if __name__ == "__main__":
    # 测试数据增强器
    augmenter = DataAugmenter("zh")

    test_text = "这个视频太震撼了！不敢相信这是真的！"
    print(f"原文: {test_text}")

    augmented = augmenter.augment_text(test_text)
    print(f"增强后: {augmented}")

    # 测试英文增强
    en_augmenter = DataAugmenter("en")
    en_text = "This is SHOCKING! You won't believe what happens next!"
    print(f"Original: {en_text}")

    en_augmented = en_augmenter.augment_text(en_text)
    print(f"Augmented: {en_augmented}")