#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练质量指标测试模块
实现BLEU分数、剧情连贯性评分、时间轴准确性等量化指标
"""

import os
import sys
import json
import re
import math
import logging
import unittest
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import Counter

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.training.en_trainer import EnTrainer
from src.training.zh_trainer import ZhTrainer

class QualityMetricsTest(unittest.TestCase):
    """训练质量指标测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.test_results = {}
        
        # 创建测试数据和参考答案
        self.test_cases_en = self._create_english_test_cases()
        self.test_cases_zh = self._create_chinese_test_cases()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _create_english_test_cases(self) -> List[Dict[str, Any]]:
        """创建英文测试用例"""
        return [
            {
                "original": "John went to the store to buy groceries. He picked up milk, bread, and eggs.",
                "reference_viral": "SHOCKING grocery run! John's INCREDIBLE store visit will BLOW YOUR MIND! What he bought next is UNBELIEVABLE!",
                "expected_features": ["SHOCKING", "INCREDIBLE", "BLOW YOUR MIND", "UNBELIEVABLE"],
                "timeline": [
                    {"start": 0, "end": 3, "text": "John went to the store"},
                    {"start": 3, "end": 6, "text": "to buy groceries"},
                    {"start": 6, "end": 10, "text": "He picked up milk, bread, and eggs"}
                ]
            },
            {
                "original": "The weather was beautiful today. Sarah decided to go for a walk in the park.",
                "reference_viral": "AMAZING weather transformation! Sarah's park adventure will CHANGE EVERYTHING you know about perfect days!",
                "expected_features": ["AMAZING", "CHANGE EVERYTHING", "perfect"],
                "timeline": [
                    {"start": 0, "end": 4, "text": "The weather was beautiful today"},
                    {"start": 4, "end": 8, "text": "Sarah decided to go for a walk in the park"}
                ]
            }
        ]
    
    def _create_chinese_test_cases(self) -> List[Dict[str, Any]]:
        """创建中文测试用例"""
        return [
            {
                "original": "小明今天去学校上课。他学了数学和语文两门课程。",
                "reference_viral": "震撼！小明的学校之旅太精彩了！这两门课程的学习效果不敢相信，改变一切！",
                "expected_features": ["震撼", "太精彩", "不敢相信", "改变一切"],
                "timeline": [
                    {"start": 0, "end": 3, "text": "小明今天去学校上课"},
                    {"start": 3, "end": 7, "text": "他学了数学和语文两门课程"}
                ]
            },
            {
                "original": "妈妈在厨房做饭。她做了红烧肉和青菜。全家人都很开心。",
                "reference_viral": "惊呆了！妈妈的厨艺史上最强！这道菜的秘密太震撼，全家反应改变一切！",
                "expected_features": ["惊呆了", "史上最强", "太震撼", "改变一切"],
                "timeline": [
                    {"start": 0, "end": 2, "text": "妈妈在厨房做饭"},
                    {"start": 2, "end": 5, "text": "她做了红烧肉和青菜"},
                    {"start": 5, "end": 7, "text": "全家人都很开心"}
                ]
            }
        ]
    
    def test_bleu_score_calculation(self):
        """测试BLEU分数计算"""
        self.logger.info("开始BLEU分数计算测试...")
        
        results = {}
        
        # 测试英文BLEU分数
        en_trainer = EnTrainer(use_gpu=False)
        for i, test_case in enumerate(self.test_cases_en):
            # 模拟生成文本（实际应该是训练后的模型生成）
            generated_text = f"AMAZING story about {test_case['original'][:20]}... INCREDIBLE results!"
            
            bleu_score = self._calculate_bleu_score(
                reference=test_case["reference_viral"],
                candidate=generated_text
            )
            
            results[f"english_case_{i+1}"] = {
                "bleu_score": bleu_score,
                "reference": test_case["reference_viral"],
                "generated": generated_text
            }
            
            # 验证BLEU分数在合理范围内
            self.assertGreaterEqual(bleu_score, 0.0, "BLEU分数不能为负")
            self.assertLessEqual(bleu_score, 1.0, "BLEU分数不能超过1.0")
        
        # 测试中文BLEU分数
        zh_trainer = ZhTrainer(use_gpu=False)
        for i, test_case in enumerate(self.test_cases_zh):
            # 模拟生成文本
            generated_text = f"震撼！{test_case['original'][:10]}的故事太精彩了！改变一切！"
            
            bleu_score = self._calculate_bleu_score(
                reference=test_case["reference_viral"],
                candidate=generated_text
            )
            
            results[f"chinese_case_{i+1}"] = {
                "bleu_score": bleu_score,
                "reference": test_case["reference_viral"],
                "generated": generated_text
            }
            
            # 验证BLEU分数在合理范围内
            self.assertGreaterEqual(bleu_score, 0.0, "BLEU分数不能为负")
            self.assertLessEqual(bleu_score, 1.0, "BLEU分数不能超过1.0")
        
        self.test_results["bleu_scores"] = results
        self.logger.info("BLEU分数计算测试完成")
    
    def test_coherence_scoring(self):
        """测试剧情连贯性评分"""
        self.logger.info("开始剧情连贯性评分测试...")
        
        results = {}
        
        # 测试英文连贯性
        for i, test_case in enumerate(self.test_cases_en):
            coherence_score = self._calculate_coherence_score(
                original=test_case["original"],
                viral=test_case["reference_viral"],
                language="en"
            )
            
            results[f"english_coherence_{i+1}"] = {
                "coherence_score": coherence_score,
                "original": test_case["original"],
                "viral": test_case["reference_viral"]
            }
            
            # 验证连贯性分数在合理范围内
            self.assertGreaterEqual(coherence_score, 0.0, "连贯性分数不能为负")
            self.assertLessEqual(coherence_score, 1.0, "连贯性分数不能超过1.0")
        
        # 测试中文连贯性
        for i, test_case in enumerate(self.test_cases_zh):
            coherence_score = self._calculate_coherence_score(
                original=test_case["original"],
                viral=test_case["reference_viral"],
                language="zh"
            )
            
            results[f"chinese_coherence_{i+1}"] = {
                "coherence_score": coherence_score,
                "original": test_case["original"],
                "viral": test_case["reference_viral"]
            }
            
            # 验证连贯性分数在合理范围内
            self.assertGreaterEqual(coherence_score, 0.0, "连贯性分数不能为负")
            self.assertLessEqual(coherence_score, 1.0, "连贯性分数不能超过1.0")
        
        self.test_results["coherence_scores"] = results
        self.logger.info("剧情连贯性评分测试完成")
    
    def test_timeline_accuracy(self):
        """测试时间轴准确性"""
        self.logger.info("开始时间轴准确性测试...")
        
        results = {}
        
        for i, test_case in enumerate(self.test_cases_en + self.test_cases_zh):
            # 模拟生成的时间轴
            generated_timeline = self._simulate_generated_timeline(test_case["timeline"])
            
            accuracy = self._calculate_timeline_accuracy(
                reference_timeline=test_case["timeline"],
                generated_timeline=generated_timeline
            )
            
            results[f"timeline_case_{i+1}"] = {
                "accuracy": accuracy,
                "reference_timeline": test_case["timeline"],
                "generated_timeline": generated_timeline
            }
            
            # 验证时间轴准确性在合理范围内
            self.assertGreaterEqual(accuracy, 0.0, "时间轴准确性不能为负")
            self.assertLessEqual(accuracy, 1.0, "时间轴准确性不能超过1.0")
            
            # 验证准确性达到最低要求（≥0.5秒精度）
            self.assertGreaterEqual(accuracy, 0.8, "时间轴准确性低于要求")
        
        self.test_results["timeline_accuracy"] = results
        self.logger.info("时间轴准确性测试完成")
    
    def test_viral_feature_detection(self):
        """测试爆款特征检测"""
        self.logger.info("开始爆款特征检测测试...")
        
        results = {}
        
        # 测试英文爆款特征
        for i, test_case in enumerate(self.test_cases_en):
            viral_score = self._calculate_viral_feature_score(
                text=test_case["reference_viral"],
                expected_features=test_case["expected_features"],
                language="en"
            )
            
            results[f"english_viral_{i+1}"] = {
                "viral_score": viral_score,
                "text": test_case["reference_viral"],
                "expected_features": test_case["expected_features"]
            }
            
            # 验证爆款特征分数
            self.assertGreaterEqual(viral_score, 0.5, "爆款特征分数过低")
        
        # 测试中文爆款特征
        for i, test_case in enumerate(self.test_cases_zh):
            viral_score = self._calculate_viral_feature_score(
                text=test_case["reference_viral"],
                expected_features=test_case["expected_features"],
                language="zh"
            )
            
            results[f"chinese_viral_{i+1}"] = {
                "viral_score": viral_score,
                "text": test_case["reference_viral"],
                "expected_features": test_case["expected_features"]
            }
            
            # 验证爆款特征分数
            self.assertGreaterEqual(viral_score, 0.5, "爆款特征分数过低")
        
        self.test_results["viral_features"] = results
        self.logger.info("爆款特征检测测试完成")
    
    def _calculate_bleu_score(self, reference: str, candidate: str) -> float:
        """计算BLEU分数"""
        try:
            # 简化的BLEU计算（实际应该使用nltk.translate.bleu_score）
            ref_tokens = reference.lower().split()
            cand_tokens = candidate.lower().split()
            
            if not cand_tokens:
                return 0.0
            
            # 计算1-gram到4-gram的精确度
            precisions = []
            for n in range(1, 5):
                ref_ngrams = self._get_ngrams(ref_tokens, n)
                cand_ngrams = self._get_ngrams(cand_tokens, n)
                
                if not cand_ngrams:
                    precisions.append(0.0)
                    continue
                
                matches = sum((ref_ngrams & cand_ngrams).values())
                total = sum(cand_ngrams.values())
                precision = matches / total if total > 0 else 0.0
                precisions.append(precision)
            
            # 计算几何平均
            if all(p > 0 for p in precisions):
                bleu = math.exp(sum(math.log(p) for p in precisions) / len(precisions))
            else:
                bleu = 0.0
            
            # 简化的长度惩罚
            bp = min(1.0, len(cand_tokens) / len(ref_tokens)) if ref_tokens else 0.0
            
            return bleu * bp
            
        except Exception as e:
            self.logger.error(f"BLEU分数计算失败: {e}")
            return 0.0
    
    def _get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """获取n-gram"""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i+n]))
        return Counter(ngrams)
    
    def _calculate_coherence_score(self, original: str, viral: str, language: str) -> float:
        """计算剧情连贯性分数"""
        try:
            # 提取关键词
            if language == "en":
                orig_keywords = re.findall(r'\b[a-zA-Z]+\b', original.lower())
                viral_keywords = re.findall(r'\b[a-zA-Z]+\b', viral.lower())
            else:  # zh
                orig_keywords = list(original)
                viral_keywords = list(viral)
            
            # 计算关键词重叠度
            orig_set = set(orig_keywords)
            viral_set = set(viral_keywords)
            
            if not orig_set:
                return 0.0
            
            overlap = len(orig_set & viral_set)
            coherence = overlap / len(orig_set)
            
            return min(1.0, coherence)
            
        except Exception as e:
            self.logger.error(f"连贯性分数计算失败: {e}")
            return 0.0
    
    def _calculate_timeline_accuracy(self, reference_timeline: List[Dict], 
                                   generated_timeline: List[Dict]) -> float:
        """计算时间轴准确性"""
        try:
            if not reference_timeline or not generated_timeline:
                return 0.0
            
            total_error = 0.0
            count = 0
            
            for ref_seg, gen_seg in zip(reference_timeline, generated_timeline):
                # 计算开始时间误差
                start_error = abs(ref_seg["start"] - gen_seg["start"])
                end_error = abs(ref_seg["end"] - gen_seg["end"])
                
                total_error += start_error + end_error
                count += 2
            
            if count == 0:
                return 0.0
            
            avg_error = total_error / count
            
            # 转换为准确性分数（误差越小，准确性越高）
            # 假设0.5秒误差对应0.8的准确性
            accuracy = max(0.0, 1.0 - (avg_error / 0.5))
            
            return min(1.0, accuracy)
            
        except Exception as e:
            self.logger.error(f"时间轴准确性计算失败: {e}")
            return 0.0
    
    def _simulate_generated_timeline(self, reference_timeline: List[Dict]) -> List[Dict]:
        """模拟生成的时间轴（添加小幅偏差）"""
        import random
        
        generated = []
        for seg in reference_timeline:
            # 添加±0.3秒的随机偏差
            start_offset = random.uniform(-0.3, 0.3)
            end_offset = random.uniform(-0.3, 0.3)
            
            generated.append({
                "start": max(0, seg["start"] + start_offset),
                "end": seg["end"] + end_offset,
                "text": seg["text"]
            })
        
        return generated
    
    def _calculate_viral_feature_score(self, text: str, expected_features: List[str], 
                                     language: str) -> float:
        """计算爆款特征分数"""
        try:
            text_upper = text.upper()
            found_features = 0
            
            for feature in expected_features:
                if feature.upper() in text_upper:
                    found_features += 1
            
            # 基础分数
            base_score = found_features / len(expected_features) if expected_features else 0.0
            
            # 额外的爆款特征检测
            if language == "en":
                viral_patterns = ["SHOCKING", "AMAZING", "INCREDIBLE", "UNBELIEVABLE", "MIND-BLOWING"]
            else:  # zh
                viral_patterns = ["震撼", "惊呆", "不敢相信", "史上最", "太精彩", "改变一切"]
            
            bonus_features = sum(1 for pattern in viral_patterns if pattern in text_upper)
            bonus_score = min(0.3, bonus_features * 0.1)  # 最多30%奖励
            
            return min(1.0, base_score + bonus_score)
            
        except Exception as e:
            self.logger.error(f"爆款特征分数计算失败: {e}")
            return 0.0
    
    def tearDown(self):
        """测试清理"""
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"quality_metrics_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"质量指标测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
