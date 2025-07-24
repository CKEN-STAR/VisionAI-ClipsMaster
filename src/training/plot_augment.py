#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剧情增强器 - 生成多样化训练样本
专门用于剧本重构训练，生成不同视角和分支情节的训练数据
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

class PlotAugmenter:
    """剧情增强器 - 剧本结构多样化工具"""

    def __init__(self, language: str = "zh"):
        """
        初始化剧情增强器

        Args:
            language: 目标语言 (zh/en)
        """
        self.language = language

        # 中文剧情模板
        self.zh_plot_templates = {
            "emotional_hooks": [
                "你绝对想不到接下来发生了什么",
                "这一幕让所有人都震惊了",
                "没人能预料到这样的结局",
                "这个转折太意外了"
            ],
            "conflict_intensifiers": [
                "矛盾升级到了顶点",
                "冲突一触即发",
                "紧张气氛达到极致",
                "关键时刻到了"
            ],
            "revelation_patterns": [
                "真相终于大白",
                "秘密被揭开了",
                "一切都明白了",
                "答案就在眼前"
            ],
            "climax_builders": [
                "高潮部分来了",
                "最精彩的时刻",
                "决定性的瞬间",
                "关键的转折点"
            ]
        }

        # 英文剧情模板
        self.en_plot_templates = {
            "emotional_hooks": [
                "You'll NEVER guess what happens next",
                "This scene shocked EVERYONE",
                "NO ONE saw this ending coming",
                "This twist is UNBELIEVABLE"
            ],
            "conflict_intensifiers": [
                "The tension reaches BREAKING POINT",
                "Conflict is about to EXPLODE",
                "The atmosphere is ELECTRIC",
                "This is the MOMENT OF TRUTH"
            ],
            "revelation_patterns": [
                "The truth is FINALLY revealed",
                "The secret is OUT",
                "Everything becomes CLEAR",
                "The answer is RIGHT HERE"
            ],
            "climax_builders": [
                "Here comes the CLIMAX",
                "The most EPIC moment",
                "The DECISIVE instant",
                "The game-changing TWIST"
            ]
        }

        # 剧情结构模式
        self.plot_structures = {
            "linear": ["开始", "发展", "高潮", "结局"],
            "flashback": ["现在", "回忆", "真相", "回到现在"],
            "parallel": ["线索A", "线索B", "交汇", "结合"],
            "mystery": ["疑问", "调查", "线索", "揭秘"]
        }

        print(f"🎭 剧情增强器初始化完成")
        print(f"🌍 目标语言: {language}")
        print(f"📊 剧情模板: {'中文' if language == 'zh' else '英文'}模式")

    def generate_plot_variations(self, original_plot: str) -> List[str]:
        """
        生成剧情变体

        Args:
            original_plot: 原始剧情

        Returns:
            剧情变体列表
        """
        variations = []
        templates = self.zh_plot_templates if self.language == "zh" else self.en_plot_templates

        # 添加情感钩子
        for hook in templates["emotional_hooks"]:
            if self.language == "zh":
                variation = f"{hook}：{original_plot}"
            else:
                variation = f"{hook}: {original_plot}"
            variations.append(variation)

        # 添加冲突强化
        for intensifier in templates["conflict_intensifiers"]:
            if self.language == "zh":
                variation = f"{original_plot}，{intensifier}！"
            else:
                variation = f"{original_plot} - {intensifier}!"
            variations.append(variation)

        return variations

    def create_multi_perspective_plots(self, base_plot: str,
                                     character_perspectives: List[str]) -> List[Dict[str, Any]]:
        """
        创建多视角剧情

        Args:
            base_plot: 基础剧情
            character_perspectives: 角色视角列表

        Returns:
            多视角剧情列表
        """
        multi_perspective_plots = []

        for perspective in character_perspectives:
            if self.language == "zh":
                perspective_plot = f"从{perspective}的角度看：{base_plot}"
                viral_version = f"震撼！{perspective}视角下的真相"
            else:
                perspective_plot = f"From {perspective}'s perspective: {base_plot}"
                viral_version = f"SHOCKING! The truth from {perspective}'s view"

            plot_data = {
                "original": perspective_plot,
                "viral": viral_version,
                "perspective": perspective,
                "base_plot": base_plot,
                "augmentation_type": "multi_perspective",
                "language": self.language
            }
            multi_perspective_plots.append(plot_data)

        return multi_perspective_plots

    def generate_branching_narratives(self, main_plot: str,
                                    decision_points: List[str]) -> List[Dict[str, Any]]:
        """
        生成分支叙事

        Args:
            main_plot: 主要剧情
            decision_points: 决策点列表

        Returns:
            分支叙事列表
        """
        branching_narratives = []

        for i, decision in enumerate(decision_points):
            if self.language == "zh":
                branch_plot = f"{main_plot}，关键选择：{decision}"
                viral_version = f"如果选择{decision}会怎样？结果太意外了！"
            else:
                branch_plot = f"{main_plot}, key choice: {decision}"
                viral_version = f"What if they chose {decision}? The result is SHOCKING!"

            narrative_data = {
                "original": branch_plot,
                "viral": viral_version,
                "decision_point": decision,
                "branch_id": f"branch_{i+1}",
                "main_plot": main_plot,
                "augmentation_type": "branching_narrative",
                "language": self.language
            }
            branching_narratives.append(narrative_data)

        return branching_narratives

    def create_temporal_variations(self, plot: str) -> List[Dict[str, Any]]:
        """
        创建时间线变体

        Args:
            plot: 原始剧情

        Returns:
            时间线变体列表
        """
        temporal_variations = []

        # 不同时间结构的变体
        time_structures = {
            "flashback": "回忆" if self.language == "zh" else "flashback",
            "flash_forward": "预告" if self.language == "zh" else "flash forward",
            "parallel_time": "同时" if self.language == "zh" else "meanwhile",
            "time_loop": "循环" if self.language == "zh" else "time loop"
        }

        for structure, time_marker in time_structures.items():
            if self.language == "zh":
                temporal_plot = f"【{time_marker}】{plot}"
                viral_version = f"时间线揭秘！{time_marker}中的惊人真相"
            else:
                temporal_plot = f"[{time_marker}] {plot}"
                viral_version = f"Timeline REVEALED! {time_marker} shows SHOCKING truth"

            variation_data = {
                "original": temporal_plot,
                "viral": viral_version,
                "time_structure": structure,
                "time_marker": time_marker,
                "base_plot": plot,
                "augmentation_type": "temporal_variation",
                "language": self.language
            }
            temporal_variations.append(variation_data)

        return temporal_variations

    def generate_emotional_arcs(self, base_plot: str) -> List[Dict[str, Any]]:
        """
        生成情感弧线变体

        Args:
            base_plot: 基础剧情

        Returns:
            情感弧线变体列表
        """
        emotional_arcs = []

        if self.language == "zh":
            emotions = {
                "悲伤": "催泪！这个情节让人心碎",
                "愤怒": "愤怒！这种行为太过分了",
                "惊喜": "惊喜！意想不到的美好结局",
                "恐惧": "恐怖！这个转折太可怕了",
                "希望": "感动！绝望中的希望之光"
            }
        else:
            emotions = {
                "sadness": "HEARTBREAKING! This scene will make you CRY",
                "anger": "OUTRAGEOUS! This behavior is UNACCEPTABLE",
                "joy": "AMAZING! The most BEAUTIFUL ending ever",
                "fear": "TERRIFYING! This twist is absolutely SCARY",
                "hope": "INSPIRING! Hope shines in the DARKEST moment"
            }

        for emotion, viral_template in emotions.items():
            emotional_data = {
                "original": base_plot,
                "viral": viral_template,
                "emotion": emotion,
                "base_plot": base_plot,
                "augmentation_type": "emotional_arc",
                "language": self.language
            }
            emotional_arcs.append(emotional_data)

        return emotional_arcs

    def augment_plot_dataset(self, training_data: List[Dict[str, Any]],
                           augmentation_types: List[str] = None) -> Dict[str, Any]:
        """
        对剧情数据集进行全面增强

        Args:
            training_data: 原始训练数据
            augmentation_types: 增强类型列表

        Returns:
            增强后的剧情数据集
        """
        if augmentation_types is None:
            augmentation_types = ["variations", "perspectives", "temporal", "emotional"]

        augmented_dataset = {
            "original_samples": training_data.copy(),
            "augmented_samples": [],
            "statistics": {
                "original_count": len(training_data),
                "augmented_count": 0,
                "augmentation_types": augmentation_types,
                "language": self.language
            }
        }

        print(f"🎭 开始剧情增强，原始样本数: {len(training_data)}")

        for i, sample in enumerate(training_data):
            original = sample.get("original", "")

            if not original:
                continue

            # 剧情变体增强
            if "variations" in augmentation_types:
                variations = self.generate_plot_variations(original)
                for variation in variations:
                    augmented_sample = {
                        "original": original,
                        "viral": variation,
                        "augmentation_type": "plot_variation",
                        "source_sample": sample,
                        "language": self.language
                    }
                    augmented_dataset["augmented_samples"].append(augmented_sample)

            # 多视角增强
            if "perspectives" in augmentation_types:
                if self.language == "zh":
                    perspectives = ["主角", "配角", "反派", "旁观者"]
                else:
                    perspectives = ["protagonist", "supporting character", "antagonist", "observer"]

                perspective_plots = self.create_multi_perspective_plots(original, perspectives)
                augmented_dataset["augmented_samples"].extend(perspective_plots)

            # 时间线增强
            if "temporal" in augmentation_types:
                temporal_plots = self.create_temporal_variations(original)
                augmented_dataset["augmented_samples"].extend(temporal_plots)

            # 情感弧线增强
            if "emotional" in augmentation_types:
                emotional_plots = self.generate_emotional_arcs(original)
                augmented_dataset["augmented_samples"].extend(emotional_plots)

            # 显示进度
            if (i + 1) % 5 == 0 or i == len(training_data) - 1:
                print(f"  📊 已处理 {i + 1}/{len(training_data)} 个剧情样本")

        # 更新统计信息
        augmented_count = len(augmented_dataset["augmented_samples"])
        augmented_dataset["statistics"]["augmented_count"] = augmented_count
        augmented_dataset["statistics"]["total_count"] = len(training_data) + augmented_count

        print(f"✅ 剧情增强完成:")
        print(f"  📊 原始样本: {len(training_data)}")
        print(f"  📊 增强样本: {augmented_count}")
        print(f"  📊 增强类型: {', '.join(augmentation_types)}")

        return augmented_dataset

    def export_plot_data(self, augmented_dataset: Dict[str, Any],
                        output_path: Optional[str] = None) -> str:
        """
        导出增强后的剧情数据

        Args:
            augmented_dataset: 增强后的数据集
            output_path: 输出路径

        Returns:
            导出文件路径
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"plot_augmented_data_{self.language}_{timestamp}.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(augmented_dataset, f, ensure_ascii=False, indent=2)

            print(f"💾 剧情增强数据已导出: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return ""

    def augment_plot(self, plot_text: str) -> str:
        """
        剧情增强主方法 - 为测试兼容性添加

        Args:
            plot_text: 原始剧情文本

        Returns:
            增强后的剧情文本
        """
        try:
            if not plot_text or not plot_text.strip():
                return plot_text

            # 应用剧情增强规则
            augmented_text = plot_text

            # 1. 情感强化
            if self.language == "zh":
                # 中文情感强化
                emotion_words = ["震撼", "惊艳", "不敢相信", "太精彩"]
                for word in emotion_words:
                    if word in augmented_text:
                        enhanced_word = random.choice(["超级" + word, "极其" + word, word + "！"])
                        augmented_text = augmented_text.replace(word, enhanced_word, 1)
            else:
                # 英文情感强化
                emotion_words = ["SHOCKING", "AMAZING", "INCREDIBLE"]
                for word in emotion_words:
                    if word in augmented_text.upper():
                        enhanced_word = random.choice(["SUPER " + word, "ULTRA " + word, word + "!!!"])
                        augmented_text = augmented_text.replace(word, enhanced_word, 1)

            # 2. 悬念增强
            if "？" in augmented_text or "?" in augmented_text:
                suspense_phrases = ["你绝对想不到", "接下来的一幕"] if self.language == "zh" else ["You won't believe", "What happens next"]
                suspense = random.choice(suspense_phrases)
                augmented_text = suspense + "..." + augmented_text

            # 3. 节奏调整
            sentences = augmented_text.split("。" if self.language == "zh" else ".")
            if len(sentences) > 2:
                # 随机调整句子顺序（保持逻辑性）
                if random.random() < 0.3:  # 30%概率调整
                    mid_point = len(sentences) // 2
                    sentences = sentences[mid_point:] + sentences[:mid_point]
                    augmented_text = ("。" if self.language == "zh" else ".").join(sentences)

            print(f"🎭 剧情增强完成: {len(plot_text)} -> {len(augmented_text)} 字符")
            return augmented_text

        except Exception as e:
            print(f"❌ 剧情增强失败: {e}")
            return plot_text  # 返回原始文本作为回退


# 为了保持向后兼容性，添加别名
PlotAugment = PlotAugmenter


if __name__ == "__main__":
    # 测试剧情增强器
    augmenter = PlotAugmenter("zh")

    test_plot = """
    第一幕：男主角在公司加班，突然接到神秘电话。
    第二幕：他发现自己被卷入了一个巨大的阴谋。
    第三幕：经过重重困难，他终于揭开了真相。
    """

    print(f"原始剧情: {test_plot}")

    augmented = augmenter.augment_plot(test_plot)
    print(f"增强后剧情: {augmented}")