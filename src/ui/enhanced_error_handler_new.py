#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强错误处理器
提供用户友好的错误提示和解决方案
"""

import sys
import traceback
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    """增强错误处理器"""
    
    def __init__(self, parent_widget=None):
        self.parent = parent_widget
        self.error_solutions = self._load_error_solutions()
    
    def _load_error_solutions(self) -> Dict[str, Dict[str, str]]:
        """加载错误解决方案"""
        return {
            "FileNotFoundError": {
                "title": "文件未找到",
                "message": "请检查文件路径是否正确，或重新选择文件",
                "solution": "1. 确认文件存在\n2. 检查文件权限\n3. 重新选择文件"
            },
            "MemoryError": {
                "title": "内存不足",
                "message": "系统内存不足，请关闭其他程序或降低处理质量",
                "solution": "1. 关闭不必要的程序\n2. 选择较低的处理质量\n3. 重启应用程序"
            },
            "ImportError": {
                "title": "模块导入失败",
                "message": "缺少必要的依赖库，请检查安装",
                "solution": "1. 运行 pip install -r requirements.txt\n2. 检查Python环境\n3. 重新安装应用"
            }
        }
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_name = exc_type.__name__
        error_message = str(exc_value)
        
        # 记录详细错误信息
        logger.error(f"未捕获异常: {error_name}: {error_message}")
        logger.error("详细错误信息:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # 显示用户友好的错误提示
        self.show_error_message(error_name, error_message)
    
    def show_error_message(self, error_name: str, error_message: str):
        """显示错误消息"""
        solution_info = self.error_solutions.get(error_name, {
            "title": "程序错误",
            "message": "程序遇到了未知错误",
            "solution": "请重启程序或联系技术支持"
        })
        
        print(f"\n❌ {solution_info['title']}")
        print(f"   {solution_info['message']}")
        print(f"   解决方案: {solution_info['solution']}")

# 全局错误处理器实例
enhanced_error_handler = EnhancedErrorHandler()

def setup_global_error_handler():
    """设置全局错误处理器"""
    sys.excepthook = enhanced_error_handler.handle_exception
