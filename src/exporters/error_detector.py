#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时错误检测器模块

提供在导出过程中实时检测和处理各类错误的功能，包括：
1. 检测导出流程中的各种错误（格式错误、引用错误、法律合规性等）
2. 集成项目中的各种验证器
3. 提供钩子机制，在导出流程的不同阶段进行错误检测
4. 汇总错误并生成报告
"""

import os
import sys
import time
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from pathlib import Path
from enum import Enum, auto
import functools

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 导入异常和错误报告相关模块
from src.utils.exceptions import ClipMasterError, ErrorCode, ValidationError
from src.exporters.error_reporter import (
    ErrorInfo, 
    ErrorLevel,
    ErrorCategory,
    ValidationResult,
    create_validation_result,
    generate_error_report
)

# 导入验证器
from src.exporters.timeline_validator import validate_timeline_continuity, validate_multi_track_timeline
from src.exporters.reference_checker import check_reference_integrity
from src.exporters.legal_validator import check_legal_metadata
from src.exporters.type_checker import validate_type

# 配置日志
logger = get_logger("error_detector")


class DetectionPhase(Enum):
    """检测阶段枚举"""
    PRE_EXPORT = auto()         # 导出前检查
    PRE_XML_GENERATE = auto()   # XML生成前检查
    POST_XML_GENERATE = auto()  # XML生成后检查 
    PRE_LEGAL_INJECT = auto()   # 法律声明注入前检查
    POST_LEGAL_INJECT = auto()  # 法律声明注入后检查
    PRE_FFMPEG_EXECUTE = auto() # FFmpeg执行前检查
    POST_FFMPEG_EXECUTE = auto()# FFmpeg执行后检查
    POST_EXPORT = auto()        # 导出后检查
    CUSTOM = auto()             # 自定义检查点


class ErrorDetector:
    """错误检测器类"""
    
    def __init__(self):
        """初始化错误检测器"""
        self.hooks = {}
        self.validation_result = create_validation_result()
        self.context = {}
        self.detection_enabled = True
        self._register_default_hooks()
    
    def _register_default_hooks(self):
        """注册默认钩子"""
        # 预生成XML检查
        self.register_hook(DetectionPhase.PRE_XML_GENERATE, self._check_template_integrity)
        
        # XML生成后检查
        self.register_hook(DetectionPhase.POST_XML_GENERATE, self._validate_xml_structure)
        
        # 法律声明注入前检查
        self.register_hook(DetectionPhase.PRE_LEGAL_INJECT, self._check_legal_requirements)
        
        # FFmpeg执行前检查
        self.register_hook(DetectionPhase.PRE_FFMPEG_EXECUTE, self._validate_ffmpeg_params)
        
        # FFmpeg执行后检查
        self.register_hook(DetectionPhase.POST_FFMPEG_EXECUTE, self._monitor_ffmpeg_output)
    
    def register_hook(self, phase: DetectionPhase, checker_func: Callable[[Dict[str, Any]], bool]) -> None:
        """
        注册检测钩子
        
        Args:
            phase: 检测阶段
            checker_func: 检测函数，接收上下文字典，返回布尔值（True表示检查通过）
        """
        if phase not in self.hooks:
            self.hooks[phase] = []
        
        self.hooks[phase].append(checker_func)
        logger.debug(f"已注册检测钩子: {checker_func.__name__} 到阶段 {phase.name}")
    
    def unregister_hook(self, phase: DetectionPhase, checker_func: Callable) -> bool:
        """
        取消注册检测钩子
        
        Args:
            phase: 检测阶段
            checker_func: 检测函数
            
        Returns:
            bool: 是否成功取消注册
        """
        if phase in self.hooks and checker_func in self.hooks[phase]:
            self.hooks[phase].remove(checker_func)
            logger.debug(f"已取消注册检测钩子: {checker_func.__name__} 从阶段 {phase.name}")
            return True
        return False
    
    def detect_errors(self, phase: DetectionPhase, context: Dict[str, Any] = None) -> bool:
        """
        执行指定阶段的错误检测
        
        Args:
            phase: 检测阶段
            context: 上下文信息
            
        Returns:
            bool: 是否全部检查通过
        """
        if not self.detection_enabled:
            logger.info("错误检测已禁用，跳过检测")
            return True
        
        # 更新上下文
        if context:
            self.context.update(context)
        
        logger.info(f"开始 {phase.name} 阶段的错误检测")
        
        # 检查是否有该阶段的钩子
        if phase not in self.hooks:
            logger.warning(f"没有找到 {phase.name} 阶段的检测钩子")
            return True
        
        # 执行所有检测钩子
        all_pass = True
        
        for checker in self.hooks[phase]:
            try:
                logger.debug(f"执行检测钩子: {checker.__name__}")
                check_pass = checker(self.context)
                
                if not check_pass:
                    logger.warning(f"检测钩子 {checker.__name__} 失败")
                    all_pass = False
                    
                    # 记录错误（如果检测器没有自己记录）
                    error_msg = f"{phase.name} 阶段的 {checker.__name__} 检测失败"
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="CHECK_FAILED",
                            message=error_msg,
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": phase.name, "checker": checker.__name__}
                        )
                    )
            except Exception as e:
                logger.error(f"检测钩子 {checker.__name__} 执行出错: {str(e)}")
                all_pass = False
                
                # 记录异常
                self.validation_result.add_error(e)
        
        if all_pass:
            logger.info(f"{phase.name} 阶段的错误检测全部通过")
        else:
            logger.warning(f"{phase.name} 阶段的错误检测存在失败项")
        
        return all_pass
    
    def enable_detection(self) -> None:
        """启用错误检测"""
        self.detection_enabled = True
        logger.info("错误检测已启用")
    
    def disable_detection(self) -> None:
        """禁用错误检测"""
        self.detection_enabled = False
        logger.info("错误检测已禁用")
    
    def reset(self) -> None:
        """重置错误检测器状态"""
        self.validation_result = create_validation_result()
        self.context = {}
        logger.info("错误检测器状态已重置")
    
    def get_validation_result(self) -> ValidationResult:
        """获取验证结果"""
        return self.validation_result
    
    def generate_report(self, format: str = "json", output_file: str = None) -> Union[str, Dict]:
        """
        生成错误报告
        
        Args:
            format: 报告格式 ("json", "text", "html")
            output_file: 输出文件路径
            
        Returns:
            Union[str, Dict]: 根据格式返回字符串或字典
        """
        # 完成验证结果
        self.validation_result.complete()
        
        # 生成报告
        return generate_error_report(
            [], 
            format=format, 
            output_file=output_file,
            context={"validation_result": self.validation_result}
        )
    
    def set_context(self, **kwargs) -> None:
        """设置上下文信息"""
        self.context.update(kwargs)
        self.validation_result.set_context(**kwargs)
    
    def add_error(self, error: Union[Exception, ErrorInfo, Dict, str]) -> None:
        """添加错误"""
        self.validation_result.add_error(error)
    
    # 默认检测钩子实现
    def _check_template_integrity(self, context: Dict[str, Any]) -> bool:
        """检查模板完整性"""
        template = context.get('template')
        
        if not template:
            logger.warning("无法检查模板完整性: 上下文中没有模板数据")
            return False
            
        try:
            # 检查模板是否为字典
            if not isinstance(template, dict):
                logger.error("模板必须是字典格式")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="INVALID_TEMPLATE_FORMAT",
                        message="模板必须是字典格式",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.VALIDATION,
                        context={"phase": "PRE_XML_GENERATE"}
                    )
                )
                return False
            
            # 检查必要的键
            required_keys = ['header', 'content', 'timeline']
            missing_keys = [key for key in required_keys if key not in template]
            
            if missing_keys:
                logger.error(f"模板缺少必要的键: {', '.join(missing_keys)}")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_TEMPLATE_KEYS",
                        message=f"模板缺少必要的键: {', '.join(missing_keys)}",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.VALIDATION,
                        context={"phase": "PRE_XML_GENERATE", "missing_keys": missing_keys}
                    )
                )
                return False
            
            # 检查header必要字段
            if 'header' in template:
                header = template['header']
                header_required_keys = ['title', 'author', 'version']
                header_missing_keys = [key for key in header_required_keys if key not in header]
                
                if header_missing_keys:
                    logger.warning(f"模板header缺少建议字段: {', '.join(header_missing_keys)}")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="MISSING_HEADER_FIELDS",
                            message=f"模板header缺少建议字段: {', '.join(header_missing_keys)}",
                            level=ErrorLevel.WARNING,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "PRE_XML_GENERATE", "missing_fields": header_missing_keys}
                        )
                    )
                    # 不返回失败，只是警告
            
            # 检查timeline完整性
            if 'timeline' in template:
                timeline = template['timeline']
                
                if not isinstance(timeline, list):
                    logger.error("模板timeline必须是列表格式")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="INVALID_TIMELINE_FORMAT",
                            message="模板timeline必须是列表格式",
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "PRE_XML_GENERATE"}
                        )
                    )
                    return False
                
                # 检查每个timeline项的必要字段
                for i, item in enumerate(timeline):
                    if not isinstance(item, dict):
                        logger.error(f"模板timeline[{i}]必须是字典格式")
                        self.validation_result.add_error(
                            ErrorInfo(
                                code="INVALID_TIMELINE_ITEM",
                                message=f"模板timeline[{i}]必须是字典格式",
                                level=ErrorLevel.ERROR,
                                category=ErrorCategory.VALIDATION,
                                context={"phase": "PRE_XML_GENERATE", "index": i}
                            )
                        )
                        return False
                    
                    # 检查必要字段
                    item_required_keys = ['start_time', 'end_time', 'type']
                    item_missing_keys = [key for key in item_required_keys if key not in item]
                    
                    if item_missing_keys:
                        logger.error(f"模板timeline[{i}]缺少必要字段: {', '.join(item_missing_keys)}")
                        self.validation_result.add_error(
                            ErrorInfo(
                                code="MISSING_TIMELINE_ITEM_FIELDS",
                                message=f"模板timeline[{i}]缺少必要字段: {', '.join(item_missing_keys)}",
                                level=ErrorLevel.ERROR,
                                category=ErrorCategory.VALIDATION,
                                context={"phase": "PRE_XML_GENERATE", "index": i, "missing_fields": item_missing_keys}
                            )
                        )
                        return False
            
            # 检查引用完整性
            if 'references' in template and template['references']:
                references = template['references']
                
                if not isinstance(references, list) and not isinstance(references, dict):
                    logger.error("模板references必须是列表或字典格式")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="INVALID_REFERENCES_FORMAT",
                            message="模板references必须是列表或字典格式",
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "PRE_XML_GENERATE"}
                        )
                    )
                    return False
                
                # 使用reference_checker检查引用
                if context.get('check_references', True):
                    check_reference_integrity(references, self.validation_result)
            
            logger.info("模板完整性检查通过")
            return True
            
        except Exception as e:
            logger.error(f"检查模板完整性时出错: {str(e)}")
            self.validation_result.add_error(e)
            return False
    
    def _validate_xml_structure(self, context: Dict[str, Any]) -> bool:
        """检查XML结构的正确性
        
        Args:
            context: 上下文信息，包含XML数据
            
        Returns:
            bool: 是否通过检查
        """
        xml_data = context.get('xml_data')
        
        if not xml_data:
            logger.warning("无法验证XML结构: 上下文中没有XML数据")
            return False
        
        try:
            # 检查XML基础结构
            if not isinstance(xml_data, str) or not xml_data.strip().startswith('<?xml'):
                logger.error("XML数据格式不正确")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="INVALID_XML_FORMAT",
                        message="XML数据格式不正确",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.FORMAT,
                        context={"phase": "POST_XML_GENERATE"}
                    )
                )
                return False
            
            # 使用内置XML解析器进行验证
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)
            
            # 检查必要的根元素
            if root.tag != 'meta_clip':
                logger.error("XML缺少必要的根元素: meta_clip")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_ROOT_ELEMENT",
                        message="XML缺少必要的根元素: meta_clip",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.VALIDATION,
                        context={"phase": "POST_XML_GENERATE", "expected_root": "meta_clip", "actual_root": root.tag}
                    )
                )
                return False
            
            # 检查必要的子元素
            required_elements = ['header', 'content', 'timeline']
            missing_elements = [elem for elem in required_elements if root.find(elem) is None]
            
            if missing_elements:
                logger.error(f"XML缺少必要的元素: {', '.join(missing_elements)}")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_REQUIRED_ELEMENTS",
                        message=f"XML缺少必要的元素: {', '.join(missing_elements)}",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.VALIDATION,
                        context={"phase": "POST_XML_GENERATE", "missing_elements": missing_elements}
                    )
                )
                return False
            
            # 检查时间轴连续性
            timeline_elem = root.find('timeline')
            if timeline_elem is not None:
                validate_timeline_continuity(timeline_elem, self.validation_result)
            
            logger.info("XML结构验证通过")
            return True
            
        except Exception as e:
            logger.error(f"XML结构验证出错: {str(e)}")
            self.validation_result.add_error(e)
            return False
    
    def _check_legal_requirements(self, context: Dict[str, Any]) -> bool:
        """检查法律声明要求
        
        Args:
            context: 上下文信息，包含法律元数据
            
        Returns:
            bool: 是否通过检查
        """
        xml_data = context.get('xml_data')
        legal_metadata = context.get('legal_metadata')
        
        if not xml_data and not legal_metadata:
            logger.warning("无法检查法律声明: 上下文中没有XML数据或法律元数据")
            return False
        
        try:
            # 如果有法律元数据，直接检查
            if legal_metadata:
                return check_legal_metadata(
                    legal_metadata, 
                    validation_result=self.validation_result,
                    context=context
                )
            
            # 否则从XML中提取法律元数据
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_data)
            
            # 获取header元素
            header = root.find('header')
            if not header:
                logger.error("XML缺少header元素，无法检查法律声明")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_HEADER",
                        message="XML缺少header元素，无法检查法律声明",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.LEGAL,
                        context={"phase": "PRE_LEGAL_INJECT"}
                    )
                )
                return False
            
            # 检查法律声明元素
            legal = header.find('legal')
            if not legal:
                logger.error("XML缺少legal元素")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_LEGAL_ELEMENT",
                        message="XML缺少legal元素",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.LEGAL,
                        context={"phase": "PRE_LEGAL_INJECT"}
                    )
                )
                return False
            
            # 提取法律元数据并检查
            extracted_metadata = {
                'copyright': legal.findtext('copyright'),
                'license': legal.findtext('license'),
                'attribution': legal.findtext('attribution'),
                'usage_rights': legal.findtext('usage_rights')
            }
            
            logger.info("从XML中提取法律元数据并检查")
            return check_legal_metadata(
                extracted_metadata, 
                validation_result=self.validation_result,
                context=context
            )
            
        except Exception as e:
            logger.error(f"检查法律声明时出错: {str(e)}")
            self.validation_result.add_error(e)
            return False
    
    def _validate_ffmpeg_params(self, context: Dict[str, Any]) -> bool:
        """验证FFmpeg参数
        
        Args:
            context: 上下文信息，包含FFmpeg参数
            
        Returns:
            bool: 是否通过验证
        """
        ffmpeg_params = context.get('ffmpeg_params')
        
        if not ffmpeg_params:
            logger.warning("无法验证FFmpeg参数: 上下文中没有FFmpeg参数")
            return False
        
        try:
            # 检查必要的参数
            required_params = ['-i', '-c:v', '-c:a']
            missing_params = []
            
            # 将列表转换为字符串以便检查参数
            if isinstance(ffmpeg_params, list):
                ffmpeg_cmd = ' '.join(str(param) for param in ffmpeg_params)
            else:
                ffmpeg_cmd = str(ffmpeg_params)
            
            for param in required_params:
                if param not in ffmpeg_cmd:
                    missing_params.append(param)
            
            if missing_params:
                logger.error(f"FFmpeg命令缺少必要参数: {', '.join(missing_params)}")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="MISSING_FFMPEG_PARAMS",
                        message=f"FFmpeg命令缺少必要参数: {', '.join(missing_params)}",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.VALIDATION,
                        context={"phase": "PRE_FFMPEG_EXECUTE", "missing_params": missing_params}
                    )
                )
                return False
            
            # 检查输出文件
            output_file = None
            if isinstance(ffmpeg_params, list):
                # 通常最后一个参数是输出文件
                output_file = ffmpeg_params[-1]
            elif 'output_file' in context:
                output_file = context['output_file']
            
            if output_file:
                # 检查输出目录是否存在
                import os
                output_dir = os.path.dirname(output_file)
                if output_dir and not os.path.exists(output_dir):
                    logger.error(f"输出目录不存在: {output_dir}")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="OUTPUT_DIR_NOT_FOUND",
                            message=f"输出目录不存在: {output_dir}",
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "PRE_FFMPEG_EXECUTE", "output_dir": output_dir}
                        )
                    )
                    return False
            
            # 检查是否有危险参数（例如覆盖确认）
            dangerous_params = ['-y', '-n']
            for param in dangerous_params:
                if param in ffmpeg_cmd:
                    logger.warning(f"FFmpeg命令包含潜在危险参数: {param}")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="DANGEROUS_FFMPEG_PARAM",
                            message=f"FFmpeg命令包含潜在危险参数: {param}",
                            level=ErrorLevel.WARNING,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "PRE_FFMPEG_EXECUTE", "dangerous_param": param}
                        )
                    )
                    # 不返回失败，只是警告
            
            logger.info("FFmpeg参数验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证FFmpeg参数时出错: {str(e)}")
            self.validation_result.add_error(e)
            return False
    
    def _monitor_ffmpeg_output(self, context: Dict[str, Any]) -> bool:
        """监控FFmpeg输出
        
        Args:
            context: 上下文信息，包含FFmpeg输出
            
        Returns:
            bool: 是否正常
        """
        ffmpeg_output = context.get('ffmpeg_output', '')
        return_code = context.get('return_code')
        
        if not ffmpeg_output and return_code is None:
            logger.warning("无法监控FFmpeg输出: 上下文中没有FFmpeg输出或返回代码")
            return False
        
        try:
            # 检查返回代码
            if return_code is not None and return_code != 0:
                logger.error(f"FFmpeg执行失败，返回代码: {return_code}")
                self.validation_result.add_error(
                    ErrorInfo(
                        code="FFMPEG_EXECUTION_FAILED",
                        message=f"FFmpeg执行失败，返回代码: {return_code}",
                        level=ErrorLevel.ERROR,
                        category=ErrorCategory.SYSTEM,
                        context={"phase": "POST_FFMPEG_EXECUTE", "return_code": return_code}
                    )
                )
                return False
            
            # 分析FFmpeg输出中的错误
            error_patterns = [
                "Error", "Invalid", "Cannot", "failed", "No such file", 
                "not found", "Unrecognized", "Unable to", "could not"
            ]
            
            # 将输出转换为字符串进行分析
            if not isinstance(ffmpeg_output, str):
                ffmpeg_output = str(ffmpeg_output)
            
            # 检查错误模式
            for pattern in error_patterns:
                if pattern.lower() in ffmpeg_output.lower():
                    # 提取相关行
                    lines = ffmpeg_output.split('\n')
                    error_lines = [line for line in lines if pattern.lower() in line.lower()]
                    error_message = '\n'.join(error_lines)
                    
                    logger.error(f"FFmpeg输出中检测到错误: {error_message}")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="FFMPEG_OUTPUT_ERROR",
                            message=f"FFmpeg输出中检测到错误: {error_message}",
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.SYSTEM,
                            context={"phase": "POST_FFMPEG_EXECUTE"}
                        )
                    )
                    return False
            
            # 检查输出文件是否存在
            output_file = context.get('output_file')
            if output_file:
                import os
                if not os.path.exists(output_file):
                    logger.error(f"FFmpeg执行后输出文件不存在: {output_file}")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="OUTPUT_FILE_NOT_FOUND",
                            message=f"FFmpeg执行后输出文件不存在: {output_file}",
                            level=ErrorLevel.ERROR,
                            category=ErrorCategory.SYSTEM,
                            context={"phase": "POST_FFMPEG_EXECUTE", "output_file": output_file}
                        )
                    )
                    return False
                
                # 检查文件大小（如果太小可能有问题）
                file_size = os.path.getsize(output_file)
                if file_size < 1024:  # 小于1KB
                    logger.warning(f"FFmpeg输出文件过小: {file_size} 字节")
                    self.validation_result.add_error(
                        ErrorInfo(
                            code="OUTPUT_FILE_TOO_SMALL",
                            message=f"FFmpeg输出文件过小: {file_size} 字节",
                            level=ErrorLevel.WARNING,
                            category=ErrorCategory.VALIDATION,
                            context={"phase": "POST_FFMPEG_EXECUTE", "file_size": file_size}
                        )
                    )
                    # 不返回失败，只是警告
            
            logger.info("FFmpeg输出监控未发现问题")
            return True
            
        except Exception as e:
            logger.error(f"监控FFmpeg输出时出错: {str(e)}")
            self.validation_result.add_error(e)
            return False
    
    def start_realtime_monitoring(self, context: Dict[str, Any] = None) -> None:
        """启动实时监控
        
        在导出过程中实时监控错误，提高检测及时性
        
        Args:
            context: 上下文信息
        """
        context = context or {}
        self.context.update(context)
        self.context["monitoring_active"] = True
        self.context["monitoring_start_time"] = time.time()
        self.context["monitoring_stats"] = {
            "checks_performed": 0,
            "errors_detected": 0,
            "warnings_detected": 0
        }
        
        logger.info("已启动实时错误监控")
    
    def stop_realtime_monitoring(self) -> Dict[str, Any]:
        """停止实时监控
        
        Returns:
            Dict[str, Any]: 监控统计信息
        """
        if self.context.get("monitoring_active"):
            self.context["monitoring_active"] = False
            self.context["monitoring_end_time"] = time.time()
            self.context["monitoring_duration"] = self.context["monitoring_end_time"] - self.context["monitoring_start_time"]
            
            logger.info("已停止实时错误监控")
            logger.info(f"监控统计: 执行了 {self.context['monitoring_stats']['checks_performed']} 次检查, "
                      f"检测到 {self.context['monitoring_stats']['errors_detected']} 个错误, "
                      f"{self.context['monitoring_stats']['warnings_detected']} 个警告")
            
            return self.get_monitoring_stats()
        return {}
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计信息
        
        Returns:
            Dict[str, Any]: 监控统计信息
        """
        return {
            "active": self.context.get("monitoring_active", False),
            "start_time": self.context.get("monitoring_start_time"),
            "end_time": self.context.get("monitoring_end_time"),
            "duration": self.context.get("monitoring_duration"),
            "stats": self.context.get("monitoring_stats", {})
        }
    
    def classify_error(self, error: Exception) -> Dict[str, Any]:
        """分类错误
        
        使用异常分类系统对错误进行分类
        
        Args:
            error: 异常对象
            
        Returns:
            Dict[str, Any]: 分类结果
        """
        try:
            from src.utils.exception_classifier import get_exception_classifier
            classifier = get_exception_classifier()
            
            # 分类异常
            classification = classifier.classify(error, self.context)
            
            # 转换为字典
            return classification.to_dict()
        except ImportError:
            logger.warning("无法导入异常分类系统，使用简单分类")
            
            # 简单分类
            severity = "ERROR"
            if isinstance(error, Warning):
                severity = "WARNING"
            
            return {
                "severity": severity,
                "source": "UNKNOWN",
                "impact": "UNKNOWN",
                "recovery": "UNKNOWN",
                "description": str(error),
                "recommended_action": "检查错误详情"
            }
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """分析错误模式
        
        分析已记录的错误，寻找模式和共性问题
        
        Returns:
            Dict[str, Any]: 错误模式分析结果
        """
        result = {
            "common_error_codes": {},
            "error_hotspots": {},
            "recovery_success_rate": 0,
            "most_critical_errors": []
        }
        
        # 获取验证结果
        validation_result = self.get_validation_result()
        
        # 统计错误代码
        error_codes = {}
        for error in validation_result.errors:
            code = error.code
            error_codes[code] = error_codes.get(code, 0) + 1
        
        # 排序获取最常见的错误代码
        result["common_error_codes"] = dict(sorted(
            error_codes.items(), 
            key=lambda item: item[1], 
            reverse=True
        )[:5])
        
        # 识别错误热点
        error_locations = {}
        for error in validation_result.errors:
            if hasattr(error, "location") and error.location:
                location = error.location
                error_locations[location] = error_locations.get(location, 0) + 1
        
        # 排序获取错误热点
        result["error_hotspots"] = dict(sorted(
            error_locations.items(), 
            key=lambda item: item[1], 
            reverse=True
        )[:3])
        
        # 获取最严重的错误
        critical_errors = [
            error for error in validation_result.errors 
            if error.level == ErrorLevel.CRITICAL or error.level == ErrorLevel.ERROR
        ]
        result["most_critical_errors"] = [
            {"code": error.code, "message": error.message}
            for error in sorted(critical_errors, key=lambda e: e.level.value)[:3]
        ]
        
        # 如果有全局错误处理器，获取恢复成功率
        try:
            from src.core.error_handler import get_error_handler
            error_handler = get_error_handler()
            
            if hasattr(error_handler, "error_stats"):
                total = error_handler.error_stats.get("total_errors", 0)
                recovered = error_handler.error_stats.get("recovered_errors", 0)
                
                if total > 0:
                    result["recovery_success_rate"] = round(recovered / total * 100, 2)
        except ImportError:
            pass
        
        return result


# 单例模式
_error_detector = None

def get_error_detector() -> ErrorDetector:
    """获取错误检测器单例
    
    Returns:
        ErrorDetector: 错误检测器实例
    """
    # 使用单例模式确保只有一个错误检测器实例
    global _error_detector
    if "_error_detector" not in globals() or _error_detector is None:
        _error_detector = ErrorDetector()
    return _error_detector


def detect_errors(phase: DetectionPhase, context: Dict[str, Any] = None) -> bool:
    """检测指定阶段的错误
    
    Args:
        phase: 检测阶段
        context: 上下文信息
        
    Returns:
        bool: 是否全部检查通过
    """
    detector = get_error_detector()
    return detector.detect_errors(phase, context)


def check_template_integrity(context: Dict[str, Any]) -> bool:
    """检查模板完整性
    
    Args:
        context: 上下文信息
    
    Returns:
        bool: 是否通过检查
    """
    detector = get_error_detector()
    return detector._check_template_integrity(context)


def validate_legal_nodes(context: Dict[str, Any]) -> bool:
    """验证法律节点
    
    Args:
        context: 上下文信息
    
    Returns:
        bool: 是否通过验证
    """
    detector = get_error_detector()
    return detector._check_legal_requirements(context)


def monitor_ffmpeg_output(context: Dict[str, Any]) -> bool:
    """监控FFmpeg输出
    
    Args:
        context: 上下文信息
    
    Returns:
        bool: 是否正常
    """
    detector = get_error_detector()
    return detector._monitor_ffmpeg_output(context)


def with_error_detection(phase: DetectionPhase):
    """错误检测装饰器
    
    Args:
        phase: 检测阶段
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取错误检测器
            detector = get_error_detector()
            
            # 构建上下文
            context = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs,
                "phase": phase.name
            }
            
            # 执行前检测
            detector.detect_errors(phase, context)
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 更新上下文
                context["result"] = result
                
                # 根据函数返回值更新检测上下文
                if isinstance(result, dict):
                    context.update(result)
                elif hasattr(result, '__dict__'):
                    context.update(result.__dict__)
                
                # 执行后根据阶段再次检测
                post_phase_map = {
                    DetectionPhase.PRE_XML_GENERATE: DetectionPhase.POST_XML_GENERATE,
                    DetectionPhase.PRE_LEGAL_INJECT: DetectionPhase.POST_LEGAL_INJECT,
                    DetectionPhase.PRE_FFMPEG_EXECUTE: DetectionPhase.POST_FFMPEG_EXECUTE,
                    DetectionPhase.PRE_EXPORT: DetectionPhase.POST_EXPORT
                }
                
                if phase in post_phase_map:
                    post_phase = post_phase_map[phase]
                    logger.debug(f"执行后检测阶段: {post_phase.name}")
                    detector.detect_errors(post_phase, context)
                
                return result
                
            except Exception as e:
                # 记录异常
                detector.add_error(e)
                
                # 获取验证结果
                validation_result = detector.get_validation_result()
                
                # 根据严重程度决定是否重新抛出异常
                if validation_result.has_critical:
                    logger.critical(f"检测到致命错误，无法继续: {str(e)}")
                    raise
                
                logger.error(f"检测到错误，但非致命: {str(e)}")
                
                # 返回默认值
                return None
        
        return wrapper
    
    return decorator 

# 集成异常分类系统
def integrate_exception_classification():
    """集成异常分类系统，增强错误检测和报告能力"""
    try:
        from src.utils.exception_classifier import get_exception_classifier, SeverityLevel, ErrorSource
        
        # 获取异常分类器
        classifier = get_exception_classifier()
        
        # 获取错误检测器
        detector = get_error_detector()
        
        # 添加自定义分类规则，用于更好地处理导出相关错误
        def is_xml_error(exception, context):
            """检查是否为XML相关错误"""
            msg = str(exception).lower()
            return ('xml' in msg and ('parse' in msg or 'invalid' in msg or 'syntax' in msg)) or \
                   isinstance(exception, (ET.ParseError if 'ET' in globals() else Exception))
        
        def is_ffmpeg_error(exception, context):
            """检查是否为FFmpeg相关错误"""
            msg = str(exception).lower()
            return 'ffmpeg' in msg or \
                   (context and context.get('phase') in 
                    ['PRE_FFMPEG_EXECUTE', 'POST_FFMPEG_EXECUTE'])
        
        def is_legal_error(exception, context):
            """检查是否为法律声明相关错误"""
            msg = str(exception).lower()
            return 'legal' in msg or 'copyright' in msg or 'license' in msg or \
                   (context and context.get('phase') in 
                    ['PRE_LEGAL_INJECT', 'POST_LEGAL_INJECT'])
        
        # 添加自定义规则
        from src.utils.exception_classifier import ErrorClassification, ImpactScope, RecoveryType
        
        classifier.add_custom_rule(
            is_xml_error,
            ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.DATA,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="XML处理错误",
                recommended_action="检查XML模板格式是否正确"
            )
        )
        
        classifier.add_custom_rule(
            is_ffmpeg_error,
            ErrorClassification(
                severity=SeverityLevel.ERROR,
                source=ErrorSource.SYSTEM,
                impact=ImpactScope.FEATURE,
                recovery=RecoveryType.USER_ASSISTED,
                description="FFmpeg执行错误",
                recommended_action="检查FFmpeg参数和输入输出文件"
            )
        )
        
        classifier.add_custom_rule(
            is_legal_error,
            ErrorClassification(
                severity=SeverityLevel.WARNING,
                source=ErrorSource.DATA,
                impact=ImpactScope.DATA,
                recovery=RecoveryType.USER_ASSISTED,
                description="法律声明错误",
                recommended_action="检查法律元数据是否完整"
            )
        )
        
        logger.info("已集成异常分类系统")
        
    except ImportError:
        logger.warning("无法导入异常分类系统，错误分类功能将受限")


# 在模块导入时集成异常分类系统
try:
    integrate_exception_classification()
except Exception as e:
    logger.warning(f"集成异常分类系统时出错: {e}") 