#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理测试临时文件
清理所有测试过程中创建的临时文件、测试数据、日志文件等
"""

import sys
import os
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def cleanup_test_temp_files():
    """清理测试临时文件"""
    print("=" * 60)
    print("清理测试临时文件")
    print("=" * 60)
    
    cleaned_files = []
    
    # 测试目录中的临时文件
    test_dir = project_root / "tests"
    temp_patterns = [
        "test_temp.srt",
        "test_workflow.srt",
        "test_output.srt",
        "*.pyc",
        "__pycache__",
    ]
    
    for pattern in temp_patterns:
        if "*" in pattern:
            # 通配符模式
            for file in test_dir.glob(pattern):
                try:
                    if file.is_file():
                        file.unlink()
                        cleaned_files.append(str(file.relative_to(project_root)))
                    elif file.is_dir():
                        shutil.rmtree(file)
                        cleaned_files.append(str(file.relative_to(project_root)))
                except Exception as e:
                    print(f"⚠ 无法删除 {file}: {e}")
        else:
            # 精确文件名
            file = test_dir / pattern
            if file.exists():
                try:
                    if file.is_file():
                        file.unlink()
                        cleaned_files.append(str(file.relative_to(project_root)))
                    elif file.is_dir():
                        shutil.rmtree(file)
                        cleaned_files.append(str(file.relative_to(project_root)))
                except Exception as e:
                    print(f"⚠ 无法删除 {file}: {e}")
    
    print(f"✓ 清理了 {len(cleaned_files)} 个测试临时文件")
    for file in cleaned_files:
        print(f"  - {file}")
    
    print()


def cleanup_log_files():
    """清理日志文件"""
    print("=" * 60)
    print("清理日志文件")
    print("=" * 60)
    
    cleaned_logs = []
    
    # 查找日志文件
    log_patterns = [
        "*.log",
        "logs/*.log",
    ]
    
    for pattern in log_patterns:
        for log_file in project_root.glob(pattern):
            # 保留最近的日志文件，删除旧的
            if log_file.is_file():
                try:
                    # 检查文件大小，如果超过10MB则清理
                    file_size = log_file.stat().st_size
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        log_file.unlink()
                        cleaned_logs.append(str(log_file.relative_to(project_root)))
                except Exception as e:
                    print(f"⚠ 无法删除 {log_file}: {e}")
    
    print(f"✓ 清理了 {len(cleaned_logs)} 个大型日志文件")
    for log in cleaned_logs:
        print(f"  - {log}")
    
    print()


def cleanup_cache_files():
    """清理缓存文件"""
    print("=" * 60)
    print("清理缓存文件")
    print("=" * 60)
    
    cleaned_cache = []
    
    # Python缓存
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            try:
                # 排除.venv目录
                if ".venv" not in str(pycache):
                    shutil.rmtree(pycache)
                    cleaned_cache.append(str(pycache.relative_to(project_root)))
            except Exception as e:
                print(f"⚠ 无法删除 {pycache}: {e}")
    
    # .pyc文件
    for pyc_file in project_root.rglob("*.pyc"):
        if pyc_file.is_file():
            try:
                # 排除.venv目录
                if ".venv" not in str(pyc_file):
                    pyc_file.unlink()
                    cleaned_cache.append(str(pyc_file.relative_to(project_root)))
            except Exception as e:
                print(f"⚠ 无法删除 {pyc_file}: {e}")
    
    print(f"✓ 清理了 {len(cleaned_cache)} 个缓存文件/目录")
    if len(cleaned_cache) > 0:
        print(f"  显示前5个:")
        for cache in cleaned_cache[:5]:
            print(f"  - {cache}")
    
    print()


def cleanup_temp_directories():
    """清理临时目录"""
    print("=" * 60)
    print("清理临时目录")
    print("=" * 60)
    
    cleaned_dirs = []
    
    # 系统临时目录中的项目临时文件
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    
    # 查找VisionAI相关的临时目录
    visionai_temp_patterns = [
        "visionai_clips",
        "visionai_*",
    ]
    
    for pattern in visionai_temp_patterns:
        for temp_path in temp_dir.glob(pattern):
            if temp_path.is_dir():
                try:
                    # 检查目录是否为空或很旧
                    shutil.rmtree(temp_path)
                    cleaned_dirs.append(str(temp_path))
                except Exception as e:
                    print(f"⚠ 无法删除 {temp_path}: {e}")
    
    print(f"✓ 清理了 {len(cleaned_dirs)} 个临时目录")
    for dir_path in cleaned_dirs:
        print(f"  - {dir_path}")
    
    print()


def cleanup_test_outputs():
    """清理测试输出文件"""
    print("=" * 60)
    print("清理测试输出文件")
    print("=" * 60)
    
    cleaned_outputs = []
    
    # 测试输出文件模式
    output_patterns = [
        "tests/test_*.mp4",
        "tests/test_*.srt",
        "tests/output_*.mp4",
        "tests/output_*.srt",
    ]
    
    for pattern in output_patterns:
        for output_file in project_root.glob(pattern):
            if output_file.is_file():
                try:
                    output_file.unlink()
                    cleaned_outputs.append(str(output_file.relative_to(project_root)))
                except Exception as e:
                    print(f"⚠ 无法删除 {output_file}: {e}")
    
    print(f"✓ 清理了 {len(cleaned_outputs)} 个测试输出文件")
    for output in cleaned_outputs:
        print(f"  - {output}")
    
    print()


def generate_cleanup_report():
    """生成清理报告"""
    print("=" * 60)
    print("生成清理报告")
    print("=" * 60)
    
    report = []
    report.append("# 测试文件清理报告")
    report.append("")
    report.append(f"清理时间: {Path(__file__).stat().st_mtime}")
    report.append("")
    
    # 统计当前测试文件
    test_files = list((project_root / "tests").glob("test_*.py"))
    report.append(f"## 当前测试文件")
    report.append(f"- 测试文件数: {len(test_files)}")
    for test_file in sorted(test_files):
        report.append(f"  - {test_file.name}")
    report.append("")
    
    # 统计项目大小
    total_size = 0
    file_count = 0
    for file in project_root.rglob("*"):
        if file.is_file() and ".venv" not in str(file) and ".git" not in str(file):
            try:
                total_size += file.stat().st_size
                file_count += 1
            except:
                pass
    
    report.append(f"## 项目统计")
    report.append(f"- 文件总数: {file_count}")
    report.append(f"- 总大小: {total_size / 1024 / 1024:.2f} MB")
    report.append("")
    
    report_content = "\n".join(report)
    
    # 保存报告
    report_path = project_root / "tests" / "cleanup_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ 清理报告已生成: {report_path}")
    print()


def main():
    """运行所有清理任务"""
    print("\n" + "=" * 60)
    print("测试文件清理工具")
    print("=" * 60 + "\n")
    
    try:
        cleanup_test_temp_files()
        cleanup_log_files()
        cleanup_cache_files()
        cleanup_temp_directories()
        cleanup_test_outputs()
        generate_cleanup_report()
        
        print("=" * 60)
        print("✓ 所有清理任务完成！")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 清理过程出错: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

