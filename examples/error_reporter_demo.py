#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误聚合报告器演示程序

该脚本演示了如何使用错误聚合报告器收集、分类和报告各种类型的错误和警告。
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# 导入错误报告器模块
try:
    from src.exporters.error_reporter import (
        ValidationResult,
        ErrorInfo,
        ErrorLevel,
        ErrorCategory,
        ValidationError,
        generate_error_report,
        combine_validation_results
    )
    
    # 模拟其他模块的错误类
    try:
        from src.utils.exceptions import (
            FileOperationError,
            ResourceError,
            TimelineError,
            ModelError,
            NetworkError
        )
    except ImportError:
        # 如果无法导入真实的异常类，使用模拟类
        print("注意: 无法导入实际异常类，使用模拟类代替")
        
        class ClipMasterError(Exception):
            def __init__(self, message, **kwargs):
                super().__init__(message)
                self.message = message
                self.details = kwargs.get('details', {})
        
        class FileOperationError(ClipMasterError):
            def __init__(self, message, file_path=None, operation=None, **kwargs):
                self.file_path = file_path
                self.operation = operation
                super().__init__(message, **kwargs)
        
        class ResourceError(ClipMasterError):
            def __init__(self, message, resource_type=None, **kwargs):
                self.resource_type = resource_type
                super().__init__(message, **kwargs)
        
        class TimelineError(ClipMasterError):
            pass
        
        class ModelError(ClipMasterError):
            def __init__(self, message, model_name=None, **kwargs):
                self.model_name = model_name
                super().__init__(message, **kwargs)
        
        class NetworkError(ClipMasterError):
            pass
    
    # 尝试导入日志模块
    try:
        from src.utils.log_handler import get_logger
        logger = get_logger("error_reporter_demo")
    except ImportError:
        # 如果无法导入日志模块，使用标准库日志
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("error_reporter_demo")

    # 模块导入成功
    IMPORT_FAILED = False
    
except ImportError as e:
    print(f"错误: 无法导入必要模块: {e}")
    print("请确保src目录在Python路径中，或在正确的目录中运行此脚本")
    IMPORT_FAILED = True

def simulate_validation_errors():
    """模拟验证过程中可能出现的各种错误"""
    result = ValidationResult()
    
    # 设置上下文信息
    result.set_context(
        file="project.xml",
        operation="export",
        timestamp=datetime.now().isoformat(),
        user="demo_user"
    )
    
    # 添加一些验证错误
    result.add_error(ValidationError("必填字段'title'缺失", code="MISSING_FIELD", 
                                  context={"field": "title", "section": "metadata"}))
    
    result.add_error({
        "code": "INVALID_FORMAT",
        "message": "时间格式无效：'2023/01/32'",
        "level": "ERROR",
        "category": ErrorCategory.VALIDATION,
        "location": "project.xml:45",
        "context": {"expected": "YYYY-MM-DD", "actual": "2023/01/32"}
    })
    
    # 添加资源错误
    try:
        raise FileOperationError("无法访问音频文件", file_path="assets/audio/bgm.mp3", operation="read")
    except Exception as e:
        result.add_error(e)
    
    # 添加时间轴错误
    try:
        raise TimelineError("时间轴片段重叠", details={"clip1": "00:01:20-00:01:35", "clip2": "00:01:30-00:01:45"})
    except Exception as e:
        result.add_error(e)
    
    # 添加一些警告
    result.add_error({
        "code": "TIMELINE_GAP",
        "message": "时间轴可能存在空隙",
        "level": "WARNING",
        "category": ErrorCategory.TIMELINE,
        "location": "timeline.xml:42",
        "context": {"gap_start": "00:02:15", "gap_end": "00:02:17"}
    })
    
    result.add_error({
        "code": "LOW_RESOLUTION",
        "message": "视频分辨率较低 (480p)",
        "level": "WARNING",
        "category": ErrorCategory.FORMAT,
        "context": {"resolution": "854x480", "recommended": "1920x1080"}
    })
    
    # 添加一些信息
    result.add_error({
        "code": "INFO_PROCESSING",
        "message": "正在处理字幕文件",
        "level": "INFO",
        "category": ErrorCategory.SYSTEM,
        "context": {"file": "subtitles.srt", "language": "zh-CN"}
    })
    
    return result

def simulate_export_errors():
    """模拟导出过程中可能出现的各种错误"""
    result = ValidationResult()
    
    # 设置上下文信息
    result.set_context(
        process="export",
        format="mp4",
        resolution="1080p",
        duration="00:15:30"
    )
    
    # 添加一些资源错误
    try:
        raise ResourceError("磁盘空间不足", resource_type="storage", 
                          details={"available": "250MB", "required": "1.2GB"})
    except Exception as e:
        result.add_error(e)
    
    # 添加网络错误
    try:
        raise NetworkError("上传到云存储失败", details={"url": "https://storage.example.com/upload", "status": 503})
    except Exception as e:
        result.add_error(e)
    
    # 添加模型错误
    try:
        raise ModelError("模型推理失败", model_name="text_enhancement", 
                        details={"error": "CUDA out of memory"})
    except Exception as e:
        result.add_error(e)
    
    # 添加一些警告
    result.add_error({
        "code": "SLOW_RENDERING",
        "message": "渲染速度较慢",
        "level": "WARNING",
        "category": ErrorCategory.SYSTEM,
        "context": {"current_fps": 15, "expected_fps": 30}
    })
    
    return result

def run_demonstration():
    """运行演示程序"""
    # 如果模块导入失败，则退出
    if IMPORT_FAILED:
        print("由于模块导入失败，无法运行演示")
        return
    
    print("\n===== 错误聚合报告器演示 =====\n")
    
    # 模拟验证错误
    print("1. 收集验证错误...")
    validation_result = simulate_validation_errors()
    
    # 模拟导出错误
    print("2. 收集导出错误...")
    export_result = simulate_export_errors()
    
    # 合并多个验证结果
    print("3. 合并多个验证结果...")
    combined_result = combine_validation_results(validation_result, export_result)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"临时目录: {temp_dir}")
    
    # 生成文本报告
    text_report_path = os.path.join(temp_dir, "error_report.txt")
    text_report = combined_result.generate_report("text", text_report_path)
    print(f"\n已保存文本报告到: {text_report_path}")
    
    # 生成JSON报告
    json_report_path = os.path.join(temp_dir, "error_report.json")
    combined_result.generate_report("json", json_report_path)
    print(f"已保存JSON报告到: {json_report_path}")
    
    # 生成HTML报告
    html_report_path = os.path.join(temp_dir, "error_report.html")
    combined_result.generate_report("html", html_report_path)
    print(f"已保存HTML报告到: {html_report_path}")
    
    # 显示摘要
    print("\n错误摘要:")
    summary = combined_result.get_error_summary()
    print(f"  总错误数: {summary['total_errors']}")
    print(f"  总警告数: {summary['total_warnings']}")
    print(f"  总信息数: {summary['total_infos']}")
    
    print("\n按类别:")
    for category, count in summary.get('by_category', {}).items():
        print(f"  {category}: {count}")
    
    print("\n按严重性:")
    for level, count in summary.get('by_level', {}).items():
        print(f"  {level}: {count}")
    
    # 使用便捷函数生成简单报告
    print("\n4. 使用便捷函数生成报告...")
    errors = [
        ValidationError("测试错误1", code="TEST_ERROR"),
        ValidationError("测试错误2", code="ANOTHER_ERROR"),
        "一个简单的字符串错误"
    ]
    
    simple_report_path = os.path.join(temp_dir, "simple_report.json")
    generate_error_report(errors, "json", simple_report_path, {"context": "simple_test"})
    print(f"已保存简单报告到: {simple_report_path}")
    
    # 显示文本报告示例
    print("\n=== 文本报告示例 ===")
    print(text_report[:500] + "...\n(报告太长已截断)")
    
    print(f"\n所有报告文件已保存到临时目录: {temp_dir}")
    print("\n演示完成!")

if __name__ == "__main__":
    run_demonstration() 