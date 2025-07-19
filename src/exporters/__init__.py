#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 导出器模块

提供各种导出格式和选项的导出功能。
"""

# 导入法律审计日志功能
from src.exporters.legal_logger import (
    LegalAuditLogger,
    log_legal_operation,
    log_legal_operation_func,
    get_legal_logger
)

# 导入流式处理管道功能
from src.exporters.stream_pipe import (
    ZeroCopyPipeline,
    StreamingPipeline,
    Processor,
    FunctionProcessor,
    TransformProcessor,
    FilterProcessor,
    CompositeProcessor,
    VideoProcessor,
    AudioProcessor,
    ProcessingMode,
    ProcessingStage,
    PipelineContext,
    create_pipeline,
    create_streaming_pipeline,
    create_processor
)

# 导入FFmpeg零拷贝集成功能
from src.exporters.ffmpeg_zerocopy import (
    ZeroCopyFFmpegPipeline,
    StreamingFFmpegPipeline,
    FFmpegSettings,
    FFmpegCodec,
    FFmpegPreset,
    FFmpegProcessor,
    FFmpegError,
    FFmpegExecutor,
    FFmpegCommandBuilder,
    VideoCutProcessor,
    VideoConcatProcessor,
    create_ffmpeg_pipeline,
    create_streaming_ffmpeg_pipeline,
    cut_video,
    concat_videos
)

# 导入元数据驱动剪辑功能
from src.exporters.metaclip_engine import (
    MetaClip,
    MetaClipEngine,
    MetaClipProcessor,
    MetaClipError,
    OperationType,
    CodecMode,
    SliceProcessor,
    ConcatProcessor,
    generate_metadata_clip,
    get_metaclip_engine
)

# 导入简化版法律审计日志功能
from src.exporters.simple_legal_logger import (
    log_legal_operation as simple_log_legal_operation,
    log_operation,
    with_legal_audit,
    log_legal_injection,
    log_disclaimer_addition
)

# 导入用户自定义法律文本处理功能
from src.exporters.custom_legal import (
    apply_custom_rules,
    load_user_config,
    save_user_config,
    create_user_template,
    apply_custom_legal,
    apply_direct,
    apply_to_legal_injector,
    get_user_variables
)

# 导入法律声明更新功能
from src.exporters.legal_updater import (
    legal_watcher,
    check_legal_updates,
    download_new_templates,
    LegalWatcher
)

# 导入数据类型校验功能
from src.exporters.type_checker import (
    validate_type,
    check_data_types,
    validate_numeric_ranges,
    validate_xml_element_types,
    get_common_type_rules,
    TypeError,
    ValidationError
)

# 导入引用完整性检查功能
from src.exporters.reference_checker import (
    check_asset_references,
    check_id_uniqueness,
    check_orphaned_assets,
    check_reference_integrity,
    check_reference_cycles,
    fix_missing_references,
    remove_orphaned_assets,
    validate_references,
    ReferenceError
)

# 导入时间轴连续性验证功能
from src.exporters.timeline_validator import (
    validate_timeline_continuity,
    validate_timeline_continuity_simple,
    validate_multi_track_timeline,
    check_timeline_gaps,
    check_scene_transition_consistency,
    validate_clip_duration,
    validate_timeline_from_file,
    TimelineError,
    TimelineConsistencyError,
    TimelineOverlapError
)

# 导入法律声明验证功能
from .legal_validator import (
    check_legal_metadata,
    validate_xml_legal_compliance,
    inject_missing_legal_elements,
    validate_srt_legal_notice,
    LegalComplianceError
)

# 导入版本兼容性适配功能
from .version_compat import (
    get_xml_version,
    is_version_compatible,
    backward_compatibility_fix,
    upgrade_version,
    process_xml_file,
    batch_process_directory,
    compare_versions,
    find_conversion_path,
    VersionError
)

# 导入错误聚合报告器功能
from .error_reporter import (
    ValidationResult,
    ErrorInfo,
    ErrorLevel,
    ErrorCategory,
    ValidationError,
    generate_error_report,
    combine_validation_results,
    create_validation_result
)

# 导入硬件检测器功能
from .hw_detector import (
    AccelerationType,
    detect_zero_copy_acceleration,
    check_nvidia_support,
    check_intel_qsv,
    get_cuda_device_info,
    get_detected_acceleration,
    print_acceleration_report
)

# 导入回退引擎功能
from .fallback_engine import (
    FallbackEngine,
    ProcessingMode,
    ZeroCopyUnavailableError,
    safe_zero_copy,
    get_fallback_engine,
    zero_copy_process,
    traditional_process,
    get_memory_usage
)

# 导入资源清理功能
from .resource_cleaner import (
    get_resource_cleaner,
    emergency_cleanup,
    resource_cleanup_context,
    CleanupPriority
)

# 导入断点续导出功能
from .resume_export import (
    ExportResumer,
    get_export_resumer,
    ResumableExporter,
    make_resumable,
    resumable_export_context
)

# 导入错误监控看板功能
from .error_dashboard import (
    LiveErrorMonitor,
    get_error_monitor
)

# 导入版本元数据提取功能
from .version_detector import (
    detect_version,
    detect_jianying_version,
    extract_version_from_xml,
    extract_version_from_json,
    detect_jianying_version_from_string,
    get_format_display_name
)

# 导入属性降级处理器模块
from .attribute_downgrader import (
    downgrade_attributes,
    process_xml_file,
    batch_downgrade_directory,
    get_supported_versions,
    compare_versions,
    normalize_version
)

# 导入动态模板引擎模块
from .dynamic_template import (
    create_template_engine,
    VersionAwareTemplate
)

# 导入版本降级兼容性功能
from src.exporters.node_compat import (
    add_required_nodes,
    remove_unsupported_nodes,
    verify_required_nodes,
    validate_version_compatibility,
    get_version_specification
)

from src.exporters.version_updater import VersionWatcher

from src.exporters.version_fallback import (
    safe_export,
    version_specific_export,
    generate_base_template,
    VersionCompatibilityError
)

# 导入日志模块组件
from src.exporters.log_schema import (
    EXPORT_LOG_SCHEMA,
    validate_log,
    mask_sensitive_data,
    create_sample_log
)

from src.exporters.structured_logger import (
    StructuredLogger,
    get_structured_logger
)

from src.exporters.log_analyzer import LogAnalyzer
from src.exporters.log_visualizer import LogVisualizer
from src.exporters.log_integration import (
    log_operation,
    log_video_process,
    log_error,
    log_model_usage,
    LoggingManager,
    get_logging_manager
)

# 导入实时日志系统组件
from src.exporters.log_writer import (
    RealtimeLogger,
    AsyncLogWriter,
    get_realtime_logger
)

from src.exporters.log_integration_realtime import (
    RealtimeLogIntegrator,
    realtime_log,
    log_realtime,
    get_log_integrator
)

from .log_path import get_log_directory, get_log_file_path, clean_old_logs
from .log_rotator import LogRotator, LogRotationManager, get_log_rotation_manager, setup_standard_log_rotation
from .log_lifecycle import LogLifecycleManager, get_log_lifecycle_manager, init_log_lifecycle, shutdown_log_lifecycle
from .log_fingerprint import generate_log_fingerprint, fingerprint_log_file, process_active_logs
from .log_query import LogSearcher, get_log_searcher, search_logs, get_log_statistics
from .log_dashboard import (
    LiveLogMonitor, 
    get_live_monitor, 
    get_dashboard_data, 
    add_dashboard_alert,
    AlertLevel,
    ChartType
)

# 添加对copyright_embedder的导入
from .copyright_embedder import CopyrightEngine

# 导出模块
__all__ = [
    # 法律审计日志功能
    'LegalAuditLogger',
    'log_legal_operation',
    'log_legal_operation_func',
    'get_legal_logger',
    
    # 流式处理管道功能
    'ZeroCopyPipeline',
    'StreamingPipeline',
    'Processor',
    'FunctionProcessor',
    'TransformProcessor',
    'FilterProcessor',
    'CompositeProcessor',
    'VideoProcessor',
    'AudioProcessor',
    'ProcessingMode',
    'ProcessingStage',
    'PipelineContext',
    'create_pipeline',
    'create_streaming_pipeline',
    'create_processor',
    
    # FFmpeg零拷贝集成功能
    'ZeroCopyFFmpegPipeline',
    'StreamingFFmpegPipeline',
    'FFmpegSettings',
    'FFmpegCodec',
    'FFmpegPreset',
    'FFmpegProcessor',
    'FFmpegError',
    'FFmpegExecutor',
    'FFmpegCommandBuilder',
    'VideoCutProcessor',
    'VideoConcatProcessor',
    'create_ffmpeg_pipeline',
    'create_streaming_ffmpeg_pipeline',
    'cut_video',
    'concat_videos',
    
    # 元数据驱动剪辑功能
    'MetaClip',
    'MetaClipEngine',
    'MetaClipProcessor',
    'MetaClipError',
    'OperationType',
    'CodecMode',
    'SliceProcessor',
    'ConcatProcessor',
    'generate_metadata_clip',
    'get_metaclip_engine',
    
    # 简化版法律审计日志功能
    'simple_log_legal_operation',
    'log_operation',
    'with_legal_audit',
    'log_legal_injection',
    'log_disclaimer_addition',
    
    # 用户自定义法律文本处理功能
    'apply_custom_rules',
    'load_user_config',
    'save_user_config',
    'create_user_template',
    'apply_custom_legal',
    'apply_direct',
    'apply_to_legal_injector',
    'get_user_variables',
    
    # 法律声明更新功能
    'legal_watcher',
    'check_legal_updates',
    'download_new_templates',
    'LegalWatcher',
    
    # 数据类型校验功能
    'validate_type',
    'check_data_types',
    'validate_numeric_ranges',
    'validate_xml_element_types',
    'get_common_type_rules',
    'TypeError',
    'ValidationError',
    
    # 引用完整性检查功能
    'check_asset_references',
    'check_id_uniqueness',
    'check_orphaned_assets',
    'check_reference_integrity',
    'check_reference_cycles',
    'fix_missing_references',
    'remove_orphaned_assets',
    'validate_references',
    'ReferenceError',
    
    # 时间轴连续性验证功能
    'validate_timeline_continuity',
    'validate_timeline_continuity_simple',
    'validate_multi_track_timeline',
    'check_timeline_gaps',
    'check_scene_transition_consistency',
    'validate_clip_duration',
    'validate_timeline_from_file',
    'TimelineError',
    'TimelineConsistencyError',
    'TimelineOverlapError',
    
    # 法律声明验证功能
    'check_legal_metadata',
    'validate_xml_legal_compliance',
    'inject_missing_legal_elements',
    'validate_srt_legal_notice',
    'LegalComplianceError',
    
    # 版本兼容性适配功能
    'get_xml_version',
    'is_version_compatible',
    'backward_compatibility_fix',
    'upgrade_version',
    'process_xml_file',
    'batch_process_directory',
    'compare_versions',
    'find_conversion_path',
    'VersionError',
    
    # 错误聚合报告器功能
    'ValidationResult',
    'ErrorInfo',
    'ErrorLevel',
    'ErrorCategory',
    'ValidationError',
    'generate_error_report',
    'combine_validation_results',
    'create_validation_result',
    
    # 硬件检测器功能
    'AccelerationType',
    'detect_zero_copy_acceleration',
    'check_nvidia_support',
    'check_intel_qsv',
    'get_cuda_device_info',
    'get_detected_acceleration',
    'print_acceleration_report',
    
    # 回退引擎功能
    'FallbackEngine',
    'ProcessingMode',
    'ZeroCopyUnavailableError',
    'safe_zero_copy',
    'get_fallback_engine',
    'zero_copy_process',
    'traditional_process',
    'get_memory_usage',
    
    # 资源清理功能
    'get_resource_cleaner',
    'emergency_cleanup',
    'resource_cleanup_context',
    'CleanupPriority',
    
    # 断点续导出功能
    'ExportResumer',
    'get_export_resumer',
    'ResumableExporter',
    'make_resumable',
    'resumable_export_context',
    
    # 错误监控看板功能
    'LiveErrorMonitor',
    'get_error_monitor',
    
    # 版本元数据提取功能
    'detect_version',
    'detect_jianying_version',
    'extract_version_from_xml',
    'extract_version_from_json',
    'detect_jianying_version_from_string',
    'get_format_display_name',
    
    # 属性降级处理器
    'downgrade_attributes',
    'process_xml_file',
    'batch_downgrade_directory',
    'get_supported_versions',
    'compare_versions',
    'normalize_version',
    
    # 动态模板引擎
    'create_template_engine',
    'VersionAwareTemplate',

    # 版本降级兼容性功能
    'add_required_nodes',
    'remove_unsupported_nodes',
    'verify_required_nodes',
    'validate_version_compatibility',
    'get_version_specification',
    'VersionWatcher',
    'safe_export',
    'version_specific_export',
    'generate_base_template',
    'VersionCompatibilityError',

    # 结构化日志功能
    'EXPORT_LOG_SCHEMA',
    'validate_log',
    'mask_sensitive_data',
    'create_sample_log',
    'StructuredLogger',
    'get_structured_logger',
    'LogAnalyzer',
    'LogVisualizer',
    'log_operation',
    'log_video_process',
    'log_error',
    'log_model_usage',
    'LoggingManager',
    'get_logging_manager',
    
    # 实时日志功能
    'RealtimeLogger',
    'AsyncLogWriter',
    'get_realtime_logger',
    'RealtimeLogIntegrator',
    'realtime_log',
    'log_realtime',
    'get_log_integrator',

    # 日志管理功能
    'get_log_directory', 'get_log_file_path', 'clean_old_logs',
    'LogRotator', 'LogRotationManager', 'get_log_rotation_manager', 'setup_standard_log_rotation',
    'LogLifecycleManager', 'get_log_lifecycle_manager', 'init_log_lifecycle', 'shutdown_log_lifecycle',
    'generate_log_fingerprint', 'fingerprint_log_file', 'process_active_logs',
    'LogSearcher', 'get_log_searcher', 'search_logs', 'get_log_statistics',
    
    # 实时日志监控看板
    'LiveLogMonitor', 'get_live_monitor', 'get_dashboard_data', 'add_dashboard_alert',
    'AlertLevel', 'ChartType',

    # 版权嵌入功能
    'CopyrightEngine'
] 