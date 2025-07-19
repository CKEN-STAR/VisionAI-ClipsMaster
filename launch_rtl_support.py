#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 文本方向适配启动器

此脚本用于启动支持RTL文本方向的VisionAI-ClipsMaster应用。
可以选择启动原始简化UI或新的主窗口，均支持RTL语言适配。
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def setup_ui_module_paths():
    """设置UI模块路径"""
    # 确保UI模块路径正确
    ui_path = os.path.join(PROJECT_ROOT, "ui")
    ui_utils_path = os.path.join(ui_path, "utils")
    
    for path in [ui_path, ui_utils_path]:
        if path not in sys.path:
            sys.path.append(path)
            logger.info(f"已添加路径: {path}")

def launch_simple_ui_with_rtl():
    """启动带有RTL支持的简化UI"""
    try:
        # 优先尝试使用扩展的RTL支持版本
        from simple_ui_text_direction import main as rtl_main
        logger.info("使用扩展版本启动 (simple_ui_text_direction.py)")
        rtl_main()
    except ImportError:
        # 如果扩展版本不可用，则直接使用原始版本
        logger.warning("扩展版本未找到，将使用原始版本启动")
        try:
            from simple_ui import main as original_main
            logger.info("使用原始版本启动 (simple_ui.py)")
            original_main()
        except ImportError:
            logger.error("无法导入simple_ui模块，请确保文件存在")
            sys.exit(1)

def launch_new_ui_with_rtl():
    """启动带有RTL支持的新UI"""
    try:
        from ui.main_window import main as new_main
        logger.info("使用新版本启动 (ui/main_window.py)")
        new_main()
    except ImportError:
        logger.error("无法导入main_window模块，请确保文件存在")
        sys.exit(1)

def launch_text_direction_demo():
    """启动文本方向适配演示应用"""
    try:
        from text_direction_demo import main as demo_main
        logger.info("启动文本方向演示应用 (text_direction_demo.py)")
        demo_main()
    except ImportError:
        logger.error("无法导入text_direction_demo模块，请确保文件存在")
        sys.exit(1)

def main():
    """主函数"""
    # 设置命令行参数
    parser = argparse.ArgumentParser(
        description="VisionAI-ClipsMaster 文本方向适配启动器"
    )
    
    # 添加UI选择参数
    parser.add_argument(
        "--ui", 
        choices=["simple", "new", "demo"], 
        default="simple",
        help="选择启动的UI版本: simple=简化UI, new=新UI, demo=文本方向演示"
    )
    
    # 添加语言选择参数
    parser.add_argument(
        "--lang",
        choices=["zh", "en", "ar", "he", "fa"],
        help="初始语言设置 (zh=中文, en=英文, ar=阿拉伯语, he=希伯来语, fa=波斯语)"
    )
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 初始化环境
    setup_ui_module_paths()
    
    # 设置环境变量传递初始语言
    if args.lang:
        os.environ["INITIAL_LANGUAGE"] = args.lang
        logger.info(f"初始语言设置为: {args.lang}")
    
    # 根据选择启动相应的UI
    if args.ui == "simple":
        launch_simple_ui_with_rtl()
    elif args.ui == "new":
        launch_new_ui_with_rtl()
    else:  # demo
        launch_text_direction_demo()

if __name__ == "__main__":
    main() 