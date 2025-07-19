#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文本方向适配增强版UI

此脚本扩展了simple_ui.py，添加了文本方向适配支持，
使界面能够根据语言自动调整布局方向，支持从右到左(RTL)的语言。
"""

import sys
import os
from pathlib import Path
import logging
import locale

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 确保UI工具模块路径正确
UI_UTILS_PATH = os.path.join(PROJECT_ROOT, "ui", "utils")
sys.path.append(UI_UTILS_PATH)

# 导入原始UI
from simple_ui import SimpleScreenplayApp, log_handler, main as original_main

# 导入文本方向适配模块
from ui.utils.text_direction import LayoutDirection, set_application_layout_direction, apply_rtl_styles

class RTLSupportedApp(SimpleScreenplayApp):
    """支持RTL文本方向的VisionAI-ClipsMaster应用
    
    扩展原有SimpleScreenplayApp，添加对从右到左文本方向的支持
    """
    
    def __init__(self):
        # 调用父类初始化
        super().__init__()
        
        # 添加文本方向支持
        self.setup_language_direction()
        
        # 记录日志
        log_handler.log("info", "已加载RTL文本方向支持")
    
    def setup_language_direction(self):
        """设置语言方向支持
        
        根据当前系统语言设置适当的文本方向，支持RTL语言
        """
        try:
            # 尝试获取系统语言设置
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                lang_code = system_lang.split('_')[0].lower()
                log_handler.log("info", f"检测到系统语言: {system_lang}, 语言代码: {lang_code}")
                
                # 设置布局方向
                set_application_layout_direction(lang_code)
                
                # 如果是RTL语言，记录日志
                if LayoutDirection.is_rtl_language(lang_code):
                    log_handler.log("info", f"检测到RTL语言({lang_code})，已调整布局方向为从右到左")
                    # 应用RTL样式
                    apply_rtl_styles(self, lang_code)
        except Exception as e:
            log_handler.log("error", f"设置语言方向时出错: {e}")
    
    def change_language_mode(self, mode):
        """修改语言模式
        
        重写父类方法，在切换语言时同时调整布局方向
        
        Args:
            mode: 语言模式，如'zh'、'en'、'ar'等
        """
        # 先调用父类方法处理基本语言切换
        super().change_language_mode(mode)
        
        # 然后设置界面方向
        set_application_layout_direction(mode)
        is_rtl = LayoutDirection.is_rtl_language(mode)
        if is_rtl:
            log_handler.log("info", f"切换到RTL语言({mode})，调整布局方向为从右到左")
            # 应用RTL样式
            apply_rtl_styles(self, mode)
        else:
            log_handler.log("info", f"切换到LTR语言({mode})，调整布局方向为从左到右")

def main():
    """主函数，启动支持RTL的应用"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建并显示支持RTL的主窗口
    window = RTLSupportedApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 