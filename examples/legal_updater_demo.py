#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 法律声明更新器演示

此脚本演示了法律声明更新器的基本功能：
1. 检查法律模板更新
2. 自动下载最新的法律模板
3. 查看更新历史
4. 配置更新设置
"""

import os
import sys
import time
import datetime
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入法律更新器模块
from src.exporters.legal_updater import (
    LegalWatcher,
    check_legal_updates,
    download_new_templates,
    legal_watcher
)

# 导入法律文本加载器
from src.utils.legal_text_loader import load_legal_text


def print_separator(title):
    """打印分隔线和标题"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "-"))
    print("=" * 50)


def demo_check_update():
    """演示检查更新功能"""
    print_separator("检查法律模板更新")
    
    # 获取更新前的版权文本
    copyright_zh_before = load_legal_text("copyright", "zh")
    print(f"更新前中文版权声明: {copyright_zh_before}")
    
    # 检查更新（强制更新，忽略时间间隔）
    has_update = check_legal_updates(force=True)
    
    if has_update:
        print("发现法律模板更新！")
        
        # 检查是否已经自动下载
        copyright_zh_after = load_legal_text("copyright", "zh")
        if copyright_zh_before != copyright_zh_after:
            print("更新已自动下载并应用")
            print(f"更新后中文版权声明: {copyright_zh_after}")
        else:
            print("自动更新已禁用，未下载更新")
    else:
        print("法律模板已是最新版本")


def demo_manual_download():
    """演示手动下载更新功能"""
    print_separator("手动下载法律模板更新")
    
    # 手动下载更新
    success = download_new_templates()
    
    if success:
        print("已成功下载最新法律模板")
        
        # 显示更新后的版权文本
        copyright_zh = load_legal_text("copyright", "zh")
        copyright_en = load_legal_text("disclaimer", "en")
        
        print(f"更新后中文版权声明: {copyright_zh}")
        print(f"更新后英文免责声明: {copyright_en}")
    else:
        print("下载法律模板失败")


def demo_update_history():
    """演示查看更新历史"""
    print_separator("查看更新历史")
    
    # 获取更新历史
    history = legal_watcher.get_update_history()
    
    if history:
        print(f"共有 {len(history)} 条更新记录:")
        for i, record in enumerate(history, 1):
            date = datetime.datetime.fromisoformat(record.get("date", "")).strftime("%Y-%m-%d %H:%M:%S")
            version = record.get("version", "未知版本")
            status = "成功" if record.get("success", False) else "失败"
            error = record.get("error", "")
            
            print(f"{i}. [{date}] 版本: {version}, 状态: {status}")
            if error:
                print(f"   错误: {error}")
    else:
        print("暂无更新历史记录")


def demo_update_settings():
    """演示配置更新设置"""
    print_separator("配置更新设置")
    
    # 显示当前设置
    print(f"当前设置:")
    print(f"  - 自动更新: {'启用' if legal_watcher.auto_update else '禁用'}")
    print(f"  - 检查间隔: {legal_watcher.check_interval}天")
    print(f"  - 更新服务器: {legal_watcher.update_url}")
    
    # 修改设置
    print("\n临时修改设置:")
    
    # 禁用自动更新
    legal_watcher.set_auto_update(False)
    print(f"  - 已禁用自动更新")
    
    # 修改检查间隔
    legal_watcher.set_check_interval(14)
    print(f"  - 已将检查间隔设为14天")
    
    # 恢复设置
    print("\n恢复设置:")
    legal_watcher.set_auto_update(True)
    legal_watcher.set_check_interval(7)
    print(f"  - 已恢复默认设置")


def demo_available_legal_texts():
    """演示所有可用的法律文本"""
    print_separator("所有可用的法律文本")
    
    # 列出所有可用的法律文本类型
    text_types = ["copyright", "disclaimer", "privacy_notice", "terms_of_use", "attribution"]
    
    print("中文法律文本:")
    for text_type in text_types:
        text = load_legal_text(text_type, "zh")
        if text:
            print(f"  - {text_type}: {text}")
    
    print("\n英文法律文本:")
    for text_type in text_types:
        text = load_legal_text(text_type, "en")
        if text:
            print(f"  - {text_type}: {text}")
    
    # 显示特殊场景法律文本
    cases = ["commercial", "educational"]
    
    print("\n特殊场景法律文本:")
    for case in cases:
        print(f"\n{case}场景:")
        for lang in ["zh", "en"]:
            for text_type in ["disclaimer", "copyright"]:
                text = load_legal_text(text_type, lang, case)
                if text:
                    print(f"  - {lang}/{text_type}: {text}")


def main():
    """主函数"""
    print("===== VisionAI-ClipsMaster 法律声明更新器演示 =====\n")
    
    # 演示检查更新
    demo_check_update()
    
    # 演示手动下载更新
    demo_manual_download()
    
    # 演示查看更新历史
    demo_update_history()
    
    # 演示配置更新设置
    demo_update_settings()
    
    # 演示所有可用的法律文本
    demo_available_legal_texts()
    
    print("\n===== 演示结束 =====")


if __name__ == "__main__":
    main() 