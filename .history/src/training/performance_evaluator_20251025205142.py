#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型性能评估器
用于评估训练后模型的性能，支持智能模型选择
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)

class PerformanceEvaluator:
    """模型性能评估器"""
    
    def __init__(self):
        """初始化性能评估器"""
        self.logger = logging.getLogger("PerformanceEvaluator")
    
    def evaluate_model(
        self,
        model_path: str,
        validation_data: Optional[List[Dict[str, Any]]] = None,
        model_type: str = "huggingface"
    ) -> float:
        """
        评估模型性能

        Args:
            model_path: 模型路径
            validation_data: 验证数据集（可选，如果不提供则使用默认测试数据）
            model_type: 模型类型 ("huggingface" 或 "gguf")

        Returns:
            性能分数（0-1之间的浮点数）
        """
        try:
            self.logger.info(f"🔍 开始评估模型: {model_path}")
            self.logger.info(f"   模型类型: {model_type}")

            # 如果没有提供验证数据，使用默认测试数据
            if validation_data is None:
                validation_data = self._get_default_validation_data()
                self.logger.info(f"   使用默认验证数据: {len(validation_data)}条")
            else:
                self.logger.info(f"   验证数据: {len(validation_data)}条")

            start_time = time.time()

            # 根据模型类型选择评估方法
            if model_type == "huggingface":
                result = self._evaluate_hf_model(model_path, validation_data)
            elif model_type == "gguf":
                result = self._evaluate_gguf_model(model_path, validation_data)
            else:
                self.logger.error(f"不支持的模型类型: {model_type}")
                return 0.0

            evaluation_time = time.time() - start_time
            performance_score = result.get('performance_score', 0.0)

            self.logger.info(f"✅ 评估完成，耗时: {evaluation_time:.2f}秒")
            self.logger.info(f"   性能得分: {performance_score:.4f}")

            return performance_score

        except Exception as e:
            self.logger.error(f"❌ 模型评估失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return 0.0

    def _get_default_validation_data(self) -> List[Dict[str, Any]]:
        """
        获取默认的验证数据集

        Returns:
            默认验证数据
        """
        # 使用一些标准的测试样本（格式：original -> viral）
        return [
            {
                "original": "今天天气很好，我去公园散步了。",
                "viral": "今天天气超级棒！我去公园散步，感觉整个人都被治愈了！"
            },
            {
                "original": "我学会了一个新技能。",
                "viral": "太激动了！我终于学会了这个超酷的新技能！"
            },
            {
                "original": "这个产品质量不错。",
                "viral": "这个产品简直太棒了！质量超出预期，强烈推荐！"
            },
            {
                "original": "我今天做了一顿饭。",
                "viral": "今天亲手做了一顿大餐，成就感爆棚！"
            },
            {
                "original": "看了一部电影。",
                "viral": "刚看完这部电影，太震撼了！强烈推荐大家去看！"
            }
        ]
    
    def _evaluate_hf_model(
        self,
        model_path: str,
        validation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估HuggingFace格式模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            # 加载模型
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            # 评估指标
            total_samples = len(validation_data)
            correct_predictions = 0
            total_loss = 0.0
            inference_times = []
            
            # 对每个验证样本进行评估
            for sample in validation_data[:min(50, total_samples)]:  # 限制评估样本数
                original = sample.get("original", "")
                expected_viral = sample.get("viral", "")
                
                # 推理
                start_time = time.time()
                inputs = tokenizer(original, return_tensors="pt", truncation=True, max_length=512)
                outputs = model.generate(**inputs, max_length=512)
                predicted_viral = tokenizer.decode(outputs[0], skip_special_tokens=True)
                inference_time = time.time() - start_time
                
                inference_times.append(inference_time)
                
                # 简单的相似度评估（实际应用中可以使用更复杂的指标）
                similarity = self._calculate_similarity(predicted_viral, expected_viral)
                if similarity > 0.7:  # 阈值
                    correct_predictions += 1
            
            # 计算性能指标
            accuracy = correct_predictions / min(50, total_samples)
            avg_inference_time = sum(inference_times) / len(inference_times)
            
            # 综合性能得分（准确率 * 0.7 + 速度得分 * 0.3）
            speed_score = max(0, 1 - (avg_inference_time / 5.0))  # 5秒为基准
            performance_score = accuracy * 0.7 + speed_score * 0.3
            
            return {
                "success": True,
                "performance_score": performance_score,
                "accuracy": accuracy,
                "avg_inference_time": avg_inference_time,
                "total_samples_evaluated": min(50, total_samples),
                "model_type": "huggingface"
            }
            
        except Exception as e:
            self.logger.error(f"HF模型评估失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _evaluate_gguf_model(
        self,
        model_path: str,
        validation_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估GGUF格式模型"""
        try:
            from llama_cpp import Llama
            
            # 加载模型
            llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4
            )
            
            # 评估指标
            total_samples = len(validation_data)
            correct_predictions = 0
            inference_times = []
            
            # 对每个验证样本进行评估
            for sample in validation_data[:min(50, total_samples)]:
                original = sample.get("original", "")
                expected_viral = sample.get("viral", "")
                
                # 推理
                start_time = time.time()
                response = llm(
                    f"Original script: {original}\nViral script:",
                    max_tokens=512,
                    temperature=0.7,
                    stop=["Original script:", "\n\n"]
                )
                predicted_viral = response["choices"][0]["text"]
                inference_time = time.time() - start_time
                
                inference_times.append(inference_time)
                
                # 相似度评估
                similarity = self._calculate_similarity(predicted_viral, expected_viral)
                if similarity > 0.7:
                    correct_predictions += 1
            
            # 计算性能指标
            accuracy = correct_predictions / min(50, total_samples)
            avg_inference_time = sum(inference_times) / len(inference_times)
            
            # 综合性能得分
            speed_score = max(0, 1 - (avg_inference_time / 3.0))  # GGUF更快，3秒为基准
            performance_score = accuracy * 0.7 + speed_score * 0.3
            
            return {
                "success": True,
                "performance_score": performance_score,
                "accuracy": accuracy,
                "avg_inference_time": avg_inference_time,
                "total_samples_evaluated": min(50, total_samples),
                "model_type": "gguf"
            }
            
        except Exception as e:
            self.logger.error(f"GGUF模型评估失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度得分 (0-1)
        """
        # 简单的基于词重叠的相似度计算
        # 实际应用中可以使用更复杂的方法（如BLEU、ROUGE等）
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def compare_models(
        self,
        model1_path: str,
        model2_path: str,
        validation_data: List[Dict[str, Any]],
        model1_type: str = "huggingface",
        model2_type: str = "huggingface"
    ) -> Dict[str, Any]:
        """
        对比两个模型的性能
        
        Args:
            model1_path: 模型1路径
            model2_path: 模型2路径
            validation_data: 验证数据
            model1_type: 模型1类型
            model2_type: 模型2类型
            
        Returns:
            对比结果
        """
        self.logger.info("🔍 开始对比模型性能...")
        
        # 评估模型1
        result1 = self.evaluate_model(model1_path, validation_data, model1_type)
        
        # 评估模型2
        result2 = self.evaluate_model(model2_path, validation_data, model2_type)
        
        if not result1["success"] or not result2["success"]:
            return {
                "success": False,
                "error": "One or both model evaluations failed"
            }
        
        # 对比结果
        score1 = result1["performance_score"]
        score2 = result2["performance_score"]
        
        improvement = ((score2 - score1) / score1) * 100 if score1 > 0 else 0
        
        return {
            "success": True,
            "model1": result1,
            "model2": result2,
            "improvement_percentage": improvement,
            "better_model": "model2" if score2 > score1 else "model1"
        }

