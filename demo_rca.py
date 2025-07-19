#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式根本原因分析(RCA)功能演示脚本

该脚本演示了RCA功能的使用，使用模拟数据代替真实数据
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("demo_rca")

# 导入PyQt5
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt5.QtCore import Qt
except ImportError:
    logger.error("未安装PyQt5库，请使用pip install PyQt5安装")
    sys.exit(1)


# 导入模拟数据源
try:
    from test_rca_stub import MockDataAggregator, MockRCAToolkit, get_mock_rca_toolkit
    logger.info("成功导入模拟数据源")
except ImportError as e:
    logger.error(f"导入模拟数据源失败: {e}")
    sys.exit(1)


# 打补丁，替换真实RCA工具为模拟RCA工具
def patch_rca():
    """打补丁，用模拟数据代替真实数据"""
    # 自动猴子补丁模块
    try:
        import ui.dashboard.rca_tool
        ui.dashboard.rca_tool.get_rca_toolkit = get_mock_rca_toolkit
        ui.dashboard.rca_tool.RCAToolkit = MockRCAToolkit
        logger.info("成功打补丁: rca_tool")
        return True
    except ImportError as e:
        logger.error(f"打补丁失败: {e}")
        return False


class RCADemoWindow(QMainWindow):
    """RCA演示窗口"""
    
    def __init__(self):
        """初始化演示窗口"""
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("交互式根本原因分析(RCA) - 演示")
        self.resize(1200, 800)
        
        # 应用补丁
        patched = patch_rca()
        
        # 主widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        if patched:
            # 导入RCA视图
            try:
                from ui.dashboard.rca_view import create_rca_view
                
                # 创建一个标签说明这是演示版本
                demo_label = QLabel("演示版本 - 使用模拟数据")
                demo_label.setStyleSheet("color: blue; font-size: 16px; font-weight: bold; padding: 5px;")
                demo_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(demo_label)
                
                # 创建视图
                self.rca_view = create_rca_view()
                layout.addWidget(self.rca_view)
                
                logger.info("成功加载RCA视图")
            except Exception as e:
                logger.error(f"初始化RCA视图失败: {e}")
                # 在界面上显示错误
                error_label = QLabel(f"加载RCA视图失败: {str(e)}")
                error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
                error_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(error_label)
        else:
            # 显示未能应用补丁
            error_label = QLabel("未能应用RCA工具补丁，无法启动演示")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            error_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_label)


def main():
    """主函数"""
    logger.info("启动RCA演示")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建并显示窗口
    window = RCADemoWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 