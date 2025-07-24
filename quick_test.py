#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 快速测试脚本
用于快速验证系统基本功能，适合开发过程中的快速检查
"""

import sys
import time
import psutil
import importlib
from pathlib import Path

class QuickTest:
    """快速测试类"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def test(self, name: str, test_func):
        """执行单个测试"""
        self.total += 1
        print(f"🧪 {name}...", end=" ")
        
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"✅ 通过 ({duration:.3f}s)")
                self.passed += 1
            else:
                print(f"❌ 失败 ({duration:.3f}s)")
                self.failed += 1
        except Exception as e:
            print(f"💥 异常: {e}")
            self.failed += 1
    
    def summary(self):
        """显示测试摘要"""
        print(f"\n📊 快速测试结果:")
        print(f"  总测试: {self.total}")
        print(f"  通过: {self.passed}")
        print(f"  失败: {self.failed}")
        print(f"  成功率: {(self.passed/self.total*100):.1f}%")
        
        if self.failed == 0:
            print("🎉 所有快速测试通过！")
        else:
            print("⚠️  存在失败的测试项目")

def test_python_version():
    """测试Python版本"""
    version = sys.version_info
    return version.major == 3 and version.minor >= 8

def test_memory_available():
    """测试可用内存"""
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    return memory_gb >= 4.0

def test_disk_space():
    """测试磁盘空间"""
    disk = psutil.disk_usage('.')
    disk_gb = disk.free / (1024**3)
    return disk_gb >= 5.0

def test_core_imports():
    """测试核心依赖导入"""
    required_packages = [
        'torch', 'transformers', 'numpy', 'pandas', 
        'psutil', 'loguru', 'yaml', 'requests'
    ]
    
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            else:
                importlib.import_module(package)
        except ImportError:
            return False
    return True

def test_ui_imports():
    """测试UI依赖导入"""
    try:
        import PyQt6
        return True
    except ImportError:
        return False

def test_cv_imports():
    """测试计算机视觉依赖"""
    try:
        import cv2
        from PIL import Image
        return True
    except ImportError:
        return False

def test_nlp_imports():
    """测试NLP依赖"""
    try:
        import jieba
        import langdetect
        return True
    except ImportError:
        return False

def test_srt_parsing():
    """测试SRT解析功能"""
    sample_srt = """1
00:00:01,000 --> 00:00:03,000
测试字幕内容

2
00:00:04,000 --> 00:00:06,000
第二段字幕
"""
    
    try:
        # 简单的SRT解析测试
        blocks = sample_srt.strip().split('\n\n')
        segments = []
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3 and ' --> ' in lines[1]:
                segments.append({
                    'index': lines[0],
                    'time': lines[1],
                    'text': '\n'.join(lines[2:])
                })
        
        return len(segments) == 2
    except:
        return False

def test_language_detection():
    """测试语言检测功能"""
    try:
        zh_text = "这是中文测试文本"
        en_text = "This is English test text"
        
        # 简单的语言检测
        zh_has_chinese = any('\u4e00' <= char <= '\u9fff' for char in zh_text)
        en_has_chinese = any('\u4e00' <= char <= '\u9fff' for char in en_text)
        
        return zh_has_chinese and not en_has_chinese
    except:
        return False

def test_time_conversion():
    """测试时间转换功能"""
    try:
        def srt_time_to_seconds(time_str):
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000
        
        # 测试几个时间转换
        test_cases = [
            ("00:00:01,000", 1.0),
            ("00:01:30,500", 90.5),
            ("01:00:00,000", 3600.0)
        ]
        
        for time_str, expected in test_cases:
            result = srt_time_to_seconds(time_str)
            if abs(result - expected) > 0.001:
                return False
        
        return True
    except:
        return False

def test_json_handling():
    """测试JSON处理"""
    try:
        import json
        
        test_data = {
            "model": "qwen2.5-7b",
            "language": "zh",
            "segments": [
                {"start": 1.0, "end": 3.0, "text": "测试"}
            ]
        }
        
        # 序列化和反序列化
        json_str = json.dumps(test_data, ensure_ascii=False)
        parsed_data = json.loads(json_str)
        
        return parsed_data["model"] == "qwen2.5-7b"
    except:
        return False

def test_file_operations():
    """测试文件操作"""
    try:
        import tempfile
        import os
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.srt') as f:
            f.write("1\n00:00:01,000 --> 00:00:03,000\n测试内容\n")
            temp_file = f.name
        
        # 读取文件
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理
        os.unlink(temp_file)
        
        return "测试内容" in content
    except:
        return False

def test_memory_usage():
    """测试当前内存使用"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        # 内存使用应该在合理范围内（小于1GB）
        return memory_mb < 1024
    except:
        return False

def test_cpu_detection():
    """测试CPU检测"""
    try:
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return cpu_count > 0 and cpu_percent >= 0
    except:
        return False

def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster 快速测试")
    print("=" * 50)
    print("快速验证系统基本功能和依赖项")
    print()
    
    tester = QuickTest()
    
    # 系统环境测试
    print("🖥️  系统环境测试:")
    tester.test("Python版本检查", test_python_version)
    tester.test("内存容量检查", test_memory_available)
    tester.test("磁盘空间检查", test_disk_space)
    tester.test("CPU检测", test_cpu_detection)
    tester.test("当前内存使用", test_memory_usage)
    
    print()
    
    # 依赖项测试
    print("📦 依赖项测试:")
    tester.test("核心依赖导入", test_core_imports)
    tester.test("UI依赖导入", test_ui_imports)
    tester.test("计算机视觉依赖", test_cv_imports)
    tester.test("NLP依赖导入", test_nlp_imports)
    
    print()
    
    # 功能测试
    print("⚙️  基本功能测试:")
    tester.test("SRT解析功能", test_srt_parsing)
    tester.test("语言检测功能", test_language_detection)
    tester.test("时间转换功能", test_time_conversion)
    tester.test("JSON处理功能", test_json_handling)
    tester.test("文件操作功能", test_file_operations)
    
    print()
    
    # 显示结果
    tester.summary()
    
    # 给出建议
    if tester.failed == 0:
        print("\n💡 建议: 系统状态良好，可以运行完整测试套件")
        print("   运行命令: python run_all_tests.py")
    elif tester.failed <= 2:
        print("\n💡 建议: 存在少量问题，建议先修复后再运行完整测试")
    else:
        print("\n💡 建议: 存在较多问题，请先检查环境配置和依赖安装")
        print("   参考文档: README.md 或 INSTALLATION.md")
    
    return tester.failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
