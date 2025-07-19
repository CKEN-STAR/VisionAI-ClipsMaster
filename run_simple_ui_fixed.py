#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 修复版简易UI启动脚本
"""

import os
import sys
import logging
import importlib.util
import traceback

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
    
    # 检查psutil模块
    if importlib.util.find_spec('psutil') is None:
        logger.warning("未安装psutil模块，系统监控功能将使用模拟数据")
    else:
        logger.info("已安装psutil模块")
    
    logger.info("环境设置完成")

def main():
    """主函数"""
    setup_environment()
    
    try:
        print("正在启动VisionAI-ClipsMaster修复版简易UI...")
        # 导入simple_ui_fixed模块
        simple_ui_fixed_spec = importlib.util.spec_from_file_location("simple_ui_fixed", "simple_ui_fixed.py")
        simple_ui_fixed = importlib.util.module_from_spec(simple_ui_fixed_spec)
        simple_ui_fixed_spec.loader.exec_module(simple_ui_fixed)
        
        # 调用main函数
        if hasattr(simple_ui_fixed, 'main'):
            simple_ui_fixed.main()
        else:
            print("错误: simple_ui_fixed.py中未找到main函数")
    except Exception as e:
        print(f"启动时出错: {e}")
        traceback.print_exc()
        input("按Enter键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()
