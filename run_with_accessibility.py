#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 可访问性启动脚本

启动应用程序并自动应用可访问性修复
"""

import os
import sys
import logging
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("a11y_launcher")

# 导入可访问性自动修复模块
try:
    from ui.ally.auto_fix import install_auto_fix
    HAS_AUTO_FIX = True
except ImportError:
    logger.error("无法导入可访问性自动修复模块")
    HAS_AUTO_FIX = False

# 尝试导入PyQt库
try:
    from PyQt6.QtWidgets import QApplication
    HAS_PYQT6 = True
    HAS_PYQT5 = False
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        HAS_PYQT6 = False
        HAS_PYQT5 = True
    except ImportError:
        logger.error("未找到PyQt库")
        HAS_PYQT6 = False
        HAS_PYQT5 = False

# 尝试导入主窗口
try:
    from ui.main_window_with_nav import MainWindowWithNav
    HAS_MAIN_WINDOW = True
except ImportError:
    logger.error("无法导入主窗口")
    HAS_MAIN_WINDOW = False


def main():
    """主函数"""
    # 检查环境
    if not (HAS_PYQT6 or HAS_PYQT5):
        logger.error("未找到PyQt库，无法启动应用程序")
        return 1
    
    if not HAS_MAIN_WINDOW:
        logger.error("无法导入主窗口，无法启动应用程序")
        return 1
    
    try:
        # 创建应用程序实例
        app = QApplication(sys.argv)
        app.setApplicationName("VisionAI-ClipsMaster")
        app.setApplicationVersion("1.0.0")
        
        # 安装可访问性自动修复
        if HAS_AUTO_FIX:
            logger.info("安装可访问性自动修复...")
            install_auto_fix()
        
        # 创建主窗口
        logger.info("创建主窗口...")
        window = MainWindowWithNav()
        
        # 显示主窗口
        logger.info("显示主窗口...")
        window.show()
        
        # 运行应用程序
        logger.info("应用程序已启动")
        return app.exec()
    except Exception as e:
        logger.error(f"启动应用程序时出错: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 