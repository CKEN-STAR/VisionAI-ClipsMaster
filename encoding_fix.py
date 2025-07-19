#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 编码兼容性修复模块
解决中文输出在Windows控制台的显示问题
"""

import sys
import os
import locale
import codecs

class EncodingFixer:
    """编码修复器"""
    
    def __init__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.encoding_fixed = False
        
    def fix_console_encoding(self):
        """修复控制台编码问题"""
        try:
            # 1. 设置环境变量
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # 2. 尝试设置控制台代码页为UTF-8
            if sys.platform == 'win32':
                try:
                    import subprocess
                    subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
                except:
                    pass
            
            # 3. 重新配置stdout和stderr
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            else:
                # 对于较老的Python版本
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach(), errors='replace')
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach(), errors='replace')
            
            # 4. 设置默认编码
            if hasattr(sys, 'setdefaultencoding'):
                sys.setdefaultencoding('utf-8')
            
            self.encoding_fixed = True
            self.safe_print("[OK] 控制台编码修复成功")
            
        except Exception as e:
            self.safe_print(f"[WARN] 控制台编码修复失败: {e}")
            
    def safe_print(self, message):
        """安全的打印函数，处理编码问题"""
        try:
            print(message)
        except UnicodeEncodeError:
            # 如果仍然有编码问题，使用ASCII安全模式
            safe_message = message.encode('ascii', errors='replace').decode('ascii')
            print(safe_message)
        except Exception:
            # 最后的回退方案
            print("[ENCODING ERROR] Message could not be displayed")
    
    def create_safe_logger(self):
        """创建安全的日志记录器"""
        class SafeLogger:
            def __init__(self, fixer):
                self.fixer = fixer
                
            def info(self, message):
                self.fixer.safe_print(f"[INFO] {message}")
                
            def warning(self, message):
                self.fixer.safe_print(f"[WARN] {message}")
                
            def error(self, message):
                self.fixer.safe_print(f"[ERROR] {message}")
                
            def success(self, message):
                self.fixer.safe_print(f"[OK] {message}")
        
        return SafeLogger(self)

# 全局编码修复器实例
encoding_fixer = EncodingFixer()
safe_logger = None

def initialize_encoding_fix():
    """初始化编码修复"""
    global safe_logger
    encoding_fixer.fix_console_encoding()
    safe_logger = encoding_fixer.create_safe_logger()
    return safe_logger

def safe_print(message):
    """全局安全打印函数"""
    encoding_fixer.safe_print(message)

# 自动初始化
if safe_logger is None:
    safe_logger = initialize_encoding_fix()
