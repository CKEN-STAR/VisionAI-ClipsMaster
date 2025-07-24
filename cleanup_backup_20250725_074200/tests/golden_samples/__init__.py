"""
黄金样本测试库

该包提供用于生成和管理黄金标准测试样本的工具。
"""

from tests.golden_samples.generate_samples import (
    create_golden_sample,
    calculate_video_hash,
    calculate_xml_hash,
    get_scene_types,
    update_golden_samples_index
)

# 导入清理模块
from tests.golden_samples.cleanup import (
    init_cleanup_system,
    auto_purge_temp_files,
    archive_old_reports,
    clean_cache_files
)

# 初始化清理系统（非后台模式，不启动调度器）
init_cleanup_system(enable_scheduler=False)

__all__ = [
    "create_golden_sample",
    "calculate_video_hash",
    "calculate_xml_hash",
    "get_scene_types",
    "update_golden_samples_index",
    "auto_purge_temp_files",
    "archive_old_reports",
    "clean_cache_files",
    "init_cleanup_system"
] 