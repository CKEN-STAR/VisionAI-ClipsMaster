#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 第一阶段体积优化脚本
安全清理：删除缓存、临时文件、重复数据
预期减少：106MB，零风险
"""

import os
import shutil
import json
import time
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

def safe_remove(path, operation_log):
    """安全删除文件或目录"""
    try:
        if os.path.exists(path):
            size_before = get_size(path)
            if os.path.isfile(path):
                os.remove(path)
                operation_log.append({
                    "type": "file",
                    "path": path,
                    "size": size_before,
                    "status": "deleted"
                })
                return size_before
            elif os.path.isdir(path):
                shutil.rmtree(path)
                operation_log.append({
                    "type": "directory", 
                    "path": path,
                    "size": size_before,
                    "status": "deleted"
                })
                return size_before
        return 0
    except Exception as e:
        operation_log.append({
            "type": "error",
            "path": path,
            "error": str(e),
            "status": "failed"
        })
        return 0

def clean_python_cache(root_path, operation_log):
    """清理Python缓存文件"""
    print("🧹 清理Python缓存文件...")
    total_cleaned = 0
    
    # 清理 __pycache__ 目录
    for root, dirs, files in os.walk(root_path):
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            size = safe_remove(cache_path, operation_log)
            total_cleaned += size
            print(f"  ✅ 删除: {cache_path} ({format_size(size)})")
    
    # 清理 .pyc 文件
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                size = safe_remove(file_path, operation_log)
                total_cleaned += size
                print(f"  ✅ 删除: {file_path} ({format_size(size)})")
    
    return total_cleaned

def clean_temporary_files(root_path, operation_log):
    """清理临时文件和目录"""
    print("🗑️ 清理临时文件和目录...")
    total_cleaned = 0
    
    temp_targets = [
        "test_outputs",
        "outputs", 
        "results",
        "snapshots",
        "recovery"
    ]
    
    for target in temp_targets:
        target_path = os.path.join(root_path, target)
        if os.path.exists(target_path):
            size = safe_remove(target_path, operation_log)
            total_cleaned += size
            print(f"  ✅ 删除目录: {target} ({format_size(size)})")
    
    return total_cleaned

def clean_log_files(root_path, operation_log):
    """清理日志文件"""
    print("📝 清理日志文件...")
    total_cleaned = 0
    
    # 清理根目录的日志文件
    for file in os.listdir(root_path):
        if file.endswith('.log'):
            file_path = os.path.join(root_path, file)
            size = safe_remove(file_path, operation_log)
            total_cleaned += size
            print(f"  ✅ 删除日志: {file} ({format_size(size)})")
    
    # 清理logs目录
    logs_path = os.path.join(root_path, "logs")
    if os.path.exists(logs_path):
        size = safe_remove(logs_path, operation_log)
        total_cleaned += size
        print(f"  ✅ 删除logs目录: ({format_size(size)})")
    
    return total_cleaned

def remove_duplicate_test_data(root_path, operation_log):
    """删除重复的测试数据文件"""
    print("🔄 删除重复的测试数据文件...")
    total_cleaned = 0
    
    # 检查重复的test_data.bin文件
    root_test_data = os.path.join(root_path, "test_data.bin")
    examples_test_data = os.path.join(root_path, "examples", "test_data.bin")
    
    if os.path.exists(root_test_data) and os.path.exists(examples_test_data):
        # 保留根目录的，删除examples中的
        size = safe_remove(examples_test_data, operation_log)
        total_cleaned += size
        print(f"  ✅ 删除重复文件: examples/test_data.bin ({format_size(size)})")
    
    return total_cleaned

def verify_core_files(root_path):
    """验证核心文件完整性"""
    print("🔍 验证核心文件完整性...")
    
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

def main():
    """主函数"""
    root_path = r"d:\zancun\VisionAI-ClipsMaster-backup"
    
    print("🎯 VisionAI-ClipsMaster 第一阶段体积优化")
    print("=" * 60)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {root_path}")
    print("优化内容: 安全清理缓存、临时文件、重复数据")
    print("预期减少: 106MB")
    print("风险等级: 极低")
    
    # 获取初始大小
    initial_size = get_size(root_path)
    print(f"\n📊 优化前总体积: {format_size(initial_size)}")
    
    # 验证核心文件
    if not verify_core_files(root_path):
        print("❌ 核心文件验证失败，停止优化")
        return
    
    # 操作日志
    operation_log = []
    total_cleaned = 0
    
    print("\n🚀 开始优化...")
    print("-" * 40)
    
    # 1. 删除重复测试数据
    cleaned = remove_duplicate_test_data(root_path, operation_log)
    total_cleaned += cleaned
    print(f"重复数据清理完成: {format_size(cleaned)}")
    
    # 2. 清理Python缓存
    cleaned = clean_python_cache(root_path, operation_log)
    total_cleaned += cleaned
    print(f"Python缓存清理完成: {format_size(cleaned)}")
    
    # 3. 清理临时文件
    cleaned = clean_temporary_files(root_path, operation_log)
    total_cleaned += cleaned
    print(f"临时文件清理完成: {format_size(cleaned)}")
    
    # 4. 清理日志文件
    cleaned = clean_log_files(root_path, operation_log)
    total_cleaned += cleaned
    print(f"日志文件清理完成: {format_size(cleaned)}")
    
    # 获取最终大小
    final_size = get_size(root_path)
    actual_reduction = initial_size - final_size
    
    print("\n" + "=" * 60)
    print("🎉 第一阶段优化完成!")
    print(f"📊 优化前体积: {format_size(initial_size)}")
    print(f"📊 优化后体积: {format_size(final_size)}")
    print(f"📊 实际减少: {format_size(actual_reduction)}")
    print(f"📊 优化比例: {(actual_reduction/initial_size*100):.2f}%")
    print(f"📊 预期减少: 106MB")
    print(f"📊 完成度: {(actual_reduction/(106*1024*1024)*100):.1f}%")
    
    # 保存操作日志
    log_data = {
        "optimization_phase": "Phase 1 - Safe Cleanup",
        "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "initial_size": initial_size,
        "final_size": final_size,
        "actual_reduction": actual_reduction,
        "expected_reduction": 106 * 1024 * 1024,
        "operations": operation_log,
        "summary": {
            "duplicate_data_cleaned": sum(op["size"] for op in operation_log if "test_data.bin" in op.get("path", "")),
            "cache_cleaned": sum(op["size"] for op in operation_log if "__pycache__" in op.get("path", "") or op.get("path", "").endswith(".pyc")),
            "temp_files_cleaned": sum(op["size"] for op in operation_log if any(temp in op.get("path", "") for temp in ["test_outputs", "outputs", "results", "snapshots", "recovery"])),
            "logs_cleaned": sum(op["size"] for op in operation_log if op.get("path", "").endswith(".log") or "logs" in op.get("path", ""))
        }
    }
    
    log_file = "VisionAI_ClipsMaster_Phase1_Optimization_Log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细日志已保存: {log_file}")
    print("\n🔍 建议下一步:")
    print("1. 运行功能验证测试:")
    print("   python VisionAI_ClipsMaster_Comprehensive_Verification_Test.py")
    print("2. 验证程序启动:")
    print("   python simple_ui_fixed.py")
    print("3. 如果测试通过，可以考虑执行第二阶段优化")

if __name__ == "__main__":
    main()
