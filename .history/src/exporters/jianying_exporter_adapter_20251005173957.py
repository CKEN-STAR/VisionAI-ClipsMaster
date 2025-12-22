"""
剪映导出器适配器
提供兼容层，将新的JianyingDraftGenerator集成到现有系统中
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from .jianying_draft_generator import JianyingDraftGenerator
    from .jianying_time_converter import TimeConverter
except ImportError:
    from src.exporters.jianying_draft_generator import JianyingDraftGenerator
    from src.exporters.jianying_time_converter import TimeConverter

logger = logging.getLogger(__name__)


class JianyingExporterAdapter:
    """
    剪映导出器适配器
    
    将现有系统的数据格式转换为新的JianyingDraftGenerator所需的格式
    保持向后兼容性
    """
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        """
        初始化适配器
        
        Args:
            width: 画布宽度
            height: 画布高度
            fps: 帧率
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.generator = None
    
    def export_project(self, project_data: Dict[str, Any], output_path: str) -> str:
        """
        导出剪映工程文件（兼容旧接口）

        Args:
            project_data: 项目数据，包含segments等信息
            output_path: 输出路径

        Returns:
            实际创建的草稿文件夹路径或文件路径，失败返回None
        """
        try:
            logger.info(f"开始导出剪映工程: {output_path}")

            # 创建生成器
            self.generator = JianyingDraftGenerator(
                width=self.width,
                height=self.height,
                fps=self.fps
            )

            # 解析项目数据
            segments = project_data.get("segments", [])
            if not segments:
                logger.error("项目数据中没有片段信息")
                return None

            # 添加片段到生成器
            self._add_segments_from_project_data(segments)

            # 保存文件
            actual_path = output_path
            if output_path.endswith('.json'):
                # 直接保存draft_content.json
                self.generator.save(output_path)
            else:
                # 创建完整的草稿文件夹
                project_name = project_data.get("project_name", "VisionAI_Project")
                output_dir = os.path.dirname(output_path) or "."
                actual_path = self.generator.create_draft_folder(output_dir, project_name)

            logger.info(f"剪映工程导出成功: {actual_path}")
            return actual_path

        except Exception as e:
            logger.error(f"导出剪映工程失败: {e}", exc_info=True)
            return None
    
    def export(self, segments: List[Dict[str, Any]], output_path: str,
               project_name: str = "VisionAI项目") -> str:
        """
        导出剪映工程文件（简化接口）

        Args:
            segments: 片段列表
            output_path: 输出路径
            project_name: 项目名称

        Returns:
            实际创建的草稿文件夹路径或文件路径，失败返回None
        """
        project_data = {
            "project_name": project_name,
            "segments": segments
        }
        return self.export_project(project_data, output_path)
    
    def _add_segments_from_project_data(self, segments: List[Dict[str, Any]]):
        """
        从项目数据中添加片段
        
        Args:
            segments: 片段列表
        """
        current_time = 0.0  # 当前时间轴位置（秒）
        
        for seg in segments:
            try:
                # 提取片段信息
                source_file = seg.get("source_file") or seg.get("video_path") or seg.get("path")
                if not source_file:
                    logger.warning(f"片段缺少源文件信息: {seg}")
                    continue
                
                # 验证文件存在
                if not os.path.exists(source_file):
                    logger.warning(f"源文件不存在: {source_file}")
                    continue
                
                # 获取时间信息（支持多种格式）
                start_time = self._parse_time(seg.get("start_time", 0))
                end_time = self._parse_time(seg.get("end_time", 0))
                duration = self._parse_time(seg.get("duration", 0))
                
                # 如果没有end_time，使用duration计算
                if end_time == 0 and duration > 0:
                    end_time = start_time + duration
                
                # 如果没有duration，使用end_time计算
                if duration == 0 and end_time > start_time:
                    duration = end_time - start_time
                
                # 验证时间有效性
                if duration <= 0:
                    logger.warning(f"片段时长无效: {seg}")
                    continue
                
                # 获取其他参数
                speed = seg.get("speed", 1.0)
                volume = seg.get("volume", 1.0)
                
                # 添加视频片段
                self.generator.add_video_segment(
                    video_path=source_file,
                    start_time=start_time,
                    end_time=end_time,
                    target_start=current_time,
                    speed=speed,
                    volume=volume
                )
                
                # 更新时间轴位置
                current_time += duration / speed
                
                logger.debug(f"添加片段: {source_file} [{start_time}-{end_time}] -> [{current_time}]")
                
            except Exception as e:
                logger.error(f"添加片段失败: {seg}, 错误: {e}")
                continue
    
    def _parse_time(self, time_value: Any) -> float:
        """
        解析时间值
        
        Args:
            time_value: 时间值（可能是秒、毫秒、字符串等）
            
        Returns:
            秒数（浮点数）
        """
        if isinstance(time_value, (int, float)):
            # 判断是秒还是毫秒
            if time_value > 10000:  # 大于10000，认为是毫秒
                return time_value / 1000.0
            else:
                return float(time_value)
        
        if isinstance(time_value, str):
            # 尝试解析字符串
            try:
                # SRT格式
                if ':' in time_value:
                    microseconds = TimeConverter.parse_srt_timestamp(time_value)
                    return TimeConverter.microseconds_to_seconds(microseconds)
                
                # 纯数字字符串
                value = float(time_value)
                if value > 10000:
                    return value / 1000.0
                else:
                    return value
            except Exception:
                logger.warning(f"无法解析时间值: {time_value}")
                return 0.0
        
        return 0.0
    
    def export_from_subtitles(self, video_path: str, subtitles: List[Dict[str, Any]],
                             output_path: str, project_name: str = "VisionAI项目") -> str:
        """
        从字幕列表导出剪映工程

        Args:
            video_path: 原视频路径
            subtitles: 字幕列表（包含start_time, end_time, text等）
            output_path: 输出路径
            project_name: 项目名称

        Returns:
            实际创建的草稿文件夹路径或文件路径，失败返回None
        """
        try:
            logger.info(f"从字幕导出剪映工程: {len(subtitles)}个字幕")

            # 创建生成器
            self.generator = JianyingDraftGenerator(
                width=self.width,
                height=self.height,
                fps=self.fps
            )

            # 从字幕创建片段
            for subtitle in subtitles:
                try:
                    start_time = self._parse_time(subtitle.get("start_time", 0))
                    end_time = self._parse_time(subtitle.get("end_time", 0))

                    if end_time <= start_time:
                        continue

                    # 添加视频片段
                    self.generator.add_video_segment(
                        video_path=video_path,
                        start_time=start_time,
                        end_time=end_time,
                        target_start=start_time,  # 保持原始时间轴
                        speed=1.0,
                        volume=1.0
                    )

                except Exception as e:
                    logger.error(f"处理字幕失败: {subtitle}, 错误: {e}")
                    continue

            # 保存文件
            actual_path = output_path
            if output_path.endswith('.json'):
                self.generator.save(output_path)
            else:
                output_dir = os.path.dirname(output_path) or "."
                actual_path = self.generator.create_draft_folder(output_dir, project_name)

            logger.info(f"从字幕导出成功: {actual_path}")
            return actual_path

        except Exception as e:
            logger.error(f"从字幕导出失败: {e}", exc_info=True)
            return None


# 便捷函数
def export_to_jianying(segments: List[Dict[str, Any]], output_path: str,
                      project_name: str = "VisionAI项目",
                      width: int = 1920, height: int = 1080, fps: int = 30) -> str:
    """
    便捷的剪映导出函数

    Args:
        segments: 片段列表
        output_path: 输出路径
        project_name: 项目名称
        width: 画布宽度
        height: 画布高度
        fps: 帧率

    Returns:
        实际创建的草稿文件夹路径或文件路径，失败返回None
    """
    adapter = JianyingExporterAdapter(width, height, fps)
    return adapter.export(segments, output_path, project_name)

