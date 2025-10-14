"""
清理剪映导出器测试文件
在测试完成后运行此脚本清理所有临时文件
"""

import os
import shutil
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent


def cleanup_test_files():
    """清理所有测试文件"""
    
    print("=" * 60)
    print("清理剪映导出器测试文件")
    print("=" * 60)
    
    files_to_delete = []
    dirs_to_delete = []
    
    # 1. 测试草稿文件夹
    jianying_drafts_dir = project_root / "data" / "output" / "jianying_drafts"
    if jianying_drafts_dir.exists():
        for item in jianying_drafts_dir.iterdir():
            if item.is_dir() and item.name.startswith("VisionAI_"):
                dirs_to_delete.append(item)
    
    # 2. 测试导出文件
    test_exports_dir = project_root / "data" / "output" / "test_exports"
    if test_exports_dir.exists():
        test_format_file = test_exports_dir / "test_format_manual.json"
        if test_format_file.exists():
            files_to_delete.append(test_format_file)
    
    # 3. 旧的编辑项目文件
    edit_projects_dir = project_root / "data" / "output" / "edit_projects"
    if edit_projects_dir.exists():
        for item in edit_projects_dir.iterdir():
            if item.is_file() and item.suffix == ".json":
                # 检查是否是测试文件（文件名包含test或core_test）
                if "test" in item.name.lower():
                    files_to_delete.append(item)
    
    # 显示将要删除的文件
    print("\n将要删除的文件夹：")
    if dirs_to_delete:
        for d in dirs_to_delete:
            print(f"  - {d}")
    else:
        print("  （无）")
    
    print("\n将要删除的文件：")
    if files_to_delete:
        for f in files_to_delete:
            print(f"  - {f}")
    else:
        print("  （无）")
    
    # 确认删除
    if not dirs_to_delete and not files_to_delete:
        print("\n✅ 没有需要清理的文件")
        return
    
    print("\n" + "=" * 60)
    confirm = input("确认删除以上文件？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ 取消清理")
        return
    
    # 执行删除
    print("\n开始清理...")
    
    # 删除文件夹
    for d in dirs_to_delete:
        try:
            shutil.rmtree(d)
            print(f"✅ 已删除文件夹: {d.name}")
        except Exception as e:
            print(f"❌ 删除失败: {d.name} - {e}")
    
    # 删除文件
    for f in files_to_delete:
        try:
            f.unlink()
            print(f"✅ 已删除文件: {f.name}")
        except Exception as e:
            print(f"❌ 删除失败: {f.name} - {e}")
    
    print("\n" + "=" * 60)
    print("✅ 清理完成！")
    print("=" * 60)
    
    # 显示保留的文件
    print("\n保留的核心文件：")
    print("  核心模块：")
    print("    - src/exporters/jianying_time_converter.py")
    print("    - src/exporters/jianying_material_manager.py")
    print("    - src/exporters/jianying_track_manager.py")
    print("    - src/exporters/jianying_draft_generator.py")
    print("    - src/exporters/jianying_exporter_adapter.py")
    print("\n  集成更新：")
    print("    - src/exporters/jianying_pro_exporter.py")
    print("    - src/export/jianying_exporter.py")
    print("    - src/exporters/__init__.py")
    print("\n  文档：")
    print("    - src/exporters/README_JIANYING_NEW_EXPORTER.md")
    print("    - JIANYING_EXPORTER_IMPLEMENTATION_REPORT.md")
    print("    - JIANYING_EXPORTER_USAGE_GUIDE.md")
    print("    - FINAL_TEST_AND_CLEANUP.md")


def cleanup_all_test_files_force():
    """强制清理所有测试文件（不询问）"""
    
    print("=" * 60)
    print("强制清理所有测试文件")
    print("=" * 60)
    
    # 1. 删除测试草稿文件夹
    jianying_drafts_dir = project_root / "data" / "output" / "jianying_drafts"
    if jianying_drafts_dir.exists():
        for item in jianying_drafts_dir.iterdir():
            if item.is_dir() and item.name.startswith("VisionAI_"):
                try:
                    shutil.rmtree(item)
                    print(f"✅ 已删除: {item.name}")
                except Exception as e:
                    print(f"❌ 删除失败: {item.name} - {e}")
    
    # 2. 删除测试导出文件
    test_exports_dir = project_root / "data" / "output" / "test_exports"
    if test_exports_dir.exists():
        test_format_file = test_exports_dir / "test_format_manual.json"
        if test_format_file.exists():
            try:
                test_format_file.unlink()
                print(f"✅ 已删除: {test_format_file.name}")
            except Exception as e:
                print(f"❌ 删除失败: {test_format_file.name} - {e}")
    
    # 3. 删除旧的编辑项目测试文件
    edit_projects_dir = project_root / "data" / "output" / "edit_projects"
    if edit_projects_dir.exists():
        for item in edit_projects_dir.iterdir():
            if item.is_file() and item.suffix == ".json" and "test" in item.name.lower():
                try:
                    item.unlink()
                    print(f"✅ 已删除: {item.name}")
                except Exception as e:
                    print(f"❌ 删除失败: {item.name} - {e}")
    
    print("\n" + "=" * 60)
    print("✅ 强制清理完成！")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        cleanup_all_test_files_force()
    else:
        cleanup_test_files()

