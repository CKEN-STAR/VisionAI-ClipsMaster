#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDE配置验证脚本
帮助用户验证IDE配置是否正确，解决WMI模块导入显示问题

验证内容:
1. Python解释器路径验证
2. site-packages路径检查
3. WMI模块位置确认
4. IDE配置建议生成
5. 修复指导提供
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

class IDEConfigValidator:
    """IDE配置验证器"""
    
    def __init__(self):
        self.validation_results = {
            "python_interpreter": {},
            "site_packages": {},
            "wmi_module": {},
            "ide_recommendations": [],
            "fix_suggestions": []
        }
    
    def validate_python_interpreter(self):
        """验证Python解释器配置"""
        print("🔍 验证Python解释器配置...")
        
        interpreter_info = {
            "executable_path": sys.executable,
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "architecture": platform.architecture()[0],
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "is_virtual_env": sys.prefix != sys.base_prefix
        }
        
        print(f"  Python解释器路径: {interpreter_info['executable_path']}")
        print(f"  Python版本: {interpreter_info['version']}")
        print(f"  Python实现: {interpreter_info['implementation']}")
        print(f"  系统架构: {interpreter_info['architecture']}")
        print(f"  安装前缀: {interpreter_info['prefix']}")
        print(f"  虚拟环境: {'是' if interpreter_info['is_virtual_env'] else '否'}")
        
        # 检查解释器是否可执行
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            interpreter_info["executable"] = result.returncode == 0
            interpreter_info["version_output"] = result.stdout.strip()
        except Exception as e:
            interpreter_info["executable"] = False
            interpreter_info["error"] = str(e)
        
        status = "✅ 正常" if interpreter_info["executable"] else "❌ 异常"
        print(f"  解释器状态: {status}")
        
        self.validation_results["python_interpreter"] = interpreter_info
        return interpreter_info
    
    def validate_site_packages(self):
        """验证site-packages路径"""
        print("\n🔍 验证site-packages路径...")
        
        site_packages_info = {
            "paths": [],
            "wmi_locations": [],
            "total_packages": 0,
            "accessible": True
        }
        
        # 查找所有site-packages路径
        for path in sys.path:
            if 'site-packages' in path and os.path.exists(path):
                site_packages_info["paths"].append({
                    "path": path,
                    "exists": os.path.exists(path),
                    "readable": os.access(path, os.R_OK),
                    "package_count": len([f for f in os.listdir(path) 
                                        if os.path.isdir(os.path.join(path, f))]) if os.path.exists(path) else 0
                })
                
                # 检查WMI模块是否在此路径
                wmi_py_path = os.path.join(path, 'wmi.py')
                wmi_dir_path = os.path.join(path, 'wmi')
                
                if os.path.exists(wmi_py_path):
                    site_packages_info["wmi_locations"].append({
                        "type": "file",
                        "path": wmi_py_path,
                        "size": os.path.getsize(wmi_py_path)
                    })
                
                if os.path.exists(wmi_dir_path):
                    site_packages_info["wmi_locations"].append({
                        "type": "directory", 
                        "path": wmi_dir_path
                    })
        
        print(f"  发现site-packages路径: {len(site_packages_info['paths'])}个")
        for i, sp_info in enumerate(site_packages_info["paths"], 1):
            status = "✅" if sp_info["exists"] and sp_info["readable"] else "❌"
            print(f"    {i}. {status} {sp_info['path']} ({sp_info['package_count']}个包)")
        
        print(f"  WMI模块位置: {len(site_packages_info['wmi_locations'])}个")
        for wmi_loc in site_packages_info["wmi_locations"]:
            print(f"    📦 {wmi_loc['type']}: {wmi_loc['path']}")
            if wmi_loc['type'] == 'file':
                print(f"        大小: {wmi_loc['size']} 字节")
        
        self.validation_results["site_packages"] = site_packages_info
        return site_packages_info
    
    def validate_wmi_module(self):
        """验证WMI模块状态"""
        print("\n🔍 验证WMI模块状态...")
        
        wmi_info = {
            "import_success": False,
            "module_file": None,
            "module_version": None,
            "module_attributes": [],
            "instance_creation": False,
            "gpu_detection": False,
            "error_details": None
        }
        
        # 1. 导入测试
        try:
            import wmi
            wmi_info["import_success"] = True
            wmi_info["module_file"] = getattr(wmi, '__file__', '内置模块')
            wmi_info["module_version"] = getattr(wmi, '__version__', '未知版本')
            
            # 获取主要属性
            wmi_info["module_attributes"] = [
                attr for attr in dir(wmi) 
                if not attr.startswith('_') and callable(getattr(wmi, attr))
            ][:10]
            
            print(f"  ✅ WMI模块导入成功")
            print(f"    模块文件: {wmi_info['module_file']}")
            print(f"    模块版本: {wmi_info['module_version']}")
            print(f"    主要方法: {', '.join(wmi_info['module_attributes'][:5])}")
            
        except ImportError as e:
            wmi_info["error_details"] = f"导入失败: {str(e)}"
            print(f"  ❌ WMI模块导入失败: {e}")
            self.validation_results["wmi_module"] = wmi_info
            return wmi_info
        
        # 2. 实例创建测试
        try:
            c = wmi.WMI()
            wmi_info["instance_creation"] = True
            print(f"  ✅ WMI实例创建成功")
        except Exception as e:
            wmi_info["error_details"] = f"实例创建失败: {str(e)}"
            print(f"  ❌ WMI实例创建失败: {e}")
        
        # 3. GPU检测测试
        if wmi_info["instance_creation"]:
            try:
                c = wmi.WMI()
                gpu_count = 0
                gpu_names = []
                
                for gpu in c.Win32_VideoController():
                    if gpu.Name:
                        gpu_count += 1
                        gpu_names.append(gpu.Name)
                
                wmi_info["gpu_detection"] = True
                wmi_info["detected_gpus"] = gpu_names
                print(f"  ✅ GPU检测功能正常 (检测到{gpu_count}个显卡)")
                for gpu_name in gpu_names:
                    print(f"    🎮 {gpu_name}")
                    
            except Exception as e:
                wmi_info["error_details"] = f"GPU检测失败: {str(e)}"
                print(f"  ❌ GPU检测功能失败: {e}")
        
        self.validation_results["wmi_module"] = wmi_info
        return wmi_info
    
    def generate_ide_recommendations(self):
        """生成IDE配置建议"""
        print("\n💡 生成IDE配置建议...")
        
        recommendations = []
        
        interpreter_info = self.validation_results.get("python_interpreter", {})
        site_packages_info = self.validation_results.get("site_packages", {})
        wmi_info = self.validation_results.get("wmi_module", {})
        
        # 基于验证结果生成建议
        if interpreter_info.get("executable", False):
            recommendations.append({
                "type": "success",
                "title": "Python解释器配置正确",
                "description": f"IDE应该使用解释器路径: {interpreter_info['executable_path']}",
                "action": "在IDE中确认Python解释器路径设置正确"
            })
        else:
            recommendations.append({
                "type": "error",
                "title": "Python解释器问题",
                "description": "Python解释器无法正常执行",
                "action": "检查Python安装并重新配置IDE解释器路径"
            })
        
        if site_packages_info.get("wmi_locations"):
            recommendations.append({
                "type": "success", 
                "title": "WMI模块位置正确",
                "description": f"WMI模块位于: {site_packages_info['wmi_locations'][0]['path']}",
                "action": "IDE应该能够在site-packages中找到WMI模块"
            })
        else:
            recommendations.append({
                "type": "warning",
                "title": "WMI模块位置问题",
                "description": "在site-packages中未找到WMI模块文件",
                "action": "重新安装WMI模块或检查安装路径"
            })
        
        if wmi_info.get("import_success", False):
            recommendations.append({
                "type": "success",
                "title": "WMI模块功能正常",
                "description": f"WMI模块版本 {wmi_info['module_version']} 工作正常",
                "action": "IDE显示错误是缓存问题，建议重启IDE或清理缓存"
            })
        else:
            recommendations.append({
                "type": "error",
                "title": "WMI模块功能异常",
                "description": wmi_info.get("error_details", "未知错误"),
                "action": "重新安装WMI模块"
            })
        
        # 输出建议
        for i, rec in enumerate(recommendations, 1):
            icon = {"success": "✅", "warning": "⚠️", "error": "❌"}.get(rec["type"], "ℹ️")
            print(f"  {i}. {icon} {rec['title']}")
            print(f"     描述: {rec['description']}")
            print(f"     建议: {rec['action']}")
        
        self.validation_results["ide_recommendations"] = recommendations
        return recommendations
    
    def generate_fix_suggestions(self):
        """生成修复建议"""
        print("\n🔧 生成修复建议...")
        
        fix_suggestions = []
        
        wmi_info = self.validation_results.get("wmi_module", {})
        
        if wmi_info.get("import_success", False):
            # WMI功能正常，只是IDE显示问题
            fix_suggestions.extend([
                {
                    "priority": 1,
                    "method": "重启IDE",
                    "description": "最简单有效的解决方案",
                    "steps": [
                        "保存所有文件",
                        "完全关闭IDE",
                        "重新启动IDE",
                        "重新打开项目"
                    ]
                },
                {
                    "priority": 2,
                    "method": "清理IDE缓存",
                    "description": "清理IDE的模块索引缓存",
                    "steps": [
                        "使用IDE的 'Invalidate Caches' 功能",
                        "重启IDE",
                        "等待重新索引完成"
                    ]
                },
                {
                    "priority": 3,
                    "method": "重新配置Python解释器",
                    "description": "确保IDE使用正确的Python环境",
                    "steps": [
                        f"设置解释器路径为: {sys.executable}",
                        "验证site-packages路径包含WMI模块",
                        "重新索引项目"
                    ]
                }
            ])
        else:
            # WMI功能异常，需要修复模块
            fix_suggestions.extend([
                {
                    "priority": 1,
                    "method": "重新安装WMI模块",
                    "description": "修复WMI模块安装问题",
                    "steps": [
                        "pip uninstall WMI",
                        "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ WMI",
                        "验证安装: python -c 'import wmi; print(wmi.__version__)'"
                    ]
                }
            ])
        
        # 输出修复建议
        for suggestion in fix_suggestions:
            print(f"  优先级 {suggestion['priority']}: {suggestion['method']}")
            print(f"    说明: {suggestion['description']}")
            print(f"    步骤:")
            for step in suggestion['steps']:
                print(f"      - {step}")
        
        self.validation_results["fix_suggestions"] = fix_suggestions
        return fix_suggestions
    
    def run_complete_validation(self):
        """运行完整的IDE配置验证"""
        print("🔍 VisionAI-ClipsMaster IDE配置验证")
        print("=" * 50)
        
        # 1. 验证Python解释器
        self.validate_python_interpreter()
        
        # 2. 验证site-packages路径
        self.validate_site_packages()
        
        # 3. 验证WMI模块
        self.validate_wmi_module()
        
        # 4. 生成IDE配置建议
        self.generate_ide_recommendations()
        
        # 5. 生成修复建议
        self.generate_fix_suggestions()
        
        # 6. 生成验证报告
        self.generate_validation_report()
        
        return self.validation_results
    
    def generate_validation_report(self):
        """生成验证报告"""
        print("\n" + "=" * 50)
        print("📊 IDE配置验证报告")
        
        interpreter_info = self.validation_results.get("python_interpreter", {})
        site_packages_info = self.validation_results.get("site_packages", {})
        wmi_info = self.validation_results.get("wmi_module", {})
        
        # 配置状态总结
        print("  配置状态总结:")
        print(f"    Python解释器: {'✅ 正常' if interpreter_info.get('executable', False) else '❌ 异常'}")
        print(f"    site-packages: {'✅ 正常' if site_packages_info.get('paths') else '❌ 异常'}")
        print(f"    WMI模块导入: {'✅ 正常' if wmi_info.get('import_success', False) else '❌ 异常'}")
        print(f"    WMI功能测试: {'✅ 正常' if wmi_info.get('gpu_detection', False) else '❌ 异常'}")
        
        # IDE配置建议
        recommendations = self.validation_results.get("ide_recommendations", [])
        success_count = sum(1 for rec in recommendations if rec["type"] == "success")
        total_count = len(recommendations)
        
        print(f"\n  IDE配置评估: {success_count}/{total_count} 项正常")
        
        # 总体状态
        overall_healthy = (
            interpreter_info.get('executable', False) and
            wmi_info.get('import_success', False) and
            wmi_info.get('gpu_detection', False)
        )
        
        print(f"\n🎯 总体状态: {'✅ 配置正确' if overall_healthy else '⚠️ 需要修复'}")
        
        if overall_healthy:
            print("✅ Python环境配置正确")
            print("✅ WMI模块功能正常")
            print("💡 IDE显示错误是缓存问题，建议重启IDE")
        else:
            print("⚠️ 发现配置问题，请按照修复建议操作")
        
        # 提供IDE配置信息
        print(f"\n📋 IDE配置信息:")
        print(f"  Python解释器路径: {interpreter_info.get('executable_path', '未知')}")
        print(f"  Python版本: {interpreter_info.get('version', '未知')}")
        
        wmi_locations = site_packages_info.get('wmi_locations', [])
        if wmi_locations:
            print(f"  WMI模块位置: {wmi_locations[0]['path']}")
        
        print(f"\n💡 使用此信息在IDE中配置Python解释器")

if __name__ == "__main__":
    # 运行IDE配置验证
    validator = IDEConfigValidator()
    results = validator.run_complete_validation()
    
    # 保存验证报告
    import json
    with open("ide_config_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细验证报告已保存到: ide_config_validation_report.json")
