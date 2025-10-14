#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 版本信息
"""

# 版本信息
__version__ = "1.1.0"
__version_info__ = (1, 1, 0)

# 发布信息
__release_date__ = "2025-10-06"
__release_name__ = "智能下载器优化版"
__build_type__ = "stable"

# 兼容性信息
__min_python_version__ = "3.8"
__supported_platforms__ = ["Windows", "Linux", "macOS"]

# 功能版本
__ui_version__ = "1.1.0"
__core_version__ = "1.1.0"
__training_version__ = "1.1.0"
__export_version__ = "1.1.0"

# 模型版本
__mistral_model_version__ = "7B-v1.0"
__qwen_model_version__ = "2.5-7B-v1.0"

def get_version():
    """获取版本字符串"""
    return __version__

def get_version_info():
    """获取版本信息字典"""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_date": __release_date__,
        "release_name": __release_name__,
        "build_type": __build_type__,
        "min_python_version": __min_python_version__,
        "supported_platforms": __supported_platforms__,
        "ui_version": __ui_version__,
        "core_version": __core_version__,
        "training_version": __training_version__,
        "export_version": __export_version__,
        "mistral_model_version": __mistral_model_version__,
        "qwen_model_version": __qwen_model_version__
    }

def print_version_info():
    """打印版本信息"""
    info = get_version_info()
    print(f"🎬 VisionAI-ClipsMaster v{info['version']}")
    print(f"📅 发布日期: {info['release_date']}")
    print(f"🏷️ 发布名称: {info['release_name']}")
    print(f"🔧 构建类型: {info['build_type']}")
    print(f"🐍 最低Python版本: {info['min_python_version']}")
    print(f"💻 支持平台: {', '.join(info['supported_platforms'])}")

if __name__ == "__main__":
    print_version_info()
