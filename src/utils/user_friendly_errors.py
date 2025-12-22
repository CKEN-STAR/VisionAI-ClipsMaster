#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户友好的错误提示模块
将技术性错误转换为用户可理解的提示，并提供解决方案
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UserFriendlyError:
    """用户友好的错误信息"""
    title: str  # 错误标题
    message: str  # 用户可理解的错误描述
    technical_details: str  # 技术细节（可选显示）
    solutions: List[str]  # 建议的解决方案
    severity: str  # 严重程度：info, warning, error, critical


class ErrorTranslator:
    """错误翻译器 - 将技术错误转换为用户友好的提示"""
    
    def __init__(self):
        self.error_patterns = self._init_error_patterns()
    
    def _init_error_patterns(self) -> Dict[str, Dict]:
        """初始化错误模式匹配规则"""
        return {
            # FFmpeg相关错误
            "ffmpeg_not_found": {
                "keywords": ["ffmpeg", "not found", "no such file"],
                "title": "视频处理工具未找到",
                "message": "系统未找到FFmpeg视频处理工具，视频剪辑功能无法使用。",
                "solutions": [
                    "请确保FFmpeg已正确安装",
                    "检查FFmpeg是否在系统PATH中",
                    "或将FFmpeg放置在项目的tools/ffmpeg/bin目录下"
                ],
                "severity": "error"
            },
            
            # 内存不足错误
            "out_of_memory": {
                "keywords": ["out of memory", "memory", "oom", "内存不足"],
                "title": "内存不足",
                "message": "系统内存不足，无法完成当前操作。",
                "solutions": [
                    "关闭其他占用内存的程序",
                    "尝试处理较小的视频文件",
                    "启用模型量化以降低内存需求",
                    "考虑升级系统内存"
                ],
                "severity": "error"
            },
            
            # GPU相关错误
            "cuda_error": {
                "keywords": ["cuda", "gpu", "nvidia"],
                "title": "GPU处理错误",
                "message": "GPU处理过程中出现错误，可能是驱动问题或显存不足。",
                "solutions": [
                    "更新NVIDIA显卡驱动",
                    "检查CUDA版本是否匹配",
                    "尝试使用CPU模式（在设置中切换）",
                    "减小批处理大小"
                ],
                "severity": "warning"
            },
            
            # 文件不存在错误
            "file_not_found": {
                "keywords": ["no such file", "file not found", "文件不存在"],
                "title": "文件未找到",
                "message": "指定的文件不存在或路径不正确。",
                "solutions": [
                    "检查文件路径是否正确",
                    "确认文件是否已被移动或删除",
                    "检查文件名是否包含特殊字符"
                ],
                "severity": "error"
            },
            
            # 模型加载错误
            "model_load_error": {
                "keywords": ["model", "load", "checkpoint", "权重"],
                "title": "模型加载失败",
                "message": "AI模型加载失败，可能是模型文件损坏或不兼容。",
                "solutions": [
                    "重新下载模型文件",
                    "检查模型文件完整性",
                    "确认模型版本与程序兼容",
                    "清理模型缓存后重试"
                ],
                "severity": "error"
            },
            
            # 字幕解析错误
            "srt_parse_error": {
                "keywords": ["srt", "subtitle", "parse", "字幕"],
                "title": "字幕文件解析失败",
                "message": "字幕文件格式不正确或编码有问题。",
                "solutions": [
                    "检查SRT文件格式是否正确",
                    "尝试使用UTF-8编码保存字幕文件",
                    "使用字幕编辑器验证文件格式",
                    "确认时间码格式正确（HH:MM:SS,mmm）"
                ],
                "severity": "error"
            },
            
            # 网络错误
            "network_error": {
                "keywords": ["network", "connection", "timeout", "网络"],
                "title": "网络连接错误",
                "message": "网络连接失败，无法下载模型或访问在线服务。",
                "solutions": [
                    "检查网络连接是否正常",
                    "尝试使用代理或VPN",
                    "稍后重试",
                    "使用离线模式（如果支持）"
                ],
                "severity": "warning"
            },
            
            # 权限错误
            "permission_error": {
                "keywords": ["permission", "access denied", "权限"],
                "title": "权限不足",
                "message": "没有足够的权限访问文件或目录。",
                "solutions": [
                    "以管理员身份运行程序",
                    "检查文件/目录权限设置",
                    "确认文件未被其他程序占用"
                ],
                "severity": "error"
            },
            
            # DLL加载错误
            "dll_error": {
                "keywords": ["dll", "动态链接库", "c10.dll", "cudnn"],
                "title": "系统库加载失败",
                "message": "缺少必要的系统库文件，可能需要安装运行时环境。",
                "solutions": [
                    "安装Visual C++ Redistributable",
                    "更新NVIDIA CUDA工具包",
                    "重新安装PyTorch",
                    "检查系统环境变量配置"
                ],
                "severity": "error"
            },
        }
    
    def translate(self, exception: Exception, context: Optional[Dict] = None) -> UserFriendlyError:
        """
        将异常转换为用户友好的错误信息
        
        Args:
            exception: 原始异常
            context: 上下文信息（可选）
        
        Returns:
            UserFriendlyError对象
        """
        error_str = str(exception).lower()
        exception_type = type(exception).__name__
        
        # 尝试匹配错误模式
        for pattern_name, pattern in self.error_patterns.items():
            if any(keyword in error_str for keyword in pattern["keywords"]):
                return UserFriendlyError(
                    title=pattern["title"],
                    message=pattern["message"],
                    technical_details=f"{exception_type}: {str(exception)}",
                    solutions=pattern["solutions"],
                    severity=pattern["severity"]
                )
        
        # 如果没有匹配的模式，返回通用错误
        return self._create_generic_error(exception, context)
    
    def _create_generic_error(self, exception: Exception, context: Optional[Dict] = None) -> UserFriendlyError:
        """创建通用错误信息"""
        exception_type = type(exception).__name__
        
        # 根据异常类型提供基本建议
        solutions = []
        if "Error" in exception_type:
            solutions.append("检查输入数据是否正确")
            solutions.append("查看详细日志了解更多信息")
            solutions.append("如果问题持续，请联系技术支持")
        
        return UserFriendlyError(
            title=f"发生错误：{exception_type}",
            message=f"程序运行过程中遇到了问题：{str(exception)[:100]}",
            technical_details=f"{exception_type}: {str(exception)}",
            solutions=solutions or ["请查看日志文件获取更多信息"],
            severity="error"
        )
    
    def format_for_display(self, error: UserFriendlyError, show_technical: bool = False) -> str:
        """
        格式化错误信息用于显示
        
        Args:
            error: UserFriendlyError对象
            show_technical: 是否显示技术细节
        
        Returns:
            格式化的错误信息字符串
        """
        lines = []
        lines.append(f"❌ {error.title}")
        lines.append("")
        lines.append(error.message)
        
        if error.solutions:
            lines.append("")
            lines.append("💡 建议解决方案：")
            for i, solution in enumerate(error.solutions, 1):
                lines.append(f"  {i}. {solution}")
        
        if show_technical and error.technical_details:
            lines.append("")
            lines.append("🔧 技术细节：")
            lines.append(f"  {error.technical_details}")
        
        return "\n".join(lines)


# 全局错误翻译器实例
_error_translator = ErrorTranslator()


def translate_error(exception: Exception, context: Optional[Dict] = None) -> UserFriendlyError:
    """
    便捷函数：翻译错误
    
    Args:
        exception: 原始异常
        context: 上下文信息
    
    Returns:
        UserFriendlyError对象
    """
    return _error_translator.translate(exception, context)


def format_error(exception: Exception, show_technical: bool = False) -> str:
    """
    便捷函数：格式化错误用于显示
    
    Args:
        exception: 原始异常
        show_technical: 是否显示技术细节
    
    Returns:
        格式化的错误信息字符串
    """
    error = translate_error(exception)
    return _error_translator.format_for_display(error, show_technical)

