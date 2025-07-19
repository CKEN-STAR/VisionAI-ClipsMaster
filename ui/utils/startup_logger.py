"""
启动日志管理器
控制启动过程中的日志输出，提供简洁的用户体验
"""

import os
import sys
from typing import Optional
from enum import Enum

class LogLevel(Enum):
    """日志级别"""
    SILENT = 0      # 静默模式
    MINIMAL = 1     # 最小输出
    NORMAL = 2      # 正常输出
    VERBOSE = 3     # 详细输出
    DEBUG = 4       # 调试输出

class StartupLogger:
    """启动日志管理器"""
    
    def __init__(self):
        # 根据环境变量确定日志级别
        debug_mode = os.getenv('VISIONAI_DEBUG', '').lower() in ['1', 'true', 'yes']
        verbose_mode = os.getenv('VISIONAI_VERBOSE', '').lower() in ['1', 'true', 'yes']
        
        if debug_mode:
            self.level = LogLevel.DEBUG
        elif verbose_mode:
            self.level = LogLevel.VERBOSE
        else:
            self.level = LogLevel.MINIMAL
        
        self.startup_phase = "初始化"
        self.component_count = 0
        self.error_count = 0
        self.warning_count = 0
    
    def set_level(self, level: LogLevel):
        """设置日志级别"""
        self.level = level
    
    def set_phase(self, phase: str):
        """设置启动阶段"""
        self.startup_phase = phase
        if self.level.value >= LogLevel.NORMAL.value:
            print(f"🔄 {phase}...")
    
    def info(self, message: str, component: Optional[str] = None):
        """输出信息日志"""
        if self.level.value >= LogLevel.NORMAL.value:
            if component:
                print(f"[OK] {component}: {message}")
            else:
                print(f"[OK] {message}")
    
    def success(self, message: str, component: Optional[str] = None):
        """输出成功日志"""
        if self.level.value >= LogLevel.MINIMAL.value:
            if component:
                print(f"✅ {component}: {message}")
            else:
                print(f"✅ {message}")
    
    def warning(self, message: str, component: Optional[str] = None):
        """输出警告日志"""
        self.warning_count += 1
        if self.level.value >= LogLevel.MINIMAL.value:
            if component:
                print(f"⚠️ {component}: {message}")
            else:
                print(f"⚠️ {message}")
    
    def error(self, message: str, component: Optional[str] = None):
        """输出错误日志"""
        self.error_count += 1
        if self.level.value >= LogLevel.MINIMAL.value:
            if component:
                print(f"❌ {component}: {message}")
            else:
                print(f"❌ {message}")
    
    def debug(self, message: str, component: Optional[str] = None):
        """输出调试日志"""
        if self.level.value >= LogLevel.DEBUG.value:
            if component:
                print(f"🔍 [DEBUG] {component}: {message}")
            else:
                print(f"🔍 [DEBUG] {message}")
    
    def verbose(self, message: str, component: Optional[str] = None):
        """输出详细日志"""
        if self.level.value >= LogLevel.VERBOSE.value:
            if component:
                print(f"[INFO] {component}: {message}")
            else:
                print(f"[INFO] {message}")
    
    def component_loaded(self, component_name: str, load_time: float = 0):
        """记录组件加载完成"""
        self.component_count += 1
        if self.level.value >= LogLevel.NORMAL.value:
            if load_time > 0:
                print(f"✅ {component_name} 加载完成 ({load_time:.2f}s)")
            else:
                print(f"✅ {component_name} 加载完成")
    
    def startup_summary(self, total_time: float):
        """输出启动总结"""
        if self.level.value >= LogLevel.MINIMAL.value:
            print("\n" + "=" * 60)
            print("🎉 VisionAI-ClipsMaster 启动完成")
            print("=" * 60)
            print(f"⏱️ 启动时间: {total_time:.2f}秒")
            print(f"📦 加载组件: {self.component_count}个")
            
            if self.warning_count > 0:
                print(f"⚠️ 警告: {self.warning_count}个")
            if self.error_count > 0:
                print(f"❌ 错误: {self.error_count}个")
            
            if self.error_count == 0 and self.warning_count == 0:
                print("✅ 所有组件正常加载")
            
            print("🎬 可以开始使用AI短剧混剪功能")
            print("=" * 60)
    
    def suppress_qt_warnings(self):
        """抑制Qt相关的警告输出"""
        if self.level.value < LogLevel.DEBUG.value:
            # 重定向stderr以抑制Qt CSS警告
            import io
            import contextlib
            
            class WarningFilter:
                def __init__(self, original_stderr):
                    self.original_stderr = original_stderr
                    self.buffer = []
                
                def write(self, text):
                    # 过滤掉CSS相关的警告
                    if any(keyword in text.lower() for keyword in [
                        'unknown property', 'css', 'stylesheet', 'qobject::',
                        'cannot create children', 'different thread'
                    ]):
                        # 静默忽略这些警告
                        return
                    
                    # 其他错误正常输出
                    self.original_stderr.write(text)
                
                def flush(self):
                    self.original_stderr.flush()
            
            # 只在非调试模式下过滤警告
            if self.level != LogLevel.DEBUG:
                sys.stderr = WarningFilter(sys.stderr)

# 全局启动日志管理器
startup_logger = StartupLogger()

def get_startup_logger() -> StartupLogger:
    """获取启动日志管理器"""
    return startup_logger

def set_log_level(level: LogLevel):
    """设置全局日志级别"""
    startup_logger.set_level(level)

def enable_debug_mode():
    """启用调试模式"""
    startup_logger.set_level(LogLevel.DEBUG)

def enable_silent_mode():
    """启用静默模式"""
    startup_logger.set_level(LogLevel.SILENT)

__all__ = [
    'StartupLogger',
    'LogLevel', 
    'startup_logger',
    'get_startup_logger',
    'set_log_level',
    'enable_debug_mode',
    'enable_silent_mode'
]
