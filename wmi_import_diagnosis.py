#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WMI模块导入问题诊断工具
直接诊断和修复WMI导入失败的根本原因

诊断内容:
1. Python环境分析
2. WMI模块安装状态检查
3. 依赖项验证
4. 版本兼容性分析
5. 提供具体修复方案
"""

import os
import sys
import platform
import subprocess
import importlib.util
from pathlib import Path

class WMIImportDiagnostic:
    """WMI导入问题诊断器"""
    
    def __init__(self):
        self.diagnosis_results = {
            "python_environment": {},
            "wmi_module_status": {},
            "dependencies_check": {},
            "installation_attempts": [],
            "fix_recommendations": []
        }
        
    def analyze_python_environment(self):
        """分析Python环境"""
        print("🔍 分析Python环境...")
        
        env_info = {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.architecture()[0],
            "platform": platform.platform(),
            "executable": sys.executable,
            "prefix": sys.prefix,
            "path": sys.path[:3]  # 显示前3个路径
        }
        
        self.diagnosis_results["python_environment"] = env_info
        
        print(f"  Python版本: {env_info['python_version']}")
        print(f"  Python实现: {env_info['python_implementation']}")
        print(f"  系统架构: {env_info['architecture']}")
        print(f"  Python路径: {env_info['executable']}")
        
        return env_info
    
    def check_wmi_module_status(self):
        """检查WMI模块状态"""
        print("\n🔍 检查WMI模块状态...")
        
        wmi_status = {
            "import_success": False,
            "import_error": None,
            "module_location": None,
            "module_version": None,
            "pywin32_available": False,
            "com_available": False
        }
        
        # 1. 尝试导入WMI模块
        try:
            import wmi
            wmi_status["import_success"] = True
            wmi_status["module_location"] = wmi.__file__ if hasattr(wmi, '__file__') else "内置模块"
            wmi_status["module_version"] = getattr(wmi, '__version__', '未知版本')
            print("  ✅ WMI模块导入成功")
            print(f"    模块位置: {wmi_status['module_location']}")
            print(f"    模块版本: {wmi_status['module_version']}")
        except ImportError as e:
            wmi_status["import_error"] = str(e)
            print(f"  ❌ WMI模块导入失败: {e}")
        except Exception as e:
            wmi_status["import_error"] = f"其他错误: {str(e)}"
            print(f"  ❌ WMI模块导入异常: {e}")
        
        # 2. 检查pywin32依赖
        try:
            import win32com.client
            wmi_status["pywin32_available"] = True
            print("  ✅ pywin32依赖可用")
        except ImportError:
            print("  ❌ pywin32依赖不可用")
        
        # 3. 检查COM接口
        try:
            import pythoncom
            wmi_status["com_available"] = True
            print("  ✅ COM接口可用")
        except ImportError:
            print("  ❌ COM接口不可用")
        
        self.diagnosis_results["wmi_module_status"] = wmi_status
        return wmi_status
    
    def check_dependencies(self):
        """检查WMI模块依赖项"""
        print("\n🔍 检查WMI模块依赖项...")
        
        dependencies = {
            "pywin32": {"available": False, "version": None},
            "pythoncom": {"available": False, "version": None},
            "win32com": {"available": False, "version": None},
            "win32api": {"available": False, "version": None}
        }
        
        # 检查各个依赖项
        for dep_name in dependencies.keys():
            try:
                module = __import__(dep_name)
                dependencies[dep_name]["available"] = True
                dependencies[dep_name]["version"] = getattr(module, '__version__', '未知版本')
                print(f"  ✅ {dep_name}: 可用 (版本: {dependencies[dep_name]['version']})")
            except ImportError as e:
                dependencies[dep_name]["error"] = str(e)
                print(f"  ❌ {dep_name}: 不可用 - {e}")
        
        self.diagnosis_results["dependencies_check"] = dependencies
        return dependencies
    
    def attempt_wmi_installation(self):
        """尝试安装WMI模块"""
        print("\n🔧 尝试安装WMI模块...")
        
        installation_methods = [
            {
                "name": "pip install WMI",
                "command": [sys.executable, "-m", "pip", "install", "WMI"],
                "description": "使用pip安装WMI模块"
            },
            {
                "name": "pip install pywin32",
                "command": [sys.executable, "-m", "pip", "install", "pywin32"],
                "description": "安装pywin32依赖"
            },
            {
                "name": "pip install wmi",
                "command": [sys.executable, "-m", "pip", "install", "wmi"],
                "description": "使用小写wmi包名安装"
            },
            {
                "name": "conda install pywin32",
                "command": ["conda", "install", "-y", "pywin32"],
                "description": "使用conda安装pywin32"
            }
        ]
        
        installation_results = []
        
        for method in installation_methods:
            print(f"  尝试: {method['name']}")
            try:
                result = subprocess.run(
                    method["command"],
                    capture_output=True,
                    text=True,
                    timeout=120  # 2分钟超时
                )
                
                if result.returncode == 0:
                    print(f"    ✅ {method['name']}: 安装成功")
                    installation_results.append({
                        "method": method["name"],
                        "success": True,
                        "output": result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
                    })
                    
                    # 安装成功后立即测试导入
                    try:
                        import importlib
                        importlib.invalidate_caches()
                        import wmi
                        print(f"    ✅ WMI模块导入测试成功")
                        break  # 成功后退出循环
                    except ImportError:
                        print(f"    ⚠️ 安装成功但导入仍失败")
                        
                else:
                    print(f"    ❌ {method['name']}: 安装失败")
                    installation_results.append({
                        "method": method["name"],
                        "success": False,
                        "error": result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
                    })
                    
            except subprocess.TimeoutExpired:
                print(f"    ❌ {method['name']}: 安装超时")
                installation_results.append({
                    "method": method["name"],
                    "success": False,
                    "error": "安装超时"
                })
            except FileNotFoundError:
                print(f"    ❌ {method['name']}: 命令不存在")
                installation_results.append({
                    "method": method["name"],
                    "success": False,
                    "error": "命令不存在"
                })
            except Exception as e:
                print(f"    ❌ {method['name']}: 异常 - {e}")
                installation_results.append({
                    "method": method["name"],
                    "success": False,
                    "error": str(e)
                })
        
        self.diagnosis_results["installation_attempts"] = installation_results
        return installation_results
    
    def find_alternative_solutions(self):
        """寻找功能等效的替代方案"""
        print("\n🔍 寻找功能等效的替代方案...")
        
        alternatives = []
        
        # 1. 检查wmi-client-wrapper
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "wmi-client-wrapper"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    import wmi_client_wrapper as wmi
                    alternatives.append({
                        "name": "wmi-client-wrapper",
                        "success": True,
                        "description": "WMI客户端包装器"
                    })
                    print("  ✅ wmi-client-wrapper: 可用")
                except ImportError:
                    print("  ❌ wmi-client-wrapper: 安装成功但导入失败")
        except Exception as e:
            print(f"  ❌ wmi-client-wrapper: 安装失败 - {e}")
        
        # 2. 检查python-wmi
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "python-wmi"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    import python_wmi as wmi
                    alternatives.append({
                        "name": "python-wmi",
                        "success": True,
                        "description": "Python WMI包"
                    })
                    print("  ✅ python-wmi: 可用")
                except ImportError:
                    print("  ❌ python-wmi: 安装成功但导入失败")
        except Exception as e:
            print(f"  ❌ python-wmi: 安装失败 - {e}")
        
        # 3. 检查win32com直接使用
        try:
            import win32com.client
            alternatives.append({
                "name": "win32com.client",
                "success": True,
                "description": "直接使用win32com.client访问WMI"
            })
            print("  ✅ win32com.client: 可用 (可直接访问WMI)")
        except ImportError:
            print("  ❌ win32com.client: 不可用")
        
        return alternatives
    
    def generate_fix_recommendations(self):
        """生成修复建议"""
        print("\n💡 生成修复建议...")
        
        recommendations = []
        
        wmi_status = self.diagnosis_results.get("wmi_module_status", {})
        dependencies = self.diagnosis_results.get("dependencies_check", {})
        installations = self.diagnosis_results.get("installation_attempts", [])
        
        # 基于诊断结果生成建议
        if not wmi_status.get("import_success", False):
            if not dependencies.get("pywin32", {}).get("available", False):
                recommendations.append({
                    "priority": 1,
                    "action": "安装pywin32依赖",
                    "command": "pip install pywin32",
                    "description": "WMI模块需要pywin32作为依赖"
                })
            
            # 检查是否有成功的安装方法
            successful_installs = [inst for inst in installations if inst.get("success", False)]
            if successful_installs:
                recommendations.append({
                    "priority": 1,
                    "action": f"使用成功的安装方法: {successful_installs[0]['method']}",
                    "command": successful_installs[0]['method'],
                    "description": "该方法已验证可以成功安装"
                })
            else:
                recommendations.append({
                    "priority": 2,
                    "action": "尝试手动安装WMI模块",
                    "command": "pip install --upgrade pip && pip install WMI",
                    "description": "升级pip后重新安装WMI模块"
                })
        
        # 如果WMI无法安装，推荐替代方案
        if not any(inst.get("success", False) for inst in installations):
            recommendations.append({
                "priority": 3,
                "action": "使用win32com.client直接访问WMI",
                "command": "import win32com.client",
                "description": "绕过WMI模块，直接使用COM接口"
            })
        
        self.diagnosis_results["fix_recommendations"] = recommendations
        
        print("  修复建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"    {i}. 优先级{rec['priority']}: {rec['action']}")
            print(f"       命令: {rec['command']}")
            print(f"       说明: {rec['description']}")
        
        return recommendations
    
    def run_complete_diagnosis(self):
        """运行完整诊断"""
        print("🔍 WMI模块导入问题完整诊断")
        print("=" * 50)
        
        # 1. 分析Python环境
        self.analyze_python_environment()
        
        # 2. 检查WMI模块状态
        wmi_status = self.check_wmi_module_status()
        
        # 3. 检查依赖项
        self.check_dependencies()
        
        # 4. 如果WMI不可用，尝试安装
        if not wmi_status.get("import_success", False):
            self.attempt_wmi_installation()
            
            # 重新检查WMI状态
            print("\n🔍 重新检查WMI模块状态...")
            updated_status = self.check_wmi_module_status()
            self.diagnosis_results["wmi_module_status"].update(updated_status)
        
        # 5. 寻找替代方案
        alternatives = self.find_alternative_solutions()
        self.diagnosis_results["alternatives"] = alternatives
        
        # 6. 生成修复建议
        self.generate_fix_recommendations()
        
        # 7. 生成诊断报告
        self.generate_diagnosis_report()
        
        return self.diagnosis_results
    
    def generate_diagnosis_report(self):
        """生成诊断报告"""
        print("\n" + "=" * 50)
        print("📊 WMI导入问题诊断报告")
        
        wmi_status = self.diagnosis_results.get("wmi_module_status", {})
        dependencies = self.diagnosis_results.get("dependencies_check", {})
        installations = self.diagnosis_results.get("installation_attempts", [])
        
        # WMI模块状态
        if wmi_status.get("import_success", False):
            print("  WMI模块状态: ✅ 可用")
            print(f"    版本: {wmi_status.get('module_version', '未知')}")
        else:
            print("  WMI模块状态: ❌ 不可用")
            print(f"    错误: {wmi_status.get('import_error', '未知错误')}")
        
        # 依赖项状态
        pywin32_available = dependencies.get("pywin32", {}).get("available", False)
        print(f"  pywin32依赖: {'✅ 可用' if pywin32_available else '❌ 不可用'}")
        
        # 安装尝试结果
        successful_installs = [inst for inst in installations if inst.get("success", False)]
        if successful_installs:
            print(f"  安装尝试: ✅ 成功 ({len(successful_installs)}/{len(installations)})")
        elif installations:
            print(f"  安装尝试: ❌ 失败 (0/{len(installations)})")
        
        # 总体状态
        overall_success = wmi_status.get("import_success", False)
        print(f"\n🎯 诊断结果: {'✅ WMI模块可用' if overall_success else '❌ WMI模块不可用'}")
        
        if not overall_success:
            recommendations = self.diagnosis_results.get("fix_recommendations", [])
            if recommendations:
                print(f"💡 建议执行优先级1的修复方案")
            else:
                print(f"⚠️ 需要手动解决WMI导入问题")

if __name__ == "__main__":
    # 运行WMI导入问题诊断
    diagnostic = WMIImportDiagnostic()
    results = diagnostic.run_complete_diagnosis()
    
    # 保存诊断报告
    import json
    with open("wmi_import_diagnosis_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细诊断报告已保存到: wmi_import_diagnosis_report.json")
