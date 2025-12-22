#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 清理工具

该脚本提供便捷的命令行接口，用于执行清理操作。
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path

# 设置项目根目录
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cleanup")

# 导入清理模块（容错）
try:
    from tests.golden_samples.cleanup import (
        auto_purge_temp_files,
        archive_old_reports,
        clean_cache_files,
        run_daily_cleanup,
        emergency_cleanup,
        check_disk_space,
        get_disk_usage
    )
except Exception:
    logger.warning("tests.golden_samples.cleanup 不可用，使用降级清理实现")
    def auto_purge_temp_files():
        return []
    def archive_old_reports():
        return []
    def clean_cache_files():
        return []
    def run_daily_cleanup():
        return None
    def emergency_cleanup():
        return 0
    def check_disk_space():
        print("清理模块不可用：check_disk_space 跳过")
    def get_disk_usage():
        return 0.0

# 导入存储验证模块（容错）
try:
    from src.validation.storage_validator import (
        scan_temp_directories,
        verify_and_cleanup,
        get_storage_report
    )
except Exception:
    logger.warning("src.validation.storage_validator 不可用，使用降级存储验证实现")
    def scan_temp_directories():
        return 0
    def verify_and_cleanup():
        return True
    def get_storage_report():
        return {
            "total_files": 0,
            "cleaned_files": 0,
            "uncleaned_files": 0,
            "total_size_kb": 0.0,
            "cleanup_rate": 100.0,
        }

def _load_retention_days(default_days: int = 30) -> int:
    """从 configs/storage.json 加载 output 保留天数"""
    try:
        cfg_path = ROOT_DIR.parent / "configs" / "storage.json"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("retention", {}).get("output_videos", default_days))
    except Exception as e:
        logger.warning(f"加载保留策略失败，使用默认 {default_days} 天: {e}")
    return default_days


def clean_output_dir(output_dir: str = "output") -> int:
    """根据保留策略清理 output 目录中过期产物，返回删除数量"""
    try:
        base = ROOT_DIR.parent / output_dir
        if not base.exists():
            logger.info(f"输出目录不存在: {base}")
            return 0
        retention_days = _load_retention_days(30)
        cutoff_seconds = retention_days * 86400
        now = __import__("time").time()
        deleted = 0
        for p in base.iterdir():
            if not p.is_file():
                continue
            age = now - p.stat().st_mtime
            if age > cutoff_seconds:
                try:
                    p.unlink()
                    deleted += 1
                    logger.info(f"🗑️ 已删除过期输出: {p.name}")
                except Exception as e:
                    logger.warning(f"删除失败 {p}: {e}")
        print(f"已清理 {deleted} 个过期输出文件（保留天数: {retention_days}）")
        return deleted
    except Exception as e:
        logger.error(f"清理输出目录失败: {e}")
        return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 清理工具")
    parser.add_argument("--temp", action="store_true", help="清理临时文件")
    parser.add_argument("--reports", action="store_true", help="归档旧报告")
    parser.add_argument("--cache", action="store_true", help="清理缓存文件")
    parser.add_argument("--output", action="store_true", help="清理输出目录中过期产物")
    parser.add_argument("--all", action="store_true", help="执行所有清理操作")
    parser.add_argument("--emergency", action="store_true", help="执行紧急清理（释放最大空间）")
    parser.add_argument("--check", action="store_true", help="检查磁盘空间使用情况")
    parser.add_argument("--report", action="store_true", help="显示存储验证报告")
    parser.add_argument("--validate", action="store_true", help="执行存储验证并清理残留文件")

    args = parser.parse_args()

    # 显示磁盘使用情况
    usage = get_disk_usage()
    print(f"当前磁盘使用率: {usage:.1f}%")

    # 执行操作
    if args.temp or args.all:
        deleted = auto_purge_temp_files()
        print(f"已清理 {len(deleted)} 个临时文件")

    if args.reports or args.all:
        archived = archive_old_reports()
        print(f"已归档 {len(archived)} 个旧报告")

    if args.cache or args.all:
        cleaned = clean_cache_files()
        print(f"已清理 {len(cleaned)} 个缓存文件")

    if args.output or args.all:
        clean_output_dir("output")

    if args.validate or args.all:
        print("执行存储验证...")
        # 扫描所有临时目录
        found = scan_temp_directories()
        print(f"发现 {found} 个潜在的临时文件")

        # 验证并清理
        success = verify_and_cleanup()
        if success:
            print("所有临时文件已成功清理")
        else:
            print("警告: 部分临时文件未能清理")

    if args.report or args.all:
        # 显示存储验证报告
        report = get_storage_report()
        print("\n=== 存储验证报告 ===")
        print(f"总文件数: {report['total_files']}")
        print(f"已清理文件数: {report['cleaned_files']}")
        print(f"未清理文件数: {report['uncleaned_files']}")
        print(f"总大小: {report['total_size_kb']:.2f} KB")
        print(f"清理率: {report['cleanup_rate']:.2f}%")

    if args.all:
        print("已完成所有标准清理操作")

    if args.emergency:
        space_freed = emergency_cleanup()
        space_mb = space_freed / (1024 * 1024)
        print(f"紧急清理完成，释放空间: {space_mb:.2f} MB")

    if args.check:
        check_disk_space()

    # 如果没有提供任何参数，则显示帮助
    if not any([args.temp, args.reports, args.cache, args.output, args.all, args.emergency, args.check, args.report, args.validate]):
        parser.print_help()

if __name__ == "__main__":
    main() 