"""
VisionAI-ClipsMaster 时间轴解析器单元测试

此模块包含对时间码解析和转换功能的全面测试，
确保在各种格式和边界条件下时间码处理的正确性。
"""

import unittest
import sys
import os
from datetime import timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parsers.timecode_parser import (
    TimeCode, 
    TimeCodeError, 
    parse_timecode, 
    parse_timecode_range, 
    adjust_timecode,
    calculate_duration
)


class TestTimeCode(unittest.TestCase):
    """测试TimeCode类的基础功能"""
    
    def test_initialization(self):
        """测试初始化和字段验证"""
        # 正常初始化
        tc = TimeCode(hours=1, minutes=30, seconds=45, milliseconds=500)
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
        
        # 默认值初始化
        tc = TimeCode()
        self.assertEqual(tc.hours, 0)
        self.assertEqual(tc.minutes, 0)
        self.assertEqual(tc.seconds, 0)
        self.assertEqual(tc.milliseconds, 0)
        
        # 字段验证 - 小时超范围
        with self.assertRaises(TimeCodeError):
            TimeCode(hours=100)
        
        # 字段验证 - 分钟超范围
        with self.assertRaises(TimeCodeError):
            TimeCode(minutes=60)
        
        # 字段验证 - 秒超范围
        with self.assertRaises(TimeCodeError):
            TimeCode(seconds=60)
        
        # 字段验证 - 毫秒超范围
        with self.assertRaises(TimeCodeError):
            TimeCode(milliseconds=1000)
    
    def test_conversion_methods(self):
        """测试时间码转换方法"""
        tc = TimeCode(hours=1, minutes=30, seconds=45, milliseconds=500)
        
        # 转换为毫秒
        self.assertEqual(tc.to_milliseconds(), 5445500)
        
        # 转换为秒
        self.assertEqual(tc.to_seconds(), 5445.5)
        
        # 转换为SRT格式
        self.assertEqual(tc.to_srt_format(), "01:30:45,500")
        
        # 转换为标准格式
        self.assertEqual(tc.to_standard_format(), "01:30:45.500")
        
        # 转换为帧率格式 (25fps)
        self.assertEqual(tc.to_frame_format(), "01:30:45:12")
        
        # 转换为帧率格式 (30fps)
        self.assertEqual(tc.to_frame_format(fps=30.0), "01:30:45:15")
    
    def test_arithmetic_operations(self):
        """测试时间码的算术运算"""
        tc1 = TimeCode(hours=1, minutes=0, seconds=0, milliseconds=0)
        tc2 = TimeCode(minutes=30, seconds=0, milliseconds=0)
        
        # 加法 - 时间码 + 时间码
        result = tc1 + tc2
        self.assertEqual(result.hours, 1)
        self.assertEqual(result.minutes, 30)
        self.assertEqual(result.seconds, 0)
        self.assertEqual(result.milliseconds, 0)
        
        # 加法 - 时间码 + 毫秒
        result = tc1 + 5000
        self.assertEqual(result.hours, 1)
        self.assertEqual(result.minutes, 0)
        self.assertEqual(result.seconds, 5)
        self.assertEqual(result.milliseconds, 0)
        
        # 减法 - 时间码 - 时间码
        result = tc1 - tc2
        self.assertEqual(result.hours, 0)
        self.assertEqual(result.minutes, 30)
        self.assertEqual(result.seconds, 0)
        self.assertEqual(result.milliseconds, 0)
        
        # 减法 - 时间码 - 毫秒
        result = tc1 - 5000
        self.assertEqual(result.hours, 0)
        self.assertEqual(result.minutes, 59)
        self.assertEqual(result.seconds, 55)
        self.assertEqual(result.milliseconds, 0)
        
        # 溢出检查 - 负结果
        with self.assertRaises(TimeCodeError):
            TimeCode() - 1000
    
    def test_comparison_operations(self):
        """测试时间码的比较运算"""
        tc1 = TimeCode(hours=1, minutes=0, seconds=0)
        tc2 = TimeCode(hours=1, minutes=30, seconds=0)
        tc3 = TimeCode(hours=1, minutes=0, seconds=0)
        
        # 等于
        self.assertEqual(tc1, tc3)
        self.assertNotEqual(tc1, tc2)
        
        # 小于/大于
        self.assertTrue(tc1 < tc2)
        self.assertTrue(tc2 > tc1)
        
        # 小于等于/大于等于
        self.assertTrue(tc1 <= tc3)
        self.assertTrue(tc1 <= tc2)
        self.assertTrue(tc2 >= tc1)
        self.assertTrue(tc3 >= tc1)
        
        # 与毫秒比较
        self.assertTrue(tc1 > 3000000)  # 1小时 > 50分钟
        self.assertTrue(tc1 < 7200000)  # 1小时 < 2小时
    
    def test_class_methods(self):
        """测试类方法"""
        # 从毫秒创建
        tc = TimeCode.from_milliseconds(5445500)
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
        
        # 从秒创建
        tc = TimeCode.from_seconds(5445.5)
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
        
        # 负值检查
        with self.assertRaises(TimeCodeError):
            TimeCode.from_milliseconds(-1000)
        
        with self.assertRaises(TimeCodeError):
            TimeCode.from_seconds(-10.5)


class TestTimecodeParser(unittest.TestCase):
    """测试时间码解析函数"""
    
    def test_parse_srt_format(self):
        """测试解析SRT格式时间码"""
        tc = parse_timecode("01:30:45,500")
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
    
    def test_parse_standard_format(self):
        """测试解析标准格式时间码"""
        tc = parse_timecode("01:30:45.500")
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
    
    def test_parse_frame_format(self):
        """测试解析帧率格式时间码"""
        tc = parse_timecode("01:30:45:12")  # 25fps, 12帧 ≈ 480ms
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 480)
    
    def test_parse_timestamp_format(self):
        """测试解析时间戳格式"""
        tc = parse_timecode("5445.5")  # 5445.5秒
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
        
        # 测试不同精度的小数部分
        tc = parse_timecode("5445.5")  # 一位小数
        self.assertEqual(tc.milliseconds, 500)
        
        tc = parse_timecode("5445.50")  # 两位小数
        self.assertEqual(tc.milliseconds, 500)
        
        tc = parse_timecode("5445.500")  # 三位小数
        self.assertEqual(tc.milliseconds, 500)
        
        tc = parse_timecode("5445.5000")  # 四位小数
        self.assertEqual(tc.milliseconds, 500)
    
    def test_parse_milliseconds_format(self):
        """测试解析纯毫秒格式"""
        tc = parse_timecode("5445500")  # 5445500毫秒
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
    
    def test_parse_range_format(self):
        """测试从范围格式中提取时间码"""
        tc = parse_timecode("01:30:45,500 --> 01:35:00,000")
        self.assertEqual(tc.hours, 1)
        self.assertEqual(tc.minutes, 30)
        self.assertEqual(tc.seconds, 45)
        self.assertEqual(tc.milliseconds, 500)
    
    def test_invalid_format(self):
        """测试无效格式"""
        with self.assertRaises(TimeCodeError):
            parse_timecode("invalid")
        
        with self.assertRaises(TimeCodeError):
            parse_timecode("1:30:45,500")  # 小时不足两位
        
        with self.assertRaises(TimeCodeError):
            parse_timecode("01:3:45,500")  # 分钟不足两位


class TestTimecodeRangeParser(unittest.TestCase):
    """测试时间码范围解析函数"""
    
    def test_parse_srt_range(self):
        """测试解析SRT格式时间码范围"""
        result = parse_timecode_range("01:30:45,500 --> 01:35:00,000")
        start = result['start']
        end = result['end']
        
        self.assertEqual(start.hours, 1)
        self.assertEqual(start.minutes, 30)
        self.assertEqual(start.seconds, 45)
        self.assertEqual(start.milliseconds, 500)
        
        self.assertEqual(end.hours, 1)
        self.assertEqual(end.minutes, 35)
        self.assertEqual(end.seconds, 0)
        self.assertEqual(end.milliseconds, 0)
    
    def test_parse_standard_range(self):
        """测试解析标准格式时间码范围"""
        result = parse_timecode_range("01:30:45.500 --> 01:35:00.000")
        start = result['start']
        end = result['end']
        
        self.assertEqual(start.hours, 1)
        self.assertEqual(start.minutes, 30)
        self.assertEqual(start.seconds, 45)
        self.assertEqual(start.milliseconds, 500)
        
        self.assertEqual(end.hours, 1)
        self.assertEqual(end.minutes, 35)
        self.assertEqual(end.seconds, 0)
        self.assertEqual(end.milliseconds, 0)
    
    def test_invalid_range(self):
        """测试无效范围格式"""
        with self.assertRaises(TimeCodeError):
            parse_timecode_range("01:30:45,500 -> 01:35:00,000")  # 箭头不正确
        
        with self.assertRaises(TimeCodeError):
            parse_timecode_range("invalid")
        
        with self.assertRaises(TimeCodeError):
            parse_timecode_range("01:30:45,500 01:35:00,000")  # 缺少箭头


class TestAdditionalFunctions(unittest.TestCase):
    """测试其他辅助函数"""
    
    def test_adjust_timecode(self):
        """测试时间码调整"""
        tc = TimeCode(hours=1, minutes=0, seconds=0)
        
        # 正向调整
        adjusted = adjust_timecode(tc, 5000)  # +5秒
        self.assertEqual(adjusted.hours, 1)
        self.assertEqual(adjusted.minutes, 0)
        self.assertEqual(adjusted.seconds, 5)
        
        # 负向调整
        adjusted = adjust_timecode(tc, -30000)  # -30秒
        self.assertEqual(adjusted.hours, 0)
        self.assertEqual(adjusted.minutes, 59)
        self.assertEqual(adjusted.seconds, 30)
        
        # 调整为负值应截断为0
        adjusted = adjust_timecode(TimeCode(seconds=10), -20000)
        self.assertEqual(adjusted.to_milliseconds(), 0)
    
    def test_calculate_duration(self):
        """测试持续时间计算"""
        start = TimeCode(hours=1, minutes=0, seconds=0)
        end = TimeCode(hours=1, minutes=30, seconds=0)
        
        # 普通情况
        duration = calculate_duration(start, end)
        self.assertEqual(duration, 1800000)  # 30分钟 = 1800000毫秒
        
        # 边界情况 - 相同时间
        duration = calculate_duration(start, start)
        self.assertEqual(duration, 0)
        
        # 结束时间早于开始时间
        with self.assertRaises(TimeCodeError):
            calculate_duration(end, start)


if __name__ == '__main__':
    unittest.main() 