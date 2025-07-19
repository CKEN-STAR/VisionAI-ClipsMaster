#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SRT字幕处理模块 - 增强版

提供对多种SRT格式的支持，包括复杂SRT格式、多行字幕、内置样式等。
"""

import os
import re
import logging
import chardet
from typing import List, Dict, Any, Optional, Tuple, Union

# 设置日志记录器
logger = logging.getLogger(__name__)

class SRTTimeCode:
    """SRT时间码对象"""
    
    def __init__(self, hours: int = 0, minutes: int = 0, seconds: int = 0, milliseconds: int = 0):
        """初始化时间码
        
        Args:
            hours: 小时
            minutes: 分钟
            seconds: 秒
            milliseconds: 毫秒
        """
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.milliseconds = milliseconds
    
    @classmethod
    def from_string(cls, time_str: str) -> 'SRTTimeCode':
        """从字符串解析时间码
        
        Args:
            time_str: 时间码字符串，格式为 HH:MM:SS,MMM
            
        Returns:
            SRTTimeCode对象
        """
        # 忽略可能的换行和空格
        time_str = time_str.strip()
        
        # 处理不同时间分隔符
        time_parts = time_str.replace(',', ':').replace('.', ':').split(':')
        
        if len(time_parts) != 4:
            raise ValueError(f"无效的时间码格式: {time_str}")
        
        try:
            return cls(
                hours=int(time_parts[0]),
                minutes=int(time_parts[1]),
                seconds=int(time_parts[2]),
                milliseconds=int(time_parts[3])
            )
        except ValueError as e:
            logger.error(f"解析时间码失败: {time_str}, 错误: {e}")
            return cls()
    
    def to_string(self) -> str:
        """转换为字符串表示
        
        Returns:
            时间码字符串，格式为 HH:MM:SS,MMM
        """
        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d},{self.milliseconds:03d}"
    
    def to_seconds(self) -> float:
        """转换为总秒数
        
        Returns:
            浮点数表示的总秒数
        """
        return (self.hours * 3600 + 
                self.minutes * 60 + 
                self.seconds + 
                self.milliseconds / 1000)
    
    @classmethod
    def from_seconds(cls, seconds: float) -> 'SRTTimeCode':
        """从总秒数创建时间码
        
        Args:
            seconds: 总秒数
            
        Returns:
            SRTTimeCode对象
        """
        total_ms = int(seconds * 1000)
        ms = total_ms % 1000
        total_secs = total_ms // 1000
        s = total_secs % 60
        total_mins = total_secs // 60
        m = total_mins % 60
        h = total_mins // 60
        
        return cls(hours=h, minutes=m, seconds=s, milliseconds=ms)
    
    def __add__(self, other: Union[float, 'SRTTimeCode']) -> 'SRTTimeCode':
        """加法运算
        
        Args:
            other: 另一个时间码或秒数
            
        Returns:
            新的SRTTimeCode对象
        """
        if isinstance(other, float):
            return SRTTimeCode.from_seconds(self.to_seconds() + other)
        elif isinstance(other, SRTTimeCode):
            return SRTTimeCode.from_seconds(self.to_seconds() + other.to_seconds())
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __sub__(self, other: Union[float, 'SRTTimeCode']) -> 'SRTTimeCode':
        """减法运算
        
        Args:
            other: 另一个时间码或秒数
            
        Returns:
            新的SRTTimeCode对象
        """
        if isinstance(other, float):
            return SRTTimeCode.from_seconds(max(0, self.to_seconds() - other))
        elif isinstance(other, SRTTimeCode):
            return SRTTimeCode.from_seconds(max(0, self.to_seconds() - other.to_seconds()))
        else:
            raise TypeError(f"不支持的操作数类型: {type(other)}")
    
    def __lt__(self, other: 'SRTTimeCode') -> bool:
        """小于比较
        
        Args:
            other: 另一个时间码
            
        Returns:
            比较结果
        """
        return self.to_seconds() < other.to_seconds()

class SRTSubtitle:
    """SRT字幕项对象"""
    
    def __init__(self, index: int = 0, 
                 start_time: Optional[SRTTimeCode] = None, 
                 end_time: Optional[SRTTimeCode] = None, 
                 text: str = "", 
                 style: Optional[Dict[str, Any]] = None):
        """初始化字幕项
        
        Args:
            index: 字幕序号
            start_time: 开始时间
            end_time: 结束时间
            text: 字幕文本
            style: 样式信息
        """
        self.index = index
        self.start_time = start_time or SRTTimeCode()
        self.end_time = end_time or SRTTimeCode()
        self.text = text
        self.style = style or {}
    
    @property
    def duration(self) -> float:
        """字幕持续时间(秒)"""
        return self.end_time.to_seconds() - self.start_time.to_seconds()
    
    def set_times(self, start_seconds: float, end_seconds: float) -> None:
        """设置时间范围
        
        Args:
            start_seconds: 开始时间(秒)
            end_seconds: 结束时间(秒)
        """
        self.start_time = SRTTimeCode.from_seconds(start_seconds)
        self.end_time = SRTTimeCode.from_seconds(end_seconds)
    
    def shift_times(self, offset_seconds: float) -> None:
        """移动时间
        
        Args:
            offset_seconds: 时间偏移量(秒)
        """
        if offset_seconds == 0:
            return
            
        self.start_time = self.start_time + offset_seconds
        self.end_time = self.end_time + offset_seconds
    
    def scale_times(self, factor: float) -> None:
        """缩放时间
        
        Args:
            factor: 缩放因子
        """
        if factor <= 0 or factor == 1:
            return
            
        start_seconds = self.start_time.to_seconds()
        duration = self.duration * factor
        
        self.end_time = SRTTimeCode.from_seconds(start_seconds + duration)
    
    def to_srt_string(self) -> str:
        """转换为SRT格式字符串
        
        Returns:
            SRT格式字符串
        """
        return (f"{self.index}\n"
                f"{self.start_time.to_string()} --> {self.end_time.to_string()}\n"
                f"{self.text}\n")

    def has_style_tags(self) -> bool:
        """检查是否包含样式标签
        
        Returns:
            是否包含样式标签
        """
        return bool(re.search(r'</?[bi]>|<font[^>]*>', self.text))
    
    def plain_text(self) -> str:
        """获取纯文本（去除样式标签）
        
        Returns:
            纯文本内容
        """
        text = re.sub(r'</?[bi]>', '', self.text)  # 移除<b>、</b>、<i>、</i>标签
        text = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', text)  # 移除<font>标签但保留内容
        return text
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SRTSubtitle':
        """从字典创建字幕项
        
        Args:
            data: 包含字幕信息的字典
            
        Returns:
            SRTSubtitle对象
        """
        index = data.get('index', 0)
        text = data.get('text', '')
        style = data.get('style', {})
        
        start_time = None
        if 'start_time' in data:
            if isinstance(data['start_time'], str):
                start_time = SRTTimeCode.from_string(data['start_time'])
            elif isinstance(data['start_time'], (int, float)):
                start_time = SRTTimeCode.from_seconds(data['start_time'])
            elif isinstance(data['start_time'], dict):
                start_time = SRTTimeCode(
                    hours=data['start_time'].get('hours', 0),
                    minutes=data['start_time'].get('minutes', 0),
                    seconds=data['start_time'].get('seconds', 0),
                    milliseconds=data['start_time'].get('milliseconds', 0)
                )
        
        end_time = None
        if 'end_time' in data:
            if isinstance(data['end_time'], str):
                end_time = SRTTimeCode.from_string(data['end_time'])
            elif isinstance(data['end_time'], (int, float)):
                end_time = SRTTimeCode.from_seconds(data['end_time'])
            elif isinstance(data['end_time'], dict):
                end_time = SRTTimeCode(
                    hours=data['end_time'].get('hours', 0),
                    minutes=data['end_time'].get('minutes', 0),
                    seconds=data['end_time'].get('seconds', 0),
                    milliseconds=data['end_time'].get('milliseconds', 0)
                )
        
        return cls(index=index, start_time=start_time, end_time=end_time, text=text, style=style)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            包含字幕信息的字典
        """
        return {
            'index': self.index,
            'start_time': self.start_time.to_string(),
            'end_time': self.end_time.to_string(),
            'text': self.text,
            'plain_text': self.plain_text(),
            'duration': self.duration,
            'has_style': self.has_style_tags(),
            'style': self.style
        }

class SRTFile:
    """SRT字幕文件对象"""
    
    def __init__(self, filepath: Optional[str] = None, subtitles: Optional[List[SRTSubtitle]] = None):
        """初始化SRT文件
        
        Args:
            filepath: SRT文件路径
            subtitles: 字幕列表
        """
        self.filepath = filepath
        self.subtitles = subtitles or []
        self.metadata = {}
        
        if filepath and os.path.exists(filepath):
            self.load_file(filepath)
    
    def load_file(self, filepath: str) -> bool:
        """加载SRT文件
        
        Args:
            filepath: SRT文件路径
            
        Returns:
            是否成功加载
        """
        try:
            self.filepath = filepath
            
            # 检测文件编码
            with open(filepath, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # 尝试读取文件
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 解析内容
            self.subtitles = self._parse_content(content)
            logger.info(f"已加载SRT文件: {filepath}, 包含 {len(self.subtitles)} 个字幕")
            return True
        except Exception as e:
            logger.error(f"加载SRT文件失败: {filepath}, 错误: {e}")
            return False
    
    def save_file(self, filepath: Optional[str] = None, encoding: str = 'utf-8') -> bool:
        """保存为SRT文件
        
        Args:
            filepath: 保存路径，如果为None则使用原路径
            encoding: 文件编码
            
        Returns:
            是否成功保存
        """
        save_path = filepath or self.filepath
        if not save_path:
            logger.error("未指定保存路径")
            return False
        
        try:
            # 重新编号
            self._renumber_subtitles()
            
            # 生成SRT内容
            content = ""
            for subtitle in self.subtitles:
                content += subtitle.to_srt_string() + "\n"
            
            # 保存文件
            with open(save_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"已保存SRT文件: {save_path}, 包含 {len(self.subtitles)} 个字幕")
            return True
        except Exception as e:
            logger.error(f"保存SRT文件失败: {save_path}, 错误: {e}")
            return False
    
    def _parse_content(self, content: str) -> List[SRTSubtitle]:
        """解析SRT内容
        
        Args:
            content: SRT文件内容
            
        Returns:
            字幕列表
        """
        subtitles = []
        
        # 使用正则表达式匹配字幕块
        # 格式: 序号 + 时间码 + 文本 + 空行
        pattern = re.compile(r'(\d+)\s*\n'  # 序号
                             r'(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})(?:[^\n]*)?\n'  # 时间码
                             r'((?:.+\n)+?)'  # 文本内容（多行）
                             r'(?:\n|$)')  # 空行或文件结尾
        
        matches = pattern.findall(content)
        for match in matches:
            try:
                index = int(match[0])
                start_time = SRTTimeCode.from_string(match[1])
                end_time = SRTTimeCode.from_string(match[2])
                text = match[3].strip()
                
                # 检测样式信息
                style = self._extract_style_info(text)
                
                subtitle = SRTSubtitle(index, start_time, end_time, text, style)
                subtitles.append(subtitle)
            except Exception as e:
                logger.warning(f"解析字幕块异常，跳过: {match}, 错误: {e}")
        
        return subtitles
    
    def _extract_style_info(self, text: str) -> Dict[str, Any]:
        """提取文本中的样式信息
        
        Args:
            text: 字幕文本
            
        Returns:
            样式信息
        """
        style = {}
        
        # 检测粗体
        if re.search(r'<b>.*?</b>', text):
            style['bold'] = True
        
        # 检测斜体
        if re.search(r'<i>.*?</i>', text):
            style['italic'] = True
        
        # 检测字体颜色
        color_match = re.search(r'<font\s+color=[\'"]([^\'"]*)[\'"]\s*>', text)
        if color_match:
            style['color'] = color_match.group(1)
        
        return style
    
    def _renumber_subtitles(self) -> None:
        """重新编号字幕"""
        for i, subtitle in enumerate(self.subtitles, 1):
            subtitle.index = i
    
    def add_subtitle(self, subtitle: SRTSubtitle) -> None:
        """添加字幕
        
        Args:
            subtitle: 字幕对象
        """
        self.subtitles.append(subtitle)
        self._sort_subtitles()
    
    def add_subtitles(self, subtitles: List[SRTSubtitle]) -> None:
        """批量添加字幕
        
        Args:
            subtitles: 字幕列表
        """
        self.subtitles.extend(subtitles)
        self._sort_subtitles()
    
    def _sort_subtitles(self) -> None:
        """按时间排序字幕"""
        self.subtitles.sort(key=lambda x: x.start_time.to_seconds())
        self._renumber_subtitles()
    
    def get_subtitles(self) -> List[SRTSubtitle]:
        """获取所有字幕
        
        Returns:
            字幕列表
        """
        return self.subtitles
    
    def get_subtitle_at_time(self, time_seconds: float) -> Optional[SRTSubtitle]:
        """获取指定时间点的字幕
        
        Args:
            time_seconds: 时间点(秒)
            
        Returns:
            字幕对象，如果没有则返回None
        """
        for subtitle in self.subtitles:
            start = subtitle.start_time.to_seconds()
            end = subtitle.end_time.to_seconds()
            if start <= time_seconds <= end:
                return subtitle
        return None
    
    def get_subtitles_in_range(self, start_seconds: float, end_seconds: float) -> List[SRTSubtitle]:
        """获取指定时间范围的字幕
        
        Args:
            start_seconds: 开始时间(秒)
            end_seconds: 结束时间(秒)
            
        Returns:
            字幕列表
        """
        results = []
        for subtitle in self.subtitles:
            sub_start = subtitle.start_time.to_seconds()
            sub_end = subtitle.end_time.to_seconds()
            
            # 判断是否有重叠
            if (sub_start <= end_seconds and sub_end >= start_seconds):
                results.append(subtitle)
        
        return results
    
    def get_subtitle_by_index(self, index: int) -> Optional[SRTSubtitle]:
        """根据索引获取字幕
        
        Args:
            index: 字幕索引
            
        Returns:
            字幕对象，如果没有则返回None
        """
        for subtitle in self.subtitles:
            if subtitle.index == index:
                return subtitle
        return None
    
    def remove_subtitle(self, subtitle: SRTSubtitle) -> bool:
        """移除字幕
        
        Args:
            subtitle: 要移除的字幕
            
        Returns:
            是否成功移除
        """
        if subtitle in self.subtitles:
            self.subtitles.remove(subtitle)
            self._renumber_subtitles()
            return True
        return False
    
    def remove_subtitle_by_index(self, index: int) -> bool:
        """根据索引移除字幕
        
        Args:
            index: 字幕索引
            
        Returns:
            是否成功移除
        """
        subtitle = self.get_subtitle_by_index(index)
        if subtitle:
            return self.remove_subtitle(subtitle)
        return False
    
    def clear_subtitles(self) -> None:
        """清空所有字幕"""
        self.subtitles = []
    
    def shift_all_subtitles(self, offset_seconds: float) -> None:
        """移动所有字幕的时间
        
        Args:
            offset_seconds: 时间偏移量(秒)
        """
        for subtitle in self.subtitles:
            subtitle.shift_times(offset_seconds)
    
    def scale_all_durations(self, factor: float) -> None:
        """缩放所有字幕的持续时间
        
        Args:
            factor: 缩放因子
        """
        for subtitle in self.subtitles:
            subtitle.scale_times(factor)
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表
        
        Returns:
            字典列表
        """
        return [subtitle.to_dict() for subtitle in self.subtitles]
    
    @classmethod
    def from_dict_list(cls, dict_list: List[Dict[str, Any]]) -> 'SRTFile':
        """从字典列表创建SRT文件
        
        Args:
            dict_list: 字典列表
            
        Returns:
            SRTFile对象
        """
        subtitles = [SRTSubtitle.from_dict(item) for item in dict_list]
        return cls(subtitles=subtitles)
    
    def get_plain_text(self, join_char: str = "\n") -> str:
        """获取所有字幕的纯文本
        
        Args:
            join_char: 连接字符
            
        Returns:
            纯文本
        """
        return join_char.join([sub.plain_text() for sub in self.subtitles])
    
    def export_as_txt(self, filepath: str, encoding: str = 'utf-8') -> bool:
        """导出为纯文本文件
        
        Args:
            filepath: 导出路径
            encoding: 文件编码
            
        Returns:
            是否成功导出
        """
        try:
            with open(filepath, 'w', encoding=encoding) as f:
                for subtitle in self.subtitles:
                    f.write(f"{subtitle.plain_text()}\n\n")
            return True
        except Exception as e:
            logger.error(f"导出纯文本文件失败: {filepath}, 错误: {e}")
            return False
    
    def split_merged_subtitles(self, max_chars_per_line: int = 40) -> None:
        """拆分合并的字幕
        
        Args:
            max_chars_per_line: 每行最大字符数
        """
        new_subtitles = []
        
        for subtitle in self.subtitles:
            lines = subtitle.text.split('\n')
            
            if len(lines) <= 2:
                # 保持原样
                new_subtitles.append(subtitle)
                continue
            
            # 计算每行平均持续时间
            total_duration = subtitle.duration
            avg_duration_per_line = total_duration / len(lines)
            
            # 拆分为多个字幕
            current_time = subtitle.start_time.to_seconds()
            
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                line_duration = avg_duration_per_line
                line_start = current_time
                line_end = line_start + line_duration
                current_time = line_end
                
                new_sub = SRTSubtitle(
                    index=0,  # 之后会重新编号
                    start_time=SRTTimeCode.from_seconds(line_start),
                    end_time=SRTTimeCode.from_seconds(line_end),
                    text=line,
                    style=subtitle.style.copy()
                )
                
                new_subtitles.append(new_sub)
        
        if new_subtitles:
            self.subtitles = new_subtitles
            self._sort_subtitles()
    
    def merge_close_subtitles(self, max_gap: float = 0.5, max_lines: int = 2) -> None:
        """合并时间接近的字幕
        
        Args:
            max_gap: 最大时间间隔(秒)
            max_lines: 合并后最大行数
        """
        if not self.subtitles or len(self.subtitles) < 2:
            return
            
        i = 0
        merged = []
        
        while i < len(self.subtitles):
            current = self.subtitles[i]
            merged_sub = SRTSubtitle(
                index=current.index,
                start_time=current.start_time,
                end_time=current.end_time,
                text=current.text,
                style=current.style.copy()
            )
            
            # 向前看，合并接近的字幕
            j = i + 1
            lines_count = current.text.count('\n') + 1
            
            while j < len(self.subtitles) and lines_count < max_lines:
                next_sub = self.subtitles[j]
                gap = next_sub.start_time.to_seconds() - merged_sub.end_time.to_seconds()
                
                next_lines = next_sub.text.count('\n') + 1
                if gap <= max_gap and lines_count + next_lines <= max_lines:
                    # 合并字幕
                    merged_sub.text += '\n' + next_sub.text
                    merged_sub.end_time = next_sub.end_time
                    lines_count += next_lines
                    j += 1
                else:
                    break
            
            merged.append(merged_sub)
            i = j
        
        self.subtitles = merged
        self._renumber_subtitles()
    
    def enforce_format(self, max_chars_per_line: int = 40, max_lines: int = 2) -> None:
        """强制执行格式规范
        
        Args:
            max_chars_per_line: 每行最大字符数
            max_lines: 最大行数
        """
        for subtitle in self.subtitles:
            lines = subtitle.text.split('\n')
            formatted_lines = []
            
            for line in lines:
                if len(line) <= max_chars_per_line:
                    formatted_lines.append(line)
                else:
                    # 拆分长行
                    words = line.split(' ') if ' ' in line else list(line)
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + (" " if current_line else "") + word
                        if len(test_line) <= max_chars_per_line:
                            current_line = test_line
                        else:
                            formatted_lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        formatted_lines.append(current_line)
            
            # 限制行数
            if len(formatted_lines) > max_lines:
                formatted_lines = formatted_lines[:max_lines]
            
            subtitle.text = '\n'.join(formatted_lines)

# 导出函数
def load_srt(filepath: str) -> Optional[SRTFile]:
    """加载SRT文件
    
    Args:
        filepath: SRT文件路径
        
    Returns:
        SRTFile对象，如果加载失败则返回None
    """
    srt_file = SRTFile()
    if srt_file.load_file(filepath):
        return srt_file
    return None

def save_srt(subtitles: List[Dict[str, Any]], filepath: str, encoding: str = 'utf-8') -> bool:
    """保存字幕到SRT文件
    
    Args:
        subtitles: 字幕字典列表
        filepath: 保存路径
        encoding: 文件编码
        
    Returns:
        是否成功保存
    """
    srt_file = SRTFile.from_dict_list(subtitles)
    return srt_file.save_file(filepath, encoding) 