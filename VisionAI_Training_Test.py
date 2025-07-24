#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 训练功能测试
测试投喂训练、中英文独立训练和课程学习策略
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class TrainingFunctionalityTester:
    def __init__(self):
        self.test_results = {
            "test_start_time": datetime.now().isoformat(),
            "training_module_tests": {},
            "data_pipeline_tests": {},
            "curriculum_tests": {},
            "bilingual_tests": {},
            "overall_status": "RUNNING"
        }
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def log_test_result(self, category, test_name, status, details=None, error=None):
        """记录测试结果"""
        result = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.test_results[category][test_name] = result
        print(f"[{status}] {category}.{test_name}: {details.get('message', '') if details else ''}")
        if error:
            print(f"    错误: {error}")
    
    def test_training_modules(self):
        """测试训练模块"""
        print("\n=== 训练模块测试 ===")
        
        # 测试英文训练器
        try:
            from src.training.en_trainer import EnTrainer
            en_trainer = EnTrainer()
            self.log_test_result("training_module_tests", "en_trainer_import", "PASS", 
                               {"message": "英文训练器导入成功"})
            
            # 测试训练器方法
            if hasattr(en_trainer, 'train'):
                self.log_test_result("training_module_tests", "en_trainer_train_method", "PASS", 
                                   {"message": "英文训练器train方法存在"})
            else:
                self.log_test_result("training_module_tests", "en_trainer_train_method", "FAIL", 
                                   {"message": "英文训练器train方法不存在"})
                
        except ImportError as e:
            self.log_test_result("training_module_tests", "en_trainer_import", "FAIL", 
                               {"message": "英文训练器导入失败"}, str(e))
        
        # 测试中文训练器
        try:
            from src.training.zh_trainer import ZhTrainer
            zh_trainer = ZhTrainer()
            self.log_test_result("training_module_tests", "zh_trainer_import", "PASS", 
                               {"message": "中文训练器导入成功"})
            
            # 测试训练器方法
            if hasattr(zh_trainer, 'train'):
                self.log_test_result("training_module_tests", "zh_trainer_train_method", "PASS", 
                                   {"message": "中文训练器train方法存在"})
            else:
                self.log_test_result("training_module_tests", "zh_trainer_train_method", "FAIL", 
                                   {"message": "中文训练器train方法不存在"})
                
        except ImportError as e:
            self.log_test_result("training_module_tests", "zh_trainer_import", "FAIL", 
                               {"message": "中文训练器导入失败"}, str(e))
        
        # 测试模型微调器
        try:
            from src.training.model_fine_tuner import ModelFineTuner
            fine_tuner = ModelFineTuner()
            self.log_test_result("training_module_tests", "model_fine_tuner_import", "PASS", 
                               {"message": "模型微调器导入成功"})
        except ImportError as e:
            self.log_test_result("training_module_tests", "model_fine_tuner_import", "FAIL", 
                               {"message": "模型微调器导入失败"}, str(e))
    
    def test_data_pipeline(self):
        """测试数据处理管道"""
        print("\n=== 数据处理管道测试 ===")
        
        # 测试数据分割器
        try:
            from src.training.data_splitter import DataSplitter
            splitter = DataSplitter()
            self.log_test_result("data_pipeline_tests", "data_splitter_import", "PASS", 
                               {"message": "数据分割器导入成功"})
            
            # 测试分割方法
            if hasattr(splitter, 'split_by_language'):
                self.log_test_result("data_pipeline_tests", "split_by_language_method", "PASS", 
                                   {"message": "split_by_language方法存在"})
            else:
                self.log_test_result("data_pipeline_tests", "split_by_language_method", "FAIL", 
                                   {"message": "split_by_language方法不存在"})
                
        except ImportError as e:
            self.log_test_result("data_pipeline_tests", "data_splitter_import", "FAIL", 
                               {"message": "数据分割器导入失败"}, str(e))
        
        # 测试数据增强器
        try:
            from src.training.data_augment import DataAugment
            augmenter = DataAugment()
            self.log_test_result("data_pipeline_tests", "data_augment_import", "PASS", 
                               {"message": "数据增强器导入成功"})
        except ImportError as e:
            self.log_test_result("data_pipeline_tests", "data_augment_import", "FAIL", 
                               {"message": "数据增强器导入失败"}, str(e))
        
        # 测试剧情增强器
        try:
            from src.training.plot_augment import PlotAugment
            plot_augmenter = PlotAugment()
            self.log_test_result("data_pipeline_tests", "plot_augment_import", "PASS", 
                               {"message": "剧情增强器导入成功"})
        except ImportError as e:
            self.log_test_result("data_pipeline_tests", "plot_augment_import", "FAIL", 
                               {"message": "剧情增强器导入失败"}, str(e))
        
        # 测试数据清洗器
        try:
            from src.training.data_cleaner import DataCleaner
            cleaner = DataCleaner()
            self.log_test_result("data_pipeline_tests", "data_cleaner_import", "PASS", 
                               {"message": "数据清洗器导入成功"})
        except ImportError as e:
            self.log_test_result("data_pipeline_tests", "data_cleaner_import", "FAIL", 
                               {"message": "数据清洗器导入失败"}, str(e))
    
    def test_curriculum_learning(self):
        """测试课程学习"""
        print("\n=== 课程学习测试 ===")
        
        # 测试课程学习策略
        try:
            from src.training.curriculum import CurriculumLearning
            curriculum = CurriculumLearning()
            self.log_test_result("curriculum_tests", "curriculum_learning_import", "PASS", 
                               {"message": "课程学习策略导入成功"})
            
            # 测试课程生成方法
            if hasattr(curriculum, 'generate_curriculum'):
                self.log_test_result("curriculum_tests", "generate_curriculum_method", "PASS", 
                                   {"message": "generate_curriculum方法存在"})
            else:
                self.log_test_result("curriculum_tests", "generate_curriculum_method", "FAIL", 
                                   {"message": "generate_curriculum方法不存在"})
                
        except ImportError as e:
            self.log_test_result("curriculum_tests", "curriculum_learning_import", "FAIL", 
                               {"message": "课程学习策略导入失败"}, str(e))
        
        # 测试训练管理器
        try:
            from src.training.train_manager import TrainManager
            train_mgr = TrainManager()
            self.log_test_result("curriculum_tests", "train_manager_import", "PASS", 
                               {"message": "训练管理器导入成功"})
        except ImportError as e:
            self.log_test_result("curriculum_tests", "train_manager_import", "FAIL", 
                               {"message": "训练管理器导入失败"}, str(e))
    
    def test_bilingual_training(self):
        """测试双语训练功能"""
        print("\n=== 双语训练测试 ===")
        
        # 检查训练数据目录结构
        training_dirs = {
            "en_base": "data/training/en",
            "zh_base": "data/training/zh",
            "en_hit_subtitles": "data/training/en/hit_subtitles",
            "zh_hit_subtitles": "data/training/zh/hit_subtitles",
            "en_raw_pairs": "data/training/en/raw_pairs",
            "zh_raw_pairs": "data/training/zh/raw_pairs"
        }
        
        for dir_name, dir_path in training_dirs.items():
            if os.path.exists(dir_path):
                self.log_test_result("bilingual_tests", f"training_dir_{dir_name}", "PASS", 
                                   {"message": f"训练目录{dir_path}存在"})
            else:
                self.log_test_result("bilingual_tests", f"training_dir_{dir_name}", "FAIL", 
                                   {"message": f"训练目录{dir_path}不存在"})
        
        # 测试训练策略配置
        training_policy_file = "configs/training_policy.yaml"
        if os.path.exists(training_policy_file):
            try:
                import yaml
                with open(training_policy_file, 'r', encoding='utf-8') as f:
                    policy = yaml.safe_load(f)
                
                # 检查是否包含中英文独立训练配置
                if 'en_training' in policy and 'zh_training' in policy:
                    self.log_test_result("bilingual_tests", "bilingual_policy_config", "PASS", 
                                       {"message": "双语训练策略配置完整"})
                else:
                    self.log_test_result("bilingual_tests", "bilingual_policy_config", "FAIL", 
                                       {"message": "双语训练策略配置不完整"})
                    
            except Exception as e:
                self.log_test_result("bilingual_tests", "bilingual_policy_config", "FAIL", 
                                   {"message": "训练策略配置加载失败"}, str(e))
        else:
            self.log_test_result("bilingual_tests", "bilingual_policy_config", "SKIP", 
                               {"message": "训练策略配置文件不存在"})
    
    def generate_report(self):
        """生成测试报告"""
        self.test_results["test_end_time"] = datetime.now().isoformat()
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for category in ["training_module_tests", "data_pipeline_tests", "curriculum_tests", "bilingual_tests"]:
            for test_name, result in self.test_results[category].items():
                total_tests += 1
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
                elif result["status"] == "SKIP":
                    skipped_tests += 1
        
        # 确定整体状态
        if failed_tests > 0:
            self.test_results["overall_status"] = "FAIL"
        elif passed_tests > 0:
            self.test_results["overall_status"] = "PASS"
        else:
            self.test_results["overall_status"] = "SKIP"
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # 保存测试报告
        report_file = self.output_dir / f"training_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 训练功能测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"成功率: {self.test_results['summary']['success_rate']}")
        print(f"整体状态: {self.test_results['overall_status']}")
        print(f"详细报告已保存到: {report_file}")
        
        return self.test_results
    
    def run_all_tests(self):
        """运行所有训练功能测试"""
        print("开始VisionAI-ClipsMaster训练功能测试...")
        print(f"测试开始时间: {self.test_results['test_start_time']}")
        
        try:
            self.test_training_modules()
            self.test_data_pipeline()
            self.test_curriculum_learning()
            self.test_bilingual_training()
        except Exception as e:
            print(f"测试执行异常: {e}")
        finally:
            return self.generate_report()

if __name__ == "__main__":
    training_tester = TrainingFunctionalityTester()
    results = training_tester.run_all_tests()
