"""
字幕解析容错与修复机制

本模块提供针对字幕文件中常见错误的自动检测和修复功能，包括：
1. 时间码格式错误修复
2. 索引错误修复
3. 编码问题处理
4. 空白行和格式异常处理
5. 智能容错解析
"""

import re
import os
import json
import logging
import unicodedata
import difflib
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from pathlib import Path

from src.core.exceptions import InvalidSRTError, FileOperationError
from src.utils.log_handler import get_logger

logger = get_logger("error_recovery")

class ParserDoctor:
    """字幕解析医生 - 专门处理字幕文件中的各种异常和错误"""
    
    def __init__(self):
        """初始化解析医生"""
        self.logger = logger
        self.stats = {"fixed": 0, "failed": 0, "warnings": 0}
        
        # 常见错误模式及修复函数映射
        self.error_fixers = {
            "timestamp_format": self.fix_timestamp_format,
            "index_sequence": self.fix_index_sequence,
            "encoding_issues": self.fix_encoding_issues,
            "blank_subtitles": self.fix_blank_subtitles,
            "malformed_blocks": self.fix_malformed_blocks,
        }
    
    def fix_common_errors(self, raw_text: str) -> str:
        """自动修复常见字幕错误
        
        Args:
            raw_text: 原始字幕文本
            
        Returns:
            修复后的字幕文本
        """
        """自动修复常见字幕错误
        
        Args:
            raw_text: 原始字幕文本
            
        Returns:
            修复后的字幕文本
        """
        self.logger.info("开始修复常见字幕错误")
        
        # 复位统计信息
        self.stats = {"fixed": 0, "failed": 0, "warnings": 0}
        
        # 处理空内容
        if not raw_text or not raw_text.strip():
            raise InvalidSRTError("Empty subtitle content")
        
        # 修复错误的时间分隔符
        repaired = re.sub(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", r"\1:\2:\3,\4", raw_text)
        
        # 修复丢失的序号
        repaired = re.sub(r"(?<![\d\n])(\d{2}:\d{2}:\d{2}),(\d{3})\s+-->\s+", 
                          r"\n\1:\2,\3 --> ", 
                          repaired)
        
        # 统一行尾换行符
        repaired = repaired.replace('\r\n', '\n').replace('\r', '\n')
        
        # 修复多余的空行
        repaired = re.sub(r'\n{3,}', '\n\n', repaired)
        
        # 修复时间戳与内容之间缺少换行的情况
        repaired = re.sub(r'(\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3})([^\n])', 
                          r'\1\n\2', 
                          repaired)
        
        # 我们已经进行了一些基本修复
        self.stats["fixed"] += 1
        
        return repaired
    
    def smart_recovery(self, malformed_data: Dict[str, Any]) -> Dict[str, Any]:
        """基于智能分析的修复机制
        
        对无法通过简单规则修复的复杂问题进行处理
        
        Args:
            malformed_data: 损坏或不完整的数据
            
        Returns:
            修复后的数据
        """
        # 检测是否有内容但没有正确解析的字幕
        if len(malformed_data.get('text', '')) > 50 and not malformed_data.get('entities', []):
            # 尝试使用备用解析器处理
            return self._retry_with_alternative_parser(malformed_data)
        
        # 尝试根据内容长度和可能的格式来推断正确的结构
        if 'text' in malformed_data and len(malformed_data['text']) > 0:
            # 检查是否可能是JSON格式
            if malformed_data['text'].strip().startswith('{') and malformed_data['text'].strip().endswith('}'):
                try:
                    fixed_data = json.loads(malformed_data['text'])
                    self.logger.info("成功修复JSON格式数据")
                    self.stats["fixed"] += 1
                    return fixed_data
                except json.JSONDecodeError:
                    self.logger.warning("尝试解析为JSON失败")
                    self.stats["warnings"] += 1
        
        # 处理文本格式不规范但可以猜测的情况
        if 'text' in malformed_data:
            # 寻找并尝试提取时间码
            timestamp_matches = re.findall(
                r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})', 
                malformed_data['text']
            )
            
            if timestamp_matches:
                self.logger.info(f"找到{len(timestamp_matches)}个可能的时间码")
                self.stats["fixed"] += 1
                
                # 重建结构化数据
                reconstructed = {
                    "blocks": []
                }
                
                # 使用时间码分割文本
                chunks = re.split(
                    r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})', 
                    malformed_data['text']
                )
                
                # 重建字幕块
                for i in range(0, len(chunks)-8, 9):
                    block = {
                        "start": f"{chunks[i+1]}:{chunks[i+2]}:{chunks[i+3]},{chunks[i+4]}",
                        "end": f"{chunks[i+5]}:{chunks[i+6]}:{chunks[i+7]},{chunks[i+8]}",
                        "text": chunks[i+9].strip() if i+9 < len(chunks) else ""
                    }
                    reconstructed["blocks"].append(block)
                
                return reconstructed
        
        # 如果都不成功，记录失败并返回原始数据
        self.logger.error("无法智能修复数据")
        self.stats["failed"] += 1
        return malformed_data
    
    def fix_timestamp_format(self, text: str) -> str:
        """修复时间戳格式问题
        
        处理常见的时间戳格式错误，如分隔符错误、数字缺失等
        
        Args:
            text: 原始文本
            
        Returns:
            修复后的文本
        """
        # 处理逗号和点的混用问题
        text = re.sub(r'(\d{2}:\d{2}:\d{2})\.(\d{3})', r'\1,\2', text)
        
        # 处理分隔符缺失问题
        text = re.sub(r'(\d{2}:\d{2}:\d{2})(\d{3})', r'\1,\2', text)
        
        # 处理时间戳连接符问题
        text = re.sub(r'(\d{2}:\d{2}:\d{2},\d{3})\s*(-->|->|>|:|-->)\s*(\d{2}:\d{2}:\d{2},\d{3})', 
                      r'\1 --> \3', text)
        
        # 处理时、分、秒格式问题（如01:2:3,400应为01:02:03,400）
        def pad_time_groups(match):
            h, m, s, ms = match.groups()
            return f"{h.zfill(2)}:{m.zfill(2)}:{s.zfill(2)},{ms.ljust(3, '0')}"
        
        text = re.sub(r'(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d{1,3})', pad_time_groups, text)
        
        return text
    
    def fix_index_sequence(self, text: str) -> str:
        """修复索引序列问题
        
        处理索引不连续、缺失或重复的问题
        
        Args:
            text: 原始文本
            
        Returns:
            修复后的文本
        """
        # 分割为字幕块
        blocks = re.split(r'\n\s*\n', text.strip())
        fixed_blocks = []
        
        for i, block in enumerate(blocks):
            lines = block.strip().split('\n')
            
            # 检查第一行是否为有效索引
            if len(lines) >= 2 and not re.match(r'^\d+$', lines[0].strip()):
                # 如果不是有效索引，添加一个
                lines.insert(0, str(i+1))
            elif len(lines) >= 1 and re.match(r'^\d+$', lines[0].strip()):
                # 如果有索引但不正确，替换它
                lines[0] = str(i+1)
                
            fixed_blocks.append('\n'.join(lines))
        
        # 重新组合文本
        return '\n\n'.join(fixed_blocks)
    
    def fix_encoding_issues(self, text: str) -> str:
        """修复编码问题
        
        处理特殊字符、非法字符和编码混乱问题
        
        Args:
            text: 原始文本
            
        Returns:
            修复后的文本
        """
        # 标准化为NFKC形式
        text = unicodedata.normalize('NFKC', text)
        
        # 替换非法或控制字符
        text = ''.join(ch if unicodedata.category(ch)[0] != 'C' else ' ' for ch in text)
        
        # 处理常见的编码错误字符
        encoding_fixes = {
            '�': '',  # 替换Unicode替换字符
            '\ufffd': '',  # 另一种表示方式
            '?': "'",  # 修复常见的引号问题
            'â€™': "'",  # 常见的UTF-8编码问题
            'â€œ': '"',
            'â€': '"'
        }
        
        for bad, good in encoding_fixes.items():
            text = text.replace(bad, good)
            
        return text
    
    def fix_blank_subtitles(self, text: str) -> str:
        """修复空白字幕问题
        
        处理内容为空的字幕块
        
        Args:
            text: 原始文本
            
        Returns:
            修复后的文本
        """
        # 分割为字幕块
        blocks = re.split(r'\n\s*\n', text.strip())
        valid_blocks = []
        
        for block in blocks:
            lines = block.strip().split('\n')
            
            # 检查是否包含时间戳和内容
            has_timestamp = any(re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}', line) 
                               for line in lines)
            
            has_content = False
            for i, line in enumerate(lines):
                if has_timestamp and i > 0 and not re.search(r'\d{2}:\d{2}:\d{2},\d{3}', line) and line.strip():
                    has_content = True
                    break
            
            # 只保留有内容的字幕块
            if has_timestamp and has_content:
                valid_blocks.append(block)
            elif has_timestamp:
                # 如果有时间戳但没内容，添加占位符
                timestamp_line_idx = next((i for i, line in enumerate(lines) 
                                         if re.search(r'\d{2}:\d{2}:\d{2},\d{3}', line)), 0)
                if timestamp_line_idx < len(lines) - 1:
                    lines.append("[占位字幕]")
                else:
                    lines.append("[占位字幕]")
                valid_blocks.append('\n'.join(lines))
        
        # 重新组合文本
        return '\n\n'.join(valid_blocks)
    
    def fix_malformed_blocks(self, text: str) -> str:
        """修复格式错误的字幕块
        
        处理格式不正确或不符合标准的字幕块
        
        Args:
            text: 原始文本
            
        Returns:
            修复后的文本
        """
        # 分割为字幕块
        blocks = re.split(r'\n\s*\n', text.strip())
        fixed_blocks = []
        
        for i, block in enumerate(blocks):
            lines = block.strip().split('\n')
            
            # 检查块是否包含至少两行（索引和时间码）
            if len(lines) < 2:
                # 如果只有一行，检查是否是一个孤立的索引或时间码
                if re.match(r'^\d+$', lines[0].strip()):
                    # 孤立的索引，跳过
                    continue
                elif re.search(r'\d{2}:\d{2}:\d{2},\d{3}', lines[0]):
                    # 孤立的时间码，使用下一个块的内容（如果有）
                    if i+1 < len(blocks):
                        next_lines = blocks[i+1].strip().split('\n')
                        if not re.search(r'\d{2}:\d{2}:\d{2},\d{3}', next_lines[0]):
                            lines.append(next_lines[0])
                            fixed_blocks.append('\n'.join([str(i+1)] + lines))
                            continue
                    # 如果没有合适的下一块，跳过
                    continue
            
            # 检查第一行是否为索引
            if not re.match(r'^\d+$', lines[0].strip()):
                lines.insert(0, str(i+1))
            
            # 检查第二行是否为时间码
            if len(lines) > 1 and not re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}', lines[1]):
                # 查找任何一行中的时间码
                time_line_idx = next((j for j, line in enumerate(lines) 
                                   if re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}', line)), -1)
                
                if time_line_idx != -1:
                    # 将时间码行移动到第二行
                    time_line = lines.pop(time_line_idx)
                    lines.insert(1, time_line)
                else:
                    # 如果没有时间码，跳过此块
                    continue
            
            # 添加修复后的块
            fixed_blocks.append('\n'.join(lines))
        
        # 重新组合文本
        return '\n\n'.join(fixed_blocks)
    
    def _retry_with_alternative_parser(self, malformed_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用备用解析器重试
        
        当主解析器失败时，尝试使用不同的方法解析
        
        Args:
            malformed_data: 损坏的数据
            
        Returns:
            修复后的数据
        """
        text = malformed_data.get('text', '')
        
        try:
            # 尝试使用更宽松的解析规则
            lines = text.split('\n')
            blocks = []
            current_block = {"index": None, "time": None, "content": []}
            
            for line in lines:
                line = line.strip()
                
                # 尝试匹配索引
                if re.match(r'^\d+$', line):
                    if current_block["content"]:
                        blocks.append(current_block)
                        current_block = {"index": int(line), "time": None, "content": []}
                    else:
                        current_block["index"] = int(line)
                        
                # 尝试匹配时间码
                elif re.search(r'\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,\.]\d{3}', line):
                    current_block["time"] = line
                    
                # 否则为内容行
                elif line:
                    current_block["content"].append(line)
            
            # 添加最后一个块
            if current_block["content"]:
                blocks.append(current_block)
            
            # 重建结构化数据
            reconstructed = {
                "blocks": [],
                "entities": []
            }
            
            for block in blocks:
                if block["time"] and block["content"]:
                    time_match = re.search(
                        r'(\d{1,2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,\.](\d{3})', 
                        block["time"]
                    )
                    
                    if time_match:
                        start_time = f"{time_match.group(1).zfill(2)}:{time_match.group(2)}:{time_match.group(3)},{time_match.group(4)}"
                        end_time = f"{time_match.group(5).zfill(2)}:{time_match.group(6)}:{time_match.group(7)},{time_match.group(8)}"
                        
                        reconstructed["blocks"].append({
                            "index": block["index"] or len(reconstructed["blocks"]) + 1,
                            "start": start_time,
                            "end": end_time,
                            "text": '\n'.join(block["content"])
                        })
            
            self.logger.info(f"备用解析器成功修复了{len(reconstructed['blocks'])}个字幕块")
            self.stats["fixed"] += 1
            return reconstructed
            
        except Exception as e:
            self.logger.error(f"备用解析器失败: {str(e)}")
            self.stats["failed"] += 1
            return malformed_data
    
    def get_recovery_stats(self) -> Dict[str, int]:
        """获取修复统计信息
        
        Returns:
            包含修复统计的字典
        """
        return self.stats


def check_and_repair_srt(file_path: str, encoding: str = 'utf-8') -> Tuple[str, Dict[str, int]]:
    """检查并修复SRT文件
    
    Args:
        file_path: SRT文件路径
        encoding: 文件编码
        
    Returns:
        修复后的文本内容和统计信息元组
    """
    doctor = ParserDoctor()
    
    try:
        # 尝试读取文件
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        encodings = ['utf-8-sig', 'gbk', 'latin1', 'big5']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                logger.info(f"成功使用{enc}编码读取文件")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise FileOperationError(f"无法以任何编码读取文件: {file_path}", file_path=file_path)
    
    # 修复常见错误
    fixed_content = doctor.fix_common_errors(content)
    
    # 获取统计信息
    stats = doctor.get_recovery_stats()
    
    return fixed_content, stats


def save_repaired_srt(file_path: str, content: str, suffix: str = '_fixed') -> str:
    """保存修复后的SRT文件
    
    Args:
        file_path: 原始文件路径
        content: 修复后的内容
        suffix: 文件名后缀
        
    Returns:
        保存后的文件路径
    """
    path = Path(file_path)
    new_path = path.with_name(f"{path.stem}{suffix}{path.suffix}")
    
    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"修复后的文件已保存至: {new_path}")
    return str(new_path) 