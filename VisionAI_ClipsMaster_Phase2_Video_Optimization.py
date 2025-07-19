#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 第二阶段体积优化脚本
测试视频文件优化：保留核心测试必需的视频文件，删除冗余或重复的测试视频
预期减少：350-400MB
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

def analyze_video_files(video_dir):
    """分析视频文件，确定保留和删除策略"""
    print(f"🔍 分析视频目录: {video_dir}")
    
    video_files = []
    for file in os.listdir(video_dir):
        if file.endswith('.mp4'):
            file_path = os.path.join(video_dir, file)
            size = get_size(file_path)
            video_files.append({
                'name': file,
                'path': file_path,
                'size': size,
                'srt_exists': os.path.exists(file_path.replace('.mp4', '.srt'))
            })
    
    # 按大小排序
    video_files.sort(key=lambda x: x['size'], reverse=True)
    
    print(f"📊 发现 {len(video_files)} 个视频文件:")
    for video in video_files:
        srt_status = "✅" if video['srt_exists'] else "❌"
        print(f"  {format_size(video['size']):>10} | {video['name']} | SRT: {srt_status}")
    
    return video_files

def determine_keep_delete_strategy(video_files):
    """确定保留和删除策略"""
    print(f"\n🎯 制定保留/删除策略...")
    
    # 核心测试文件（必须保留）
    core_test_files = [
        'base_30s.mp4',      # 基础30秒测试
        'edge_5s.mp4',       # 边界5秒测试
        'action_scene.mp4',  # 动作场景测试
        'dialog_heavy.mp4',  # 对话重测试
        'special_chars.mp4'  # 特殊字符测试
    ]
    
    # 数字编号文件保留策略（保留小文件，删除大文件）
    numbered_files = [v for v in video_files if v['name'].split('.')[0].isdigit()]
    numbered_files.sort(key=lambda x: x['size'])  # 按大小排序，小的在前
    
    keep_files = []
    delete_files = []
    
    for video in video_files:
        file_name = video['name']
        
        # 1. 核心测试文件必须保留
        if file_name in core_test_files:
            keep_files.append(video)
            print(f"  ✅ 保留核心测试文件: {file_name}")
            continue
        
        # 2. 数字编号文件策略：保留前3个最小的，删除其余
        if file_name.split('.')[0].isdigit():
            if video in numbered_files[:3]:  # 保留最小的3个
                keep_files.append(video)
                print(f"  ✅ 保留小型数字文件: {file_name} ({format_size(video['size'])})")
            else:
                delete_files.append(video)
                print(f"  🗑️ 删除大型数字文件: {file_name} ({format_size(video['size'])})")
            continue
        
        # 3. 其他文件：如果有对应的SRT文件且文件较小，则保留
        if video['srt_exists'] and video['size'] < 20 * 1024 * 1024:  # 小于20MB
            keep_files.append(video)
            print(f"  ✅ 保留小型配对文件: {file_name} ({format_size(video['size'])})")
        else:
            delete_files.append(video)
            print(f"  🗑️ 删除大型/无配对文件: {file_name} ({format_size(video['size'])})")
    
    total_keep_size = sum(v['size'] for v in keep_files)
    total_delete_size = sum(v['size'] for v in delete_files)
    
    print(f"\n📊 策略总结:")
    print(f"  保留文件: {len(keep_files)} 个, {format_size(total_keep_size)}")
    print(f"  删除文件: {len(delete_files)} 个, {format_size(total_delete_size)}")
    print(f"  预期减少: {format_size(total_delete_size)}")
    
    return keep_files, delete_files

def safe_delete_videos(delete_files, operation_log):
    """安全删除视频文件"""
    print(f"\n🗑️ 开始删除冗余视频文件...")
    total_deleted = 0
    
    for video in delete_files:
        try:
            # 删除视频文件
            if os.path.exists(video['path']):
                size = get_size(video['path'])
                os.remove(video['path'])
                total_deleted += size
                operation_log.append({
                    "type": "video_file",
                    "path": video['path'],
                    "size": size,
                    "status": "deleted"
                })
                print(f"  ✅ 删除视频: {video['name']} ({format_size(size)})")
            
            # 删除对应的SRT文件
            srt_path = video['path'].replace('.mp4', '.srt')
            if os.path.exists(srt_path):
                srt_size = get_size(srt_path)
                os.remove(srt_path)
                total_deleted += srt_size
                operation_log.append({
                    "type": "srt_file",
                    "path": srt_path,
                    "size": srt_size,
                    "status": "deleted"
                })
                print(f"  ✅ 删除字幕: {os.path.basename(srt_path)} ({format_size(srt_size)})")
                
        except Exception as e:
            operation_log.append({
                "type": "error",
                "path": video['path'],
                "error": str(e),
                "status": "failed"
            })
            print(f"  ❌ 删除失败: {video['name']} - {str(e)}")
    
    return total_deleted

def verify_core_functionality(root_path):
    """验证核心功能文件完整性"""
    print(f"\n🔍 验证核心功能文件完整性...")
    
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
    video_dir = os.path.join(root_path, "tests", "golden_samples", "zh")
    
    print("🎯 VisionAI-ClipsMaster 第二阶段体积优化")
    print("=" * 60)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {root_path}")
    print(f"视频目录: {video_dir}")
    print("优化内容: 测试视频文件优化")
    print("预期减少: 350-400MB")
    print("风险等级: 中等")
    
    # 获取初始大小
    initial_size = get_size(root_path)
    initial_video_size = get_size(video_dir)
    print(f"\n📊 优化前总体积: {format_size(initial_size)}")
    print(f"📊 视频目录体积: {format_size(initial_video_size)}")
    
    # 验证核心文件
    if not verify_core_functionality(root_path):
        print("❌ 核心文件验证失败，停止优化")
        return
    
    # 分析视频文件
    video_files = analyze_video_files(video_dir)
    if not video_files:
        print("❌ 未发现视频文件，停止优化")
        return
    
    # 制定策略
    keep_files, delete_files = determine_keep_delete_strategy(video_files)
    
    # 确认操作
    print(f"\n⚠️ 即将删除 {len(delete_files)} 个视频文件")
    print("按 Enter 继续，或 Ctrl+C 取消...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
        return
    
    # 操作日志
    operation_log = []
    
    print("\n🚀 开始优化...")
    print("-" * 40)
    
    # 删除冗余视频文件
    deleted_size = safe_delete_videos(delete_files, operation_log)
    
    # 获取最终大小
    final_size = get_size(root_path)
    final_video_size = get_size(video_dir)
    actual_reduction = initial_size - final_size
    
    print("\n" + "=" * 60)
    print("🎉 第二阶段优化完成!")
    print(f"📊 优化前总体积: {format_size(initial_size)}")
    print(f"📊 优化后总体积: {format_size(final_size)}")
    print(f"📊 实际减少: {format_size(actual_reduction)}")
    print(f"📊 优化比例: {(actual_reduction/initial_size*100):.2f}%")
    print(f"📊 视频目录: {format_size(initial_video_size)} -> {format_size(final_video_size)}")
    print(f"📊 预期减少: 350-400MB")
    print(f"📊 完成度: {(actual_reduction/(375*1024*1024)*100):.1f}%")
    
    # 保存操作日志
    log_data = {
        "optimization_phase": "Phase 2 - Video Optimization",
        "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "initial_size": initial_size,
        "final_size": final_size,
        "actual_reduction": actual_reduction,
        "expected_reduction": 375 * 1024 * 1024,  # 375MB平均值
        "video_optimization": {
            "initial_video_size": initial_video_size,
            "final_video_size": final_video_size,
            "video_reduction": initial_video_size - final_video_size,
            "files_kept": len(keep_files),
            "files_deleted": len(delete_files)
        },
        "operations": operation_log
    }
    
    log_file = "VisionAI_ClipsMaster_Phase2_Video_Optimization_Log.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细日志已保存: {log_file}")
    print("\n🔍 建议下一步:")
    print("1. 运行功能验证测试:")
    print("   python VisionAI_ClipsMaster_Comprehensive_Verification_Test.py")
    print("2. 验证程序启动:")
    print("   python simple_ui_fixed.py")
    print("3. 检查测试视频功能是否正常")

if __name__ == "__main__":
    main()
