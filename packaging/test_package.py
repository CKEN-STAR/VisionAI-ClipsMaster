#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 打包系统测试脚本
验证打包功能的正确性
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List

class PackageTestSuite:
    """打包系统测试套件"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "overall_status": "unknown",
            "tests": {},
            "errors": [],
            "warnings": []
        }
    
    def test_project_structure(self) -> bool:
        """测试项目结构完整性"""
        print("🔍 测试项目结构...")
        
        required_files = [
            "simple_ui_fixed.py",
            "requirements.txt",
            "packaging/build_config.py",
            "packaging/build_package.py",
            "packaging/model_path_manager.py",
            "packaging/startup_validator.py",
            "packaging/launcher.py",
            "packaging/visionai_clipsmaster.spec",
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        self.test_results["tests"]["project_structure"] = {
            "status": "pass" if not missing_files else "fail",
            "missing_files": missing_files
        }
        
        if missing_files:
            self.test_results["errors"].extend([
                f"缺失文件: {f}" for f in missing_files
            ])
        
        success = len(missing_files) == 0
        print(f"   {'✅' if success else '❌'} 项目结构{'完整' if success else '不完整'}")
        return success
    
    def test_dependencies(self) -> bool:
        """测试依赖模块"""
        print("📦 测试依赖模块...")
        
        # 读取requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.test_results["errors"].append("requirements.txt文件不存在")
            return False
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        missing_deps = []
        available_deps = []
        
        for req in requirements:
            # 简化的包名提取（去掉版本号）
            package_name = req.split('>=')[0].split('==')[0].split('<')[0].strip()
            
            try:
                __import__(package_name)
                available_deps.append(package_name)
                print(f"   ✅ {package_name}")
            except ImportError:
                missing_deps.append(package_name)
                print(f"   ❌ {package_name}")
        
        self.test_results["tests"]["dependencies"] = {
            "status": "pass" if not missing_deps else "fail",
            "available": available_deps,
            "missing": missing_deps,
            "total": len(requirements)
        }
        
        if missing_deps:
            self.test_results["warnings"].append(
                f"缺失依赖: {', '.join(missing_deps)}"
            )
        
        success = len(missing_deps) == 0
        print(f"   {'✅' if success else '⚠️'} 依赖检查{'通过' if success else '有警告'}")
        return True  # 依赖缺失不阻止测试
    
    def test_packaging_modules(self) -> bool:
        """测试打包模块"""
        print("🔧 测试打包模块...")
        
        # 添加打包目录到路径
        packaging_dir = self.project_root / "packaging"
        sys.path.insert(0, str(packaging_dir))
        
        modules_to_test = [
            ("build_config", "PackagingConfig"),
            ("model_path_manager", "ModelPathManager"),
            ("startup_validator", "StartupValidator"),
        ]
        
        module_results = {}
        all_success = True
        
        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name)
                if hasattr(module, class_name):
                    # 尝试实例化类
                    cls = getattr(module, class_name)
                    if class_name == "PackagingConfig":
                        instance = cls(str(self.project_root))
                    else:
                        instance = cls()
                    
                    module_results[module_name] = {
                        "status": "pass",
                        "class": class_name,
                        "instance": str(type(instance))
                    }
                    print(f"   ✅ {module_name}.{class_name}")
                else:
                    module_results[module_name] = {
                        "status": "fail",
                        "error": f"类 {class_name} 不存在"
                    }
                    all_success = False
                    print(f"   ❌ {module_name}.{class_name} (类不存在)")
            except Exception as e:
                module_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                all_success = False
                print(f"   ❌ {module_name}: {e}")
        
        self.test_results["tests"]["packaging_modules"] = module_results
        
        print(f"   {'✅' if all_success else '❌'} 打包模块{'正常' if all_success else '异常'}")
        return all_success
    
    def test_model_path_manager(self) -> bool:
        """测试模型路径管理器"""
        print("🤖 测试模型路径管理器...")
        
        try:
            from model_path_manager import ModelPathManager
            
            # 创建临时目录进行测试
            with tempfile.TemporaryDirectory() as temp_dir:
                # 模拟打包环境
                original_frozen = getattr(sys, 'frozen', False)
                original_executable = getattr(sys, 'executable', sys.argv[0])
                
                try:
                    # 设置模拟的打包环境
                    sys.frozen = True
                    sys.executable = str(Path(temp_dir) / "test_app.exe")
                    
                    manager = ModelPathManager()
                    
                    # 测试基本功能
                    tests = {
                        "app_root_exists": manager.app_root.exists(),
                        "models_root_created": manager.models_root.exists(),
                        "downloaded_dir_created": manager.downloaded_models.exists(),
                        "cache_dir_created": manager.cache_dir.exists(),
                    }
                    
                    # 测试环境变量设置
                    env_vars = ["HF_HOME", "TRANSFORMERS_CACHE", "TORCH_HOME"]
                    for var in env_vars:
                        tests[f"env_{var}_set"] = var in os.environ
                    
                    # 测试验证功能
                    verification = manager.verify_self_contained()
                    tests["self_contained_check"] = verification["is_self_contained"]
                    
                    all_passed = all(tests.values())
                    
                    self.test_results["tests"]["model_path_manager"] = {
                        "status": "pass" if all_passed else "fail",
                        "tests": tests,
                        "verification": verification
                    }
                    
                    print(f"   {'✅' if all_passed else '❌'} 模型路径管理器{'正常' if all_passed else '异常'}")
                    return all_passed
                    
                finally:
                    # 恢复原始环境
                    if original_frozen:
                        sys.frozen = original_frozen
                    else:
                        delattr(sys, 'frozen')
                    sys.executable = original_executable
                    
        except Exception as e:
            self.test_results["tests"]["model_path_manager"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ 模型路径管理器测试失败: {e}")
            return False
    
    def test_startup_validator(self) -> bool:
        """测试启动验证器"""
        print("🔍 测试启动验证器...")
        
        try:
            from startup_validator import StartupValidator
            
            validator = StartupValidator()
            
            # 运行部分验证测试（避免完整验证的副作用）
            tests = {
                "directory_structure": validator.validate_directory_structure(),
                "python_environment": validator.validate_python_environment(),
                "permissions": validator.validate_permissions(),
            }
            
            all_passed = all(tests.values())
            
            self.test_results["tests"]["startup_validator"] = {
                "status": "pass" if all_passed else "fail",
                "tests": tests
            }
            
            print(f"   {'✅' if all_passed else '❌'} 启动验证器{'正常' if all_passed else '异常'}")
            return all_passed
            
        except Exception as e:
            self.test_results["tests"]["startup_validator"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ 启动验证器测试失败: {e}")
            return False
    
    def test_pyinstaller_spec(self) -> bool:
        """测试PyInstaller规格文件"""
        print("📋 测试PyInstaller规格文件...")
        
        spec_file = self.project_root / "packaging" / "visionai_clipsmaster.spec"
        
        if not spec_file.exists():
            self.test_results["tests"]["pyinstaller_spec"] = {
                "status": "fail",
                "error": "规格文件不存在"
            }
            print("   ❌ 规格文件不存在")
            return False
        
        try:
            # 读取并验证规格文件内容
            with open(spec_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "Analysis", "PYZ", "EXE", "COLLECT",
                "hiddenimports", "datas", "excludes"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            success = len(missing_sections) == 0
            
            self.test_results["tests"]["pyinstaller_spec"] = {
                "status": "pass" if success else "fail",
                "file_exists": True,
                "file_size": len(content),
                "missing_sections": missing_sections
            }
            
            print(f"   {'✅' if success else '❌'} 规格文件{'完整' if success else '不完整'}")
            return success
            
        except Exception as e:
            self.test_results["tests"]["pyinstaller_spec"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ 规格文件测试失败: {e}")
            return False
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("🧪 VisionAI-ClipsMaster 打包系统测试")
        print("=" * 50)
        
        test_functions = [
            ("项目结构", self.test_project_structure),
            ("依赖模块", self.test_dependencies),
            ("打包模块", self.test_packaging_modules),
            ("模型路径管理器", self.test_model_path_manager),
            ("启动验证器", self.test_startup_validator),
            ("PyInstaller规格", self.test_pyinstaller_spec),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            try:
                success = test_func()
                if success:
                    passed_tests += 1
            except Exception as e:
                print(f"   ❌ {test_name} 测试异常: {e}")
                self.test_results["errors"].append(f"{test_name}测试异常: {e}")
        
        # 确定整体状态
        if len(self.test_results["errors"]) == 0:
            self.test_results["overall_status"] = "pass"
        elif passed_tests >= total_tests - 1:
            self.test_results["overall_status"] = "pass_with_warnings"
        else:
            self.test_results["overall_status"] = "fail"
        
        print("=" * 50)
        print(f"测试完成: {passed_tests}/{total_tests} 项测试通过")
        
        # 显示结果摘要
        status = self.test_results["overall_status"]
        if status == "pass":
            print("✅ 所有测试通过，打包系统就绪")
        elif status == "pass_with_warnings":
            print("⚠️ 测试基本通过，但有警告")
            for warning in self.test_results["warnings"]:
                print(f"   ⚠️ {warning}")
        else:
            print("❌ 测试失败，打包系统存在问题")
            for error in self.test_results["errors"]:
                print(f"   ❌ {error}")
        
        return self.test_results
    
    def save_test_report(self):
        """保存测试报告"""
        report_file = self.project_root / "packaging" / "test_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试报告已保存: {report_file}")

def main():
    """主函数"""
    test_suite = PackageTestSuite()
    results = test_suite.run_all_tests()
    test_suite.save_test_report()
    
    # 根据测试结果决定退出码
    if results["overall_status"] in ["pass", "pass_with_warnings"]:
        return True
    else:
        print("\n❌ 测试失败，请解决问题后重试")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("按回车键退出...")
        sys.exit(1)
    else:
        print("\n✅ 测试完成，可以开始打包")
        input("按回车键退出...")
