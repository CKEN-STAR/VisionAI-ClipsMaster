#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模型加载测试
测试双模型系统的加载和切换功能
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

class ModelLoadingTest:
    """模型加载测试类"""
    
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
    
    def test_model_files_existence(self):
        """测试模型文件是否存在"""
        print("\n🔍 检查模型文件...")
        
        # 检查模型目录结构
        model_paths = {
            "mistral_quantized": "models/mistral/quantized/Q4_K_M.gguf",
            "qwen_base": "models/qwen/base",
            "qwen_quantized": "models/qwen/quantized",
            "model_config": "configs/model_config.yaml"
        }
        
        for name, path in model_paths.items():
            if os.path.exists(path):
                if os.path.isfile(path):
                    size_mb = os.path.getsize(path) / (1024*1024)
                    self.log_result(f"model_file_{name}", "PASS", 
                                  f"文件存在，大小: {size_mb:.1f}MB")
                else:
                    self.log_result(f"model_dir_{name}", "PASS", "目录存在")
            else:
                self.log_result(f"model_{name}", "FAIL", "文件/目录不存在")
    
    def test_model_config_loading(self):
        """测试模型配置加载"""
        print("\n⚙️ 测试模型配置...")
        
        try:
            # 测试配置文件加载
            from src.core.model_loader import ModelLoader
            loader = ModelLoader()
            
            self.log_result("model_loader_init", "PASS", "模型加载器初始化成功")
            
            # 测试配置解析
            if hasattr(loader, 'load_config'):
                config = loader.load_config()
                self.log_result("config_loading", "PASS", 
                              f"配置加载成功，包含 {len(config)} 项")
            else:
                self.log_result("config_loading", "WARN", "配置加载方法不可用")
                
        except Exception as e:
            self.log_result("model_loader_init", "FAIL", "", str(e))
    
    def test_language_detection(self):
        """测试语言检测功能"""
        print("\n🌐 测试语言检测...")
        
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            # 测试中英文检测
            test_texts = {
                "chinese": "今天天气很好，我去了公园散步。",
                "english": "Today is a beautiful day, I went for a walk in the park.",
                "mixed": "今天的weather很好，I went to the park。"
            }
            
            results = {}
            for lang, text in test_texts.items():
                try:
                    detected = detector.detect_language(text)
                    results[lang] = detected
                    self.log_result(f"language_detection_{lang}", "PASS", 
                                  f"检测结果: {detected}")
                except Exception as e:
                    self.log_result(f"language_detection_{lang}", "FAIL", "", str(e))
            
            # 检测准确性
            if results.get("chinese") == "zh" and results.get("english") == "en":
                self.log_result("language_detection_accuracy", "PASS", "检测准确性良好")
            else:
                self.log_result("language_detection_accuracy", "WARN", 
                              f"检测结果: {results}")
                
        except Exception as e:
            self.log_result("language_detector_init", "FAIL", "", str(e))
    
    def test_model_switching(self):
        """测试模型切换功能"""
        print("\n🔄 测试模型切换...")
        
        try:
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()
            
            self.log_result("model_switcher_init", "PASS", "模型切换器初始化成功")
            
            # 测试切换方法
            methods = ['switch_to_chinese', 'switch_to_english', 'get_current_model']
            available_methods = []
            
            for method in methods:
                if hasattr(switcher, method):
                    available_methods.append(method)
            
            self.log_result("model_switcher_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
            # 测试内存使用
            if hasattr(switcher, 'get_memory_usage'):
                memory_usage = switcher.get_memory_usage()
                self.log_result("memory_monitoring", "PASS", 
                              f"内存使用: {memory_usage}MB")
            else:
                self.log_result("memory_monitoring", "WARN", "内存监控不可用")
                
        except Exception as e:
            self.log_result("model_switcher_init", "FAIL", "", str(e))
    
    def test_quantization_support(self):
        """测试量化支持"""
        print("\n⚡ 测试量化支持...")
        
        try:
            # 检查量化配置
            config_path = "configs/model_config.yaml"
            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                if 'quantization' in config:
                    quant_levels = config['quantization'].get('available_levels', {})
                    self.log_result("quantization_config", "PASS", 
                                  f"支持 {len(quant_levels)} 种量化级别")
                    
                    # 检查内存自适应
                    if 'memory_adaptive_levels' in config['quantization']:
                        self.log_result("adaptive_quantization", "PASS", 
                                      "支持内存自适应量化")
                    else:
                        self.log_result("adaptive_quantization", "WARN", 
                                      "不支持内存自适应量化")
                else:
                    self.log_result("quantization_config", "FAIL", "量化配置缺失")
            else:
                self.log_result("quantization_config", "FAIL", "配置文件不存在")
                
        except Exception as e:
            self.log_result("quantization_test", "FAIL", "", str(e))
    
    def test_memory_constraints(self):
        """测试内存限制"""
        print("\n💾 测试内存限制...")
        
        try:
            import psutil
            
            # 获取系统内存信息
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            
            self.log_result("system_memory", "PASS", 
                          f"总内存: {total_gb:.1f}GB, 可用: {available_gb:.1f}GB")
            
            # 检查是否满足4GB设备要求
            if available_gb >= 3.5:
                self.log_result("memory_requirement", "PASS", 
                              "满足4GB设备内存要求")
            else:
                self.log_result("memory_requirement", "WARN", 
                              "可用内存不足，可能影响模型加载")
            
            # 测试内存监控
            try:
                from src.utils.memory_guard import MemoryGuard
                guard = MemoryGuard()
                self.log_result("memory_guard", "PASS", "内存监控器可用")
            except:
                self.log_result("memory_guard", "WARN", "内存监控器不可用")
                
        except Exception as e:
            self.log_result("memory_test", "FAIL", "", str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎬 开始VisionAI-ClipsMaster 模型加载测试")
        print("=" * 60)
        
        self.test_model_files_existence()
        self.test_model_config_loading()
        self.test_language_detection()
        self.test_model_switching()
        self.test_quantization_support()
        self.test_memory_constraints()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 模型加载测试报告")
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
        report_file = f"model_loading_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存至: {report_file}")

if __name__ == "__main__":
    test = ModelLoadingTest()
    test.run_all_tests()
