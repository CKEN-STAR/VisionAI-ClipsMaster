#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 地域合规适配器独立测试脚本

完全独立的测试脚本，仅依赖Python标准库，用于验证地域合规适配器功能
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("standalone_test")

# 加载region_compliance.py文件内容
def load_module_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# 执行模块代码
def execute_module(filepath):
    # 读取文件内容
    code = load_module_content(filepath)
    
    # 创建命名空间
    namespace = {
        "__name__": "__main__",
        "__file__": filepath,
    }
    
    # 执行代码
    try:
        exec(code, namespace)
        return namespace
    except Exception as e:
        logger.error(f"执行模块时出错: {str(e)}")
        return None

# 进行简单测试
def run_test():
    logger.info("开始独立测试地域合规适配器")
    
    # 获取模块路径
    module_path = os.path.join(os.path.dirname(__file__), "region_compliance.py")
    
    if not os.path.exists(module_path):
        logger.error(f"模块文件不存在: {module_path}")
        return False
    
    # 执行模块（会执行模块的__main__块）
    logger.info("执行模块自测...")
    execute_module(module_path)
    
    logger.info("测试完成!")
    return True

if __name__ == "__main__":
    run_test() 