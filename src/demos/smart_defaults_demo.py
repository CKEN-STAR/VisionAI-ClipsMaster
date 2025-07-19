#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能默认值引擎演示脚本

展示智能默认值引擎的功能和用法。
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.config.defaults import smart_defaults
    from src.config.smart_updater import smart_updater, initialize_updater
    from src.config.config_manager import config_manager
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

def print_section(title):
    """打印带有分隔线的节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "-"))
    print("=" * 60)

def print_json(data):
    """格式化打印JSON数据"""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def detect_hardware():
    """检测并显示硬件感知设置"""
    print_section("硬件感知智能默认值")
    hw_defaults = smart_defaults.get_hardware_aware_defaults()
    
    print("基于系统硬件检测的推荐设置:")
    print_json(hw_defaults)
    
    if hw_defaults.get("resolution") == "4K":
        print("\n✓ 检测到您的GPU支持4K处理")
    else:
        print("\n✓ 推荐使用1080p作为最佳分辨率")
    
    print(f"\n✓ 推荐的显示刷新率: {hw_defaults.get('frame_rate')}fps")
    print(f"✓ 建议的GPU内存限制: {hw_defaults.get('gpu_memory')}MB")
    print(f"✓ 最佳CPU线程数: {hw_defaults.get('cpu_threads')}")
    print(f"✓ 推荐缓存大小: {hw_defaults.get('cache_size')}MB")
    
    print("\n这些设置将根据您的硬件能力自动调整，以获得最佳性能。")

def detect_software():
    """检测并显示软件环境感知设置"""
    print_section("软件环境感知智能默认值")
    sw_defaults = smart_defaults.get_software_aware_defaults()
    
    print("基于系统软件环境检测的推荐设置:")
    print_json(sw_defaults)
    
    print(f"\n✓ 推荐界面语言: {sw_defaults.get('language')}")
    print(f"✓ 最佳编解码器: {sw_defaults.get('codec')}")
    print(f"✓ 匹配系统的界面主题: {sw_defaults.get('theme')}")
    
    print("\n这些设置将根据您的系统环境自动调整，以获得最佳用户体验。")

def detect_usage():
    """检测并显示使用模式感知设置"""
    print_section("使用模式感知智能默认值")
    usage_defaults = smart_defaults.get_usage_aware_defaults()
    
    print("基于使用模式预测的推荐设置:")
    print_json(usage_defaults)
    
    print(f"\n✓ 建议的自动保存间隔: {usage_defaults.get('auto_save_interval')}分钟")
    print(f"✓ 推荐的导出预设: {usage_defaults.get('export_preset')}")
    print(f"✓ 适合您显示器的时间线缩放级别: {usage_defaults.get('timeline_zoom')}")
    
    print("\n随着您使用软件，这些设置将逐渐学习您的偏好并自动调整。")

def apply_settings(force=False):
    """将智能默认值应用到配置"""
    print_section("应用智能默认值到配置")
    
    # 获取应用前的配置
    try:
        before = {
            "resolution": config_manager.get_config("user", "export.resolution"),
            "frame_rate": config_manager.get_config("user", "export.frame_rate"),
            "gpu_memory": config_manager.get_config("system", "gpu.memory_limit"),
            "threads": config_manager.get_config("system", "cpu.threads"),
            "theme": config_manager.get_config("app", "theme")
        }
        print("当前配置:")
        print_json(before)
    except Exception as e:
        print(f"获取当前配置失败: {str(e)}")
        before = {}
    
    # 应用智能默认值
    print("\n正在应用智能默认值...")
    result = smart_defaults.apply_to_config(config_manager, override_existing=force)
    print(f"应用结果: {'成功' if result else '失败'}")
    
    # 获取应用后的配置
    try:
        after = {
            "resolution": config_manager.get_config("user", "export.resolution"),
            "frame_rate": config_manager.get_config("user", "export.frame_rate"),
            "gpu_memory": config_manager.get_config("system", "gpu.memory_limit"),
            "threads": config_manager.get_config("system", "cpu.threads"),
            "theme": config_manager.get_config("app", "theme")
        }
        print("\n应用后的配置:")
        print_json(after)
        
        # 显示变化
        print("\n配置变化:")
        for key in before:
            if key in after and before[key] != after[key]:
                print(f"✓ {key}: {before[key]} -> {after[key]}")
            elif key in after and before[key] == after[key]:
                print(f"- {key}: 未变化 ({before[key]})")
    except Exception as e:
        print(f"获取更新后配置失败: {str(e)}")

def usage_simulation():
    """模拟用户使用模式并更新统计"""
    print_section("用户使用模式模拟")
    
    # 初始化智能更新器
    updater = initialize_updater()
    if not updater:
        print("初始化智能更新器失败")
        return
    
    print("模拟用户导出操作...")
    # 模拟多次导出 1080p h264 mp4
    for _ in range(5):
        updater.update_export_stats("1080p", "h264", "mp4")
    
    # 模拟导出 4K h265 mp4
    for _ in range(2):
        updater.update_export_stats("4K", "h265", "mp4")
    
    # 模拟界面使用
    print("模拟用户界面操作...")
    for _ in range(3):
        updater.update_interface_stats(5, "dark")
    
    for _ in range(2):
        updater.update_interface_stats(6, "dark")
    
    # 模拟性能指标
    print("模拟性能监测...")
    for render_time in [1.2, 1.5, 1.3, 1.8, 1.4]:
        updater.update_performance_stats(render_time, 2048 + render_time * 100)
    
    print("\n已记录模拟使用数据，运行智能更新...")
    result = updater.check_and_update(force=True)
    print(f"更新结果: {'已更新设置' if result else '无需更新'}")
    
    # 获取最常用设置
    print("\n根据使用模式检测到的最常用设置:")
    print(f"最常用分辨率: {updater.get_most_used_setting('export', 'resolutions')}")
    print(f"最常用编解码器: {updater.get_most_used_setting('export', 'codecs')}")
    print(f"最常用格式: {updater.get_most_used_setting('export', 'formats')}")
    print(f"最常用时间线缩放: {updater.get_most_used_setting('interface', 'timeline_zoom')}")
    print(f"最常用主题: {updater.get_most_used_setting('interface', 'theme')}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="智能默认值引擎演示")
    parser.add_argument('--all', action='store_true', help="运行所有演示")
    parser.add_argument('--hardware', action='store_true', help="仅运行硬件检测")
    parser.add_argument('--software', action='store_true', help="仅运行软件环境检测")
    parser.add_argument('--usage', action='store_true', help="仅运行使用模式检测")
    parser.add_argument('--apply', action='store_true', help="应用智能默认值到配置")
    parser.add_argument('--force', action='store_true', help="强制覆盖已有设置")
    parser.add_argument('--simulate', action='store_true', help="模拟用户使用模式")
    
    args = parser.parse_args()
    
    # 如果没有指定具体参数，运行所有演示
    run_all = args.all or not (args.hardware or args.software or args.usage or args.apply or args.simulate)
    
    print_section("VisionAI-ClipsMaster 智能默认值引擎演示")
    print("智能默认值引擎可以根据您的系统硬件、软件环境和使用习惯，")
    print("自动调整最佳设置，提供个性化的用户体验。")
    
    if run_all or args.hardware:
        detect_hardware()
    
    if run_all or args.software:
        detect_software()
    
    if run_all or args.usage:
        detect_usage()
    
    if run_all or args.apply:
        apply_settings(force=args.force)
    
    if run_all or args.simulate:
        usage_simulation()
    
    print_section("演示结束")
    print("智能默认值引擎可以持续学习用户习惯，随着使用时间的增长，")
    print("推荐设置将变得更加准确和个性化。\n")

if __name__ == "__main__":
    main() 