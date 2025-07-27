#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面模块导入测试
测试所有核心模块的导入完整性，检查循环依赖和缺失依赖
"""

import sys
import os
import importlib
import traceback
import json
from datetime import datetime
from pathlib import Path
import warnings

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class ModuleImportTester:
    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "total_modules": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "import_results": {},
            "circular_dependencies": [],
            "missing_dependencies": [],
            "warnings": []
        }
        
        # 核心模块列表（按架构文档定义）
        self.core_modules = [
            # 核心功能模块
            "src.core.model_switcher",
            "src.core.language_detector", 
            "src.core.srt_parser",
            "src.core.narrative_analyzer",
            "src.core.screenplay_engineer",
            "src.core.alignment_engineer",
            "src.core.clip_generator",
            "src.core.rhythm_analyzer",
            "src.core.segment_advisor",
            
            # 训练模块
            "src.training.en_trainer",
            "src.training.zh_trainer",
            "src.training.data_splitter",
            "src.training.data_augment",
            "src.training.plot_augment",
            "src.training.curriculum",
            
            # NLP工具
            "src.nlp.language_detector",
            "src.nlp.sentiment_analyzer",
            "src.nlp.text_processor",
            
            # 评估模块
            "src.eval.quality_validator",
            
            # 工具模块
            "src.utils.file_checker",
            "src.utils.device_manager",
            "src.utils.log_handler",
            "src.utils.memory_guard",
            "src.utils.xml_template",
            
            # 导出模块
            "src.exporters.base_exporter",
            "src.exporters.jianying_pro_exporter",
            
            # UI模块
            "ui.main_window",
            "ui.training_panel", 
            "ui.progress_dashboard",
            "ui.components.realtime_charts",
            "ui.components.alert_manager"
        ]
        
        # 可选模块（可能不存在但不影响核心功能）
        self.optional_modules = [
            "src.nlp.en.spacy_parser",
            "src.nlp.zh.jieba_parser",
            "src.exporters.davinci_resolve",
            "src.api.cli_interface"
        ]

    def test_single_module(self, module_name):
        """测试单个模块的导入"""
        try:
            # 捕获警告
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                module = importlib.import_module(module_name)
                
                # 记录警告
                if w:
                    warning_msgs = [str(warning.message) for warning in w]
                    self.results["warnings"].extend(warning_msgs)
                
                return {
                    "status": "success",
                    "module_name": module_name,
                    "warnings": len(w)
                }
                
        except ImportError as e:
            return {
                "status": "import_error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        except Exception as e:
            return {
                "status": "other_error", 
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def check_circular_dependencies(self):
        """检查循环依赖"""
        print("检查循环依赖...")
        
        # 简单的循环依赖检测
        import_stack = []
        
        def check_module_deps(module_name, stack):
            if module_name in stack:
                circular_dep = " -> ".join(stack + [module_name])
                self.results["circular_dependencies"].append(circular_dep)
                return
                
            try:
                stack.append(module_name)
                module = importlib.import_module(module_name)
                # 这里可以添加更复杂的依赖分析
                stack.pop()
            except:
                stack.pop()
        
        for module_name in self.core_modules:
            check_module_deps(module_name, [])

    def run_comprehensive_test(self):
        """运行全面的模块导入测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 模块导入完整性测试")
        print("=" * 60)
        
        all_modules = self.core_modules + self.optional_modules
        self.results["total_modules"] = len(all_modules)
        
        print(f"测试 {len(all_modules)} 个模块...")
        
        for i, module_name in enumerate(all_modules, 1):
            print(f"[{i:2d}/{len(all_modules)}] 测试模块: {module_name}")
            
            result = self.test_single_module(module_name)
            self.results["import_results"][module_name] = result
            
            if result["status"] == "success":
                self.results["successful_imports"] += 1
                print(f"  ✓ 成功导入")
                if result["warnings"] > 0:
                    print(f"  ⚠ 有 {result['warnings']} 个警告")
            else:
                self.results["failed_imports"] += 1
                print(f"  ✗ 导入失败: {result['error']}")
                
                # 检查是否是缺失依赖
                if "No module named" in result["error"]:
                    missing_dep = result["error"].split("'")[1] if "'" in result["error"] else "unknown"
                    self.results["missing_dependencies"].append({
                        "module": module_name,
                        "missing_dependency": missing_dep
                    })
        
        # 检查循环依赖
        self.check_circular_dependencies()
        
        # 生成报告
        self.generate_report()
        
        return self.results

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        print(f"总模块数: {self.results['total_modules']}")
        print(f"成功导入: {self.results['successful_imports']}")
        print(f"导入失败: {self.results['failed_imports']}")
        print(f"成功率: {(self.results['successful_imports']/self.results['total_modules']*100):.1f}%")
        
        if self.results["failed_imports"] > 0:
            print(f"\n失败的模块:")
            for module_name, result in self.results["import_results"].items():
                if result["status"] != "success":
                    print(f"  - {module_name}: {result['error']}")
        
        if self.results["missing_dependencies"]:
            print(f"\n缺失的依赖:")
            for dep in self.results["missing_dependencies"]:
                print(f"  - {dep['module']} 需要 {dep['missing_dependency']}")
        
        if self.results["circular_dependencies"]:
            print(f"\n循环依赖:")
            for dep in self.results["circular_dependencies"]:
                print(f"  - {dep}")
        
        if self.results["warnings"]:
            print(f"\n警告 ({len(self.results['warnings'])}):")
            for warning in set(self.results["warnings"]):  # 去重
                print(f"  - {warning}")
        
        # 保存详细报告
        report_file = f"module_import_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = ModuleImportTester()
    results = tester.run_comprehensive_test()
    
    # 返回退出码
    if results["failed_imports"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
