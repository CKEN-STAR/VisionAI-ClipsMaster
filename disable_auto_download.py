#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
禁用VisionAI-ClipsMaster中的自动下载功能
确保程序在缺少模型时使用Mock AI模式而不是提示下载
"""

import os
import sys
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def disable_auto_download():
    """禁用自动下载功能"""
    logger.info("🚫 开始禁用自动下载功能...")
    
    ui_file = Path("simple_ui_fixed.py")
    if not ui_file.exists():
        logger.error("simple_ui_fixed.py 文件不存在")
        return False
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file = ui_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"✅ 已备份原文件到: {backup_file}")
    
    # 修改内容
    modifications = []
    
    # 1. 修改check_zh_model函数 - 禁用下载提示
    old_zh_check = '''            if not model_exists:
                # 显示警告提示
                reply = QMessageBox.question(
                    self,
                    "中文模型未安装",
                    "中文模型尚未下载，是否现在下载？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 如果主窗口存在，使用主窗口的下载方法
                    main_window = self.window()
                    if hasattr(main_window, 'download_zh_model'):
                        main_window.download_zh_model()
                    else:
                        QMessageBox.warning(
                            self,
                            "模型安装",
                            "请在主界面进行模型安装"
                        )'''
    
    new_zh_check = '''            if not model_exists:
                # 显示信息提示，不再提供下载选项
                QMessageBox.information(
                    self,
                    "中文模型未安装",
                    "中文模型尚未安装，将使用Mock AI模式进行演示。\\n\\n"
                    "Mock AI模式可以展示程序功能，但不会进行真实的AI处理。\\n"
                    "如需使用真实AI功能，请手动安装模型文件。",
                    QMessageBox.StandardButton.Ok
                )
                log_handler.log("info", "中文模型未安装，使用Mock AI模式")'''
    
    if old_zh_check in content:
        content = content.replace(old_zh_check, new_zh_check)
        modifications.append("修改训练页面中文模型检查")
    
    # 2. 修改check_en_model函数 - 禁用下载提示
    old_en_check = '''                # 直接在训练页面弹出确认对话框，而不是调用主窗口的check_en_model
                reply = QMessageBox.question(
                    self, 
                    "英文模型未安装",
                    "英文模型尚未下载，是否现在下载？\\n(约4GB，需要较长时间)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 获取主窗口并调用下载方法
                    main_window = self.window()
                    if hasattr(main_window, 'download_en_model'):
                        main_window.download_en_model()
                    else:
                        QMessageBox.warning(
                            self,
                            "模型安装",
                            "请在主界面进行模型安装"
                        )'''
    
    new_en_check = '''                # 显示信息提示，不再提供下载选项
                QMessageBox.information(
                    self, 
                    "英文模型未安装",
                    "英文模型尚未安装，将使用Mock AI模式进行演示。\\n\\n"
                    "Mock AI模式可以展示程序功能，但不会进行真实的AI处理。\\n"
                    "如需使用真实AI功能，请手动安装模型文件。",
                    QMessageBox.StandardButton.Ok
                )
                log_handler.log("info", "英文模型未安装，使用Mock AI模式")'''
    
    if old_en_check in content:
        content = content.replace(old_en_check, new_en_check)
        modifications.append("修改训练页面英文模型检查")
    
    # 3. 修改主窗口的check_en_model函数
    old_main_en_check = '''        try:
            if not self.en_model_exists:
                reply = QMessageBox.question(
                    self, 
                    "英文模型未安装",
                    "英文模型尚未下载，是否现在下载？\\n(约4GB，需要较长时间)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.download_en_model()'''
    
    new_main_en_check = '''        try:
            if not self.en_model_exists:
                QMessageBox.information(
                    self, 
                    "英文模型未安装",
                    "英文模型尚未安装，将使用Mock AI模式进行演示。\\n\\n"
                    "Mock AI模式可以展示程序功能，但不会进行真实的AI处理。\\n"
                    "如需使用真实AI功能，请手动安装模型文件。",
                    QMessageBox.StandardButton.Ok
                )
                log_handler.log("info", "英文模型未安装，使用Mock AI模式")'''
    
    if old_main_en_check in content:
        content = content.replace(old_main_en_check, new_main_en_check)
        modifications.append("修改主窗口英文模型检查")
    
    # 4. 修改主窗口的check_zh_model函数
    old_main_zh_check = '''        try:
            if not self.zh_model_exists:
                reply = QMessageBox.question(
                    self, 
                    "中文模型未安装",
                    "中文模型尚未下载，是否现在下载？\\n(约4GB，需要较长时间)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.download_zh_model()'''
    
    new_main_zh_check = '''        try:
            if not self.zh_model_exists:
                QMessageBox.information(
                    self, 
                    "中文模型未安装",
                    "中文模型尚未安装，将使用Mock AI模式进行演示。\\n\\n"
                    "Mock AI模式可以展示程序功能，但不会进行真实的AI处理。\\n"
                    "如需使用真实AI功能，请手动安装模型文件。",
                    QMessageBox.StandardButton.Ok
                )
                log_handler.log("info", "中文模型未安装，使用Mock AI模式")'''
    
    if old_main_zh_check in content:
        content = content.replace(old_main_zh_check, new_main_zh_check)
        modifications.append("修改主窗口中文模型检查")
    
    # 5. 在change_language_mode函数中禁用模型检查
    old_lang_mode_en = '''        # 如果选择了英文模式，检查英文模型是否已下载
        if mode == "en":
            if not self.en_model_exists:
                self.check_en_model()
                # 如果在训练页面，也更新训练页面的语言选择
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("en")
                return  # 在下载对话框中用户可能会切换回其他模式，此处直接返回'''
    
    new_lang_mode_en = '''        # 如果选择了英文模式，记录日志但不检查模型
        if mode == "en":
            if not self.en_model_exists:
                log_handler.log("info", "英文模式已选择，将使用Mock AI模式")
                # 如果在训练页面，也更新训练页面的语言选择
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("en")'''
    
    if old_lang_mode_en in content:
        content = content.replace(old_lang_mode_en, new_lang_mode_en)
        modifications.append("修改语言模式切换-英文")
    
    old_lang_mode_zh = '''        # 如果选择了中文模式，检查中文模型是否已下载
        if mode == "zh":
            if not self.zh_model_exists:
                self.check_zh_model()
                # 如果在训练页面，也更新训练页面的语言选择
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("zh")
                return  # 在下载对话框中用户可能会切换回其他模式，此处直接返回'''
    
    new_lang_mode_zh = '''        # 如果选择了中文模式，记录日志但不检查模型
        if mode == "zh":
            if not self.zh_model_exists:
                log_handler.log("info", "中文模式已选择，将使用Mock AI模式")
                # 如果在训练页面，也更新训练页面的语言选择
                if hasattr(self, 'train_feeder'):
                    self.train_feeder.switch_training_language("zh")'''
    
    if old_lang_mode_zh in content:
        content = content.replace(old_lang_mode_zh, new_lang_mode_zh)
        modifications.append("修改语言模式切换-中文")
    
    # 6. 添加配置标志位来禁用自动下载
    config_addition = '''
# 禁用自动下载配置
AUTO_DOWNLOAD_DISABLED = True  # 设置为True禁用自动下载功能

'''
    
    # 在文件开头添加配置
    if "AUTO_DOWNLOAD_DISABLED" not in content:
        # 找到第一个import语句后添加
        import_end = content.find('\n\n')
        if import_end != -1:
            content = content[:import_end] + config_addition + content[import_end:]
            modifications.append("添加自动下载禁用配置")
    
    # 写入修改后的内容
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("=" * 50)
    logger.info("🎉 自动下载功能禁用完成!")
    logger.info("📋 完成的修改:")
    for i, mod in enumerate(modifications, 1):
        logger.info(f"  {i}. {mod}")
    logger.info("=" * 50)
    
    return True

def create_config_file():
    """创建配置文件来永久禁用自动下载"""
    config_dir = Path("configs")
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "auto_download_config.yaml"
    
    config_content = """# VisionAI-ClipsMaster 自动下载配置
# 此文件用于控制模型自动下载行为

auto_download:
  enabled: false  # 设置为false禁用自动下载
  show_download_prompts: false  # 设置为false禁用下载提示对话框
  use_mock_ai_when_missing: true  # 设置为true在模型缺失时使用Mock AI

# Mock AI 配置
mock_ai:
  enabled: true
  show_mock_warnings: true  # 显示Mock AI模式警告
  
# 模型路径配置
models:
  qwen:
    base_path: "models/models/qwen/base"
    quantized_path: "models/models/qwen/quantized"
  mistral:
    base_path: "models/mistral/base"
    quantized_path: "models/mistral/quantized"

# 日志配置
logging:
  log_model_status: true
  log_mock_ai_usage: true
"""
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"✅ 已创建配置文件: {config_file}")

def main():
    """主函数"""
    logger.info("🚀 开始禁用自动下载功能...")
    
    # 确认操作
    print("⚠️ 此操作将修改 simple_ui_fixed.py 文件")
    print("📋 将进行的修改：")
    print("  1. 禁用所有模型下载提示对话框")
    print("  2. 将下载提示替换为Mock AI模式说明")
    print("  3. 在语言切换时不再检查模型")
    print("  4. 添加配置标志位")
    print("  5. 创建配置文件")
    print()
    print("✅ 修改后的行为：")
    print("  - 程序在缺少模型时会显示信息提示")
    print("  - 自动使用Mock AI模式进行演示")
    print("  - 不会弹出下载确认对话框")
    print("  - 保留原文件备份")
    print()
    
    confirm = input("确认禁用自动下载功能? (y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 执行修改
    success = disable_auto_download()
    
    if success:
        # 创建配置文件
        create_config_file()
        
        print("\n✅ 自动下载功能已成功禁用!")
        print("📄 原文件已备份为: simple_ui_fixed.py.backup")
        print("⚙️ 配置文件已创建: configs/auto_download_config.yaml")
        print("\n🔧 现在程序将：")
        print("  - 在模型缺失时使用Mock AI模式")
        print("  - 显示信息提示而不是下载对话框")
        print("  - 记录相关日志信息")
    else:
        print("\n❌ 修改失败，请检查错误信息")

if __name__ == "__main__":
    main()
