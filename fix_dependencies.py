#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 依赖修复脚本
自动安装缺失的关键依赖项
"""

import subprocess
import sys

def install_package(package_name):
    """安装单个包"""
    try:
        print(f"正在安装 {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始修复VisionAI-ClipsMaster依赖项...")
    print("=" * 50)

    # 需要安装的包列表
    packages_to_install = [
        "advanced_emotion_analysis_engine",  # advanced_emotion_analysis_engine - 1 个文件使用
        "event_tracer",  # event_tracer - 1 个文件使用
        "placeholder",  # placeholder - 1 个文件使用
        "legal_injector",  # legal_injector - 1 个文件使用
        "advanced_plot_point_analyzer",  # advanced_plot_point_analyzer - 1 个文件使用
        "chinese_ui_engine",  # chinese_ui_engine - 1 个文件使用
        "window_initializer",  # window_initializer - 1 个文件使用
        "main_layout",  # main_layout - 1 个文件使用
        "encoding_fix",  # encoding_fix - 1 个文件使用
        "visionai_clipsmaster",  # visionai_clipsmaster - 1 个文件使用
        "emotion_continuity_standalone",  # emotion_continuity_standalone - 1 个文件使用
        "resource",  # resource - 1 个文件使用
        "modelscope",  # modelscope - 1 个文件使用
        "tabulate",  # tabulate - 6 个文件使用
        "knowledge_service",  # knowledge_service - 1 个文件使用
        "lxml",  # lxml - 1 个文件使用
    ]

    success_count = 0
    total_count = len(packages_to_install)

    for package in packages_to_install:
        if install_package(package):
            success_count += 1

    print("=" * 50)
    print(f"安装完成: {success_count}/{total_count} 个包安装成功")

    if success_count == total_count:
        print("✅ 所有依赖项安装成功！")
    else:
        print("⚠️  部分依赖项安装失败，请手动检查")

if __name__ == "__main__":
    main()
