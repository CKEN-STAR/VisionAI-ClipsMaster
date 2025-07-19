"""
字幕文件恢复模块

提供针对字幕文件的高级修复和恢复功能，处理常见的字幕错误：
1. 时间码错误与不一致
2. 编码问题与字符集错误
3. 索引错误与缺失
4. 格式损坏的字幕块
5. 中英文混合字幕智能修复
"""

import re
import os
import unicodedata
import difflib
import chardet
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from loguru import logger
from src.utils.exceptions import InvalidSRTError, FileOperationError, ErrorCode
from src.parsers.error_recovery import ParserDoctor
from src.parsers.srt_decoder import parse_srt_to_dict


class SubtitleRecovery:
    """字幕恢复专家类"""
    
    def __init__(self):
        """初始化字幕恢复系统"""
        self.parser_doctor = ParserDoctor()
        self.recovery_stats = {
            "attempts": 0,
            "successes": 0,
            "warnings": 0,
            "error_types": {}
        }
    
    def detect_encoding(self, file_path: str) -> str:
        """
        检测字幕文件编码
        
        Args:
            file_path: 字幕文件路径
            
        Returns:
            检测到的编码
        """
        # 读取文件的二进制内容
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)  # 读取前4KB进行检测
                
            # 使用chardet检测编码
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            logger.debug(f"检测到文件编码: {encoding} (置信度: {confidence:.2f})")
            
            # 如果置信度低，尝试常见编码
            if confidence < 0.7:
                logger.warning(f"编码检测置信度低 ({confidence:.2f})，将尝试常见编码")
                # 返回原检测结果，但在读取时会尝试多种编码
                return "auto"
            
            return encoding or "utf-8"
        except Exception as e:
            logger.error(f"编码检测失败: {e}")
            return "utf-8"  # 默认返回UTF-8
    
    def read_with_fallback_encodings(self, file_path: str, primary_encoding: str = "utf-8") -> str:
        """
        尝试多种编码读取文件内容
        
        Args:
            file_path: 文件路径
            primary_encoding: 首选编码
            
        Returns:
            文件内容
            
        Raises:
            FileOperationError: 如果所有编码尝试都失败
        """
        # 尝试的编码列表（按优先级排序）
        encodings = []
        
        # 如果检测到自动模式，尝试多种编码
        if primary_encoding == "auto":
            encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "big5", "latin-1"]
        else:
            # 首选指定的编码，然后是常见的备选编码
            encodings = [primary_encoding, "utf-8", "utf-8-sig", "gbk", "latin-1"]
        
        # 记录错误信息
        errors = []
        
        # 尝试每种编码
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"成功使用编码 {encoding} 读取文件")
                return content
            except UnicodeDecodeError as e:
                errors.append(f"{encoding}: {str(e)}")
                continue
            except Exception as e:
                errors.append(f"{encoding}: {str(e)}")
                continue
        
        # 所有编码都失败，尝试二进制读取并强制解码
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            # 使用errors='replace'强制解码，替换无法识别的字符
            decoded = content.decode("utf-8", errors="replace")
            logger.warning("使用替换模式强制解码文件")
            return decoded
        except Exception as e:
            errors.append(f"binary fallback: {str(e)}")
        
        # 如果所有方法都失败
        error_msg = f"无法读取文件，尝试了以下编码: {', '.join(encodings)}"
        logger.error(error_msg)
        for err in errors:
            logger.error(f" - {err}")
        raise FileOperationError(error_msg, file_path=file_path)
    
    def recover_srt_file(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        恢复和修复SRT文件
        
        Args:
            file_path: SRT文件路径
            
        Returns:
            Tuple[str, Dict]: 修复后的内容和统计信息
            
        Raises:
            InvalidSRTError: 如果文件无法修复
            FileOperationError: 如果文件无法读取
        """
        self.recovery_stats["attempts"] += 1
        
        try:
            # 检测文件编码
            encoding = self.detect_encoding(file_path)
            
            # 读取文件内容
            raw_content = self.read_with_fallback_encodings(file_path, encoding)
            
            # 应用基本修复
            repaired_content = self.parser_doctor.fix_common_errors(raw_content)
            
            # 尝试解析修复后的内容
            try:
                parse_srt_to_dict(repaired_content)
                logger.info(f"基本修复成功: {file_path}")
                self.recovery_stats["successes"] += 1
                return repaired_content, self.parser_doctor.stats
            except Exception as parse_error:
                logger.warning(f"基本修复后仍存在问题，尝试高级修复: {parse_error}")
                
                # 尝试更多修复技术
                repaired_content = self._apply_advanced_repairs(repaired_content)
                
                # 再次尝试解析
                try:
                    parse_srt_to_dict(repaired_content)
                    logger.info(f"高级修复成功: {file_path}")
                    self.recovery_stats["successes"] += 1
                    return repaired_content, self.parser_doctor.stats
                except Exception as adv_parse_error:
                    logger.error(f"高级修复后仍无法解析: {adv_parse_error}")
                    error_type = "parse_error"
                    self.recovery_stats["error_types"][error_type] = self.recovery_stats["error_types"].get(error_type, 0) + 1
                    raise InvalidSRTError(f"无法修复SRT文件: {adv_parse_error}")
                
        except FileOperationError:
            # 传递文件操作错误
            raise
        except Exception as e:
            logger.error(f"SRT恢复过程中发生错误: {e}")
            error_type = "unknown_error"
            self.recovery_stats["error_types"][error_type] = self.recovery_stats["error_types"].get(error_type, 0) + 1
            raise InvalidSRTError(f"SRT恢复失败: {str(e)}")
    
    def _apply_advanced_repairs(self, content: str) -> str:
        """
        应用高级修复技术
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 1. 修复时间戳格式
        content = self._fix_timestamp_formats(content)
        
        # 2. 重建索引序列
        content = self._rebuild_subtitle_indices(content)
        
        # 3. 修复空白行
        content = self._fix_empty_subtitles(content)
        
        # 4. 修复块之间分隔符
        content = self._normalize_block_separators(content)
        
        # 5. 修复重叠时间戳
        content = self._fix_overlapping_timestamps(content)
        
        # 6. 修复缺失的结束时间
        content = self._fix_missing_end_times(content)
        
        return content
    
    def _fix_timestamp_formats(self, content: str) -> str:
        """
        修复各种错误的时间戳格式
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 替换逗号/点分隔符不一致的情况
        content = re.sub(r'(\d{2}:\d{2}:\d{2})[.,](\d{3})', r'\1,\2', content)
        
        # 修复缺少小时部分的时间戳 (MM:SS,ms -> HH:MM:SS,ms)
        def fix_short_timestamp(match):
            mins, secs, ms = match.groups()
            return f"00:{mins.zfill(2)}:{secs.zfill(2)},{ms}"
        
        content = re.sub(r'(?<!\d)(\d{1,2}):(\d{1,2}),(\d{3})', fix_short_timestamp, content)
        
        # 修复时间分隔符不一致 (00:00:00 --> 00:00:00)
        content = re.sub(r'(\d{2}:\d{2}:\d{2},\d{3})\s*[-=]+>\s*', r'\1 --> ', content)
        
        # 修复缺少毫秒的时间戳 (00:00:00 -> 00:00:00,000)
        content = re.sub(r'(\d{2}:\d{2}:\d{2})(?!\d|,)', r'\1,000', content)
        
        # 确保时、分、秒都是两位数
        def pad_time_components(match):
            hours, mins, secs, ms = match.groups()
            return f"{hours.zfill(2)}:{mins.zfill(2)}:{secs.zfill(2)},{ms}"
        
        content = re.sub(r'(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{3})', pad_time_components, content)
        
        return content
    
    def _rebuild_subtitle_indices(self, content: str) -> str:
        """
        重建字幕索引
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 分割为字幕块
        blocks = re.split(r'\n\s*\n', content.strip())
        fixed_blocks = []
        
        for i, block in enumerate(blocks, 1):
            lines = block.strip().split('\n')
            
            # 检查是否有时间戳行
            timestamp_line_idx = -1
            for j, line in enumerate(lines):
                if re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', line):
                    timestamp_line_idx = j
                    break
            
            if timestamp_line_idx == -1:
                # 如果没有时间戳行，跳过这个块
                logger.debug(f"跳过没有时间戳的块: {block}")
                continue
            
            new_block = []
            
            # 添加正确的索引作为第一行
            new_block.append(str(i))
            
            # 如果索引行不是第一行，或者第一行不是有效索引，调整顺序
            if timestamp_line_idx != 0 and not re.match(r'^\d+$', lines[0]):
                # 添加时间戳行
                new_block.append(lines[timestamp_line_idx])
                
                # 添加其他内容行
                for j, line in enumerate(lines):
                    if j != timestamp_line_idx and not (j == 0 and re.match(r'^\d+$', line)):
                        new_block.append(line)
            else:
                # 保持原始顺序，但替换索引
                for j, line in enumerate(lines):
                    if j == 0 and re.match(r'^\d+$', line):
                        continue  # 跳过原始索引
                    new_block.append(line)
            
            fixed_blocks.append('\n'.join(new_block))
        
        # 重新组合内容
        return '\n\n'.join(fixed_blocks)
    
    def _fix_empty_subtitles(self, content: str) -> str:
        """
        修复空白字幕块
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 分割为字幕块
        blocks = re.split(r'\n\s*\n', content.strip())
        fixed_blocks = []
        
        for block in blocks:
            lines = block.strip().split('\n')
            
            # 检查是否有时间戳但没有文本内容
            has_timestamp = False
            has_text = False
            
            for line in lines:
                if re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', line):
                    has_timestamp = True
                elif line.strip() and not re.match(r'^\d+$', line.strip()):
                    has_text = True
            
            # 只保留有时间戳和文本的块
            if has_timestamp and has_text:
                fixed_blocks.append(block)
            elif has_timestamp:
                # 如果有时间戳但没有文本，添加占位符
                fixed_block = block + "\n[空白字幕]"
                fixed_blocks.append(fixed_block)
                logger.debug(f"在空白字幕块中添加占位符: {block}")
        
        # 重新组合内容
        return '\n\n'.join(fixed_blocks)
    
    def _normalize_block_separators(self, content: str) -> str:
        """
        标准化字幕块之间的分隔符
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 首先统一换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # 然后标准化块之间的分隔
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 确保每个块之间只有一个空行
        blocks = [block.strip() for block in re.split(r'\n\s*\n', content) if block.strip()]
        return '\n\n'.join(blocks)
    
    def _fix_overlapping_timestamps(self, content: str) -> str:
        """
        修复重叠的时间戳
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 提取所有时间戳
        timestamp_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        timestamps = re.findall(timestamp_pattern, content)
        
        # 如果不到两个时间戳，无需修复重叠
        if len(timestamps) < 2:
            return content
        
        # 转换为毫秒并排序
        def to_ms(h, m, s, ms):
            return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        
        def from_ms(ms):
            h = ms // 3600000
            ms %= 3600000
            m = ms // 60000
            ms %= 60000
            s = ms // 1000
            ms %= 1000
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        
        # 创建时间段列表 [(开始, 结束, 原始匹配, 索引)]
        time_spans = []
        for i, (h1, m1, s1, ms1, h2, m2, s2, ms2) in enumerate(timestamps):
            start_ms = to_ms(h1, m1, s1, ms1)
            end_ms = to_ms(h2, m2, s2, ms2)
            
            # 如果开始时间大于结束时间，交换它们
            if start_ms > end_ms:
                logger.warning(f"修复倒置的时间戳: {from_ms(start_ms)} --> {from_ms(end_ms)}")
                start_ms, end_ms = end_ms, start_ms
            
            match = re.search(timestamp_pattern, content)
            if match:
                time_spans.append((start_ms, end_ms, match.group(0), i))
        
        # 排序并检测重叠
        time_spans.sort()
        fixed_content = content
        
        for i in range(len(time_spans) - 1):
            curr_start, curr_end, curr_match, curr_idx = time_spans[i]
            next_start, next_end, next_match, next_idx = time_spans[i + 1]
            
            # 检查重叠
            if curr_end > next_start:
                # 调整当前字幕的结束时间
                new_end = next_start - 1
                if new_end < curr_start:
                    new_end = curr_start + 1000  # 至少持续1秒
                
                new_time = f"{from_ms(curr_start)} --> {from_ms(new_end)}"
                fixed_content = fixed_content.replace(curr_match, new_time)
                logger.debug(f"修复重叠时间戳: {curr_match} -> {new_time}")
        
        return fixed_content
    
    def _fix_missing_end_times(self, content: str) -> str:
        """
        修复缺失的结束时间
        
        Args:
            content: 字幕内容
            
        Returns:
            修复后的内容
        """
        # 查找只有开始时间的时间戳
        single_timestamp_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})(?!\s*-->)'
        matches = re.finditer(single_timestamp_pattern, content)
        
        fixed_content = content
        for match in matches:
            if '-->' not in match.string[match.start():match.start()+30]:
                # 找到只有开始时间的情况，补充结束时间
                start_time = match.group(1)
                
                # 将时间戳转换为毫秒
                h, m, s = start_time.split(':')
                s, ms = s.split(',')
                start_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
                
                # 结束时间设为开始时间后3秒
                end_ms = start_ms + 3000
                
                h = end_ms // 3600000
                end_ms %= 3600000
                m = end_ms // 60000
                end_ms %= 60000
                s = end_ms // 1000
                end_ms %= 1000
                
                end_time = f"{h:02d}:{m:02d}:{s:02d},{end_ms:03d}"
                
                # 替换为完整时间戳
                new_timestamp = f"{start_time} --> {end_time}"
                fixed_content = fixed_content.replace(start_time, new_timestamp, 1)
                logger.debug(f"修复缺失的结束时间: {start_time} -> {new_timestamp}")
        
        return fixed_content
    
    def save_repaired_srt(self, file_path: str, content: str, suffix: str = '_fixed') -> str:
        """
        保存修复后的SRT文件
        
        Args:
            file_path: 原始文件路径
            content: 修复后的内容
            suffix: 文件名后缀
            
        Returns:
            保存的文件路径
        """
        # 构建新文件路径
        base_name, ext = os.path.splitext(file_path)
        new_file_path = f"{base_name}{suffix}{ext}"
        
        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已保存修复后的字幕文件: {new_file_path}")
            return new_file_path
        except Exception as e:
            logger.error(f"保存修复后的字幕文件失败: {e}")
            raise FileOperationError(f"保存修复后的字幕文件失败: {e}", file_path=new_file_path)
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        return self.recovery_stats


# 全局字幕恢复实例
_subtitle_recovery = None

def get_subtitle_recovery() -> SubtitleRecovery:
    """获取字幕恢复实例"""
    global _subtitle_recovery
    if _subtitle_recovery is None:
        _subtitle_recovery = SubtitleRecovery()
    return _subtitle_recovery


def recover_subtitle_file(file_path: str, save_fixed: bool = True) -> Tuple[str, Dict[str, Any]]:
    """
    恢复字幕文件的便捷函数
    
    Args:
        file_path: 字幕文件路径
        save_fixed: 是否保存修复后的文件
        
    Returns:
        Tuple[str, Dict]: 修复后的内容和统计信息
    """
    recovery = get_subtitle_recovery()
    
    # 修复字幕
    repaired_content, stats = recovery.recover_srt_file(file_path)
    
    # 如果需要，保存修复后的文件
    if save_fixed:
        recovery.save_repaired_srt(file_path, repaired_content)
    
    return repaired_content, stats 