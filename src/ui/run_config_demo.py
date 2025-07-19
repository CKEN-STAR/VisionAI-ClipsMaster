#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置绑定演示启动脚本

这个脚本用于启动配置绑定演示，展示配置和UI的双向绑定。
"""

import os
import sys
import argparse
from pathlib import Path

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动配置绑定演示")
    parser.add_argument("--type", choices=["panel", "integration", "all"], default="all",
                      help="启动的演示类型: panel=配置面板, integration=集成示例, all=全部")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # 导入PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("错误: 未安装PyQt6。请使用以下命令安装:")
        print("pip install PyQt6")
        sys.exit(1)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格，在所有平台上都很好看
    
    # 根据参数启动相应的演示
    windows = []
    
    if args.type in ["panel", "all"]:
        try:
            # 导入配置面板
            from src.ui.config_panel import ConfigPanel
            
            # 创建配置面板
            config_panel = ConfigPanel()
            config_panel.setWindowTitle("VisionAI-ClipsMaster 配置面板")
            config_panel.resize(700, 600)
            config_panel.show()
            
            # 添加到窗口列表
            windows.append(config_panel)
            
            print("已启动配置面板演示")
        except Exception as e:
            print(f"启动配置面板失败: {str(e)}")
    
    if args.type in ["integration", "all"]:
        try:
            # 导入集成示例
            from src.ui.config_integration_example import IntegrationExampleApp
            
            # 创建集成示例应用
            integration_app = IntegrationExampleApp()
            integration_app.setWindowTitle("VisionAI-ClipsMaster 配置集成示例")
            integration_app.show()
            
            # 添加到窗口列表
            windows.append(integration_app)
            
            print("已启动集成示例演示")
        except Exception as e:
            print(f"启动集成示例失败: {str(e)}")
    
    # 如果没有成功启动任何窗口，显示错误
    if not windows:
        print("错误: 未能启动任何演示窗口")
        return 1
    
    # 运行应用程序事件循环
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 