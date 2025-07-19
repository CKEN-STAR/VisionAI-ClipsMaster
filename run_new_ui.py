#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 新版UI系统启动器
"""

import sys
import os
import logging
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置日志目录
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "new_ui.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 在创建QApplication之前设置高DPI缩放
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMenuBar, QMenu, QAction, QStatusBar

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# 直接导入需要的模块，避开包导入问题
sys.path.insert(0, str(PROJECT_ROOT / "ui" / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "ui" / "layouts"))
sys.path.insert(0, str(PROJECT_ROOT / "ui" / "themes"))
sys.path.insert(0, str(PROJECT_ROOT / "ui" / "i18n"))
import window_initializer
import main_layout

def main():
    """应用程序入口"""
    logging.info("启动VisionAI-ClipsMaster新版UI系统")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    app.setApplicationName("VisionAI-ClipsMaster")
    app.setApplicationDisplayName("VisionAI-ClipsMaster Pro")
    app.setOrganizationName("CKEN-STAR")
    
    # 设置字体和样式配置
    try:
        import qt_chinese_patch
        logging.info("已加载中文字体补丁")
    except ImportError:
        logging.warning("未找到中文字体补丁")
        # 应用默认中文字体
        from PyQt5.QtGui import QFont
        font = QFont("Microsoft YaHei UI", 10)
        app.setFont(font)
    
    # 创建主窗口 - 开启主题支持
    logging.info("正在初始化主窗口...")
    main_window = window_initializer.create_main_window(apply_theme=True)
    
    # 创建菜单栏
    menu_bar = main_window.menuBar()
    
    # 文件菜单
    file_menu = menu_bar.addMenu("文件")
    file_menu.addAction("新建项目")
    file_menu.addAction("打开项目")
    file_menu.addSeparator()
    exit_action = file_menu.addAction("退出")
    exit_action.triggered.connect(app.quit)
    
    # 编辑菜单
    edit_menu = menu_bar.addMenu("编辑")
    edit_menu.addAction("撤销")
    edit_menu.addAction("重做")
    edit_menu.addSeparator()
    edit_menu.addAction("剪切")
    edit_menu.addAction("复制")
    edit_menu.addAction("粘贴")
    
    # 视图菜单
    view_menu = menu_bar.addMenu("视图")
    
    # 主题子菜单
    theme_menu = view_menu.addMenu("主题")
    
    # 语言子菜单
    language_menu = view_menu.addMenu("语言")
    
    try:
        # 导入主题管理器
        from ui.themes.theme_manager import get_theme_manager, get_available_themes, switch_theme
        
        # 获取所有可用主题
        themes = get_available_themes()
        theme_manager = get_theme_manager()
        
        # 创建主题切换动作
        for theme_id in themes:
            theme_info = theme_manager.get_theme_info(theme_id)
            theme_action = theme_menu.addAction(theme_info["name"])
            theme_action.setData(theme_id)
            theme_action.triggered.connect(lambda checked, tid=theme_id: switch_theme(tid))
            
        logging.info(f"已加载 {len(themes)} 个主题")
        
        # 添加状态栏主题切换器
        from ui.themes.theme_switcher import CompactThemeSwitch
        compact_theme_switch = CompactThemeSwitch()
        main_window.statusBar().addPermanentWidget(compact_theme_switch)
        
    except ImportError as e:
        logging.error(f"无法加载主题系统: {e}")
        theme_menu.addAction("默认主题").setEnabled(False)
    
    # 添加语言切换菜单
    try:
        # 导入语言管理器
        from ui.i18n.lang_loader import get_language_manager, get_available_languages, switch_language
        
        # 获取所有可用语言
        languages = get_available_languages()
        lang_manager = get_language_manager()
        
        # 创建语言切换动作
        for lang_code, lang_info in languages.items():
            lang_action = language_menu.addAction(lang_info["native_name"])
            lang_action.setData(lang_code)
            lang_action.triggered.connect(lambda checked, lc=lang_code: switch_language(lc))
            
        logging.info(f"已加载 {len(languages)} 种语言")
        
        # 添加状态栏语言切换器
        from ui.i18n.language_switcher import CompactLanguageSwitcher
        compact_lang_switch = CompactLanguageSwitcher()
        main_window.statusBar().addPermanentWidget(compact_lang_switch)
        
        # 尝试检测系统语言并设置
        system_lang = lang_manager.detect_system_language()
        if system_lang:
            lang_manager.switch_lang(system_lang)
            logging.info(f"已设置系统检测到的语言: {system_lang}")
        
    except ImportError as e:
        logging.error(f"无法加载语言系统: {e}")
        language_menu.addAction("默认语言").setEnabled(False)
    
    # 帮助菜单
    help_menu = menu_bar.addMenu("帮助")
    help_menu.addAction("帮助文档")
    help_menu.addAction("检查更新")
    about_action = help_menu.addAction("关于")
    
    # 创建并应用三栏布局
    logging.info("初始化三栏布局系统...")
    triple_layout = main_layout.TripleLayout()
    window_initializer.apply_layout(main_window, triple_layout)
    
    # 显示主窗口
    main_window.show()
    logging.info("窗口初始化完成")
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 