#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 简易UI补丁

此脚本演示如何将个性化推荐器集成到simple_ui.py中
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 导入simple_ui模块
try:
    from simple_ui import SimpleScreenplayApp, QApplication
except ImportError:
    print("错误: 无法导入simple_ui模块")
    sys.exit(1)

# 导入个性化推荐器集成模块
try:
    from ui.assistant.simple_ui_integration import integrate_with_simple_ui
    HAS_PERSONALIZATION = True
except ImportError:
    print("警告: 无法导入个性化推荐器集成模块，将使用原始UI")
    HAS_PERSONALIZATION = False


class EnhancedSimpleScreenplayApp(SimpleScreenplayApp):
    """增强的简易UI应用
    
    集成了个性化推荐器的简易UI
    """
    
    def __init__(self):
        """初始化增强的简易UI应用"""
        # 调用父类初始化
        super().__init__()
        
        # 集成个性化推荐器
        if HAS_PERSONALIZATION:
            try:
                integrate_with_simple_ui(self)
                print("已集成个性化推荐器")
                
                # 添加个性化推荐器菜单项
                self._add_personalization_menu()
            except Exception as e:
                print(f"个性化推荐器集成失败: {e}")
    
    def _add_personalization_menu(self):
        """添加个性化推荐器菜单项"""
        # 检查是否有帮助菜单
        if hasattr(self, "menuBar") and self.menuBar():
            # 获取帮助菜单
            help_menu = None
            for action in self.menuBar().actions():
                if action.text() == "帮助(&H)":
                    help_menu = action.menu()
                    break
            
            # 如果没有帮助菜单，创建一个
            if not help_menu:
                help_menu = self.menuBar().addMenu("帮助(&H)")
            
            # 添加个性化推荐器菜单项
            from PyQt6.QtGui import QAction
            personalization_action = QAction("个性化设置", self)
            personalization_action.triggered.connect(self.show_personalization_dialog)
            
            # 添加到帮助菜单
            help_menu.addSeparator()
            help_menu.addAction(personalization_action)
    
    def show_personalization_dialog(self):
        """显示个性化设置对话框"""
        try:
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                        QComboBox, QCheckBox, QPushButton, QGroupBox)
            from ui.assistant.simple_ui_integration import get_assistant
            
            # 获取助手实例
            assistant = get_assistant()
            
            # 创建对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("个性化设置")
            dialog.setMinimumWidth(400)
            
            # 创建布局
            layout = QVBoxLayout(dialog)
            
            # 用户级别组
            level_group = QGroupBox("用户级别")
            level_layout = QVBoxLayout(level_group)
            
            # 获取当前用户级别
            current_level = assistant.get_current_user_level()
            
            # 用户级别标签
            level_label = QLabel(f"当前级别: {current_level}")
            level_layout.addWidget(level_label)
            
            # 用户级别描述
            level_descriptions = {
                "beginner": "新手: 显示基础操作提示，简化界面",
                "intermediate": "进阶: 显示效率优化技巧，中等复杂度界面",
                "expert": "专家: 显示高级参数调整，完整功能界面"
            }
            
            description_label = QLabel(level_descriptions.get(current_level, ""))
            level_layout.addWidget(description_label)
            
            layout.addWidget(level_group)
            
            # 界面设置组
            settings_group = QGroupBox("界面设置")
            settings_layout = QVBoxLayout(settings_group)
            
            # 获取当前界面设置
            settings = assistant.get_interface_settings()
            
            # 显示高级功能复选框
            show_advanced_cb = QCheckBox("显示高级功能")
            show_advanced_cb.setChecked(settings.get("show_advanced_features", True))
            settings_layout.addWidget(show_advanced_cb)
            
            # 显示提示复选框
            show_tooltips_cb = QCheckBox("显示操作提示")
            show_tooltips_cb.setChecked(settings.get("show_tooltips", True))
            settings_layout.addWidget(show_tooltips_cb)
            
            # 显示键盘快捷键复选框
            show_shortcuts_cb = QCheckBox("显示键盘快捷键")
            show_shortcuts_cb.setChecked(settings.get("show_keyboard_shortcuts", True))
            settings_layout.addWidget(show_shortcuts_cb)
            
            # 紧凑模式复选框
            compact_mode_cb = QCheckBox("紧凑模式")
            compact_mode_cb.setChecked(settings.get("compact_mode", False))
            settings_layout.addWidget(compact_mode_cb)
            
            layout.addWidget(settings_group)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            
            # 保存按钮
            save_button = QPushButton("保存")
            save_button.clicked.connect(lambda: self._save_personalization_settings(
                assistant,
                show_advanced_cb.isChecked(),
                show_tooltips_cb.isChecked(),
                show_shortcuts_cb.isChecked(),
                compact_mode_cb.isChecked(),
                dialog
            ))
            button_layout.addWidget(save_button)
            
            # 取消按钮
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            dialog.exec()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"无法显示个性化设置对话框: {e}")
    
    def _save_personalization_settings(self, assistant, show_advanced, show_tooltips, 
                                      show_shortcuts, compact_mode, dialog):
        """保存个性化设置
        
        Args:
            assistant: 助手实例
            show_advanced: 是否显示高级功能
            show_tooltips: 是否显示提示
            show_shortcuts: 是否显示键盘快捷键
            compact_mode: 是否使用紧凑模式
            dialog: 对话框实例
        """
        try:
            # 更新用户偏好
            assistant.update_user_preference("interface", "show_advanced_features", show_advanced)
            assistant.update_user_preference("interface", "show_tooltips", show_tooltips)
            assistant.update_user_preference("interface", "show_keyboard_shortcuts", show_shortcuts)
            assistant.update_user_preference("interface", "compact_mode", compact_mode)
            
            # 应用界面设置
            settings = {
                "show_advanced_features": show_advanced,
                "show_tooltips": show_tooltips,
                "show_keyboard_shortcuts": show_shortcuts,
                "compact_mode": compact_mode
            }
            
            # 导入应用界面设置函数
            from ui.assistant.simple_ui_integration import _apply_interface_settings
            _apply_interface_settings(self, settings)
            
            # 关闭对话框
            dialog.accept()
            
            # 显示成功消息
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "成功", "个性化设置已保存并应用")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"保存个性化设置失败: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = EnhancedSimpleScreenplayApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 