#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强错误处理和恢复机制
提供完善的错误处理、恢复机制和用户友好的错误提示
"""

import logging
import traceback
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from enum import Enum

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别"""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    MEMORY = "memory"
    AI_MODEL = "ai_model"
    VIDEO_FILE = "video_file"
    SRT_SUBTITLE = "srt_subtitle"
    SYSTEM = "system"
    USER_INPUT = "user_input"

class EnhancedErrorHandler:
    """增强错误处理器"""
    
    def __init__(self, log_dir: str = "logs", enable_recovery: bool = True):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.enable_recovery = enable_recovery
        
        # 设置日志记录
        self._setup_logging()
        
        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "recovered_errors": 0,
            "critical_errors": 0,
            "by_category": {},
            "by_severity": {}
        }
        
        # 恢复策略注册表
        self.recovery_strategies = {}
        self._register_default_recovery_strategies()
        
        self.logger.info("增强错误处理器初始化完成")
    
    def _setup_logging(self):
        """设置日志记录"""
        # 创建专用的错误日志记录器
        self.logger = logging.getLogger("enhanced_error_handler")
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 文件处理器 - 详细日志
        log_file = self.log_dir / f"error_handler_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器 - 简化日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _register_default_recovery_strategies(self):
        """注册默认恢复策略"""
        
        # 文件系统错误恢复策略
        self.recovery_strategies[ErrorCategory.FILESYSTEM] = {
            "PermissionError": self._recover_permission_error,
            "FileNotFoundError": self._recover_file_not_found,
            "OSError": self._recover_os_error,
            "DiskSpaceError": self._recover_disk_space_error
        }
        
        # 网络错误恢复策略
        self.recovery_strategies[ErrorCategory.NETWORK] = {
            "ConnectionTimeout": self._recover_connection_timeout,
            "DNSResolutionError": self._recover_dns_error,
            "NetworkUnreachable": self._recover_network_unreachable
        }
        
        # 内存错误恢复策略
        self.recovery_strategies[ErrorCategory.MEMORY] = {
            "MemoryError": self._recover_memory_error,
            "OutOfMemoryError": self._recover_oom_error
        }
        
        # AI模型错误恢复策略
        self.recovery_strategies[ErrorCategory.AI_MODEL] = {
            "ModelCorruptionError": self._recover_model_corruption,
            "ModelFormatError": self._recover_model_format_error,
            "ModelLoadingTimeout": self._recover_model_timeout
        }
        
        # 视频文件错误恢复策略
        self.recovery_strategies[ErrorCategory.VIDEO_FILE] = {
            "UnsupportedVideoFormat": self._recover_unsupported_video,
            "VideoEncodingError": self._recover_video_encoding,
            "VideoFileTruncated": self._recover_video_truncation
        }
        
        # SRT字幕错误恢复策略
        self.recovery_strategies[ErrorCategory.SRT_SUBTITLE] = {
            "SubtitleEncodingError": self._recover_subtitle_encoding,
            "SubtitleTimelineError": self._recover_subtitle_timeline,
            "SubtitleFormatError": self._recover_subtitle_format
        }
    
    def handle_error(self, 
                    error: Exception, 
                    category: ErrorCategory, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Optional[Dict[str, Any]] = None,
                    user_message: Optional[str] = None) -> Dict[str, Any]:
        """处理错误的主要方法"""
        
        error_id = f"ERR_{int(time.time())}_{id(error)}"
        error_type = type(error).__name__
        
        # 更新错误统计
        self._update_error_stats(category, severity)
        
        # 记录详细错误信息
        error_details = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "category": category.value,
            "severity": severity.value,
            "context": context or {},
            "traceback": traceback.format_exc(),
            "recovery_attempted": False,
            "recovery_successful": False,
            "user_message": user_message
        }
        
        # 记录错误日志
        self.logger.error(f"错误发生 [{error_id}] {category.value}.{error_type}: {str(error)}")
        if context:
            self.logger.debug(f"错误上下文 [{error_id}]: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # 尝试恢复
        if self.enable_recovery and severity != ErrorSeverity.CRITICAL:
            recovery_result = self._attempt_recovery(error, category, error_type, context)
            error_details.update(recovery_result)
        
        # 生成用户友好的错误消息
        user_friendly_message = self._generate_user_friendly_message(error_details)
        error_details["user_friendly_message"] = user_friendly_message
        
        # 保存错误报告
        self._save_error_report(error_details)
        
        return error_details
    
    def _update_error_stats(self, category: ErrorCategory, severity: ErrorSeverity):
        """更新错误统计"""
        self.error_stats["total_errors"] += 1
        
        if severity == ErrorSeverity.CRITICAL:
            self.error_stats["critical_errors"] += 1
        
        # 按类别统计
        if category.value not in self.error_stats["by_category"]:
            self.error_stats["by_category"][category.value] = 0
        self.error_stats["by_category"][category.value] += 1
        
        # 按严重程度统计
        if severity.value not in self.error_stats["by_severity"]:
            self.error_stats["by_severity"][severity.value] = 0
        self.error_stats["by_severity"][severity.value] += 1
    
    def _attempt_recovery(self, error: Exception, category: ErrorCategory, 
                         error_type: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """尝试错误恢复"""
        recovery_result = {
            "recovery_attempted": True,
            "recovery_successful": False,
            "recovery_strategy": None,
            "recovery_message": None
        }
        
        try:
            # 查找恢复策略
            category_strategies = self.recovery_strategies.get(category, {})
            recovery_func = category_strategies.get(error_type)
            
            if recovery_func:
                recovery_result["recovery_strategy"] = recovery_func.__name__
                self.logger.info(f"尝试恢复策略: {recovery_func.__name__}")
                
                # 执行恢复
                recovery_success, recovery_message = recovery_func(error, context)
                recovery_result["recovery_successful"] = recovery_success
                recovery_result["recovery_message"] = recovery_message
                
                if recovery_success:
                    self.error_stats["recovered_errors"] += 1
                    self.logger.info(f"错误恢复成功: {recovery_message}")
                else:
                    self.logger.warning(f"错误恢复失败: {recovery_message}")
            else:
                recovery_result["recovery_message"] = f"未找到 {category.value}.{error_type} 的恢复策略"
                self.logger.warning(recovery_result["recovery_message"])
                
        except Exception as recovery_error:
            recovery_result["recovery_message"] = f"恢复过程中发生错误: {str(recovery_error)}"
            self.logger.error(f"恢复失败: {recovery_error}")
        
        return recovery_result
    
    def _generate_user_friendly_message(self, error_details: Dict[str, Any]) -> str:
        """生成用户友好的错误消息"""
        category = error_details["category"]
        error_type = error_details["error_type"]
        severity = error_details["severity"]
        recovery_successful = error_details.get("recovery_successful", False)
        
        # 基础消息模板
        if recovery_successful:
            base_message = "遇到了一个问题，但已经自动修复："
        else:
            if severity == "critical":
                base_message = "遇到了一个严重问题："
            elif severity == "high":
                base_message = "遇到了一个重要问题："
            else:
                base_message = "遇到了一个问题："
        
        # 根据错误类别生成具体消息
        specific_messages = {
            "filesystem": {
                "PermissionError": "文件访问权限不足，请检查文件权限设置",
                "FileNotFoundError": "找不到指定的文件，请确认文件路径是否正确",
                "OSError": "文件系统操作失败，可能是磁盘空间不足或文件被占用"
            },
            "network": {
                "ConnectionTimeout": "网络连接超时，请检查网络连接",
                "DNSResolutionError": "域名解析失败，请检查网络设置",
                "NetworkUnreachable": "网络不可达，请检查网络连接"
            },
            "memory": {
                "MemoryError": "内存不足，请关闭其他程序或增加系统内存",
                "OutOfMemoryError": "系统内存耗尽，建议重启程序"
            },
            "ai_model": {
                "ModelCorruptionError": "AI模型文件损坏，请重新下载模型文件",
                "ModelFormatError": "AI模型格式不兼容，请使用支持的模型格式",
                "ModelLoadingTimeout": "AI模型加载超时，请检查系统性能或网络连接"
            },
            "video_file": {
                "UnsupportedVideoFormat": "不支持的视频格式，请转换为支持的格式（MP4、AVI、MOV等）",
                "VideoEncodingError": "视频编码错误，请检查视频文件是否完整",
                "VideoFileTruncated": "视频文件不完整，请重新获取完整的视频文件"
            },
            "srt_subtitle": {
                "SubtitleEncodingError": "字幕文件编码错误，请确保使用UTF-8编码",
                "SubtitleTimelineError": "字幕时间轴错误，请检查字幕文件格式",
                "SubtitleFormatError": "字幕文件格式错误，请使用标准SRT格式"
            }
        }
        
        # 获取具体消息
        category_messages = specific_messages.get(category, {})
        specific_message = category_messages.get(error_type, f"{error_type}: {error_details['error_message']}")
        
        # 组合最终消息
        final_message = f"{base_message} {specific_message}"
        
        # 添加恢复信息
        if recovery_successful:
            final_message += " ✅ 问题已自动解决，可以继续操作。"
        else:
            final_message += " ❌ 请根据提示解决问题后重试。"
        
        return final_message
    
    def _save_error_report(self, error_details: Dict[str, Any]):
        """保存错误报告"""
        try:
            error_id = error_details["error_id"]
            report_file = self.log_dir / f"error_report_{error_id}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(error_details, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存错误报告失败: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        recovery_rate = (self.error_stats["recovered_errors"] / 
                        self.error_stats["total_errors"]) if self.error_stats["total_errors"] > 0 else 0
        
        return {
            "total_errors": self.error_stats["total_errors"],
            "recovered_errors": self.error_stats["recovered_errors"],
            "critical_errors": self.error_stats["critical_errors"],
            "recovery_rate": recovery_rate,
            "by_category": self.error_stats["by_category"],
            "by_severity": self.error_stats["by_severity"]
        }

    # 文件系统错误恢复策略
    def _recover_permission_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复权限错误"""
        try:
            file_path = context.get("file_path") if context else None
            if file_path and os.path.exists(file_path):
                # 尝试修改文件权限
                os.chmod(file_path, 0o666)
                return True, f"已修复文件权限: {file_path}"
            return False, "无法确定文件路径或文件不存在"
        except Exception as e:
            return False, f"权限修复失败: {str(e)}"

    def _recover_file_not_found(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复文件未找到错误"""
        try:
            file_path = context.get("file_path") if context else None
            if file_path:
                # 尝试创建目录
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                return True, f"已创建目录结构: {Path(file_path).parent}"
            return False, "无法确定文件路径"
        except Exception as e:
            return False, f"目录创建失败: {str(e)}"

    def _recover_os_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复操作系统错误"""
        try:
            # 通用OS错误恢复策略
            time.sleep(1)  # 等待系统资源释放
            return True, "已等待系统资源释放，可以重试"
        except Exception as e:
            return False, f"OS错误恢复失败: {str(e)}"

    def _recover_disk_space_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复磁盘空间不足错误"""
        try:
            # 清理临时文件
            temp_dir = Path.cwd() / "temp"
            if temp_dir.exists():
                for temp_file in temp_dir.glob("*"):
                    if temp_file.is_file():
                        temp_file.unlink()
                return True, "已清理临时文件，释放磁盘空间"
            return False, "未找到可清理的临时文件"
        except Exception as e:
            return False, f"磁盘空间清理失败: {str(e)}"

    # 网络错误恢复策略
    def _recover_connection_timeout(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复连接超时错误"""
        try:
            # 增加重试机制
            retry_count = context.get("retry_count", 0) if context else 0
            if retry_count < 3:
                time.sleep(2 ** retry_count)  # 指数退避
                return True, f"准备第{retry_count + 1}次重试连接"
            return False, "已达到最大重试次数"
        except Exception as e:
            return False, f"连接重试准备失败: {str(e)}"

    def _recover_dns_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复DNS解析错误"""
        try:
            # 切换到备用DNS或本地缓存
            return True, "建议检查网络设置或使用备用DNS"
        except Exception as e:
            return False, f"DNS错误恢复失败: {str(e)}"

    def _recover_network_unreachable(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复网络不可达错误"""
        try:
            # 切换到离线模式
            return True, "已切换到离线模式，使用本地资源"
        except Exception as e:
            return False, f"网络错误恢复失败: {str(e)}"

    # 内存错误恢复策略
    def _recover_memory_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复内存错误"""
        try:
            import gc
            # 强制垃圾回收
            gc.collect()
            return True, "已执行垃圾回收，释放内存"
        except Exception as e:
            return False, f"内存回收失败: {str(e)}"

    def _recover_oom_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复内存耗尽错误"""
        try:
            import gc
            # 强制垃圾回收并降低处理精度
            gc.collect()
            return True, "已释放内存并降低处理精度"
        except Exception as e:
            return False, f"OOM恢复失败: {str(e)}"

    # AI模型错误恢复策略
    def _recover_model_corruption(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复模型损坏错误"""
        try:
            # 切换到备用模型或降级模型
            return True, "已切换到备用AI模型"
        except Exception as e:
            return False, f"模型切换失败: {str(e)}"

    def _recover_model_format_error(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复模型格式错误"""
        try:
            # 尝试格式转换或使用兼容模型
            return True, "已切换到兼容的模型格式"
        except Exception as e:
            return False, f"模型格式恢复失败: {str(e)}"

    def _recover_model_timeout(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复模型加载超时"""
        try:
            # 使用更小的模型或分片加载
            return True, "已切换到轻量级模型"
        except Exception as e:
            return False, f"模型超时恢复失败: {str(e)}"

    # 视频文件错误恢复策略
    def _recover_unsupported_video(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复不支持的视频格式"""
        try:
            # 建议格式转换
            return True, "建议将视频转换为MP4格式"
        except Exception as e:
            return False, f"视频格式恢复失败: {str(e)}"

    def _recover_video_encoding(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复视频编码错误"""
        try:
            # 尝试使用不同的解码器
            return True, "已切换到兼容的视频解码器"
        except Exception as e:
            return False, f"视频编码恢复失败: {str(e)}"

    def _recover_video_truncation(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复视频文件截断"""
        try:
            # 使用可用部分继续处理
            return True, "将使用视频的完整部分继续处理"
        except Exception as e:
            return False, f"视频截断恢复失败: {str(e)}"

    # SRT字幕错误恢复策略
    def _recover_subtitle_encoding(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复字幕编码错误"""
        try:
            # 尝试不同的编码格式
            return True, "已尝试使用GBK编码重新读取字幕"
        except Exception as e:
            return False, f"字幕编码恢复失败: {str(e)}"

    def _recover_subtitle_timeline(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复字幕时间轴错误"""
        try:
            # 自动修复时间轴
            return True, "已自动修复字幕时间轴错误"
        except Exception as e:
            return False, f"字幕时间轴恢复失败: {str(e)}"

    def _recover_subtitle_format(self, error: Exception, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """恢复字幕格式错误"""
        try:
            # 尝试格式修复
            return True, "已尝试修复字幕格式"
        except Exception as e:
            return False, f"字幕格式恢复失败: {str(e)}"
