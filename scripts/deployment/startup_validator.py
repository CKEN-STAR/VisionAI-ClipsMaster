#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 启动验证器
检查整合包完整性和模型可用性
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess

class StartupValidator:
    """启动验证器"""
    
    def __init__(self):
        # 获取应用根目录
        if getattr(sys, 'frozen', False):
            self.app_root = Path(sys.executable).parent
        else:
            self.app_root = Path(__file__).parent.parent
        
        self.validation_results = {
            "overall_status": "unknown",
            "checks": {},
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
    
    def validate_directory_structure(self) -> bool:
        """验证目录结构完整性"""
        print("🔍 检查目录结构...")
        
        required_dirs = [
            "models",
            "models/downloaded", 
            "configs",
            "data",
            "logs",
            "temp"
        ]
        
        required_files = [
            "simple_ui_fixed.py",
            "model_downloader.py",
            "config.json"
        ]
        
        missing_dirs = []
        missing_files = []
        
        # 检查目录
        for dir_path in required_dirs:
            full_path = self.app_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
                # 尝试创建缺失的目录
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"   ✅ 已创建目录: {dir_path}")
                except Exception as e:
                    print(f"   ❌ 无法创建目录 {dir_path}: {e}")
        
        # 检查文件
        for file_path in required_files:
            full_path = self.app_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        # 记录结果
        self.validation_results["checks"]["directory_structure"] = {
            "status": "pass" if not missing_dirs and not missing_files else "fail",
            "missing_dirs": missing_dirs,
            "missing_files": missing_files
        }
        
        if missing_files:
            self.validation_results["errors"].extend([
                f"缺失关键文件: {f}" for f in missing_files
            ])
        
        success = len(missing_files) == 0
        print(f"   {'✅' if success else '❌'} 目录结构检查{'通过' if success else '失败'}")
        return success
    
    def validate_python_environment(self) -> bool:
        """验证Python环境"""
        print("🐍 检查Python环境...")
        
        checks = {}
        
        # Python版本检查
        python_version = sys.version_info
        min_version = (3, 8)
        version_ok = python_version >= min_version
        
        checks["python_version"] = {
            "current": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            "minimum": f"{min_version[0]}.{min_version[1]}",
            "status": "pass" if version_ok else "fail"
        }
        
        if not version_ok:
            self.validation_results["errors"].append(
                f"Python版本过低: {python_version.major}.{python_version.minor}, 需要 >= {min_version[0]}.{min_version[1]}"
            )
        
        # 关键模块检查
        critical_modules = [
            "PyQt6", "torch", "transformers", "cv2", 
            "numpy", "requests", "psutil"
        ]
        
        module_status = {}
        for module in critical_modules:
            try:
                __import__(module)
                module_status[module] = "available"
                print(f"   ✅ {module}")
            except ImportError as e:
                module_status[module] = f"missing: {e}"
                print(f"   ❌ {module}: {e}")
                self.validation_results["errors"].append(f"缺失模块: {module}")
        
        checks["modules"] = module_status
        
        self.validation_results["checks"]["python_environment"] = checks
        
        # 检查是否有缺失的关键模块
        missing_critical = [m for m, status in module_status.items() 
                          if not status == "available"]
        
        success = version_ok and len(missing_critical) == 0
        print(f"   {'✅' if success else '❌'} Python环境检查{'通过' if success else '失败'}")
        return success
    
    def validate_model_availability(self) -> bool:
        """验证模型可用性"""
        print("🤖 检查AI模型...")
        
        from model_path_manager import get_model_path_manager
        
        path_manager = get_model_path_manager()
        available_models = path_manager.get_available_models()
        
        required_models = ["mistral-7b-en", "Qwen3-1.7B-zh"]
        missing_models = [m for m in required_models if m not in available_models]
        
        model_info = {}
        for model in required_models:
            if model in available_models:
                model_path = path_manager.get_model_path(model)
                model_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                model_info[model] = {
                    "status": "available",
                    "path": str(model_path),
                    "size_mb": model_size / 1024 / 1024
                }
                print(f"   ✅ {model} ({model_info[model]['size_mb']:.1f} MB)")
            else:
                model_info[model] = {
                    "status": "missing",
                    "path": None,
                    "size_mb": 0
                }
                print(f"   ❌ {model} (缺失)")
        
        self.validation_results["checks"]["models"] = {
            "available": available_models,
            "required": required_models,
            "missing": missing_models,
            "details": model_info
        }
        
        if missing_models:
            self.validation_results["warnings"].append(
                f"缺失AI模型: {', '.join(missing_models)} - 首次运行时将自动下载"
            )
        
        # 模型缺失不算失败，因为可以自动下载
        success = True
        print(f"   {'✅' if success else '❌'} 模型检查完成")
        return success
    
    def validate_disk_space(self) -> bool:
        """验证磁盘空间"""
        print("💾 检查磁盘空间...")
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.app_root)
            
            # 转换为GB
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            
            # 检查是否有足够空间（至少需要10GB用于模型下载）
            min_required_gb = 10
            space_ok = free_gb >= min_required_gb
            
            disk_info = {
                "total_gb": round(total_gb, 1),
                "used_gb": round(used_gb, 1),
                "free_gb": round(free_gb, 1),
                "required_gb": min_required_gb,
                "sufficient": space_ok
            }
            
            self.validation_results["checks"]["disk_space"] = disk_info
            
            if not space_ok:
                self.validation_results["errors"].append(
                    f"磁盘空间不足: 可用 {free_gb:.1f}GB, 需要至少 {min_required_gb}GB"
                )
            
            print(f"   💾 可用空间: {free_gb:.1f}GB / {total_gb:.1f}GB")
            print(f"   {'✅' if space_ok else '❌'} 磁盘空间{'充足' if space_ok else '不足'}")
            
            return space_ok
            
        except Exception as e:
            self.validation_results["errors"].append(f"磁盘空间检查失败: {e}")
            print(f"   ❌ 磁盘空间检查失败: {e}")
            return False
    
    def validate_network_connectivity(self) -> bool:
        """验证网络连接（用于模型下载）"""
        print("🌐 检查网络连接...")
        
        test_urls = [
            "https://huggingface.co",
            "https://github.com",
            "https://www.google.com"
        ]
        
        connectivity_results = {}
        any_success = False
        
        for url in test_urls:
            try:
                import requests
                response = requests.get(url, timeout=5)
                success = response.status_code == 200
                connectivity_results[url] = {
                    "status": "success" if success else "failed",
                    "status_code": response.status_code
                }
                if success:
                    any_success = True
                    print(f"   ✅ {url}")
                else:
                    print(f"   ❌ {url} (状态码: {response.status_code})")
            except Exception as e:
                connectivity_results[url] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"   ❌ {url} (错误: {e})")
        
        self.validation_results["checks"]["network"] = connectivity_results
        
        if not any_success:
            self.validation_results["warnings"].append(
                "网络连接异常 - 如果需要下载模型，请检查网络设置"
            )
        
        print(f"   {'✅' if any_success else '⚠️'} 网络连接{'正常' if any_success else '异常'}")
        return True  # 网络问题不阻止启动
    
    def validate_permissions(self) -> bool:
        """验证文件权限"""
        print("🔐 检查文件权限...")
        
        test_paths = [
            self.app_root / "models",
            self.app_root / "data", 
            self.app_root / "logs",
            self.app_root / "temp"
        ]
        
        permission_results = {}
        all_ok = True
        
        for path in test_paths:
            try:
                # 测试写入权限
                test_file = path / "permission_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                permission_results[str(path)] = "writable"
                print(f"   ✅ {path.name}")
            except Exception as e:
                permission_results[str(path)] = f"error: {e}"
                all_ok = False
                print(f"   ❌ {path.name}: {e}")
                self.validation_results["errors"].append(f"权限不足: {path}")
        
        self.validation_results["checks"]["permissions"] = permission_results
        
        print(f"   {'✅' if all_ok else '❌'} 文件权限检查{'通过' if all_ok else '失败'}")
        return all_ok
    
    def run_full_validation(self) -> Dict:
        """运行完整验证"""
        print("🚀 VisionAI-ClipsMaster 启动验证")
        print("=" * 50)
        
        validation_steps = [
            ("目录结构", self.validate_directory_structure),
            ("Python环境", self.validate_python_environment),
            ("AI模型", self.validate_model_availability),
            ("磁盘空间", self.validate_disk_space),
            ("网络连接", self.validate_network_connectivity),
            ("文件权限", self.validate_permissions),
        ]
        
        passed_checks = 0
        total_checks = len(validation_steps)
        
        for step_name, step_func in validation_steps:
            try:
                success = step_func()
                if success:
                    passed_checks += 1
            except Exception as e:
                print(f"   ❌ {step_name} 检查异常: {e}")
                self.validation_results["errors"].append(f"{step_name}检查异常: {e}")
        
        # 确定整体状态
        if len(self.validation_results["errors"]) == 0:
            self.validation_results["overall_status"] = "ready"
        elif passed_checks >= total_checks - 1:  # 允许一个非关键检查失败
            self.validation_results["overall_status"] = "ready_with_warnings"
        else:
            self.validation_results["overall_status"] = "not_ready"
        
        print("=" * 50)
        print(f"验证完成: {passed_checks}/{total_checks} 项检查通过")
        
        # 显示结果摘要
        status = self.validation_results["overall_status"]
        if status == "ready":
            print("✅ 系统就绪，可以启动")
        elif status == "ready_with_warnings":
            print("⚠️ 系统基本就绪，但有警告")
            for warning in self.validation_results["warnings"]:
                print(f"   ⚠️ {warning}")
        else:
            print("❌ 系统未就绪，存在严重问题")
            for error in self.validation_results["errors"]:
                print(f"   ❌ {error}")
        
        return self.validation_results
    
    def save_validation_report(self):
        """保存验证报告"""
        report_file = self.app_root / "logs" / "startup_validation.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 验证报告已保存: {report_file}")

def main():
    """主函数"""
    validator = StartupValidator()
    results = validator.run_full_validation()
    validator.save_validation_report()
    
    # 根据验证结果决定是否继续启动
    if results["overall_status"] in ["ready", "ready_with_warnings"]:
        return True
    else:
        print("\n❌ 验证失败，无法启动程序")
        print("请解决上述问题后重试")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        input("按回车键退出...")
        sys.exit(1)
