"""
API模式定义

定义VisionAI-ClipsMaster的API请求和响应数据结构
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class QuantizationLevel(str, Enum):
    """量化等级枚举"""
    Q2_K = "Q2_K"  # 最低内存占用(~2GB)，质量较低
    Q4_K_M = "Q4_K_M"  # 平衡内存占用(~4GB)和质量
    Q5_K_M = "Q5_K_M"  # 较高质量，内存占用~5GB
    Q8_0 = "Q8_0"  # 最高质量，内存占用最大(~7GB)

class Language(str, Enum):
    """支持的语言枚举"""
    CHINESE = "zh"
    ENGLISH = "en"

class ExportFormat(str, Enum):
    """导出格式枚举"""
    VIDEO = "video"  # 仅视频文件
    PROJECT = "project"  # 仅项目文件 
    BOTH = "both"  # 视频和项目文件

class ClipRequest(BaseModel):
    """
    视频剪辑生成请求体
    """
    video_path: str = Field(..., description="视频文件路径，支持相对路径或绝对路径")
    srt_path: str = Field(..., description="字幕文件路径，支持SRT或ASS格式")
    quant_level: QuantizationLevel = Field(QuantizationLevel.Q4_K_M, description="量化等级，影响内存占用和生成质量")
    lang: Language = Field(Language.CHINESE, description="处理语言，zh或en，英文模型仅配置不下载，下载后可无缝激活")
    export_format: ExportFormat = Field(ExportFormat.BOTH, description="导出格式：视频、项目文件或两者")
    max_duration: Optional[float] = Field(None, description="最大输出时长(秒)，None表示不限制")
    narrative_focus: Optional[List[str]] = Field(None, description="叙事重点关键词列表，指导模型关注特定内容")
    temperature: float = Field(0.7, description="生成温度，控制创意度(0.1-1.0)")
    preserve_segments: Optional[List[Dict[str, float]]] = Field(None, description="必须保留的片段时间点列表，格式[{start: 秒, end: 秒}]")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0.1 or v > 1.0:
            raise ValueError('temperature必须在0.1到1.0之间')
        return v

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"

class ClipResponse(BaseModel):
    """
    视频剪辑生成响应体
    """
    task_id: str = Field(..., description="任务ID，可用于后续查询状态")
    project_path: Optional[str] = Field(None, description="生成的工程文件路径")
    video_path: Optional[str] = Field(None, description="生成的视频文件路径")
    render_time: float = Field(..., description="渲染耗时（秒）")
    status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[float] = Field(None, description="处理进度(0-1)，仅适用于processing状态")
    message: Optional[str] = Field(None, description="详细信息或错误描述")
    metrics: Optional[Dict[str, Any]] = Field(None, description="性能和质量指标")

class StatusRequest(BaseModel):
    """
    任务状态查询请求体
    """
    task_id: str = Field(..., description="任务ID")

class BatchClipRequest(BaseModel):
    """
    批量视频剪辑请求
    """
    clips: List[ClipRequest] = Field(..., description="剪辑请求列表")
    parallel: int = Field(1, description="并行处理数量，默认为1")
    
    @validator('parallel')
    def validate_parallel(cls, v):
        if v < 1 or v > 8:
            raise ValueError('parallel必须在1到8之间')
        return v

class BatchClipResponse(BaseModel):
    """
    批量视频剪辑响应
    """
    batch_id: str = Field(..., description="批次ID")
    task_ids: List[str] = Field(..., description="任务ID列表")
    status: TaskStatus = Field(..., description="批次整体状态")
    completed: int = Field(0, description="已完成任务数量")
    total: int = Field(..., description="总任务数量")
    message: Optional[str] = Field(None, description="详细信息") 