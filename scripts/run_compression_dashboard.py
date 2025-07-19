#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行压缩监控仪表盘

此脚本可以直接启动独立的压缩监控仪表盘，用于查看压缩系统性能。
"""

import os
import sys
import logging

# 确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("compression_dashboard")

def main():
    """主函数"""
    try:
        # 导入仪表盘模块
        from src.ui.compression_dashboard import run_dashboard
        
        # 运行仪表盘
        logger.info("启动压缩监控仪表盘...")
        run_dashboard()
    
    except ImportError as e:
        logger.error(f"导入仪表盘模块失败: {e}")
        print("错误: 未能导入压缩监控仪表盘模块。")
        print("请确保已安装所需依赖，特别是PyQt6和pyqtgraph。")
        print("可以运行: pip install PyQt6 pyqtgraph")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"启动仪表盘失败: {e}")
        print(f"错误: 启动仪表盘时遇到问题: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 