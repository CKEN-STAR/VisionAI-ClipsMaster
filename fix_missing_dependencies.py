#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 缺失依赖修复脚本
基于依赖分析结果，安装真正缺失的关键第三方依赖项
"""

import subprocess
import sys
import importlib
import json
from pathlib import Path

# 缺失的关键依赖项配置
MISSING_DEPENDENCIES = {
    "critical": [
        {
            "package": "lxml",
            "version": ">=4.9.0",
            "purpose": "XML处理和模式验证",
            "files_affected": 1,
            "install_cmd": "lxml>=4.9.0"
        }
    ],
    "important": [
        {
            "package": "tabulate", 
            "version": ">=0.9.0",
            "purpose": "表格格式化输出",
            "files_affected": 6,
            "install_cmd": "tabulate>=0.9.0"
        },
        {
            "package": "modelscope",
            "version": ">=1.9.0", 
            "purpose": "AI模型下载和管理",
            "files_affected": 1,
            "install_cmd": "modelscope>=1.9.0"
        }
    ],
    "optional": []
}

def check_package_installed(package_name):
    """检查包是否已安装"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_spec, purpose):
    """安装单个包"""
    package_name = package_spec.split('>=')[0].split('==')[0]
    
    print(f"\n📦 正在安装 {package_name}...")
    print(f"   用途: {purpose}")
    print(f"   版本要求: {package_spec}")
    
    try:
        # 检查是否已安装
        if check_package_installed(package_name):
            print(f"✅ {package_name} 已安装，跳过")
            return True
            
        # 执行安装
        cmd = [sys.executable, "-m", "pip", "install", package_spec]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # 验证安装
        if check_package_installed(package_name):
            print(f"✅ {package_name} 安装成功")
            return True
        else:
            print(f"❌ {package_name} 安装后验证失败")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败:")
        print(f"   错误信息: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {package_name} 安装过程中出现异常: {e}")
        return False

def create_backup_requirements():
    """创建当前环境的备份"""
    try:
        print("💾 创建当前环境备份...")
        result = subprocess.run([sys.executable, "-m", "pip", "freeze"], 
                              capture_output=True, text=True, check=True)
        
        backup_file = "requirements_backup.txt"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print(f"✅ 环境备份已保存到 {backup_file}")
        return True
    except Exception as e:
        print(f"⚠️  创建备份失败: {e}")
        return False

def install_dependencies_by_priority():
    """按优先级安装依赖项"""
    results = {
        "critical": {"success": [], "failed": []},
        "important": {"success": [], "failed": []},
        "optional": {"success": [], "failed": []}
    }
    
    for priority in ["critical", "important", "optional"]:
        deps = MISSING_DEPENDENCIES[priority]
        if not deps:
            continue
            
        print(f"\n🔥 安装 {priority.upper()} 优先级依赖项:")
        print("=" * 50)
        
        for dep in deps:
            success = install_package(dep["install_cmd"], dep["purpose"])
            if success:
                results[priority]["success"].append(dep["package"])
            else:
                results[priority]["failed"].append(dep["package"])
                
                # 关键依赖安装失败时询问是否继续
                if priority == "critical":
                    response = input(f"\n⚠️  关键依赖 {dep['package']} 安装失败，是否继续？(y/N): ")
                    if response.lower() != 'y':
                        print("❌ 用户选择停止安装")
                        return results
    
    return results

def generate_install_report(results):
    """生成安装报告"""
    print("\n📊 安装结果报告:")
    print("=" * 60)
    
    total_success = 0
    total_failed = 0
    
    for priority in ["critical", "important", "optional"]:
        success_count = len(results[priority]["success"])
        failed_count = len(results[priority]["failed"])
        
        total_success += success_count
        total_failed += failed_count
        
        if success_count > 0 or failed_count > 0:
            print(f"\n{priority.upper()} 优先级:")
            if success_count > 0:
                print(f"  ✅ 成功安装: {', '.join(results[priority]['success'])}")
            if failed_count > 0:
                print(f"  ❌ 安装失败: {', '.join(results[priority]['failed'])}")
    
    print(f"\n总计: {total_success} 成功, {total_failed} 失败")
    
    # 生成后续建议
    if total_failed > 0:
        print(f"\n🔧 失败依赖的手动安装建议:")
        for priority in ["critical", "important", "optional"]:
            for failed_pkg in results[priority]["failed"]:
                for dep in MISSING_DEPENDENCIES[priority]:
                    if dep["package"] == failed_pkg:
                        print(f"  pip install {dep['install_cmd']}")
    
    if results["critical"]["failed"]:
        print(f"\n⚠️  关键依赖安装失败可能影响以下功能:")
        for failed_pkg in results["critical"]["failed"]:
            for dep in MISSING_DEPENDENCIES["critical"]:
                if dep["package"] == failed_pkg:
                    print(f"  - {dep['purpose']}")
    
    return total_success, total_failed

def verify_core_functionality():
    """验证核心功能依赖"""
    print(f"\n🔍 验证核心功能依赖...")
    
    core_deps = [
        ("numpy", "数值计算"),
        ("torch", "深度学习框架"),
        ("transformers", "NLP模型"),
        ("cv2", "计算机视觉"),
        ("PyQt6", "用户界面"),
        ("psutil", "系统监控"),
        ("loguru", "日志系统"),
        ("yaml", "配置文件")
    ]
    
    missing_core = []
    for pkg, purpose in core_deps:
        if not check_package_installed(pkg):
            missing_core.append((pkg, purpose))
    
    if missing_core:
        print("❌ 发现缺失的核心依赖:")
        for pkg, purpose in missing_core:
            print(f"  - {pkg}: {purpose}")
        print("\n建议运行: pip install -r requirements.txt")
    else:
        print("✅ 所有核心依赖都已安装")

def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster 缺失依赖修复工具")
    print("=" * 60)
    print("基于依赖分析结果，安装真正缺失的关键第三方依赖项")
    print()
    
    # 1. 创建环境备份
    create_backup_requirements()
    
    # 2. 验证核心功能依赖
    verify_core_functionality()
    
    # 3. 显示将要安装的依赖
    print(f"\n📋 将要安装的缺失依赖项:")
    for priority in ["critical", "important"]:
        deps = MISSING_DEPENDENCIES[priority]
        if deps:
            print(f"\n{priority.upper()} 优先级:")
            for dep in deps:
                print(f"  - {dep['package']} {dep['version']}: {dep['purpose']}")
                print(f"    影响文件数: {dep['files_affected']}")
    
    # 4. 确认安装
    response = input(f"\n是否继续安装？(Y/n): ")
    if response.lower() == 'n':
        print("❌ 用户取消安装")
        return
    
    # 5. 执行安装
    results = install_dependencies_by_priority()
    
    # 6. 生成报告
    success_count, failed_count = generate_install_report(results)
    
    # 7. 最终状态
    if failed_count == 0:
        print(f"\n🎉 所有依赖项安装完成！")
        print("现在可以正常使用VisionAI-ClipsMaster的所有功能。")
    else:
        print(f"\n⚠️  部分依赖项安装失败，请查看上述建议进行手动安装。")
    
    print(f"\n💡 提示: 如需回滚，可使用以下命令:")
    print(f"   pip install -r requirements_backup.txt --force-reinstall")

if __name__ == "__main__":
    main()
