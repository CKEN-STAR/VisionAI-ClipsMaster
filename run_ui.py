#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI启动脚本

此脚本启动VisionAI-ClipsMaster的图形用户界面，
用于剧本重构、视频剪辑和预览。
"""

import sys
import os
import logging
from pathlib import Path

print("开始导入PyQt6")

try:
    # 直接导入PyQt6模块
    import PyQt6
    from PyQt6 import QtWidgets, QtCore
    print(f"PyQt6导入成功")
    HAS_PYQT = True
except ImportError as e:
    print(f"PyQt6导入异常: {str(e)}")
    HAS_PYQT = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockPyQt:
    class QtWidgets:
        class QApplication:
            def __init__(self, args):
                pass
            
            def exec(self):
                logger.error("PyQt6未安装，无法启动UI")
                print("错误: 缺少必要的依赖项。请运行以下命令安装依赖:")
                print("pip install PyQt6")
                return 1
                
            def setStyle(self, style):
                pass
    
    class QtCore:
        def __init__(self):
            pass

# 尝试导入所需模块
if HAS_PYQT:
    try:
        from PyQt6.QtWidgets import QApplication
        print("成功导入QApplication")
        try:
            from ui.screenplay_app import ScreenplayApp
            print("成功导入ScreenplayApp")
        except ImportError as e:
            print(f"导入ScreenplayApp失败: {str(e)}")
            HAS_PYQT = False
    except ImportError as e:
        print(f"导入QApplication失败: {str(e)}")
        HAS_PYQT = False

# 使用模拟版本
if not HAS_PYQT:
    logger.warning("PyQt6未安装或导入错误，使用模拟版本")
    QApplication = MockPyQt.QtWidgets.QApplication

# 模拟NLP处理
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    print("spaCy未安装，将使用备用方法进行NLP处理")
    HAS_SPACY = False

# 模拟情感分析
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    print("主要情感分析器不可用，使用备用版本")
    HAS_TRANSFORMERS = False

# 模拟文本嵌入
try:
    import torch
    HAS_TORCH = True
except ImportError:
    print("文本嵌入功能不可用")
    HAS_TORCH = False

def main():
    """主入口函数"""
    # 创建Qt应用
    if HAS_PYQT:
        app = QApplication(sys.argv)
    else:
        app = MockPyQt.QtWidgets.QApplication(sys.argv)
    
    # 如果PyQt6没有安装，模拟版本会直接退出
    if not HAS_PYQT:
        return app.exec()
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    try:
        # 创建并显示主窗口
        window = ScreenplayApp()
        window.show()
        
        # 运行应用事件循环
        return app.exec()
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        print(f"应用启动失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 