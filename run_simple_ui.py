#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 简易UI启动脚本
"""

import os
import sys
import logging
import importlib.util

def setup_environment():
    """设置环境变量并确保依赖库正常加载"""
    # 添加当前目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 检查tensorflow模块
    if importlib.util.find_spec('tensorflow') is None:
        logger.info("使用本地TensorFlow模拟模块")
    else:
        logger.info("使用已安装的TensorFlow模块")
    
    logger.info("环境设置完成")

def main():
    """主函数"""
    setup_environment()
    
    try:
        print("正在启动VisionAI-ClipsMaster简易UI...")
        import simple_ui
        simple_ui.main()
    except Exception as e:
        print(f"启动时出错: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 