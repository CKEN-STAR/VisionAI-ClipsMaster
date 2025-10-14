#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据清理工具

清理项目中的测试文件和临时数据
"""

import os
import shutil
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def cleanup_test_outputs():
    """清理测试输出文件"""
    print("=" * 60)
    print("清理测试输出文件")
    print("=" * 60)
    
    # 测试输出目录
    test_dirs = [
        "data/output/test_exports",
        "data/output/real_jianying_draft",
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"✓ 删除目录: {test_dir}")
            except Exception as e:
                print(f"✗ 删除失败: {test_dir} - {e}")
    
    print()


def cleanup_test_edit_projects():
    """清理测试编辑项目"""
    print("=" * 60)
    print("清理测试编辑项目")
    print("=" * 60)
    
    edit_projects_dir = "data/output/edit_projects"
    
    if not os.path.exists(edit_projects_dir):
        print("编辑项目目录不存在")
        return
    
    # 测试项目关键词
    test_keywords = [
        "test_",
        "core_test",
        "compatibility_test",
        "performance_test",
        "timeline_test",
        "workflow_test",
        "integrity_test",
        "real_test",
    ]
    
    deleted_count = 0
    
    for filename in os.listdir(edit_projects_dir):
        filepath = os.path.join(edit_projects_dir, filename)
        
        # 检查是否是测试文件
        is_test_file = any(keyword in filename.lower() for keyword in test_keywords)
        
        if is_test_file and os.path.isfile(filepath):
            try:
                os.remove(filepath)
                print(f"✓ 删除文件: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ 删除失败: {filename} - {e}")
    
    print(f"\n共删除 {deleted_count} 个测试项目文件")
    print()


def cleanup_test_videos():
    """清理测试视频"""
    print("=" * 60)
    print("清理测试视频")
    print("=" * 60)
    
    final_videos_dir = "data/output/final_videos"
    
    if not os.path.exists(final_videos_dir):
        print("视频输出目录不存在")
        return
    
    # 测试视频关键词
    test_keywords = [
        "test_",
        "workflow_test",
    ]
    
    deleted_count = 0
    
    for filename in os.listdir(final_videos_dir):
        filepath = os.path.join(final_videos_dir, filename)
        
        # 检查是否是测试文件
        is_test_file = any(keyword in filename.lower() for keyword in test_keywords)
        
        if is_test_file and os.path.isfile(filepath):
            try:
                os.remove(filepath)
                print(f"✓ 删除文件: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ 删除失败: {filename} - {e}")
    
    print(f"\n共删除 {deleted_count} 个测试视频文件")
    print()


def cleanup_old_reports():
    """清理旧报告"""
    print("=" * 60)
    print("清理旧报告")
    print("=" * 60)
    
    reports_dir = "data/output/reports"
    
    if not os.path.exists(reports_dir):
        print("报告目录不存在")
        return
    
    deleted_count = 0
    
    for filename in os.listdir(reports_dir):
        filepath = os.path.join(reports_dir, filename)
        
        if os.path.isfile(filepath):
            try:
                os.remove(filepath)
                print(f"✓ 删除文件: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ 删除失败: {filename} - {e}")
    
    print(f"\n共删除 {deleted_count} 个报告文件")
    print()


def keep_real_draft():
    """保留真实测试草稿"""
    print("=" * 60)
    print("保留真实测试草稿")
    print("=" * 60)
    
    draft_dir = "data/output/真实测试项目"
    
    if os.path.exists(draft_dir):
        print(f"✓ 保留草稿: {draft_dir}")
        print("  这是用于验证剪映导出功能的真实草稿")
    else:
        print("真实测试草稿不存在")
    
    print()


def cleanup_all():
    """清理所有测试数据"""
    print("\n" + "=" * 60)
    print("开始清理测试数据")
    print("=" * 60 + "\n")
    
    cleanup_test_outputs()
    cleanup_test_edit_projects()
    cleanup_test_videos()
    cleanup_old_reports()
    keep_real_draft()
    
    print("=" * 60)
    print("清理完成")
    print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试数据清理工具')
    parser.add_argument('--all', action='store_true', help='清理所有测试数据')
    parser.add_argument('--outputs', action='store_true', help='只清理测试输出')
    parser.add_argument('--projects', action='store_true', help='只清理测试项目')
    parser.add_argument('--videos', action='store_true', help='只清理测试视频')
    parser.add_argument('--reports', action='store_true', help='只清理旧报告')
    
    args = parser.parse_args()
    
    if args.all or not any([args.outputs, args.projects, args.videos, args.reports]):
        cleanup_all()
    else:
        if args.outputs:
            cleanup_test_outputs()
        if args.projects:
            cleanup_test_edit_projects()
        if args.videos:
            cleanup_test_videos()
        if args.reports:
            cleanup_old_reports()


if __name__ == "__main__":
    main()

