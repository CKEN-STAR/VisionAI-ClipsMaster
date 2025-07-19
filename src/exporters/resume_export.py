#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
断点续导出模块

为VisionAI-ClipsMaster项目提供断点续导出功能：
1. 保存导出进度状态
2. 验证导出进度状态
3. 从中断点恢复导出
4. 支持多种导出格式
5. 支持进度报告
"""

import os
import sys
import json
import pickle
import time
import hashlib
import traceback
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from src.utils.log_handler import get_logger
from src.exporters.resource_cleaner import get_resource_cleaner, resource_cleanup_context

class ExportResumer:
    """导出续传类
    
    负责管理导出过程的状态，支持在导出中断后从上一个保存点恢复。
    """
    
    def __init__(self, state_file: Optional[str] = None):
        """初始化导出续传器
        
        Args:
            state_file: 状态文件路径，默认为`.export_state`
        """
        self.logger = get_logger("export_resumer")
        self.state_file = state_file or ".export_state"
        self.progress = 0.0
        self.checksum = None
        self.last_save_time = 0
        self.save_interval = 5  # 默认每5秒保存一次状态
        
    def save_state(self, progress: float) -> None:
        """保存导出进度状态
        
        Args:
            progress: 当前进度(0.0-1.0)
        """
        # 避免频繁保存
        current_time = time.time()
        if current_time - self.last_save_time < self.save_interval and progress < 1.0:
            return
            
        self.last_save_time = current_time
        self.progress = progress
        
        # 创建状态数据
        state_data = {
            "progress": progress,
            "timestamp": current_time,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 计算校验和
        checksum = hashlib.md5(str(progress).encode()).hexdigest()
        state_data["checksum"] = checksum
        self.checksum = checksum
        
        # 保存状态
        with open(self.state_file, 'wb') as f:
            pickle.dump(state_data, f)
            
        self.logger.debug(f"已保存导出进度: {progress:.2%}")
    
    def load_state(self) -> Optional[float]:
        """加载导出进度状态
        
        Returns:
            Optional[float]: 加载的进度值，如果没有有效状态则返回None
        """
        if not os.path.exists(self.state_file):
            self.logger.debug("未找到导出状态文件")
            return None
            
        try:
            with open(self.state_file, 'rb') as f:
                state_data = pickle.load(f)
                
            # 验证状态数据
            progress = state_data.get("progress", 0.0)
            checksum = state_data.get("checksum", "")
            expected_checksum = hashlib.md5(str(progress).encode()).hexdigest()
            
            if checksum != expected_checksum:
                self.logger.error("导出状态校验和不匹配，状态可能已损坏")
                return None
                
            self.progress = progress
            self.checksum = checksum
            self.last_save_time = state_data.get("timestamp", time.time())
            
            self.logger.info(f"已加载导出进度: {progress:.2%} (保存于 {state_data.get('date', 'unknown')})")
            return progress
            
        except Exception as e:
            self.logger.error(f"加载导出状态失败: {str(e)}")
            return None
    
    def _verify_state(self) -> bool:
        """验证导出进度状态的完整性
        
        Returns:
            bool: 状态是否有效
        """
        if not os.path.exists(self.state_file):
            return False
            
        try:
            with open(self.state_file, 'rb') as f:
                state_data = pickle.load(f)
                
            progress = state_data.get("progress", 0.0)
            checksum = state_data.get("checksum", "")
            expected_checksum = hashlib.md5(str(progress).encode()).hexdigest()
            
            return checksum == expected_checksum
            
        except Exception:
            return False
    
    def clear_state(self) -> bool:
        """清除导出进度状态
        
        Returns:
            bool: 是否成功清除
        """
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
                self.progress = 0.0
                self.checksum = None
                self.last_save_time = 0
                self.logger.debug("已清除导出进度状态")
                return True
            except Exception as e:
                self.logger.error(f"清除导出状态失败: {str(e)}")
                return False
        return True
    
    @contextmanager
    def resumable_export(self, callback: Optional[Callable[[float], None]] = None):
        """创建可恢复导出的上下文管理器
        
        Args:
            callback: 进度回调函数
            
        Yields:
            ExportResumer: 导出续传器实例
        """
        # 使用资源清理上下文
        with resource_cleanup_context("export") as context:
            try:
                # 尝试加载之前的状态
                self.load_state()
                
                # 提供自身实例
                yield self
                
                # 导出成功，清除状态
                self.clear_state()
                
            except Exception as e:
                # 发生异常，保存当前状态
                self.logger.error(f"导出过程中断: {str(e)}")
                
                # 确保已保存当前进度
                if self.progress > 0:
                    self.save_state(self.progress)
                    
                if callback:
                    callback(self.progress)
                    
                # 重新抛出异常
                raise

class ExportResumer:
    """导出续传类
    
    负责管理导出过程的状态，支持在导出中断后从上一个保存点恢复。
    """
    
    def __init__(self, state_file: Optional[str] = None):
        """初始化导出续传器
        
        Args:
            state_file: 状态文件路径，默认为`.export_state`
        """
        self.logger = get_logger("export_resumer")
        self.state_file = state_file or ".export_state"
        self.progress = 0.0
        self.checksum = None
        self.last_save_time = 0
        self.save_interval = 5  # 默认每5秒保存一次状态
        
    def save_state(self, progress: float) -> None:
        """保存导出进度状态
        
        Args:
            progress: 当前进度(0.0-1.0)
        """
        # 避免频繁保存
        current_time = time.time()
        if current_time - self.last_save_time < self.save_interval and progress < 1.0:
            return
            
        self.last_save_time = current_time
        self.progress = progress
        
        # 创建状态数据
        state_data = {
            "progress": progress,
            "timestamp": current_time,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 计算校验和
        checksum = hashlib.md5(str(progress).encode()).hexdigest()
        state_data["checksum"] = checksum
        self.checksum = checksum
        
        # 保存状态
        with open(self.state_file, 'wb') as f:
            pickle.dump(state_data, f)
            
        self.logger.debug(f"已保存导出进度: {progress:.2%}")
    
    def load_state(self) -> Optional[float]:
        """加载导出进度状态
        
        Returns:
            Optional[float]: 加载的进度值，如果没有有效状态则返回None
        """
        if not os.path.exists(self.state_file):
            self.logger.debug("未找到导出状态文件")
            return None
            
        try:
            with open(self.state_file, 'rb') as f:
                state_data = pickle.load(f)
                
            # 验证状态数据
            progress = state_data.get("progress", 0.0)
            checksum = state_data.get("checksum", "")
            expected_checksum = hashlib.md5(str(progress).encode()).hexdigest()
            
            if checksum != expected_checksum:
                self.logger.error("导出状态校验和不匹配，状态可能已损坏")
                return None
                
            self.progress = progress
            self.checksum = checksum
            self.last_save_time = state_data.get("timestamp", time.time())
            
            self.logger.info(f"已加载导出进度: {progress:.2%} (保存于 {state_data.get('date', 'unknown')})")
            return progress
            
        except Exception as e:
            self.logger.error(f"加载导出状态失败: {str(e)}")
            return None
    
    def _verify_state(self) -> bool:
        """验证导出进度状态的完整性
        
        Returns:
            bool: 状态是否有效
        """
        if not os.path.exists(self.state_file):
            return False
            
        try:
            with open(self.state_file, 'rb') as f:
                state_data = pickle.load(f)
                
            progress = state_data.get("progress", 0.0)
            checksum = state_data.get("checksum", "")
            expected_checksum = hashlib.md5(str(progress).encode()).hexdigest()
            
            return checksum == expected_checksum
            
        except Exception:
            return False
    
    def clear_state(self) -> bool:
        """清除导出进度状态
        
        Returns:
            bool: 是否成功清除
        """
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
                self.progress = 0.0
                self.checksum = None
                self.last_save_time = 0
                self.logger.debug("已清除导出进度状态")
                return True
            except Exception as e:
                self.logger.error(f"清除导出状态失败: {str(e)}")
                return False
        return True
    
    @contextmanager
    def resumable_export(self, callback: Optional[Callable[[float], None]] = None):
        """创建可恢复导出的上下文管理器
        
        Args:
            callback: 进度回调函数
            
        Yields:
            ExportResumer: 导出续传器实例
        """
        # 使用资源清理上下文
        with resource_cleanup_context("export") as context:
            try:
                # 尝试加载之前的状态
                self.load_state()
                
                # 提供自身实例
                yield self
                
                # 导出成功，清除状态
                self.clear_state()
                
            except Exception as e:
                # 发生异常，保存当前状态
                self.logger.error(f"导出过程中断: {str(e)}")
                
                # 确保已保存当前进度
                if self.progress > 0:
                    self.save_state(self.progress)
                    
                if callback:
                    callback(self.progress)
                    
                # 重新抛出异常
                raise


class ExportResumerSingleton:
    """导出续传单例
    
    确保全局使用同一个导出续传器实例
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls, state_file: Optional[str] = None) -> ExportResumer:
        """获取导出续传器实例
        
        Args:
            state_file: 状态文件路径
            
        Returns:
            ExportResumer: 导出续传器实例
        """
        if cls._instance is None:
            cls._instance = ExportResumer(state_file)
        return cls._instance


def get_export_resumer(state_file: Optional[str] = None) -> ExportResumer:
    """获取导出续传器实例
    
    Args:
        state_file: 状态文件路径
        
    Returns:
        ExportResumer: 导出续传器实例
    """
    return ExportResumerSingleton.get_instance(state_file)


class ResumableExporter:
    """可恢复导出器
    
    在基本导出器基础上增加断点续传功能
    """
    
    def __init__(self, exporter: Any):
        """初始化可恢复导出器
        
        Args:
            exporter: 基本导出器实例
        """
        self.exporter = exporter
        self.logger = get_logger(f"resumable_exporter.{exporter.name}")
        self.resumer = get_export_resumer()
        
    def export(self, 
               version: Dict[str, Any], 
               output_path: str,
               progress_callback: Optional[Callable[[float], None]] = None) -> str:
        """执行可恢复导出
        
        Args:
            version: 版本数据
            output_path: 输出路径
            progress_callback: 进度回调函数
            
        Returns:
            str: 导出文件路径
        """
        with self.resumer.resumable_export(progress_callback) as resumer:
            # 获取已完成的进度
            start_progress = resumer.progress
            
            # 判断是否需要继续之前的导出
            if start_progress > 0:
                self.logger.info(f"继续之前的导出，从 {start_progress:.2%} 开始")
                
                # 根据start_progress恢复导出状态
                self._restore_export_state(version, output_path, start_progress)
            else:
                self.logger.info("开始新的导出")
            
            # 封装进度回调
            def track_progress(progress):
                # 调整进度，考虑已完成的部分
                adjusted_progress = start_progress + (1 - start_progress) * progress
                resumer.save_state(adjusted_progress)
                
                if progress_callback:
                    progress_callback(adjusted_progress)
            
            # 添加进度跟踪
            version['_progress_callback'] = track_progress
            
            # 执行导出
            result = self.exporter.export(version, output_path)
            
            # 设置100%完成
            track_progress(1.0)
            
            return result
    
    def _restore_export_state(self, 
                             version: Dict[str, Any], 
                             output_path: str, 
                             progress: float) -> None:
        """恢复导出状态
        
        Args:
            version: 版本数据
            output_path: 输出路径
            progress: 已完成的进度
        """
        # 检查是否存在部分完成的文件
        if os.path.exists(output_path):
            self.logger.info(f"发现部分完成的导出文件: {output_path}")
            
            # 如果是支持断点续传的导出器，可以在这里恢复特定状态
            # 例如，对于分段导出的格式，可以跳过已导出的部分
            
            # 在version中添加恢复信息
            version['_resume_info'] = {
                'progress': progress,
                'output_path': output_path,
                'timestamp': time.time()
            }
            
            # 现实中，这里需要根据不同的导出器类型，实现不同的恢复逻辑


def make_resumable(exporter: Any) -> ResumableExporter:
    """将普通导出器转换为可恢复导出器
    
    Args:
        exporter: 基本导出器实例
        
    Returns:
        ResumableExporter: 可恢复导出器
    """
    return ResumableExporter(exporter)


@contextmanager
def resumable_export_context(state_file: Optional[str] = None):
    """创建可恢复导出上下文
    
    Args:
        state_file: 状态文件路径
        
    Yields:
        ExportResumer: 导出续传器实例
    """
    resumer = get_export_resumer(state_file)
    with resumer.resumable_export() as r:
        yield r 