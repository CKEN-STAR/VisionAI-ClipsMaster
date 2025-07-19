#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分离器 - 按语言和难度分离训练数据
支持中英文数据自动分类和质量评估
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Tuple, Optional

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class DataSplitter:
    """数据分离器 - 多语言数据分离和分类"""

    def __init__(self):
        """初始化数据分离器"""
        self.language_patterns = {
            "zh": {
                "char_range": ('\u4e00', '\u9fff'),  # 中文字符范围
                "min_ratio": 0.3,  # 最小中文字符比例
                "keywords": ["的", "是", "在", "了", "和", "有", "我", "你", "他"]
            },
            "en": {
                "char_range": (ord('a'), ord('z')),  # 英文字符范围
                "min_ratio": 0.5,  # 最小英文字符比例
                "keywords": ["the", "and", "is", "in", "to", "of", "a", "that", "it"]
            }
        }

        print("🔄 数据分离器初始化完成")
        print("📊 支持语言: 中文(zh), 英文(en)")

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        检测文本语言

        Args:
            text: 输入文本

        Returns:
            (语言代码, 置信度)
        """
        if not text:
            return "unknown", 0.0

        text_lower = text.lower()
        total_chars = len(text)

        # 中文检测
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0

        # 英文检测
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        english_ratio = english_chars / total_chars if total_chars > 0 else 0

        # 关键词检测
        chinese_keywords = sum(1 for keyword in self.language_patterns["zh"]["keywords"] if keyword in text)
        english_keywords = sum(1 for keyword in self.language_patterns["en"]["keywords"] if keyword in text_lower)

        # 综合判断
        chinese_score = chinese_ratio * 0.7 + (chinese_keywords / 10) * 0.3
        english_score = english_ratio * 0.7 + (english_keywords / 10) * 0.3

        if chinese_score > english_score and chinese_ratio >= 0.3:
            return "zh", chinese_score
        elif english_score > chinese_score and english_ratio >= 0.5:
            return "en", english_score
        else:
            return "mixed", max(chinese_score, english_score)

    def assess_difficulty(self, text: str, language: str) -> Tuple[str, Dict[str, Any]]:
        """
        评估文本难度

        Args:
            text: 输入文本
            language: 语言代码

        Returns:
            (难度等级, 详细信息)
        """
        difficulty_info = {
            "length": len(text),
            "word_count": 0,
            "complexity_score": 0,
            "factors": []
        }

        if language == "zh":
            # 中文难度评估
            chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
            difficulty_info["word_count"] = chinese_chars

            # 复杂度因子
            if chinese_chars > 100:
                difficulty_info["factors"].append("长文本")
                difficulty_info["complexity_score"] += 2

            # 检查复杂句式
            complex_patterns = ["虽然", "但是", "不仅", "而且", "因为", "所以"]
            complex_count = sum(1 for pattern in complex_patterns if pattern in text)
            if complex_count > 2:
                difficulty_info["factors"].append("复杂句式")
                difficulty_info["complexity_score"] += 1

        elif language == "en":
            # 英文难度评估
            words = re.findall(r'\b[a-zA-Z]+\b', text)
            difficulty_info["word_count"] = len(words)

            # 复杂度因子
            if len(words) > 50:
                difficulty_info["factors"].append("long text")
                difficulty_info["complexity_score"] += 2

            # 检查复杂词汇
            complex_words = [word for word in words if len(word) > 8]
            if len(complex_words) > 3:
                difficulty_info["factors"].append("complex vocabulary")
                difficulty_info["complexity_score"] += 1

            # 检查复杂句式
            if ";" in text or text.count(",") > 3:
                difficulty_info["factors"].append("complex sentences")
                difficulty_info["complexity_score"] += 1

        # 确定难度等级
        if difficulty_info["complexity_score"] >= 4:
            difficulty = "hard"
        elif difficulty_info["complexity_score"] >= 2:
            difficulty = "medium"
        else:
            difficulty = "easy"

        return difficulty, difficulty_info

    def split_by_language(self, training_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按语言分离训练数据

        Args:
            training_data: 原始训练数据

        Returns:
            按语言分组的数据
        """
        split_data = {
            "zh": [],
            "en": [],
            "mixed": [],
            "unknown": []
        }

        statistics = {
            "total_samples": len(training_data),
            "language_distribution": {"zh": 0, "en": 0, "mixed": 0, "unknown": 0},
            "quality_scores": []
        }

        for item in training_data:
            original = item.get("original", "")
            viral = item.get("viral", "")

            # 检测语言
            lang, confidence = self.detect_language(original)

            # 评估难度
            difficulty, difficulty_info = self.assess_difficulty(original, lang)

            # 创建增强的数据项
            enhanced_item = {
                **item,
                "language": lang,
                "confidence": confidence,
                "difficulty": difficulty,
                "difficulty_info": difficulty_info,
                "quality_score": confidence * 0.6 + (1 - difficulty_info["complexity_score"] / 5) * 0.4
            }

            # 分组
            split_data[lang].append(enhanced_item)
            statistics["language_distribution"][lang] += 1
            statistics["quality_scores"].append(enhanced_item["quality_score"])

        # 计算统计信息
        if statistics["quality_scores"]:
            statistics["avg_quality"] = sum(statistics["quality_scores"]) / len(statistics["quality_scores"])
            statistics["min_quality"] = min(statistics["quality_scores"])
            statistics["max_quality"] = max(statistics["quality_scores"])

        return {
            "data": split_data,
            "statistics": statistics
        }

    def split_by_difficulty(self, language_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按难度分离数据

        Args:
            language_data: 单语言数据

        Returns:
            按难度分组的数据
        """
        difficulty_split = {
            "easy": [],
            "medium": [],
            "hard": []
        }

        for item in language_data:
            difficulty = item.get("difficulty", "medium")
            difficulty_split[difficulty].append(item)

        return difficulty_split

    def create_training_splits(self, data: Dict[str, Any],
                             train_ratio: float = 0.8,
                             val_ratio: float = 0.1,
                             test_ratio: float = 0.1) -> Dict[str, Any]:
        """
        创建训练/验证/测试数据分割

        Args:
            data: 分离后的数据
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例

        Returns:
            分割后的数据集
        """
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
            raise ValueError("比例之和必须等于1.0")

        splits = {
            "train": {"zh": [], "en": []},
            "val": {"zh": [], "en": []},
            "test": {"zh": [], "en": []}
        }

        for lang in ["zh", "en"]:
            lang_data = data["data"][lang]
            total_samples = len(lang_data)

            if total_samples == 0:
                continue

            # 计算分割点
            train_end = int(total_samples * train_ratio)
            val_end = train_end + int(total_samples * val_ratio)

            # 分割数据
            splits["train"][lang] = lang_data[:train_end]
            splits["val"][lang] = lang_data[train_end:val_end]
            splits["test"][lang] = lang_data[val_end:]

        # 添加统计信息
        splits["statistics"] = {
            "train_samples": sum(len(splits["train"][lang]) for lang in ["zh", "en"]),
            "val_samples": sum(len(splits["val"][lang]) for lang in ["zh", "en"]),
            "test_samples": sum(len(splits["test"][lang]) for lang in ["zh", "en"]),
            "language_distribution": {
                lang: {
                    "train": len(splits["train"][lang]),
                    "val": len(splits["val"][lang]),
                    "test": len(splits["test"][lang])
                }
                for lang in ["zh", "en"]
            }
        }

        return splits