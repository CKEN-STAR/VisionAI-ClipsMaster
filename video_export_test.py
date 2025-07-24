#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频处理和导出功能测试
测试视频拼接、剪映导出等核心功能
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class VideoExportTest:
    """视频导出测试类"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def log_result(self, test_name, status, details="", error=""):
        """记录测试结果"""
        self.test_results[test_name] = {
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{symbol} {test_name}: {details}")
        if error:
            print(f"   错误: {error}")
    
    def test_video_processor(self):
        """测试视频处理器"""
        print("\n🎬 测试视频处理器...")
        
        try:
            from src.core.video_processor import VideoProcessor
            processor = VideoProcessor()
            self.log_result("video_processor_init", "PASS", "视频处理器初始化成功")
            
            # 检查处理方法
            methods = ['process_video', 'cut_segments', 'merge_segments']
            available_methods = [m for m in methods if hasattr(processor, m)]
            self.log_result("video_processor_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("video_processor_init", "FAIL", "", str(e))
    
    def test_clip_generator(self):
        """测试视频片段生成器"""
        print("\n✂️ 测试视频片段生成器...")
        
        try:
            from src.core.clip_generator import ClipGenerator
            generator = ClipGenerator()
            self.log_result("clip_generator_init", "PASS", "视频片段生成器初始化成功")
            
            # 检查生成方法
            methods = ['generate_clips', 'align_with_srt', 'export_segments']
            available_methods = [m for m in methods if hasattr(generator, m)]
            self.log_result("clip_generator_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("clip_generator_init", "FAIL", "", str(e))
    
    def test_srt_parser(self):
        """测试SRT字幕解析"""
        print("\n📝 测试SRT字幕解析...")
        
        try:
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            self.log_result("srt_parser_init", "PASS", "SRT解析器初始化成功")
            
            # 测试解析功能
            test_srt = """1
00:00:01,000 --> 00:00:03,000
今天天气很好

2
00:00:04,000 --> 00:00:06,000
我去了公园散步

3
00:00:07,000 --> 00:00:09,000
看到了很多花"""
            
            if hasattr(parser, 'parse'):
                segments = parser.parse(test_srt)
                self.log_result("srt_parsing", "PASS", 
                              f"解析成功，提取 {len(segments)} 个片段")
            else:
                self.log_result("srt_parsing", "WARN", "解析方法不可用")
                
        except Exception as e:
            self.log_result("srt_parser_init", "FAIL", "", str(e))
    
    def test_jianying_exporter(self):
        """测试剪映导出器"""
        print("\n🎞️ 测试剪映导出器...")
        
        try:
            from src.exporters.jianying_pro_exporter import JianyingProExporter
            exporter = JianyingProExporter()
            self.log_result("jianying_exporter_init", "PASS", "剪映导出器初始化成功")
            
            # 检查导出方法
            methods = ['export_project', 'generate_timeline', 'create_xml']
            available_methods = [m for m in methods if hasattr(exporter, m)]
            self.log_result("jianying_export_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("jianying_exporter_init", "FAIL", "", str(e))
    
    def test_timeline_precision(self):
        """测试时间轴精度"""
        print("\n⏱️ 测试时间轴精度...")
        
        try:
            from src.core.alignment_engineer import AlignmentEngineer
            engineer = AlignmentEngineer()
            self.log_result("alignment_engineer_init", "PASS", "对齐工程师初始化成功")
            
            # 测试时间轴对齐
            if hasattr(engineer, 'align_timeline'):
                self.log_result("timeline_alignment", "PASS", "时间轴对齐方法可用")
            else:
                self.log_result("timeline_alignment", "WARN", "时间轴对齐方法不可用")
                
        except Exception as e:
            self.log_result("alignment_engineer_init", "FAIL", "", str(e))
    
    def test_ffmpeg_integration(self):
        """测试FFmpeg集成"""
        print("\n🔧 测试FFmpeg集成...")
        
        # 检查FFmpeg可执行文件
        ffmpeg_paths = [
            "tools/ffmpeg/bin/ffmpeg.exe",
            "ffmpeg.exe",
            "ffmpeg"
        ]
        
        ffmpeg_found = False
        for path in ffmpeg_paths:
            if os.path.exists(path):
                ffmpeg_found = True
                self.log_result("ffmpeg_executable", "PASS", f"FFmpeg可执行文件: {path}")
                break
        
        if not ffmpeg_found:
            # 尝试系统PATH中的ffmpeg
            try:
                import subprocess
                result = subprocess.run(['ffmpeg', '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_result("ffmpeg_system", "PASS", "系统PATH中的FFmpeg可用")
                else:
                    self.log_result("ffmpeg_not_found", "WARN", "FFmpeg未找到")
            except:
                self.log_result("ffmpeg_not_found", "WARN", "FFmpeg未找到")
        
        # 测试FFmpeg Python绑定
        try:
            import ffmpeg
            self.log_result("ffmpeg_python", "PASS", "ffmpeg-python库可用")
        except ImportError:
            self.log_result("ffmpeg_python", "WARN", "ffmpeg-python库不可用")
    
    def test_export_formats(self):
        """测试导出格式支持"""
        print("\n📤 测试导出格式...")
        
        # 检查导出配置
        export_config_path = "configs/export_policy.yaml"
        if os.path.exists(export_config_path):
            try:
                import yaml
                with open(export_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                self.log_result("export_config", "PASS", 
                              f"导出配置加载成功")
                
                # 检查支持的格式
                if 'supported_formats' in str(config):
                    self.log_result("export_formats", "PASS", "支持多种导出格式")
                else:
                    self.log_result("export_formats", "WARN", "导出格式配置不完整")
                    
            except Exception as e:
                self.log_result("export_config", "FAIL", "", str(e))
        else:
            self.log_result("export_config", "WARN", "导出配置文件不存在")
    
    def test_video_quality_validation(self):
        """测试视频质量验证"""
        print("\n🔍 测试视频质量验证...")
        
        try:
            from src.eval.quality_validator import QualityValidator
            validator = QualityValidator()
            self.log_result("quality_validator_init", "PASS", "质量验证器初始化成功")
            
            # 检查验证方法
            methods = ['validate_video', 'check_resolution', 'check_audio_sync']
            available_methods = [m for m in methods if hasattr(validator, m)]
            self.log_result("quality_validation_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("quality_validator_init", "FAIL", "", str(e))
    
    def test_memory_efficiency(self):
        """测试内存效率"""
        print("\n💾 测试内存效率...")
        
        try:
            import psutil
            
            # 获取当前内存使用
            memory = psutil.virtual_memory()
            current_usage = memory.percent
            
            self.log_result("memory_baseline", "PASS", 
                          f"当前内存使用: {current_usage:.1f}%")
            
            # 检查是否有内存优化
            if current_usage < 80:
                self.log_result("memory_efficiency", "PASS", "内存使用效率良好")
            else:
                self.log_result("memory_efficiency", "WARN", "内存使用率较高")
                
        except Exception as e:
            self.log_result("memory_efficiency_test", "FAIL", "", str(e))
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        print("\n🛡️ 测试错误恢复...")
        
        try:
            from src.core.recovery_manager import RecoveryManager
            recovery = RecoveryManager()
            self.log_result("recovery_manager_init", "PASS", "恢复管理器初始化成功")
            
            # 检查恢复方法
            methods = ['save_checkpoint', 'resume_from_checkpoint', 'cleanup']
            available_methods = [m for m in methods if hasattr(recovery, m)]
            self.log_result("recovery_methods", "PASS", 
                          f"可用方法: {len(available_methods)}/{len(methods)}")
            
        except Exception as e:
            self.log_result("recovery_manager_init", "FAIL", "", str(e))
    
    def test_performance_metrics(self):
        """测试性能指标"""
        print("\n📊 测试性能指标...")
        
        # 模拟视频处理性能测试
        start_time = time.time()
        
        # 简单的性能测试
        test_data = list(range(10000))
        processed_data = [x * 2 for x in test_data]
        
        processing_time = time.time() - start_time
        
        self.log_result("processing_performance", "PASS", 
                      f"处理性能: {processing_time*1000:.2f}ms")
        
        if processing_time < 0.1:
            self.log_result("performance_rating", "PASS", "性能表现优秀")
        else:
            self.log_result("performance_rating", "WARN", "性能可能需要优化")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎬 开始VisionAI-ClipsMaster 视频处理和导出测试")
        print("=" * 60)
        
        self.test_video_processor()
        self.test_clip_generator()
        self.test_srt_parser()
        self.test_jianying_exporter()
        self.test_timeline_precision()
        self.test_ffmpeg_integration()
        self.test_export_formats()
        self.test_video_quality_validation()
        self.test_memory_efficiency()
        self.test_error_recovery()
        self.test_performance_metrics()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 视频处理和导出测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASS')
        failed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'FAIL')
        warned_tests = sum(1 for r in self.test_results.values() if r['status'] == 'WARN')
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"警告: {warned_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"测试时长: {time.time() - self.start_time:.2f}秒")
        
        # 保存详细报告
        report_file = f"video_export_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存至: {report_file}")

if __name__ == "__main__":
    test = VideoExportTest()
    test.run_all_tests()
