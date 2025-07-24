#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程学习策略 - 渐进式训练计划
实现从简单到复杂的训练策略，提高模型学习效果
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class CurriculumLearning:
    """课程学习策略 - 渐进式训练管理"""

    def __init__(self, language: str = "zh"):
        """
        初始化课程学习策略

        Args:
            language: 目标语言 (zh/en)
        """
        self.language = language
        self.current_stage = 0
        self.total_stages = 3

        # 定义学习阶段
        self.stages = {
            0: {
                "name": "基础对齐阶段",
                "description": "学习基础时间轴对齐",
                "difficulty": "easy",
                "max_samples": 50,
                "epochs": 2,
                "learning_rate": 5e-5,
                "focus": "alignment"
            },
            1: {
                "name": "结构理解阶段",
                "description": "掌握剧情结构重组",
                "difficulty": "medium",
                "max_samples": 100,
                "epochs": 3,
                "learning_rate": 3e-5,
                "focus": "structure"
            },
            2: {
                "name": "高级重构阶段",
                "description": "掌握非线性叙事结构",
                "difficulty": "hard",
                "max_samples": 200,
                "epochs": 4,
                "learning_rate": 2e-5,
                "focus": "nonlinear"
            }
        }

        # 语言特定配置
        if language == "zh":
            self.language_config = {
                "model_name": "Qwen2.5-7B",
                "quantization": "Q4_K_M",
                "batch_size": 2,
                "special_tokens": ["震撼", "惊呆", "不敢相信", "史上最"]
            }
        else:  # en
            self.language_config = {
                "model_name": "Mistral-7B",
                "quantization": "Q5_K",
                "batch_size": 3,
                "special_tokens": ["SHOCKING", "AMAZING", "UNBELIEVABLE", "INCREDIBLE"]
            }

        print(f"📚 课程学习策略初始化完成")
        print(f"🌍 目标语言: {language}")
        print(f"📊 训练阶段: {self.total_stages}个阶段")
        print(f"🎯 当前阶段: {self.stages[0]['name']}")

    def get_current_stage_config(self) -> Dict[str, Any]:
        """
        获取当前阶段配置

        Returns:
            当前阶段的配置信息
        """
        stage_config = self.stages[self.current_stage].copy()
        stage_config.update(self.language_config)
        stage_config["stage_number"] = self.current_stage
        stage_config["total_stages"] = self.total_stages

        return stage_config

    def filter_data_by_stage(self, training_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据当前阶段过滤训练数据

        Args:
            training_data: 原始训练数据

        Returns:
            适合当前阶段的训练数据
        """
        stage_config = self.stages[self.current_stage]
        target_difficulty = stage_config["difficulty"]
        max_samples = stage_config["max_samples"]

        # 按难度过滤
        filtered_data = []
        for item in training_data:
            item_difficulty = item.get("difficulty", "medium")

            # 阶段0: 只要easy
            # 阶段1: easy + medium
            # 阶段2: 所有难度
            if self.current_stage == 0 and item_difficulty == "easy":
                filtered_data.append(item)
            elif self.current_stage == 1 and item_difficulty in ["easy", "medium"]:
                filtered_data.append(item)
            elif self.current_stage == 2:  # 接受所有难度
                filtered_data.append(item)

        # 限制样本数量
        if len(filtered_data) > max_samples:
            # 优先选择质量分数高的样本
            filtered_data.sort(key=lambda x: x.get("quality_score", 0.5), reverse=True)
            filtered_data = filtered_data[:max_samples]

        return filtered_data

    def should_advance_stage(self, training_result: Dict[str, Any]) -> bool:
        """
        判断是否应该进入下一阶段

        Args:
            training_result: 当前阶段训练结果

        Returns:
            是否应该进入下一阶段
        """
        if not training_result.get("success", False):
            return False

        # 检查准确率阈值
        accuracy = training_result.get("accuracy", 0.0)
        loss = training_result.get("loss", 1.0)

        # 不同阶段的晋级标准
        if self.current_stage == 0:
            # 基础阶段: 准确率>80%, loss<0.4
            return accuracy > 0.80 and loss < 0.4
        elif self.current_stage == 1:
            # 中级阶段: 准确率>85%, loss<0.3
            return accuracy > 0.85 and loss < 0.3
        else:
            # 高级阶段: 已经是最后阶段
            return False

    def advance_to_next_stage(self) -> bool:
        """
        进入下一阶段

        Returns:
            是否成功进入下一阶段
        """
        if self.current_stage < self.total_stages - 1:
            self.current_stage += 1
            next_stage = self.stages[self.current_stage]
            print(f"🎓 进入下一阶段: {next_stage['name']}")
            print(f"📝 阶段描述: {next_stage['description']}")
            return True
        else:
            print("🏆 已完成所有训练阶段！")
            return False

    def generate_curriculum(self, data_complexity_levels: List[str] = None) -> Dict[str, Any]:
        """
        生成课程学习计划

        Args:
            data_complexity_levels: 数据复杂度级别列表

        Returns:
            Dict: 生成的课程计划
        """
        if data_complexity_levels is None:
            data_complexity_levels = ["basic", "intermediate", "advanced"]

        curriculum_plan = {
            "language": self.language,
            "total_stages": self.total_stages,
            "current_stage": self.current_stage,
            "stages": [],
            "complexity_levels": data_complexity_levels,
            "estimated_duration": f"{self.total_stages * 2} hours"
        }

        for stage_id, stage_info in self.stages.items():
            stage_plan = {
                "stage_id": stage_id,
                "name": stage_info["name"],
                "description": stage_info["description"],
                "complexity_level": data_complexity_levels[min(stage_id, len(data_complexity_levels) - 1)],
                "learning_objectives": stage_info.get("objectives", []),
                "estimated_time": "2 hours",
                "difficulty": stage_info.get("difficulty", "medium"),
                "focus": stage_info.get("focus", "general")
            }
            curriculum_plan["stages"].append(stage_plan)

        print(f"📚 已生成 {self.language} 语言的课程学习计划")
        print(f"🎯 总阶段数: {self.total_stages}")
        print(f"⏱️ 预计总时长: {curriculum_plan['estimated_duration']}")

        return curriculum_plan

    def execute_curriculum_training(self, training_data: List[Dict[str, Any]],
                                  trainer_class,
                                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行课程学习训练

        Args:
            training_data: 训练数据
            trainer_class: 训练器类
            progress_callback: 进度回调函数

        Returns:
            完整的训练结果
        """
        curriculum_results = {
            "language": self.language,
            "total_stages": self.total_stages,
            "stage_results": [],
            "overall_success": False,
            "final_accuracy": 0.0,
            "final_loss": 1.0,
            "training_duration": 0
        }

        start_time = time.time()

        try:
            # 重置到第一阶段
            self.current_stage = 0

            while self.current_stage < self.total_stages:
                stage_config = self.get_current_stage_config()
                stage_name = stage_config["name"]

                if progress_callback:
                    overall_progress = self.current_stage / self.total_stages
                    progress_callback(overall_progress, f"开始{stage_name}...")

                print(f"\n🎯 开始{stage_name} (阶段 {self.current_stage + 1}/{self.total_stages})")

                # 过滤适合当前阶段的数据
                stage_data = self.filter_data_by_stage(training_data)
                print(f"📊 阶段数据: {len(stage_data)}个样本 (难度: {stage_config['difficulty']})")

                if not stage_data:
                    print(f"⚠️ 阶段{self.current_stage + 1}没有合适的训练数据，跳过")
                    self.advance_to_next_stage()
                    continue

                # 创建训练器
                trainer = trainer_class(use_gpu=False)

                # 执行阶段训练
                def stage_progress_callback(progress, message):
                    if progress_callback:
                        # 将阶段进度映射到总体进度
                        stage_progress = self.current_stage / self.total_stages + progress / self.total_stages
                        progress_callback(stage_progress, f"{stage_name}: {message}")
                    return True

                stage_result = trainer.train(
                    training_data=stage_data,
                    progress_callback=stage_progress_callback
                )

                # 记录阶段结果
                stage_summary = {
                    "stage": self.current_stage,
                    "stage_name": stage_name,
                    "config": stage_config,
                    "samples_used": len(stage_data),
                    "result": stage_result,
                    "success": stage_result.get("success", False)
                }

                curriculum_results["stage_results"].append(stage_summary)

                if stage_result.get("success", False):
                    accuracy = stage_result.get("accuracy", 0.0)
                    loss = stage_result.get("loss", 1.0)
                    print(f"✅ {stage_name}完成: 准确率{accuracy:.1%}, 损失{loss:.3f}")

                    # 更新最终指标
                    curriculum_results["final_accuracy"] = accuracy
                    curriculum_results["final_loss"] = loss

                    # 检查是否可以进入下一阶段
                    if self.should_advance_stage(stage_result):
                        if not self.advance_to_next_stage():
                            break  # 已完成所有阶段
                    else:
                        print(f"⚠️ {stage_name}未达到晋级标准，重复训练")
                        # 可以选择重复当前阶段或调整参数
                        break
                else:
                    print(f"❌ {stage_name}失败: {stage_result.get('error', '未知错误')}")
                    break

            # 判断整体成功
            curriculum_results["overall_success"] = (
                len(curriculum_results["stage_results"]) > 0 and
                all(stage["success"] for stage in curriculum_results["stage_results"])
            )

            end_time = time.time()
            curriculum_results["training_duration"] = end_time - start_time

            if progress_callback:
                progress_callback(1.0, "课程学习训练完成！")

            return curriculum_results

        except Exception as e:
            curriculum_results["error"] = str(e)
            curriculum_results["overall_success"] = False

            if progress_callback:
                progress_callback(1.0, f"课程学习训练失败: {str(e)}")

            return curriculum_results

    def get_training_summary(self) -> Dict[str, Any]:
        """
        获取训练总结

        Returns:
            训练总结信息
        """
        return {
            "language": self.language,
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "completed_stages": self.current_stage,
            "progress_percentage": (self.current_stage / self.total_stages) * 100,
            "next_stage": self.stages.get(self.current_stage + 1, {}).get("name", "已完成"),
            "language_config": self.language_config
        }

    def get_current_stage(self) -> Dict[str, Any]:
        """
        获取当前阶段信息 - 为测试兼容性添加

        Returns:
            当前阶段的详细信息
        """
        return self.stages.get(self.current_stage, {})

    def advance_stage(self) -> Dict[str, Any]:
        """
        推进到下一阶段 - 为测试兼容性添加

        Returns:
            新的当前阶段信息
        """
        if self.current_stage < self.total_stages - 1:
            self.current_stage += 1
        return self.get_current_stage()

# 为了兼容性，提供别名
Curriculum = CurriculumLearning