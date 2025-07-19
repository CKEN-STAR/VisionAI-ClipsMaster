#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 主题预览生成器演示

演示如何使用主题预览生成器并与simple_ui.py集成
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入PyQt
try:
    from PyQt6.QtWidgets import QApplication
    logger.info("使用 PyQt6")
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        logger.info("使用 PyQt5")
    except ImportError:
        logger.error("错误: 无法导入PyQt，请安装PyQt5或PyQt6")
        sys.exit(1)

# 导入simple_ui
try:
    import simple_ui
    logger.info("成功导入 simple_ui.py")
except ImportError as e:
    logger.error(f"错误: 无法导入simple_ui.py: {e}")
    sys.exit(1)

# 导入主题预览功能
try:
    from ui.themes.simple_ui_theme_preview import integrate_with_simple_ui
    from ui.themes.theme_preview import show_theme_preview
    logger.info("成功导入主题预览模块")
except ImportError as e:
    logger.error(f"错误: 无法导入主题预览模块: {e}")
    sys.exit(1)

def main():
    """主函数"""
    # 创建应用实例
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建simple_ui主窗口
    logger.info("创建SimpleScreenplayApp实例")
    main_window = simple_ui.SimpleScreenplayApp()
    
    # 集成主题预览功能
    logger.info("正在集成主题预览功能...")
    success = integrate_with_simple_ui(main_window)
    if not success:
        logger.warning("主题预览功能集成失败")
    else:
        logger.info("主题预览功能集成成功")
    
    # 显示主窗口
    logger.info("显示主窗口")
    main_window.show()
    
    # 运行应用
    logger.info("启动应用")
    sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())

if __name__ == "__main__":
    main()
