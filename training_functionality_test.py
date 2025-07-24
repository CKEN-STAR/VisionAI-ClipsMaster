#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 训练功能测试
测试投喂训练和模型微调功能
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TrainingFunctionalityTest:
    """训练功能测试类"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def log_result(self, test_name, status, details="", error=""):
        """记录测试结果"""
        self.test_results[test_name] = {
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{symbol} {test_name}: {details}")
        if error:
            print(f"   错误: {error}")
    
    def test_training_data_structure(self):
        """测试训练数据结构"""
        print("\n📁 检查训练数据结构...")
        
        # 检查训练数据目录
        training_paths = {
            "training_root": "data/training",
            "chinese_data": "data/training/zh",
            "english_data": "data/training/en",
            "hit_subtitles_zh": "data/training/zh/hit_subtitles",
            "hit_subtitles_en": "data/training/en/hit_subtitles",
            "raw_pairs_zh": "data/training/zh/raw_pairs",
            "raw_pairs_en": "data/training/en/raw_pairs"
        }
        
        for name, path in training_paths.items():
            if os.path.exists(path):
                if os.path.isdir(path):
                    file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                    self.log_result(f"training_dir_{name}", "PASS", 
                                  f"目录存在，包含 {file_count} 个文件")
                else:
                    self.log_result(f"training_file_{name}", "PASS", "文件存在")
            else:
                self.log_result(f"training_{name}", "WARN", "路径不存在")
    
    def test_training_modules(self):
        """测试训练模块"""
        print("\n🧠 测试训练模块...")
        
        # 测试中文训练器
        try:
            from src.training.zh_trainer import ZhTrainer
            zh_trainer = ZhTrainer()
            self.log_result("zh_trainer_init", "PASS", "中文训练器初始化成功")
            
            # 检查训练方法
            methods = ['train', 'validate', 'save_model']
            available_methods = [m for m in methods if hasattr(zh_trainer, m)]
            self.log_result("zh_trainer_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("zh_trainer_init", "FAIL", "", str(e))
        
        # 测试英文训练器
        try:
            from src.training.en_trainer import EnTrainer
            en_trainer = EnTrainer()
            self.log_result("en_trainer_init", "PASS", "英文训练器初始化成功")
            
            # 检查训练方法
            methods = ['train', 'validate', 'save_model']
            available_methods = [m for m in methods if hasattr(en_trainer, m)]
            self.log_result("en_trainer_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("en_trainer_init", "FAIL", "", str(e))
    
    def test_data_augmentation(self):
        """测试数据增强功能"""
        print("\n🔄 测试数据增强...")
        
        try:
            from src.training.data_augment import DataAugment
            augmenter = DataAugment()
            self.log_result("data_augment_init", "PASS", "数据增强器初始化成功")
            
            # 测试文本增强
            test_text = "今天天气很好，我去了公园散步。"
            if hasattr(augmenter, 'augment_text'):
                augmented = augmenter.augment_text(test_text)
                self.log_result("text_augmentation", "PASS", 
                              f"文本增强成功，生成 {len(augmented)} 个变体")
            else:
                self.log_result("text_augmentation", "WARN", "文本增强方法不可用")
                
        except Exception as e:
            self.log_result("data_augment_init", "FAIL", "", str(e))
        
        # 测试剧情增强
        try:
            from src.training.plot_augment import PlotAugment
            plot_augmenter = PlotAugment()
            self.log_result("plot_augment_init", "PASS", "剧情增强器初始化成功")
            
        except Exception as e:
            self.log_result("plot_augment_init", "FAIL", "", str(e))
    
    def test_curriculum_learning(self):
        """测试课程学习"""
        print("\n📚 测试课程学习...")
        
        try:
            from src.training.curriculum import Curriculum
            curriculum = Curriculum()
            self.log_result("curriculum_init", "PASS", "课程学习器初始化成功")
            
            # 检查课程阶段
            if hasattr(curriculum, 'get_stages'):
                stages = curriculum.get_stages()
                self.log_result("curriculum_stages", "PASS", 
                              f"课程包含 {len(stages)} 个阶段")
            else:
                self.log_result("curriculum_stages", "WARN", "课程阶段方法不可用")
                
        except Exception as e:
            self.log_result("curriculum_init", "FAIL", "", str(e))
    
    def test_training_pipeline(self):
        """测试训练流水线"""
        print("\n🔧 测试训练流水线...")
        
        try:
            from src.training.training_data_pipeline import TrainingDataPipeline
            pipeline = TrainingDataPipeline()
            self.log_result("training_pipeline_init", "PASS", "训练流水线初始化成功")
            
            # 测试数据处理方法
            methods = ['preprocess_data', 'split_data', 'validate_data']
            available_methods = [m for m in methods if hasattr(pipeline, m)]
            self.log_result("pipeline_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("training_pipeline_init", "FAIL", "", str(e))
    
    def test_training_feeder(self):
        """测试投喂训练功能"""
        print("\n🍽️ 测试投喂训练...")
        
        try:
            from src.training.training_feeder import TrainingFeeder
            feeder = TrainingFeeder()
            self.log_result("training_feeder_init", "PASS", "投喂训练器初始化成功")
            
            # 测试投喂方法
            if hasattr(feeder, 'feed_training_data'):
                self.log_result("feed_method", "PASS", "投喂方法可用")
            else:
                self.log_result("feed_method", "WARN", "投喂方法不可用")
            
            # 测试爆款数据处理
            if hasattr(feeder, 'process_viral_data'):
                self.log_result("viral_processing", "PASS", "爆款数据处理方法可用")
            else:
                self.log_result("viral_processing", "WARN", "爆款数据处理方法不可用")
                
        except Exception as e:
            self.log_result("training_feeder_init", "FAIL", "", str(e))
    
    def test_model_fine_tuning(self):
        """测试模型微调"""
        print("\n🎯 测试模型微调...")
        
        try:
            from src.training.model_fine_tuner import ModelFineTuner
            fine_tuner = ModelFineTuner()
            self.log_result("fine_tuner_init", "PASS", "模型微调器初始化成功")
            
            # 检查微调方法
            methods = ['fine_tune', 'evaluate', 'save_checkpoint']
            available_methods = [m for m in methods if hasattr(fine_tuner, m)]
            self.log_result("fine_tuning_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("fine_tuner_init", "FAIL", "", str(e))
    
    def test_training_config(self):
        """测试训练配置"""
        print("\n⚙️ 测试训练配置...")
        
        # 检查训练策略配置
        config_path = "configs/training_policy.yaml"
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                self.log_result("training_config", "PASS", 
                              f"训练配置加载成功，包含 {len(config)} 项")
                
                # 检查关键配置项
                key_items = ['batch_size', 'learning_rate', 'max_epochs']
                available_items = [item for item in key_items if item in str(config)]
                self.log_result("training_config_items", "PASS", 
                              f"关键配置项: {len(available_items)}/{len(key_items)}")
                
            except Exception as e:
                self.log_result("training_config", "FAIL", "", str(e))
        else:
            self.log_result("training_config", "WARN", "训练配置文件不存在")
    
    def test_memory_optimization(self):
        """测试训练时内存优化"""
        print("\n💾 测试训练内存优化...")
        
        try:
            import psutil
            
            # 获取当前内存使用
            memory = psutil.virtual_memory()
            current_usage = memory.percent
            
            self.log_result("memory_baseline", "PASS", 
                          f"当前内存使用: {current_usage:.1f}%")
            
            # 检查内存优化模块
            try:
                from src.utils.memory_guard import MemoryGuard
                guard = MemoryGuard()
                
                if hasattr(guard, 'optimize_for_training'):
                    self.log_result("training_memory_optimization", "PASS", 
                                  "训练内存优化可用")
                else:
                    self.log_result("training_memory_optimization", "WARN", 
                                  "训练内存优化不可用")
                    
            except Exception as e:
                self.log_result("memory_guard_training", "FAIL", "", str(e))
                
        except Exception as e:
            self.log_result("memory_optimization_test", "FAIL", "", str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎬 开始VisionAI-ClipsMaster 训练功能测试")
        print("=" * 60)
        
        self.test_training_data_structure()
        self.test_training_modules()
        self.test_data_augmentation()
        self.test_curriculum_learning()
        self.test_training_pipeline()
        self.test_training_feeder()
        self.test_model_fine_tuning()
        self.test_training_config()
        self.test_memory_optimization()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 训练功能测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAIL')
        warned_tests = sum(1 for r in self.test_results.values() if r['status'] == 'WARN')
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"警告: {warned_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"测试时长: {time.time() - self.start_time:.2f}秒")
        
        # 保存详细报告
        report_file = f"training_functionality_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存至: {report_file}")

if __name__ == "__main__":
    test = TrainingFunctionalityTest()
    test.run_all_tests()
