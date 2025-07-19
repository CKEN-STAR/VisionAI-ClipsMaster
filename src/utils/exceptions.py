#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常模块 - 简化版（UI演示用）
"""

import enum
import os

class ErrorCode(enum.Enum):
    """错误代码枚举"""
    GENERAL_ERROR = 1000
    FILE_NOT_FOUND = 1001
    PERMISSION_DENIED = 1002
    DEPENDENCY_ERROR = 1003
    MEMORY_ERROR = 1004
    MODEL_ERROR = 1005
    VALIDATION_ERROR = 1006
    PROCESSING_ERROR = 1007
    FORMAT_ERROR = 1008
    NETWORK_ERROR = 1009
    USER_INPUT_ERROR = 1010
    SYSTEM_ERROR = 1011
    TIMEOUT_ERROR = 1012
    
class ClipMasterError(Exception):
    """VisionAI-ClipsMaster基础异常类"""
    
    def __init__(self, message, code=None, critical=False):
        """初始化异常"""
        super().__init__(message)
        self.message = message
        self.code = code
        self.critical = critical

class MemoryError(ClipMasterError):
    """内存错误"""

    def __init__(self, message="内存相关错误"):
        """初始化内存异常"""
        super().__init__(message, code="MEMORY_ERROR", critical=True)

class MemoryOverflowError(ClipMasterError):
    """内存溢出错误"""

    def __init__(self, message="内存不足，请关闭其他应用或使用更小的模型"):
        """初始化内存溢出异常"""
        super().__init__(message, code="MEMORY_ERROR", critical=True)

class BaseError(Exception):
    """基础异常类"""
    pass

# 情感相关异常
class EmotionError(BaseError):
    """情感处理相关异常的基类"""
    pass

class EmotionJumpError(EmotionError):
    """情感跳跃异常"""
    
    def __init__(self, message=None, from_emotion=None, to_emotion=None, position=None):
        self.from_emotion = from_emotion
        self.to_emotion = to_emotion
        self.position = position
        
        if message is None:
            message = f"情感跳跃: 从 {from_emotion} 到 {to_emotion}"
            if position is not None:
                message += f" 在位置 {position}"
        
        super().__init__(message)

class EmotionMissingError(EmotionError):
    """情感缺失异常"""
    
    def __init__(self, message=None, position=None, expected_emotion=None):
        self.position = position
        self.expected_emotion = expected_emotion
        
        if message is None:
            message = "情感缺失"
            if expected_emotion is not None:
                message += f": 期望 {expected_emotion}"
            if position is not None:
                message += f" 在位置 {position}"
        
        super().__init__(message)

class EmotionInconsistencyError(EmotionError):
    """情感不一致异常"""
    
    def __init__(self, message=None, context=None, inconsistent_parts=None):
        self.context = context
        self.inconsistent_parts = inconsistent_parts or []
        
        if message is None:
            message = "情感不一致"
            if context is not None:
                message += f": {context}"
        
        super().__init__(message)

class ModelCorruptionError(ClipMasterError):
    """模型损坏异常"""
    
    def __init__(self, message=None, model_path=None):
        """初始化模型损坏异常"""
        self.model_path = model_path
        
        if message is None:
            message = "模型文件已损坏"
            if model_path is not None:
                message += f": {model_path}"
        
        super().__init__(message, code=ErrorCode.MODEL_ERROR, critical=True)

class UserInputError(ClipMasterError):
    """用户输入错误异常"""
    
    def __init__(self, message=None, field=None, value=None):
        """初始化用户输入错误异常"""
        self.field = field
        self.value = value
        
        if message is None:
            message = "用户输入无效"
            if field is not None:
                message += f": {field}"
                if value is not None:
                    message += f" = {value}"
        
        super().__init__(message, code=ErrorCode.USER_INPUT_ERROR, critical=False)

class ResourceError(ClipMasterError):
    """资源错误异常"""
    
    def __init__(self, message=None, resource_type=None, resource_id=None):
        """初始化资源错误异常"""
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if message is None:
            message = "资源访问错误"
            if resource_type is not None:
                message += f": {resource_type}"
                if resource_id is not None:
                    message += f" ({resource_id})"
        
        super().__init__(message, code=ErrorCode.GENERAL_ERROR, critical=False)

class HybridContentError(ClipMasterError):
    """混合内容错误异常"""
    
    def __init__(self, message=None, content_type=None, details=None):
        """初始化混合内容错误异常"""
        self.content_type = content_type
        self.details = details or {}
        
        if message is None:
            message = "混合内容错误"
            if content_type is not None:
                message += f": {content_type}"
        
        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=False)

class LanguageDetectionError(ClipMasterError):
    """语言检测错误异常"""
    
    def __init__(self, message=None, text_sample=None, languages=None):
        """初始化语言检测错误异常"""
        self.text_sample = text_sample
        self.languages = languages or []
        
        if message is None:
            message = "语言检测错误"
            if text_sample is not None and len(text_sample) > 30:
                text_sample = text_sample[:30] + "..."
            if text_sample:
                message += f": {text_sample}"
        
        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=False)

class NarrativeAnalysisError(ClipMasterError):
    """叙事分析错误异常"""
    
    def __init__(self, message=None, narrative_type=None, details=None):
        """初始化叙事分析错误异常"""
        self.narrative_type = narrative_type
        self.details = details or {}
        
        if message is None:
            message = "叙事分析错误"
            if narrative_type is not None:
                message += f": {narrative_type}"
        
        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=False)

class VideoProcessError(ClipMasterError):
    """视频处理错误异常"""
    
    def __init__(self, message=None, video_path=None, stage=None, details=None):
        """初始化视频处理错误异常"""
        self.video_path = video_path
        self.stage = stage
        self.details = details or {}
        
        if message is None:
            message = "视频处理错误"
            if stage is not None:
                message += f" 在{stage}阶段"
            if video_path is not None:
                message += f": {os.path.basename(video_path)}"
        
        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=True)

class AudioProcessError(ClipMasterError):
    """音频处理错误异常"""
    
    def __init__(self, message=None, audio_path=None, stage=None, details=None):
        """初始化音频处理错误异常"""
        self.audio_path = audio_path
        self.stage = stage
        self.details = details or {}
        
        if message is None:
            message = "音频处理错误"
            if stage is not None:
                message += f" 在{stage}阶段"
            if audio_path is not None:
                message += f": {os.path.basename(audio_path)}"
        
        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=True)

class InvalidSRTError(ClipMasterError):
    """无效SRT文件异常"""
    
    def __init__(self, message=None, srt_path=None, line_number=None, details=None):
        """初始化无效SRT文件异常"""
        self.srt_path = srt_path
        self.line_number = line_number
        self.details = details or {}
        
        if message is None:
            message = "无效的SRT文件"
            if srt_path is not None:
                message += f": {os.path.basename(srt_path)}"
            if line_number is not None:
                message += f" (行 {line_number})"
        
        super().__init__(message, code=ErrorCode.FORMAT_ERROR, critical=False)

class ModelLoadError(ClipMasterError):
    """模型加载错误异常"""
    
    def __init__(self, message=None, model_name=None, model_path=None, details=None):
        """初始化模型加载错误异常"""
        self.model_name = model_name
        self.model_path = model_path
        self.details = details or {}
        
        if message is None:
            message = "模型加载错误"
            if model_name is not None:
                message += f": {model_name}"
            if model_path is not None:
                message += f" ({os.path.basename(model_path)})"
        
        super().__init__(message, code=ErrorCode.MODEL_ERROR, critical=True)

class SecurityError(ClipMasterError):
    """安全错误异常"""
    
    def __init__(self, message=None, operation=None, details=None):
        """初始化安全错误异常"""
        self.operation = operation
        self.details = details or {}
        
        if message is None:
            message = "安全错误"
            if operation is not None:
                message += f": {operation}"
        
        super().__init__(message, code=ErrorCode.SYSTEM_ERROR, critical=True)

class ValidationError(ClipMasterError):
    """验证错误异常"""
    
    def __init__(self, message=None, field=None, value=None, details=None):
        """初始化验证错误异常"""
        self.field = field
        self.value = value
        self.details = details or {}
        
        if message is None:
            message = "验证错误"
            if field is not None:
                message += f": {field}"
                if value is not None:
                    message += f" = {value}"
        
        super().__init__(message, code=ErrorCode.VALIDATION_ERROR, critical=False)

class FileOperationError(ClipMasterError):
    """文件操作错误异常"""
    
    def __init__(self, message=None, file_path=None, operation=None, details=None):
        """初始化文件操作错误异常"""
        self.file_path = file_path
        self.operation = operation
        self.details = details or {}
        
        if message is None:
            message = "文件操作错误"
            if operation is not None:
                message += f" ({operation})"
            if file_path is not None:
                message += f": {os.path.basename(file_path)}"
        
        super().__init__(message, code=ErrorCode.FILE_NOT_FOUND, critical=False)

class ProcessTimeoutError(ClipMasterError):
    """处理超时错误异常"""
    
    def __init__(self, message=None, process_name=None, timeout=None, details=None):
        """初始化处理超时错误异常"""
        self.process_name = process_name
        self.timeout = timeout
        self.details = details or {}
        
        if message is None:
            message = "处理超时错误"
            if process_name is not None:
                message += f": {process_name}"
            if timeout is not None:
                message += f" (超时: {timeout}秒)"
        
        super().__init__(message, code=ErrorCode.TIMEOUT_ERROR, critical=True)

class ResourceExhaustionError(ClipMasterError):
    """资源耗尽错误异常"""
    
    def __init__(self, message=None, resource_type=None, limit=None, details=None):
        """初始化资源耗尽错误异常"""
        self.resource_type = resource_type
        self.limit = limit
        self.details = details or {}
        
        if message is None:
            message = "资源耗尽错误"
            if resource_type is not None:
                message += f": {resource_type}"
            if limit is not None:
                message += f" (限制: {limit})"
        
        super().__init__(message, code=ErrorCode.MEMORY_ERROR, critical=True)

class EvaluationError(ClipMasterError):
    """评估错误异常"""
    
    def __init__(self, message=None, metric=None, expected=None, actual=None, details=None):
        """初始化评估错误异常"""
        self.metric = metric
        self.expected = expected
        self.actual = actual
        self.details = details or {}
        
        if message is None:
            message = "评估错误"
            if metric is not None:
                message += f": {metric}"
            if expected is not None and actual is not None:
                message += f" (期望: {expected}, 实际: {actual})"
        
        super().__init__(message, code=ErrorCode.VALIDATION_ERROR, critical=False)

class ProcessingError(ClipMasterError):
    """处理错误异常"""

    def __init__(self, message=None, process_type=None, stage=None, details=None):
        """初始化处理错误异常"""
        self.process_type = process_type
        self.stage = stage
        self.details = details or {}

        if message is None:
            message = "处理错误"
            if process_type is not None:
                message += f": {process_type}"
            if stage is not None:
                message += f" 在{stage}阶段"

        super().__init__(message, code=ErrorCode.PROCESSING_ERROR, critical=False)
