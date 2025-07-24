#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的日志处理器
处理emoji和特殊字符的编码问题
"""

import logging
import sys
import os

class SafeStreamHandler(logging.StreamHandler):
    """安全的流处理器，处理编码问题"""
    
    def __init__(self, stream=None):
        super().__init__(stream)
        self.encoding = 'utf-8'
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            
            # 处理编码问题
            if hasattr(stream, 'mode') and 'b' not in stream.mode:
                # 文本模式
                if hasattr(stream, 'encoding'):
                    # 如果流有编码属性，使用安全编码
                    try:
                        stream.write(msg + self.terminator)
                    except UnicodeEncodeError:
                        # 如果编码失败，移除emoji和特殊字符
                        safe_msg = self._make_safe(msg)
                        stream.write(safe_msg + self.terminator)
                else:
                    # 没有编码属性，直接写入
                    stream.write(msg + self.terminator)
            else:
                # 二进制模式
                msg_bytes = (msg + self.terminator).encode('utf-8', errors='replace')
                stream.write(msg_bytes)
            
            self.flush()
        except Exception:
            self.handleError(record)
    
    def _make_safe(self, text):
        """移除可能导致编码问题的字符"""
        # 移除emoji和特殊Unicode字符
        safe_text = ""
        for char in text:
            try:
                # 尝试编码到GBK（Windows默认编码）
                char.encode('gbk')
                safe_text += char
            except UnicodeEncodeError:
                # 如果无法编码，替换为安全字符
                if ord(char) > 127:
                    safe_text += "?"
                else:
                    safe_text += char
        return safe_text

class SafeFileHandler(logging.FileHandler):
    """安全的文件处理器"""
    
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)
    
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # 如果编码失败，使用安全模式
            try:
                msg = self.format(record)
                safe_msg = self._make_safe(msg)
                
                if self.stream is None:
                    self.stream = self._open()
                
                self.stream.write(safe_msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
    
    def _make_safe(self, text):
        """移除可能导致编码问题的字符"""
        return ''.join(char if ord(char) < 128 else '?' for char in text)

def setup_safe_logging():
    """设置安全的日志系统"""
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 移除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加安全的控制台处理器
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
    
    # 添加文件处理器
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = SafeFileHandler(log_dir / "visionai_safe.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    
    return True
