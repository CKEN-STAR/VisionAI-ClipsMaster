#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import logging

# 禁用CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加GPU检测补丁函数
def patched_detect_gpu_info():
    """检测系统GPU信息的补丁版本，处理CUDA被禁用的情况
    
    返回:
        dict: GPU信息，包含可用性和设备名称
    """
    gpu_info = {"available": False, "name": "GPU已禁用（CPU模式）"}
    return gpu_info

# 运行UI前打补丁
sys.path.append(os.path.dirname(__file__))

# 尝试导入兼容性模块
try:
    from ui.compat import handle_qt_version, setup_compat
    logger.info("正在应用兼容性设置...")
    
    # 设置兼容性
    handle_qt_version()
    setup_compat()
    
    logger.info("兼容性设置已完成")
except ImportError:
    logger.warning("无法导入兼容性模块，将以基本模式运行")

# 导入simple_ui模块并应用补丁
from simple_ui import main
import simple_ui

# 替换原始函数
simple_ui.detect_gpu_info = patched_detect_gpu_info

if __name__ == "__main__":
    sys.exit(main())