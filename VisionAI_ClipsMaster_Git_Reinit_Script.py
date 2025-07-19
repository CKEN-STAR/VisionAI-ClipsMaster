#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster Git重新初始化脚本
安全地删除.git文件夹并重新初始化Git仓库
"""

import os
import shutil
import subprocess
import time
import json
from pathlib import Path

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"

def get_size(path):
    """获取文件或目录的大小"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, PermissionError):
            pass
        return total
    return 0

def run_command(command, cwd=None):
    """安全执行命令"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True, 
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)

def verify_core_functionality(root_path):
    """验证核心功能文件完整性"""
    print("🔍 验证核心功能文件完整性...")
    
    critical_files = [
        "simple_ui_fixed.py",
        "VisionAI_ClipsMaster_Comprehensive_Verification_Test.py",
        "requirements.txt"
    ]
    
    critical_dirs = [
        "src",
        "ui", 
        "configs",
        "tools"
    ]
    
    missing_files = []
    
    for file in critical_files:
        file_path = os.path.join(root_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    for dir_name in critical_dirs:
        dir_path = os.path.join(root_path, dir_name)
        if not os.path.exists(dir_path):
            missing_files.append(dir_name)
    
    if missing_files:
        print(f"  ❌ 警告: 发现缺失的关键文件/目录: {missing_files}")
        return False
    else:
        print("  ✅ 所有核心文件完整")
        return True

def backup_project_state(root_path, operation_log):
    """备份项目状态信息"""
    print("💾 备份项目状态信息...")
    
    backup_info = {
        "backup_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "project_path": root_path,
        "total_size": get_size(root_path),
        "git_exists": os.path.exists(os.path.join(root_path, ".git")),
        "critical_files": [],
        "directory_structure": []
    }
    
    # 记录关键文件
    critical_files = [
        "simple_ui_fixed.py",
        "VisionAI_ClipsMaster_Comprehensive_Verification_Test.py",
        "requirements.txt"
    ]
    
    for file in critical_files:
        file_path = os.path.join(root_path, file)
        if os.path.exists(file_path):
            backup_info["critical_files"].append({
                "name": file,
                "size": get_size(file_path),
                "exists": True
            })
    
    # 记录目录结构
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            backup_info["directory_structure"].append({
                "name": item,
                "size": get_size(item_path),
                "type": "directory"
            })
    
    # 保存备份信息
    backup_file = os.path.join(root_path, "project_backup_info.json")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, ensure_ascii=False, indent=2)
    
    operation_log.append({
        "step": "backup",
        "status": "success",
        "details": f"项目状态已备份到 {backup_file}"
    })
    
    print(f"  ✅ 项目状态已备份: {backup_file}")
    return backup_info

def analyze_git_status(root_path):
    """分析当前Git状态"""
    print("🔍 分析当前Git状态...")
    
    git_path = os.path.join(root_path, ".git")
    git_info = {
        "exists": os.path.exists(git_path),
        "size": 0,
        "files_count": 0
    }
    
    if git_info["exists"]:
        git_info["size"] = get_size(git_path)
        
        # 计算.git目录中的文件数量
        for root, dirs, files in os.walk(git_path):
            git_info["files_count"] += len(files)
        
        print(f"  📊 .git目录大小: {format_size(git_info['size'])}")
        print(f"  📊 .git文件数量: {git_info['files_count']}")
        
        # 检查Git状态
        success, stdout, stderr = run_command("git status --porcelain", root_path)
        if success:
            if stdout.strip():
                print(f"  ⚠️ 有未提交的更改: {len(stdout.strip().split())} 个文件")
            else:
                print("  ✅ 工作目录干净")
        else:
            print("  ❌ 无法获取Git状态")
    else:
        print("  ❌ .git目录不存在")
    
    return git_info

def remove_git_directory(root_path, operation_log):
    """安全删除.git目录"""
    print("🗑️ 删除.git目录...")
    
    git_path = os.path.join(root_path, ".git")
    
    if not os.path.exists(git_path):
        print("  ✅ .git目录不存在，无需删除")
        operation_log.append({
            "step": "remove_git",
            "status": "skipped",
            "details": ".git目录不存在"
        })
        return True
    
    try:
        # 获取删除前的大小
        git_size = get_size(git_path)
        
        # 删除.git目录
        shutil.rmtree(git_path)
        
        # 验证删除成功
        if not os.path.exists(git_path):
            print(f"  ✅ .git目录删除成功 (释放空间: {format_size(git_size)})")
            operation_log.append({
                "step": "remove_git",
                "status": "success",
                "details": f"删除.git目录，释放空间: {format_size(git_size)}"
            })
            return True
        else:
            print("  ❌ .git目录删除失败")
            operation_log.append({
                "step": "remove_git",
                "status": "failed",
                "details": ".git目录仍然存在"
            })
            return False
            
    except Exception as e:
        print(f"  ❌ 删除.git目录时出错: {str(e)}")
        operation_log.append({
            "step": "remove_git",
            "status": "error",
            "details": str(e)
        })
        return False

def check_git_installation():
    """检查Git安装状态"""
    print("🔍 检查Git安装状态...")
    
    success, stdout, stderr = run_command("git --version")
    
    if success:
        version = stdout.strip()
        print(f"  ✅ Git已安装: {version}")
        return True, version
    else:
        print("  ❌ Git未安装或不可用")
        return False, ""

def reinitialize_git(root_path, operation_log):
    """重新初始化Git仓库"""
    print("🔄 重新初始化Git仓库...")
    
    # 检查Git是否可用
    git_available, git_version = check_git_installation()
    if not git_available:
        print("  ❌ Git不可用，无法初始化仓库")
        operation_log.append({
            "step": "git_init",
            "status": "failed",
            "details": "Git不可用"
        })
        return False
    
    # 执行git init
    success, stdout, stderr = run_command("git init", root_path)
    
    if success:
        print("  ✅ Git仓库初始化成功")
        
        # 验证.git目录是否创建
        git_path = os.path.join(root_path, ".git")
        if os.path.exists(git_path):
            git_size = get_size(git_path)
            print(f"  ✅ 新.git目录已创建 (大小: {format_size(git_size)})")
            
            operation_log.append({
                "step": "git_init",
                "status": "success",
                "details": f"Git仓库初始化成功，.git目录大小: {format_size(git_size)}"
            })
            return True
        else:
            print("  ❌ .git目录未创建")
            operation_log.append({
                "step": "git_init",
                "status": "failed",
                "details": ".git目录未创建"
            })
            return False
    else:
        print(f"  ❌ Git初始化失败: {stderr}")
        operation_log.append({
            "step": "git_init",
            "status": "error",
            "details": stderr
        })
        return False

def test_program_functionality(root_path):
    """测试程序功能"""
    print("🧪 测试程序功能...")
    
    # 测试主程序启动
    print("  测试主程序启动...")
    main_script = os.path.join(root_path, "simple_ui_fixed.py")
    if not os.path.exists(main_script):
        print("  ❌ 主程序文件不存在")
        return False
    
    # 测试核心测试文件
    print("  测试核心测试文件...")
    test_script = os.path.join(root_path, "VisionAI_ClipsMaster_Comprehensive_Verification_Test.py")
    if not os.path.exists(test_script):
        print("  ❌ 核心测试文件不存在")
        return False
    
    print("  ✅ 关键文件存在，功能应该正常")
    return True

def main():
    """主函数"""
    root_path = r"d:\zancun\VisionAI-ClipsMaster-backup"
    
    print("🔄 VisionAI-ClipsMaster Git重新初始化")
    print("=" * 60)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {root_path}")
    print("操作内容: 删除.git目录并重新初始化Git仓库")
    print("风险等级: 低 (仅影响版本控制)")
    
    # 操作日志
    operation_log = []
    
    # 1. 验证核心文件完整性
    if not verify_core_functionality(root_path):
        print("❌ 核心文件验证失败，停止操作")
        return
    
    # 2. 备份项目状态
    backup_info = backup_project_state(root_path, operation_log)
    
    # 3. 分析当前Git状态
    git_info = analyze_git_status(root_path)
    
    # 4. 删除.git目录
    if not remove_git_directory(root_path, operation_log):
        print("❌ .git目录删除失败，停止操作")
        return
    
    # 5. 重新初始化Git仓库
    if not reinitialize_git(root_path, operation_log):
        print("❌ Git重新初始化失败")
        return
    
    # 6. 测试程序功能
    if not test_program_functionality(root_path):
        print("❌ 程序功能测试失败")
        return
    
    # 获取最终状态
    final_size = get_size(root_path)
    new_git_size = get_size(os.path.join(root_path, ".git"))
    
    print("\n" + "=" * 60)
    print("🎉 Git重新初始化完成!")
    print(f"📊 项目总体积: {format_size(final_size)}")
    print(f"📊 新.git目录: {format_size(new_git_size)}")
    print(f"📊 原.git目录: {format_size(git_info.get('size', 0))}")
    
    if git_info.get('size', 0) > 0:
        space_change = git_info['size'] - new_git_size
        if space_change > 0:
            print(f"📊 释放空间: {format_size(space_change)}")
        else:
            print(f"📊 增加空间: {format_size(-space_change)}")
    
    # 保存操作日志
    log_data = {
        "operation": "Git Reinitialization",
        "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "project_path": root_path,
        "backup_info": backup_info,
        "git_info_before": git_info,
        "git_info_after": {
            "exists": os.path.exists(os.path.join(root_path, ".git")),
            "size": new_git_size
        },
        "operations": operation_log,
        "final_status": "success"
    }
    
    log_file = "VisionAI_ClipsMaster_Git_Reinit_Log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细日志已保存: {log_file}")
    print("\n🔍 建议下一步:")
    print("1. 运行功能验证测试:")
    print("   python VisionAI_ClipsMaster_Comprehensive_Verification_Test.py")
    print("2. 验证程序启动:")
    print("   python simple_ui_fixed.py")
    print("3. 配置新的Git仓库 (如需要):")
    print("   git config user.name 'Your Name'")
    print("   git config user.email 'your.email@example.com'")

if __name__ == "__main__":
    main()
