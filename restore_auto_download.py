#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
恢复VisionAI-ClipsMaster自动下载功能
将程序恢复到优化前的状态
"""

import os
import sys
from pathlib import Path
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def restore_auto_download():
    """恢复自动下载功能"""
    logger.info("🔄 开始恢复自动下载功能...")
    
    # 1. 恢复原始UI文件
    ui_file = Path("simple_ui_fixed.py")
    backup_file = Path("simple_ui_fixed.py.backup")
    
    if backup_file.exists():
        shutil.copy2(backup_file, ui_file)
        logger.info("✅ 已恢复原始UI文件")
    else:
        logger.warning("⚠️ 备份文件不存在，无法自动恢复")
        logger.info("💡 您需要手动修改 simple_ui_fixed.py 文件")
        return False
    
    # 2. 修改配置文件
    config_file = Path("configs/auto_download_config.yaml")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 启用自动下载
        content = content.replace('enabled: false', 'enabled: true')
        content = content.replace('show_download_prompts: false', 'show_download_prompts: true')
        content = content.replace('use_mock_ai_when_missing: true', 'use_mock_ai_when_missing: false')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ 已更新配置文件")
    
    logger.info("🎉 自动下载功能恢复完成!")
    logger.info("📋 恢复后的行为:")
    logger.info("  - 模型缺失时会弹出下载确认对话框")
    logger.info("  - 用户可以选择自动下载模型")
    logger.info("  - 不再默认使用Mock AI模式")
    
    return True

def main():
    """主函数"""
    print("🔄 VisionAI-ClipsMaster 自动下载功能恢复工具")
    print("=" * 50)
    print()
    print("⚠️ 此操作将:")
    print("  1. 恢复原始的UI文件 (从备份)")
    print("  2. 启用自动下载配置")
    print("  3. 恢复模型下载提示对话框")
    print()
    print("📋 恢复后的行为:")
    print("  - 模型缺失时会弹出下载确认对话框")
    print("  - 用户点击'是'会自动下载大模型文件")
    print("  - 可能会意外下载14.4GB的模型文件")
    print()
    
    confirm = input("确认恢复自动下载功能? (y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    success = restore_auto_download()
    
    if success:
        print("\n✅ 自动下载功能已成功恢复!")
        print("🔄 请重启程序以使更改生效")
    else:
        print("\n❌ 恢复失败，请检查错误信息")

if __name__ == "__main__":
    main()
