#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 爆款SRT解析器端到端测试

此模块专门测试爆款SRT文件的解析功能，验证从SRT文件到视频片段提取的完整流程。
包括时间码解析、片段边界检测、格式验证等关键功能。
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.srt_parser import SRTParser
from src.core.viral_srt_processor import ViralSRTProcessor
from src.utils.log_handler import LogHandler
from src.utils.file_checker import FileChecker

logger = logging.getLogger(__name__)


@dataclass
class SRTParsingResult:
    """SRT解析测试结果数据类"""
    test_name: str
    srt_file_path: str
    parsing_success: bool
    total_segments: int
    valid_segments: int
    invalid_segments: int
    parsing_time: float
    total_duration: float
    segment_details: List[Dict[str, Any]]
    format_errors: List[str]
    timecode_errors: List[str]
    encoding_issues: List[str]
    success: bool
    error_message: Optional[str] = None


class ViralSRTParserTester:
    """爆款SRT解析器测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化SRT解析器测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.srt_parser = SRTParser()
        self.viral_srt_processor = ViralSRTProcessor()
        self.file_checker = FileChecker()
        
        # 测试结果存储
        self.test_results = []
        
        # 质量标准
        self.quality_standards = self.config.get('quality_standards', {})
        self.timecode_precision = self.quality_standards.get('functional', {}).get('timecode_precision_seconds', 0.1)
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp/e2e'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/end_to_end_validation/e2e_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'quality_standards': {'functional': {'timecode_precision_seconds': 0.1}},
                'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp/e2e'}
            }
    
    def test_srt_format_validation(self, srt_file_path: str) -> SRTParsingResult:
        """
        测试SRT文件格式验证
        
        Args:
            srt_file_path: SRT文件路径
            
        Returns:
            SRTParsingResult: 解析测试结果
        """
        test_name = "srt_format_validation"
        start_time = time.time()
        
        try:
            # 检查文件存在性
            if not os.path.exists(srt_file_path):
                raise FileNotFoundError(f"SRT文件不存在: {srt_file_path}")
            
            # 检查文件完整性
            if not self.file_checker.check_file_integrity(srt_file_path):
                raise ValueError(f"SRT文件损坏或无法访问: {srt_file_path}")
            
            # 检查文件编码
            encoding_result = self._detect_file_encoding(srt_file_path)
            encoding_issues = []
            if encoding_result['encoding'] != 'utf-8':
                encoding_issues.append(f"文件编码为{encoding_result['encoding']}，建议使用UTF-8")
            
            # 读取文件内容
            with open(srt_file_path, 'r', encoding=encoding_result['encoding']) as f:
                content = f.read()
            
            # 验证SRT格式
            format_errors = self._validate_srt_format(content)
            
            # 解析SRT内容
            segments = self.srt_parser.parse(srt_file_path)
            
            # 验证解析结果
            parsing_success = len(segments) > 0 and len(format_errors) == 0
            valid_segments = 0
            invalid_segments = 0
            segment_details = []
            timecode_errors = []
            
            for i, segment in enumerate(segments):
                segment_valid = True
                segment_detail = {
                    'index': i + 1,
                    'start_time': segment.get('start_time', ''),
                    'end_time': segment.get('end_time', ''),
                    'text': segment.get('text', ''),
                    'duration': 0.0,
                    'valid': True,
                    'errors': []
                }
                
                # 验证时间码格式
                start_time_valid = self._validate_timecode_format(segment.get('start_time', ''))
                end_time_valid = self._validate_timecode_format(segment.get('end_time', ''))
                
                if not start_time_valid:
                    segment_detail['errors'].append(f"开始时间码格式无效: {segment.get('start_time', '')}")
                    segment_valid = False
                
                if not end_time_valid:
                    segment_detail['errors'].append(f"结束时间码格式无效: {segment.get('end_time', '')}")
                    segment_valid = False
                
                # 计算片段时长
                if start_time_valid and end_time_valid:
                    start_seconds = self._timecode_to_seconds(segment.get('start_time', ''))
                    end_seconds = self._timecode_to_seconds(segment.get('end_time', ''))
                    
                    if start_seconds is not None and end_seconds is not None:
                        duration = end_seconds - start_seconds
                        segment_detail['duration'] = duration
                        
                        if duration <= 0:
                            segment_detail['errors'].append(f"片段时长无效: {duration}秒")
                            segment_valid = False
                    else:
                        segment_detail['errors'].append("无法计算片段时长")
                        segment_valid = False
                
                # 验证文本内容
                if not segment.get('text', '').strip():
                    segment_detail['errors'].append("字幕文本为空")
                    segment_valid = False
                
                segment_detail['valid'] = segment_valid
                segment_details.append(segment_detail)
                
                if segment_valid:
                    valid_segments += 1
                else:
                    invalid_segments += 1
                    timecode_errors.extend(segment_detail['errors'])
            
            # 计算总时长
            total_duration = 0.0
            if segment_details:
                last_segment = segment_details[-1]
                if last_segment['valid']:
                    end_seconds = self._timecode_to_seconds(last_segment['end_time'])
                    if end_seconds is not None:
                        total_duration = end_seconds
            
            parsing_time = time.time() - start_time
            
            result = SRTParsingResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                parsing_success=parsing_success,
                total_segments=len(segments),
                valid_segments=valid_segments,
                invalid_segments=invalid_segments,
                parsing_time=parsing_time,
                total_duration=total_duration,
                segment_details=segment_details,
                format_errors=format_errors,
                timecode_errors=timecode_errors,
                encoding_issues=encoding_issues,
                success=parsing_success and invalid_segments == 0
            )
            
            self.test_results.append(result)
            self.logger.info(f"SRT格式验证完成: {srt_file_path}, 有效片段: {valid_segments}/{len(segments)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"SRT格式验证失败: {srt_file_path}, 错误: {str(e)}")
            return SRTParsingResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                parsing_success=False,
                total_segments=0,
                valid_segments=0,
                invalid_segments=0,
                parsing_time=time.time() - start_time,
                total_duration=0.0,
                segment_details=[],
                format_errors=[],
                timecode_errors=[],
                encoding_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def test_timecode_precision(self, srt_file_path: str, reference_video_duration: float = None) -> SRTParsingResult:
        """
        测试时间码精度
        
        Args:
            srt_file_path: SRT文件路径
            reference_video_duration: 参考视频时长（秒）
            
        Returns:
            SRTParsingResult: 测试结果
        """
        test_name = "timecode_precision"
        start_time = time.time()
        
        try:
            # 首先进行基础格式验证
            format_result = self.test_srt_format_validation(srt_file_path)
            if not format_result.parsing_success:
                return format_result
            
            # 解析SRT文件
            segments = self.srt_parser.parse(srt_file_path)
            
            # 精度验证
            precision_errors = []
            overlap_errors = []
            gap_errors = []
            boundary_errors = []
            
            # 检查片段间的时间关系
            for i in range(len(segments)):
                current_segment = segments[i]
                current_start = self._timecode_to_seconds(current_segment.get('start_time', ''))
                current_end = self._timecode_to_seconds(current_segment.get('end_time', ''))
                
                if current_start is None or current_end is None:
                    continue
                
                # 检查片段内部时间逻辑
                if current_end <= current_start:
                    precision_errors.append(f"片段{i+1}: 结束时间不晚于开始时间")
                
                # 检查与下一个片段的关系
                if i < len(segments) - 1:
                    next_segment = segments[i + 1]
                    next_start = self._timecode_to_seconds(next_segment.get('start_time', ''))
                    
                    if next_start is not None:
                        # 检查重叠
                        if current_end > next_start + self.timecode_precision:
                            overlap_errors.append(f"片段{i+1}与片段{i+2}重叠: {current_end - next_start:.3f}秒")
                        
                        # 检查间隙
                        gap = next_start - current_end
                        if gap > 300:  # 超过5分钟的间隙
                            gap_errors.append(f"片段{i+1}与片段{i+2}间隙过大: {gap:.1f}秒")
                
                # 检查边界条件
                if current_start < 0:
                    boundary_errors.append(f"片段{i+1}: 开始时间为负数")
                
                if reference_video_duration and current_end > reference_video_duration:
                    boundary_errors.append(f"片段{i+1}: 结束时间超出视频时长")
            
            # 计算精度统计
            all_errors = precision_errors + overlap_errors + gap_errors + boundary_errors
            precision_success = len(all_errors) == 0
            
            # 更新结果
            result = format_result
            result.test_name = test_name
            result.timecode_errors.extend(all_errors)
            result.success = precision_success and result.success
            result.parsing_time = time.time() - start_time
            
            # 添加精度分析详情
            result.precision_analysis = {
                'overlap_count': len(overlap_errors),
                'gap_count': len(gap_errors),
                'boundary_errors': len(boundary_errors),
                'precision_errors': len(precision_errors),
                'total_errors': len(all_errors)
            }
            
            self.test_results.append(result)
            self.logger.info(f"时间码精度验证完成: {srt_file_path}, 精度错误: {len(all_errors)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"时间码精度验证失败: {srt_file_path}, 错误: {str(e)}")
            return SRTParsingResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                parsing_success=False,
                total_segments=0,
                valid_segments=0,
                invalid_segments=0,
                parsing_time=time.time() - start_time,
                total_duration=0.0,
                segment_details=[],
                format_errors=[],
                timecode_errors=[],
                encoding_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def test_segment_extraction_logic(self, srt_file_path: str) -> SRTParsingResult:
        """
        测试片段提取逻辑
        
        Args:
            srt_file_path: SRT文件路径
            
        Returns:
            SRTParsingResult: 测试结果
        """
        test_name = "segment_extraction_logic"
        start_time = time.time()
        
        try:
            # 解析SRT文件
            segments = self.srt_parser.parse(srt_file_path)
            
            # 使用病毒式SRT处理器提取片段信息
            extraction_result = self.viral_srt_processor.extract_segments(srt_file_path)
            
            # 验证提取逻辑
            extraction_errors = []
            
            # 检查提取的片段数量
            if len(extraction_result.segments) != len(segments):
                extraction_errors.append(f"提取片段数量不匹配: 期望{len(segments)}, 实际{len(extraction_result.segments)}")
            
            # 验证每个片段的提取信息
            for i, (original_segment, extracted_segment) in enumerate(zip(segments, extraction_result.segments)):
                # 验证时间码转换
                original_start = self._timecode_to_seconds(original_segment.get('start_time', ''))
                original_end = self._timecode_to_seconds(original_segment.get('end_time', ''))
                
                extracted_start = extracted_segment.get('start_seconds')
                extracted_end = extracted_segment.get('end_seconds')
                
                if original_start is not None and extracted_start is not None:
                    time_diff = abs(original_start - extracted_start)
                    if time_diff > self.timecode_precision:
                        extraction_errors.append(f"片段{i+1}开始时间转换误差: {time_diff:.3f}秒")
                
                if original_end is not None and extracted_end is not None:
                    time_diff = abs(original_end - extracted_end)
                    if time_diff > self.timecode_precision:
                        extraction_errors.append(f"片段{i+1}结束时间转换误差: {time_diff:.3f}秒")
                
                # 验证片段元数据
                if not extracted_segment.get('text'):
                    extraction_errors.append(f"片段{i+1}文本内容丢失")
                
                if extracted_segment.get('duration', 0) <= 0:
                    extraction_errors.append(f"片段{i+1}时长计算错误")
            
            # 验证片段排序
            for i in range(len(extraction_result.segments) - 1):
                current_end = extraction_result.segments[i].get('end_seconds', 0)
                next_start = extraction_result.segments[i + 1].get('start_seconds', 0)
                
                if current_end > next_start:
                    extraction_errors.append(f"片段{i+1}和{i+2}时间顺序错误")
            
            extraction_success = len(extraction_errors) == 0
            
            result = SRTParsingResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                parsing_success=True,
                total_segments=len(segments),
                valid_segments=len(extraction_result.segments),
                invalid_segments=len(segments) - len(extraction_result.segments),
                parsing_time=time.time() - start_time,
                total_duration=extraction_result.total_duration,
                segment_details=[],
                format_errors=[],
                timecode_errors=extraction_errors,
                encoding_issues=[],
                success=extraction_success
            )
            
            # 添加提取详情
            result.extraction_details = {
                'extracted_segments': extraction_result.segments,
                'total_extracted_duration': extraction_result.total_duration,
                'extraction_metadata': extraction_result.metadata
            }
            
            self.test_results.append(result)
            self.logger.info(f"片段提取逻辑验证完成: {srt_file_path}, 提取错误: {len(extraction_errors)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"片段提取逻辑验证失败: {srt_file_path}, 错误: {str(e)}")
            return SRTParsingResult(
                test_name=test_name,
                srt_file_path=srt_file_path,
                parsing_success=False,
                total_segments=0,
                valid_segments=0,
                invalid_segments=0,
                parsing_time=time.time() - start_time,
                total_duration=0.0,
                segment_details=[],
                format_errors=[],
                timecode_errors=[],
                encoding_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def _detect_file_encoding(self, file_path: str) -> Dict[str, Any]:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            result = chardet.detect(raw_data)
            return {
                'encoding': result.get('encoding', 'utf-8').lower(),
                'confidence': result.get('confidence', 0.0)
            }
        except ImportError:
            # 如果没有chardet，尝试常见编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read()
                    return {'encoding': encoding, 'confidence': 1.0}
                except UnicodeDecodeError:
                    continue
            return {'encoding': 'utf-8', 'confidence': 0.5}
    
    def _validate_srt_format(self, content: str) -> List[str]:
        """验证SRT格式"""
        errors = []
        
        # 检查基本结构
        if not content.strip():
            errors.append("SRT文件为空")
            return errors
        
        # 分割为块
        blocks = content.strip().split('\n\n')
        
        for i, block in enumerate(blocks):
            lines = block.strip().split('\n')
            
            if len(lines) < 3:
                errors.append(f"块{i+1}: 格式不完整，至少需要3行")
                continue
            
            # 验证序号
            try:
                seq_num = int(lines[0].strip())
                if seq_num != i + 1:
                    errors.append(f"块{i+1}: 序号不连续，期望{i+1}，实际{seq_num}")
            except ValueError:
                errors.append(f"块{i+1}: 序号格式错误")
            
            # 验证时间码行
            if '-->' not in lines[1]:
                errors.append(f"块{i+1}: 时间码行格式错误")
            
            # 验证字幕文本
            if len(lines) < 3 or not any(line.strip() for line in lines[2:]):
                errors.append(f"块{i+1}: 缺少字幕文本")
        
        return errors
    
    def _validate_timecode_format(self, timecode: str) -> bool:
        """验证时间码格式"""
        # SRT时间码格式：HH:MM:SS,mmm
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, timecode.strip()))
    
    def _timecode_to_seconds(self, timecode: str) -> Optional[float]:
        """将时间码转换为秒数"""
        try:
            if not self._validate_timecode_format(timecode):
                return None
            
            time_part, ms_part = timecode.strip().split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        except (ValueError, IndexError):
            return None


class TestViralSRTParser(unittest.TestCase):
    """爆款SRT解析器测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = ViralSRTParserTester()
        cls.test_srt_file = cls._create_test_srt_file()
    
    @classmethod
    def _create_test_srt_file(cls) -> str:
        """创建测试SRT文件"""
        test_content = """1
00:00:10,000 --> 00:00:15,000
这是第一个测试片段

2
00:00:20,000 --> 00:00:25,000
这是第二个测试片段

3
00:00:30,000 --> 00:00:35,000
这是第三个测试片段
"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8')
        temp_file.write(test_content)
        temp_file.close()
        
        return temp_file.name
    
    def test_srt_format_validation(self):
        """测试SRT格式验证"""
        result = self.tester.test_srt_format_validation(self.test_srt_file)
        
        self.assertTrue(result.parsing_success, "SRT格式验证应该成功")
        self.assertEqual(result.total_segments, 3, "应该解析出3个片段")
        self.assertEqual(result.valid_segments, 3, "所有片段都应该有效")
        self.assertEqual(len(result.format_errors), 0, "不应该有格式错误")
    
    def test_timecode_precision(self):
        """测试时间码精度"""
        result = self.tester.test_timecode_precision(self.test_srt_file, reference_video_duration=60.0)
        
        self.assertTrue(result.success, "时间码精度验证应该成功")
        self.assertEqual(len(result.timecode_errors), 0, "不应该有时间码错误")
    
    def test_segment_extraction_logic(self):
        """测试片段提取逻辑"""
        result = self.tester.test_segment_extraction_logic(self.test_srt_file)
        
        self.assertTrue(result.success, "片段提取逻辑验证应该成功")
        self.assertEqual(result.valid_segments, 3, "应该成功提取3个片段")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(cls.test_srt_file):
            os.unlink(cls.test_srt_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
