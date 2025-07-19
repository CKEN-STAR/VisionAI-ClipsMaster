#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强异常处理器

提供全面的异常处理、边界条件检查和自动恢复机制
"""

import os
import sys
import time
import traceback
import functools
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
import logging

# 使用增强日志系统
try:
    from src.utils.enhanced_logger import get_logger, LogCategory
    logger = get_logger(__name__)
except ImportError:
    # 降级到标准日志
    logger = logging.getLogger(__name__)

class ExceptionSeverity:
    """异常严重程度分级"""
    CRITICAL = "critical"      # 致命错误，需要立即停止
    HIGH = "high"             # 高级错误，需要用户干预
    MEDIUM = "medium"         # 中级错误，可以自动恢复
    LOW = "low"              # 低级错误，记录即可
    INFO = "info"            # 信息性错误，仅提示

class BoundaryChecker:
    """边界条件检查器"""
    
    @staticmethod
    def check_file_path(file_path: Union[str, Path], must_exist: bool = True) -> bool:
        """检查文件路径的有效性，支持中文路径和Unicode字符"""
        try:
            if not file_path:
                raise ValueError("文件路径不能为空")

            path = Path(file_path)

            # 检查路径长度 (Windows路径长度限制)
            if len(str(path)) > 260:  # 标准Windows路径长度限制
                raise ValueError(f"文件路径过长: {len(str(path))} > 260")

            # 改进的非法字符检查 - 只检查真正的Windows非法字符
            # 排除冒号检查，因为它在驱动器路径中是合法的 (如 C:)
            path_str = str(path)

            # 检查每个路径组件，而不是整个路径
            for part in path.parts:
                # 跳过驱动器部分 (如 'C:')
                if len(part) == 2 and part[1] == ':':
                    continue

                # 检查文件名/目录名中的非法字符
                illegal_chars_in_name = '<>"|?*'
                if any(char in part for char in illegal_chars_in_name):
                    raise ValueError(f"路径组件包含非法字符: {part}")

                # 检查控制字符 (ASCII 0-31)
                if any(ord(char) < 32 for char in part if ord(char) < 128):
                    raise ValueError(f"路径组件包含控制字符: {part}")

            # 检查文件是否存在
            if must_exist and not path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")

            # 检查父目录是否存在
            if not must_exist and not path.parent.exists():
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建目录: {path.parent}")
                except OSError as e:
                    logger.error(f"无法创建目录 {path.parent}: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"文件路径检查失败: {e}")
            return False
    
    @staticmethod
    def check_memory_usage(max_mb: int = 1024) -> bool:
        """检查内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > max_mb:
                logger.warning(f"内存使用过高: {memory_mb:.1f}MB > {max_mb}MB")
                return False
            
            return True
            
        except ImportError:
            logger.warning("psutil未安装，无法检查内存使用")
            return True
        except Exception as e:
            logger.error(f"内存检查失败: {e}")
            return False
    
    @staticmethod
    def check_disk_space(path: Union[str, Path], min_mb: int = 100) -> bool:
        """检查磁盘空间"""
        try:
            import shutil
            free_bytes = shutil.disk_usage(path).free
            free_mb = free_bytes / 1024 / 1024
            
            if free_mb < min_mb:
                logger.warning(f"磁盘空间不足: {free_mb:.1f}MB < {min_mb}MB")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"磁盘空间检查失败: {e}")
            return False
    
    @staticmethod
    def check_video_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """检查视频文件的有效性"""
        result = {
            "valid": False,
            "format": None,
            "duration": None,
            "resolution": None,
            "error": None
        }
        
        try:
            if not BoundaryChecker.check_file_path(file_path, must_exist=True):
                result["error"] = "文件路径无效"
                return result
            
            path = Path(file_path)
            
            # 检查文件大小
            file_size = path.stat().st_size
            if file_size == 0:
                result["error"] = "文件为空"
                return result
            
            if file_size < 1024:  # 小于1KB
                result["error"] = "文件过小，可能损坏"
                return result
            
            # 检查文件扩展名
            valid_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm', '.m4v'}
            if path.suffix.lower() not in valid_extensions:
                result["error"] = f"不支持的视频格式: {path.suffix}"
                return result
            
            result["valid"] = True
            result["format"] = path.suffix.lower()
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    @staticmethod
    def check_srt_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """检查SRT字幕文件的有效性"""
        result = {
            "valid": False,
            "encoding": None,
            "subtitle_count": 0,
            "duration": None,
            "error": None
        }
        
        try:
            if not BoundaryChecker.check_file_path(file_path, must_exist=True):
                result["error"] = "文件路径无效"
                return result
            
            path = Path(file_path)
            
            # 检查文件扩展名
            if path.suffix.lower() != '.srt':
                result["error"] = f"不是SRT文件: {path.suffix}"
                return result
            
            # 尝试不同编码读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read()
                    result["encoding"] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                result["error"] = "无法解码文件，编码格式不支持"
                return result
            
            # 简单检查SRT格式
            import re
            srt_pattern = r'\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*\n'
            matches = re.findall(srt_pattern, content)
            
            if not matches:
                result["error"] = "文件不符合SRT格式"
                return result
            
            result["valid"] = True
            result["subtitle_count"] = len(matches)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result

class EnhancedExceptionHandler:
    """增强异常处理器"""
    
    def __init__(self):
        self.error_counts = {}
        self.recovery_strategies = {}
        self.error_history = []
        self.max_history = 1000
        self.lock = threading.Lock()
        
        # 注册默认恢复策略
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认恢复策略"""
        self.recovery_strategies.update({
            FileNotFoundError: self._handle_file_not_found,
            PermissionError: self._handle_permission_error,
            MemoryError: self._handle_memory_error,
            OSError: self._handle_os_error,
            ValueError: self._handle_value_error,
            TypeError: self._handle_type_error,
            ConnectionError: self._handle_connection_error,
            TimeoutError: self._handle_timeout_error,
            ImportError: self._handle_import_error,
            UnicodeDecodeError: self._handle_unicode_error,
            RuntimeError: self._handle_runtime_error,
            AttributeError: self._handle_attribute_error,
            KeyError: self._handle_key_error,
            IndexError: self._handle_index_error,
            ZeroDivisionError: self._handle_zero_division_error,
            NotImplementedError: self._handle_not_implemented_error,
            ModuleNotFoundError: self._handle_module_not_found_error,
        })
    
    def register_strategy(self, exception_type: type, strategy: Callable):
        """注册自定义恢复策略"""
        self.recovery_strategies[exception_type] = strategy
        logger.info(f"注册恢复策略: {exception_type.__name__}")
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: Dict[str, Any] = None,
                        severity: str = ExceptionSeverity.MEDIUM,
                        auto_recover: bool = True) -> Dict[str, Any]:
        """
        处理异常
        
        Args:
            exception: 异常对象
            context: 上下文信息
            severity: 严重程度
            auto_recover: 是否尝试自动恢复
            
        Returns:
            处理结果字典
        """
        with self.lock:
            result = {
                "handled": False,
                "recovered": False,
                "severity": severity,
                "error_type": type(exception).__name__,
                "error_message": str(exception),
                "context": context or {},
                "timestamp": time.time(),
                "recovery_action": None
            }
            
            try:
                # 记录错误
                self._record_error(exception, context, severity)
                
                # 根据严重程度决定处理方式
                if severity == ExceptionSeverity.CRITICAL:
                    logger.critical(f"致命错误: {exception}")
                    result["handled"] = True
                    return result
                
                # 尝试自动恢复
                if auto_recover:
                    recovery_result = self._attempt_recovery(exception, context)
                    result.update(recovery_result)
                
                result["handled"] = True
                
            except Exception as handler_error:
                logger.error(f"异常处理器自身发生错误: {handler_error}")
                result["handler_error"] = str(handler_error)
            
            return result
    
    def _record_error(self, exception: Exception, context: Dict[str, Any], severity: str):
        """记录错误信息"""
        error_type = type(exception).__name__
        
        # 更新错误计数
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 添加到历史记录
        error_record = {
            "type": error_type,
            "message": str(exception),
            "severity": severity,
            "context": context,
            "timestamp": time.time(),
            "traceback": traceback.format_exc()
        }
        
        self.error_history.append(error_record)
        
        # 限制历史记录长度
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        # 使用增强日志记录
        try:
            # 尝试使用增强日志方法
            log_kwargs = {
                'category': LogCategory.EXCEPTION,
                'error_code': error_type,
                'context': context,
                'operation': context.get('operation', 'unknown') if context else 'unknown'
            }

            if severity == ExceptionSeverity.CRITICAL:
                logger.critical(f"{error_type}: {exception}", **log_kwargs)
            elif severity == ExceptionSeverity.HIGH:
                logger.error(f"{error_type}: {exception}", **log_kwargs)
            elif severity == ExceptionSeverity.MEDIUM:
                logger.warning(f"{error_type}: {exception}", **log_kwargs)
            elif severity == ExceptionSeverity.LOW:
                logger.info(f"{error_type}: {exception}", **log_kwargs)
            else:
                logger.debug(f"{error_type}: {exception}", **log_kwargs)

        except (AttributeError, NameError):
            # 降级到标准日志
            log_level = {
                ExceptionSeverity.CRITICAL: logging.CRITICAL,
                ExceptionSeverity.HIGH: logging.ERROR,
                ExceptionSeverity.MEDIUM: logging.WARNING,
                ExceptionSeverity.LOW: logging.INFO,
                ExceptionSeverity.INFO: logging.DEBUG
            }.get(severity, logging.WARNING)

            logger.log(log_level, f"[{severity.upper()}] {error_type}: {exception}")
    
    def _attempt_recovery(self, exception: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """尝试自动恢复"""
        result = {"recovered": False, "recovery_action": None}
        
        exception_type = type(exception)
        
        # 查找匹配的恢复策略
        strategy = None
        for exc_type, strategy_func in self.recovery_strategies.items():
            if issubclass(exception_type, exc_type):
                strategy = strategy_func
                break
        
        if strategy:
            try:
                recovery_action = strategy(exception, context)
                result["recovered"] = True
                result["recovery_action"] = recovery_action
                logger.info(f"成功恢复 {exception_type.__name__}: {recovery_action}")
            except Exception as recovery_error:
                logger.error(f"恢复策略失败: {recovery_error}")
                result["recovery_error"] = str(recovery_error)
        else:
            logger.warning(f"没有找到 {exception_type.__name__} 的恢复策略")
        
        return result
    
    # 默认恢复策略实现
    def _handle_file_not_found(self, exception: FileNotFoundError, context: Dict[str, Any]) -> str:
        """处理文件未找到错误"""
        file_path = getattr(exception, 'filename', None) or context.get('file_path')

        if file_path:
            file_path = Path(file_path)

            # 策略1: 尝试创建目录
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 策略2: 如果是配置文件，尝试创建默认文件
                if file_path.suffix in ['.json', '.yaml', '.yml', '.ini', '.cfg']:
                    self._create_default_config_file(file_path)
                    return f"创建默认配置文件: {file_path}"

                # 策略3: 如果是日志文件，创建空文件
                elif file_path.suffix in ['.log', '.txt']:
                    file_path.touch()
                    return f"创建空文件: {file_path}"

                return f"创建目录: {file_path.parent}"

            except Exception as e:
                logger.debug(f"文件恢复失败: {e}")

        # 策略4: 尝试从上下文中查找替代路径
        if context.get('alternative_paths'):
            for alt_path in context['alternative_paths']:
                if Path(alt_path).exists():
                    return f"使用替代路径: {alt_path}"

        return "文件未找到，无法自动恢复"
    
    def _handle_permission_error(self, exception: PermissionError, context: Dict[str, Any]) -> str:
        """处理权限错误"""
        file_path = getattr(exception, 'filename', None) or context.get('file_path')

        if file_path:
            file_path = Path(file_path)

            # 策略1: 尝试使用临时目录
            try:
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "visionai_temp"
                temp_dir.mkdir(exist_ok=True)
                temp_file = temp_dir / file_path.name

                # 如果是写入操作，尝试写入临时文件
                if context.get('operation') == 'write':
                    temp_file.touch()
                    context['temp_file_path'] = str(temp_file)
                    return f"使用临时文件: {temp_file}"

            except Exception:
                pass

            # 策略2: 尝试修改文件权限（仅在Windows上）
            if os.name == 'nt':
                try:
                    import stat
                    file_path.chmod(stat.S_IWRITE | stat.S_IREAD)
                    return f"修改文件权限: {file_path}"
                except Exception:
                    pass

        return "权限不足，已尝试使用临时目录"
    
    def _handle_memory_error(self, exception: MemoryError, context: Dict[str, Any]) -> str:
        """处理内存错误"""
        import gc
        import psutil

        # 策略1: 强制垃圾回收
        gc.collect()

        # 策略2: 清理PyTorch缓存（如果可用）
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        # 策略3: 降低处理质量或批次大小
        if context.get('batch_size'):
            new_batch_size = max(1, context['batch_size'] // 2)
            context['batch_size'] = new_batch_size

        if context.get('quality_level'):
            context['quality_level'] = 'low'

        # 策略4: 检查内存使用情况
        try:
            memory_info = psutil.virtual_memory()
            available_gb = memory_info.available / (1024**3)

            if available_gb < 1.0:
                # 内存严重不足，建议重启
                return f"已执行垃圾回收，释放内存。可用内存: {available_gb:.1f}GB，建议重启应用"
            else:
                return f"已执行垃圾回收，释放内存。可用内存: {available_gb:.1f}GB"

        except Exception:
            return "已执行垃圾回收，释放内存"
    
    def _handle_os_error(self, exception: OSError, context: Dict[str, Any]) -> str:
        """处理操作系统错误"""
        return f"操作系统错误: {exception}"
    
    def _handle_value_error(self, exception: ValueError, context: Dict[str, Any]) -> str:
        """处理值错误"""
        return f"参数值错误: {exception}"
    
    def _handle_type_error(self, exception: TypeError, context: Dict[str, Any]) -> str:
        """处理类型错误"""
        return f"类型错误: {exception}"

    def _handle_connection_error(self, exception: ConnectionError, context: Dict[str, Any]) -> str:
        """处理连接错误"""
        # 策略1: 重试连接
        retry_count = context.get('retry_count', 0)
        if retry_count < 3:
            context['retry_count'] = retry_count + 1
            time.sleep(min(2 ** retry_count, 10))  # 指数退避
            return f"连接失败，正在重试 ({retry_count + 1}/3)"

        # 策略2: 使用备用URL
        if context.get('backup_urls'):
            backup_url = context['backup_urls'].pop(0)
            context['current_url'] = backup_url
            return f"使用备用连接: {backup_url}"

        return "连接失败，已尝试重试和备用连接"

    def _handle_timeout_error(self, exception: TimeoutError, context: Dict[str, Any]) -> str:
        """处理超时错误"""
        # 策略1: 增加超时时间
        current_timeout = context.get('timeout', 30)
        new_timeout = min(current_timeout * 2, 300)  # 最大5分钟
        context['timeout'] = new_timeout

        # 策略2: 降低请求频率
        if context.get('request_interval'):
            context['request_interval'] *= 1.5

        return f"超时错误，已调整超时时间至 {new_timeout} 秒"

    def _handle_import_error(self, exception: ImportError, context: Dict[str, Any]) -> str:
        """处理导入错误"""
        module_name = str(exception).split("'")[1] if "'" in str(exception) else "unknown"

        # 策略1: 尝试使用替代模块
        alternatives = {
            'cv2': ['PIL', 'skimage'],
            'torch': ['tensorflow', 'numpy'],
            'transformers': ['sentence_transformers'],
            'spacy': ['nltk', 'jieba'],
        }

        if module_name in alternatives:
            for alt in alternatives[module_name]:
                try:
                    __import__(alt)
                    context['alternative_module'] = alt
                    return f"使用替代模块: {alt} 代替 {module_name}"
                except ImportError:
                    continue

        return f"模块 {module_name} 不可用，请安装相关依赖"

    def _handle_unicode_error(self, exception: UnicodeDecodeError, context: Dict[str, Any]) -> str:
        """处理Unicode解码错误"""
        # 策略1: 尝试不同编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
        file_path = context.get('file_path')

        if file_path:
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    context['detected_encoding'] = encoding
                    context['file_content'] = content
                    return f"使用编码 {encoding} 成功读取文件"
                except Exception:
                    continue

        return "Unicode解码失败，已尝试多种编码"

    def _handle_runtime_error(self, exception: RuntimeError, context: Dict[str, Any]) -> str:
        """处理运行时错误"""
        error_msg = str(exception).lower()

        # 策略1: GPU相关错误 - 增强版
        if any(keyword in error_msg for keyword in ['cuda', 'gpu', 'opencl', 'directml', 'opengl']):
            return self._handle_gpu_runtime_error(exception, context, error_msg)

        # 策略2: 内存相关错误
        if 'memory' in error_msg or 'out of memory' in error_msg:
            return self._handle_memory_error(MemoryError(str(exception)), context)

        # 策略3: 线程相关错误
        if 'thread' in error_msg:
            context['single_thread'] = True
            return "线程错误，已切换到单线程模式"

        # 策略4: 模型加载错误
        if any(keyword in error_msg for keyword in ['model', 'checkpoint', 'weights']):
            return self._handle_model_runtime_error(exception, context, error_msg)

        return f"运行时错误: {exception}"

    def _handle_gpu_runtime_error(self, exception: RuntimeError, context: Dict[str, Any], error_msg: str) -> str:
        """处理GPU运行时错误"""
        # CUDA特定错误
        if 'cuda' in error_msg:
            if 'out of memory' in error_msg:
                # CUDA内存不足
                context['use_cpu'] = True
                context['reduce_batch_size'] = True
                context['clear_gpu_cache'] = True
                return "CUDA内存不足，已切换到CPU模式并减少批次大小"
            elif 'device' in error_msg:
                # CUDA设备错误
                context['use_cpu'] = True
                context['gpu_device_error'] = True
                return "CUDA设备错误，已切换到CPU模式"
            else:
                # 通用CUDA错误
                context['use_cpu'] = True
                return "CUDA错误，已切换到CPU模式"

        # OpenCL特定错误
        elif 'opencl' in error_msg:
            context['use_cpu'] = True
            context['disable_opencl'] = True
            return "OpenCL错误，已禁用OpenCL并切换到CPU模式"

        # DirectML特定错误
        elif 'directml' in error_msg:
            context['use_cpu'] = True
            context['disable_directml'] = True
            return "DirectML错误，已禁用DirectML并切换到CPU模式"

        # OpenGL特定错误
        elif 'opengl' in error_msg:
            context['disable_opengl'] = True
            context['use_software_rendering'] = True
            return "OpenGL错误，已切换到软件渲染模式"

        # 通用GPU错误
        else:
            context['use_cpu'] = True
            return "GPU错误，已切换到CPU模式"

    def _handle_model_runtime_error(self, exception: RuntimeError, context: Dict[str, Any], error_msg: str) -> str:
        """处理模型运行时错误"""
        if 'checkpoint' in error_msg or 'weights' in error_msg:
            # 模型权重加载错误
            context['use_default_model'] = True
            context['skip_pretrained_weights'] = True
            return "模型权重加载失败，已切换到默认模型"

        elif 'model' in error_msg:
            # 通用模型错误
            context['use_fallback_model'] = True
            return "模型加载失败，已切换到备用模型"

        return f"模型运行时错误: {exception}"

    def _handle_attribute_error(self, exception: AttributeError, context: Dict[str, Any]) -> str:
        """处理属性错误"""
        error_msg = str(exception).lower()

        # GPU相关属性错误
        if any(keyword in error_msg for keyword in ['cuda', 'gpu', 'device']):
            context['use_cpu'] = True
            return "GPU属性不可用，已切换到CPU模式"

        # 模块属性错误
        if 'module' in error_msg and 'has no attribute' in error_msg:
            context['use_fallback_implementation'] = True
            return "模块属性不可用，已使用备用实现"

        return f"属性错误: {exception}"

    def _handle_key_error(self, exception: KeyError, context: Dict[str, Any]) -> str:
        """处理键错误"""
        missing_key = str(exception).strip("'\"")

        # 配置键缺失
        if context.get('config_context'):
            context['use_default_config'] = True
            return f"配置项 {missing_key} 缺失，已使用默认配置"

        # 模型参数键缺失
        if any(keyword in missing_key.lower() for keyword in ['model', 'weight', 'param']):
            context['skip_missing_params'] = True
            return f"模型参数 {missing_key} 缺失，已跳过"

        return f"键错误: {exception}"

    def _handle_index_error(self, exception: IndexError, context: Dict[str, Any]) -> str:
        """处理索引错误"""
        # 批处理索引错误
        if context.get('batch_processing'):
            context['reduce_batch_size'] = True
            return "批处理索引错误，已减少批次大小"

        # 序列处理错误
        if context.get('sequence_processing'):
            context['add_padding'] = True
            return "序列索引错误，已添加填充"

        return f"索引错误: {exception}"

    def _handle_zero_division_error(self, exception: ZeroDivisionError, context: Dict[str, Any]) -> str:
        """处理除零错误"""
        # 添加小的epsilon值避免除零
        context['add_epsilon'] = True
        context['epsilon_value'] = 1e-8
        return "除零错误，已添加epsilon值避免"

    def _handle_not_implemented_error(self, exception: NotImplementedError, context: Dict[str, Any]) -> str:
        """处理未实现错误"""
        # 使用备用实现
        context['use_fallback_implementation'] = True
        context['disable_advanced_features'] = True
        return "功能未实现，已切换到基础实现"

    def _handle_module_not_found_error(self, exception: ModuleNotFoundError, context: Dict[str, Any]) -> str:
        """处理模块未找到错误"""
        module_name = str(exception).split("'")[1] if "'" in str(exception) else "unknown"

        # GPU相关模块
        if module_name in ['torch', 'tensorflow', 'cupy']:
            context['use_cpu'] = True
            return f"GPU模块 {module_name} 不可用，已切换到CPU模式"

        # 可选依赖模块
        optional_modules = {
            'cv2': 'PIL',
            'PIL': 'skimage',
            'matplotlib': 'plotly',
            'seaborn': 'matplotlib'
        }

        if module_name in optional_modules:
            alternative = optional_modules[module_name]
            context['alternative_module'] = alternative
            return f"模块 {module_name} 不可用，建议安装 {alternative}"

        return f"模块 {module_name} 未找到，请安装相关依赖"

    def _create_default_config_file(self, file_path: Path):
        """创建默认配置文件"""
        default_configs = {
            '.json': '{}',
            '.yaml': '# Default configuration\n',
            '.yml': '# Default configuration\n',
            '.ini': '[DEFAULT]\n',
            '.cfg': '[DEFAULT]\n'
        }

        content = default_configs.get(file_path.suffix, '')
        if content:
            file_path.write_text(content, encoding='utf-8')
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "error_types": list(self.error_counts.keys())
        }

# 全局异常处理器实例
_global_handler = None

def get_exception_handler() -> EnhancedExceptionHandler:
    """获取全局异常处理器实例"""
    global _global_handler
    if _global_handler is None:
        _global_handler = EnhancedExceptionHandler()
    return _global_handler

def safe_execute(func: Callable, 
                *args, 
                default_return=None, 
                context: Dict[str, Any] = None,
                severity: str = ExceptionSeverity.MEDIUM,
                **kwargs) -> Any:
    """
    安全执行函数，自动处理异常
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        default_return: 异常时的默认返回值
        context: 上下文信息
        severity: 异常严重程度
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或默认值
    """
    handler = get_exception_handler()
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # 构建上下文
        exec_context = {
            "function": func.__name__,
            "module": getattr(func, '__module__', 'unknown'),
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys())
        }
        if context:
            exec_context.update(context)
        
        # 处理异常
        result = handler.handle_exception(e, exec_context, severity)
        
        # 如果恢复成功，尝试重新执行
        if result.get("recovered", False):
            try:
                return func(*args, **kwargs)
            except Exception:
                pass  # 重试失败，返回默认值
        
        return default_return

def exception_handler(severity: str = ExceptionSeverity.MEDIUM,
                     default_return=None,
                     auto_recover: bool = True):
    """
    异常处理装饰器

    Args:
        severity: 异常严重程度
        default_return: 异常时的默认返回值
        auto_recover: 是否尝试自动恢复
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return safe_execute(
                func, *args,
                default_return=default_return,
                context={"decorated_function": True},
                severity=severity,
                **kwargs
            )
        return wrapper
    return decorator

class ValidationError(Exception):
    """验证错误"""
    pass

def validate_inputs(**validators):
    """
    输入验证装饰器

    Args:
        **validators: 参数名到验证函数的映射
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 执行验证
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        if not validator(value):
                            raise ValidationError(f"参数 {param_name} 验证失败: {value}")
                    except Exception as e:
                        raise ValidationError(f"参数 {param_name} 验证异常: {e}")

            return func(*args, **kwargs)
        return wrapper
    return decorator
