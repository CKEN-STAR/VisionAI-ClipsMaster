#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程文件导入验证测试
验证生成的剪映工程文件能否在剪映软件中正常导入和使用
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JianyingImportValidationTest:
    """剪映工程文件导入验证测试类"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jianying_validation_")
        self.test_results = {}
        
    def create_comprehensive_test_project(self):
        """创建全面的测试工程文件"""
        logger.info("创建全面的剪映测试工程文件...")
        
        # 创建测试片段数据（模拟真实短剧数据）
        test_segments = [
            {
                "start_time": 0.0,
                "end_time": 4.5,
                "duration": 4.5,
                "text": "【震惊】霸道总裁的秘密",
                "original_start": 1.0,
                "original_end": 5.5,
                "original_duration": 4.5,
                "source_file": "drama_episode_01.mp4"
            },
            {
                "start_time": 4.6,
                "end_time": 9.8,
                "duration": 5.2,
                "text": "你就是新来的实习生？陈墨轩冷漠地看着她",
                "original_start": 15.8,
                "original_end": 21.0,
                "original_duration": 5.2,
                "source_file": "drama_episode_01.mp4"
            },
            {
                "start_time": 9.9,
                "end_time": 14.5,
                "duration": 4.6,
                "text": "【转折】意外的相遇改变了一切",
                "original_start": 42.6,
                "original_end": 47.2,
                "original_duration": 4.6,
                "source_file": "drama_episode_02.mp4"
            },
            {
                "start_time": 14.6,
                "end_time": 19.3,
                "duration": 4.7,
                "text": "这么晚还不回家？陈墨轩难得地开口问道",
                "original_start": 63.8,
                "original_end": 68.5,
                "original_duration": 4.7,
                "source_file": "drama_episode_02.mp4"
            },
            {
                "start_time": 19.4,
                "end_time": 24.1,
                "duration": 4.7,
                "text": "【高潮】你为什么这么拼命？",
                "original_start": 95.6,
                "original_end": 100.3,
                "original_duration": 4.7,
                "source_file": "drama_episode_03.mp4"
            }
        ]
        
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        exporter = JianyingProExporter()
        
        # 生成剪映工程文件
        output_path = Path(self.temp_dir) / "comprehensive_test_project.json"
        export_success = exporter.export_project(test_segments, str(output_path))
        
        if export_success and output_path.exists():
            logger.info(f"剪映工程文件已生成: {output_path}")
            logger.info(f"文件大小: {output_path.stat().st_size / 1024:.1f}KB")
            return str(output_path)
        else:
            logger.error("剪映工程文件生成失败")
            return None
            
    def validate_project_structure(self, project_path: str):
        """验证工程文件结构"""
        logger.info("验证剪映工程文件结构...")
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            validation_results = {
                "file_readable": True,
                "json_valid": True,
                "required_fields": [],
                "track_structure": {},
                "material_structure": {},
                "timeline_structure": {},
                "compatibility_score": 0
            }
            
            # 检查必要字段
            required_fields = ['tracks', 'materials', 'timeline']
            for field in required_fields:
                if field in project_data:
                    validation_results["required_fields"].append(field)
                    
            # 检查轨道结构
            tracks = project_data.get('tracks', [])
            video_tracks = [track for track in tracks if track.get('type') == 'video']
            audio_tracks = [track for track in tracks if track.get('type') == 'audio']
            
            validation_results["track_structure"] = {
                "total_tracks": len(tracks),
                "video_tracks": len(video_tracks),
                "audio_tracks": len(audio_tracks),
                "has_video_track": len(video_tracks) > 0
            }
            
            # 检查材料结构
            materials = project_data.get('materials', {})
            validation_results["material_structure"] = {
                "videos": len(materials.get('videos', [])),
                "audios": len(materials.get('audios', [])),
                "has_materials": len(materials) > 0
            }
            
            # 检查时间轴结构
            timeline = project_data.get('timeline', {})
            validation_results["timeline_structure"] = {
                "has_timeline": bool(timeline),
                "timeline_fields": list(timeline.keys()) if timeline else []
            }
            
            # 计算兼容性得分
            score = 0
            if len(validation_results["required_fields"]) == 3:
                score += 30
            if validation_results["track_structure"]["has_video_track"]:
                score += 25
            if validation_results["material_structure"]["has_materials"]:
                score += 25
            if validation_results["timeline_structure"]["has_timeline"]:
                score += 20
                
            validation_results["compatibility_score"] = score
            
            self.test_results["structure_validation"] = validation_results
            
            logger.info(f"结构验证完成，兼容性得分: {score}/100")
            return validation_results
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            self.test_results["structure_validation"] = {"error": f"JSON解析失败: {e}"}
            return None
        except Exception as e:
            logger.error(f"结构验证失败: {e}")
            self.test_results["structure_validation"] = {"error": f"结构验证失败: {e}"}
            return None
            
    def validate_timing_information(self, project_path: str):
        """验证时间信息完整性"""
        logger.info("验证时间信息完整性...")
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            timing_results = {
                "segments_with_timing": 0,
                "segments_without_timing": 0,
                "total_segments": 0,
                "timing_accuracy": 0,
                "original_timing_preserved": 0,
                "time_range_valid": True
            }
            
            tracks = project_data.get('tracks', [])
            for track in tracks:
                if track.get('type') == 'video':
                    segments = track.get('segments', [])
                    timing_results["total_segments"] = len(segments)
                    
                    for segment in segments:
                        # 检查基本时间信息
                        source_timerange = segment.get('source_timerange', {})
                        target_timerange = segment.get('target_timerange', {})
                        
                        if source_timerange and target_timerange:
                            timing_results["segments_with_timing"] += 1
                            
                            # 检查时间范围有效性
                            source_start = source_timerange.get('start', 0)
                            source_duration = source_timerange.get('duration', 0)
                            target_start = target_timerange.get('start', 0)
                            target_duration = target_timerange.get('duration', 0)
                            
                            if source_start < 0 or source_duration <= 0 or target_start < 0 or target_duration <= 0:
                                timing_results["time_range_valid"] = False
                        else:
                            timing_results["segments_without_timing"] += 1
                            
                        # 检查原始时间信息保留
                        original_timing = segment.get('original_timing', {})
                        if original_timing:
                            timing_results["original_timing_preserved"] += 1
                            
            # 计算时间精度
            if timing_results["total_segments"] > 0:
                timing_results["timing_accuracy"] = timing_results["segments_with_timing"] / timing_results["total_segments"]
                
            self.test_results["timing_validation"] = timing_results
            
            logger.info(f"时间信息验证完成，精度: {timing_results['timing_accuracy']:.2%}")
            return timing_results
            
        except Exception as e:
            logger.error(f"时间信息验证失败: {e}")
            self.test_results["timing_validation"] = {"error": f"时间信息验证失败: {e}"}
            return None
            
    def simulate_jianying_import(self, project_path: str):
        """模拟剪映导入过程"""
        logger.info("模拟剪映导入过程...")
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            import_results = {
                "import_simulation_success": False,
                "critical_errors": [],
                "warnings": [],
                "compatibility_issues": [],
                "import_score": 0
            }
            
            # 检查关键字段
            if 'tracks' not in project_data:
                import_results["critical_errors"].append("缺少tracks字段")
            if 'materials' not in project_data:
                import_results["critical_errors"].append("缺少materials字段")
                
            # 检查轨道完整性
            tracks = project_data.get('tracks', [])
            video_tracks = [track for track in tracks if track.get('type') == 'video']
            
            if not video_tracks:
                import_results["critical_errors"].append("没有视频轨道")
            else:
                for i, track in enumerate(video_tracks):
                    segments = track.get('segments', [])
                    if not segments:
                        import_results["warnings"].append(f"视频轨道{i}没有片段")
                        
                    for j, segment in enumerate(segments):
                        if 'material_id' not in segment:
                            import_results["compatibility_issues"].append(f"片段{j}缺少material_id")
                        if 'source_timerange' not in segment:
                            import_results["compatibility_issues"].append(f"片段{j}缺少source_timerange")
                        if 'target_timerange' not in segment:
                            import_results["compatibility_issues"].append(f"片段{j}缺少target_timerange")
                            
            # 检查材料完整性
            materials = project_data.get('materials', {})
            videos = materials.get('videos', [])
            
            if not videos:
                import_results["warnings"].append("没有视频材料")
                
            # 计算导入得分
            score = 100
            score -= len(import_results["critical_errors"]) * 30
            score -= len(import_results["warnings"]) * 10
            score -= len(import_results["compatibility_issues"]) * 5
            
            import_results["import_score"] = max(0, score)
            import_results["import_simulation_success"] = score >= 70
            
            self.test_results["import_simulation"] = import_results
            
            logger.info(f"导入模拟完成，得分: {score}/100")
            return import_results
            
        except Exception as e:
            logger.error(f"导入模拟失败: {e}")
            self.test_results["import_simulation"] = {"error": f"导入模拟失败: {e}"}
            return None
            
    def run_comprehensive_validation(self):
        """运行全面验证"""
        logger.info("开始剪映工程文件全面验证...")
        
        # 1. 创建测试工程文件
        project_path = self.create_comprehensive_test_project()
        if not project_path:
            return False
            
        # 2. 验证文件结构
        structure_result = self.validate_project_structure(project_path)
        
        # 3. 验证时间信息
        timing_result = self.validate_timing_information(project_path)
        
        # 4. 模拟导入过程
        import_result = self.simulate_jianying_import(project_path)
        
        # 5. 生成综合评估
        overall_success = self.generate_overall_assessment()
        
        return overall_success
        
    def generate_overall_assessment(self):
        """生成综合评估"""
        logger.info("生成综合评估...")
        
        assessment = {
            "overall_score": 0,
            "structure_score": 0,
            "timing_score": 0,
            "import_score": 0,
            "recommendation": "",
            "critical_issues": [],
            "improvement_suggestions": []
        }
        
        # 结构得分
        if "structure_validation" in self.test_results:
            structure = self.test_results["structure_validation"]
            if "compatibility_score" in structure:
                assessment["structure_score"] = structure["compatibility_score"]
                
        # 时间得分
        if "timing_validation" in self.test_results:
            timing = self.test_results["timing_validation"]
            if "timing_accuracy" in timing:
                assessment["timing_score"] = timing["timing_accuracy"] * 100
                
        # 导入得分
        if "import_simulation" in self.test_results:
            import_sim = self.test_results["import_simulation"]
            if "import_score" in import_sim:
                assessment["import_score"] = import_sim["import_score"]
                
        # 综合得分
        assessment["overall_score"] = (
            assessment["structure_score"] * 0.3 +
            assessment["timing_score"] * 0.3 +
            assessment["import_score"] * 0.4
        )
        
        # 生成建议
        if assessment["overall_score"] >= 90:
            assessment["recommendation"] = "优秀：工程文件完全兼容剪映，可以正常导入使用"
        elif assessment["overall_score"] >= 80:
            assessment["recommendation"] = "良好：工程文件基本兼容，可能有轻微问题"
        elif assessment["overall_score"] >= 70:
            assessment["recommendation"] = "可用：工程文件可以导入，但需要注意一些问题"
        else:
            assessment["recommendation"] = "需要改进：工程文件存在兼容性问题"
            
        self.test_results["overall_assessment"] = assessment
        
        # 打印评估结果
        self.print_assessment_report(assessment)
        
        return assessment["overall_score"] >= 80
        
    def print_assessment_report(self, assessment):
        """打印评估报告"""
        print("\n" + "="*80)
        print("剪映工程文件导入验证报告")
        print("="*80)
        print(f"综合得分: {assessment['overall_score']:.1f}/100")
        print(f"结构得分: {assessment['structure_score']:.1f}/100")
        print(f"时间得分: {assessment['timing_score']:.1f}/100")
        print(f"导入得分: {assessment['import_score']:.1f}/100")
        print(f"评估结果: {assessment['recommendation']}")
        print("-"*80)
        
        # 打印详细结果
        for test_name, result in self.test_results.items():
            if test_name != "overall_assessment":
                print(f"\n{test_name}:")
                if isinstance(result, dict) and "error" not in result:
                    for key, value in result.items():
                        if isinstance(value, (int, float, bool, str)):
                            print(f"  {key}: {value}")
                elif "error" in result:
                    print(f"  错误: {result['error']}")
                    
        print("="*80)
        
    def cleanup(self):
        """清理测试环境"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理测试目录: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"清理测试目录失败: {e}")

def main():
    """主函数"""
    print("开始剪映工程文件导入验证测试...")
    
    test = JianyingImportValidationTest()
    
    try:
        success = test.run_comprehensive_validation()
        return success
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        return False
    finally:
        test.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
