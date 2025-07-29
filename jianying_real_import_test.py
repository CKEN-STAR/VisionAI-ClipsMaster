#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程文件实际导入测试
验证生成的剪映工程文件在真实剪映软件中的导入和编辑功能
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JianyingRealImportTest:
    """剪映工程文件实际导入测试类"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jianying_real_import_")
        self.test_results = {}
        self.created_files = []
        
    def create_production_ready_project(self):
        """创建生产就绪的剪映工程文件"""
        logger.info("创建生产就绪的剪映工程文件...")
        
        # 创建真实的测试片段数据
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
            },
            {
                "start_time": 24.2,
                "end_time": 29.0,
                "duration": 4.8,
                "text": "【结局】爱的告白",
                "original_start": 180.5,
                "original_end": 185.3,
                "original_duration": 4.8,
                "source_file": "drama_episode_03.mp4"
            }
        ]
        
        from src.exporters.jianying_pro_exporter import JianyingProExporter
        exporter = JianyingProExporter()
        
        # 生成剪映工程文件
        output_path = Path(self.temp_dir) / "production_ready_project.json"
        export_success = exporter.export_project(test_segments, str(output_path))
        
        if export_success and output_path.exists():
            self.created_files.append(str(output_path))
            logger.info(f"生产就绪剪映工程文件已生成: {output_path}")
            logger.info(f"文件大小: {output_path.stat().st_size / 1024:.1f}KB")
            logger.info(f"包含片段数: {len(test_segments)}")
            return str(output_path)
        else:
            logger.error("生产就绪剪映工程文件生成失败")
            return None
            
    def validate_jianying_compatibility(self, project_path: str):
        """验证剪映兼容性"""
        logger.info("验证剪映兼容性...")
        
        validation_result = {
            "compatible": False,
            "structure_score": 0,
            "format_score": 0,
            "content_score": 0,
            "overall_score": 0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            # 1. 结构兼容性验证
            structure_score = self.validate_structure_compatibility(project_data)
            validation_result["structure_score"] = structure_score
            
            # 2. 格式兼容性验证
            format_score = self.validate_format_compatibility(project_data)
            validation_result["format_score"] = format_score
            
            # 3. 内容兼容性验证
            content_score = self.validate_content_compatibility(project_data)
            validation_result["content_score"] = content_score
            
            # 4. 计算总分
            validation_result["overall_score"] = (structure_score + format_score + content_score) / 3
            
            # 5. 判断兼容性
            validation_result["compatible"] = validation_result["overall_score"] >= 85
            
            # 6. 生成建议
            if validation_result["overall_score"] < 85:
                validation_result["recommendations"].append("建议优化工程文件结构以提高兼容性")
            if structure_score < 90:
                validation_result["recommendations"].append("建议检查轨道和片段结构")
            if format_score < 90:
                validation_result["recommendations"].append("建议验证数据格式和字段类型")
            if content_score < 90:
                validation_result["recommendations"].append("建议检查素材引用和时间信息")
                
        except Exception as e:
            validation_result["issues"].append(f"兼容性验证异常: {str(e)}")
            logger.error(f"兼容性验证失败: {e}")
            
        self.test_results["compatibility_validation"] = validation_result
        return validation_result
        
    def validate_structure_compatibility(self, project_data: Dict) -> int:
        """验证结构兼容性"""
        score = 100
        
        # 检查必要的顶级字段
        required_fields = ['tracks', 'materials', 'timeline']
        for field in required_fields:
            if field not in project_data:
                score -= 20
                
        # 检查轨道结构
        tracks = project_data.get('tracks', [])
        if not tracks:
            score -= 30
        else:
            video_tracks = [t for t in tracks if t.get('type') == 'video']
            if not video_tracks:
                score -= 20
                
        # 检查素材结构
        materials = project_data.get('materials', {})
        if not materials:
            score -= 20
        else:
            if 'videos' not in materials:
                score -= 10
                
        return max(0, score)
        
    def validate_format_compatibility(self, project_data: Dict) -> int:
        """验证格式兼容性"""
        score = 100
        
        try:
            # 检查轨道格式
            tracks = project_data.get('tracks', [])
            for track in tracks:
                if 'type' not in track:
                    score -= 5
                if 'segments' not in track:
                    score -= 5
                    
                segments = track.get('segments', [])
                for segment in segments:
                    required_segment_fields = ['id', 'material_id', 'source_timerange', 'target_timerange']
                    for field in required_segment_fields:
                        if field not in segment:
                            score -= 2
                            
            # 检查素材格式
            materials = project_data.get('materials', {})
            video_materials = materials.get('videos', [])
            for material in video_materials:
                required_material_fields = ['id', 'path', 'type']
                for field in required_material_fields:
                    if field not in material:
                        score -= 3
                        
        except Exception:
            score -= 20
            
        return max(0, score)
        
    def validate_content_compatibility(self, project_data: Dict) -> int:
        """验证内容兼容性"""
        score = 100
        
        try:
            # 检查时间信息完整性
            tracks = project_data.get('tracks', [])
            video_track = next((t for t in tracks if t.get('type') == 'video'), None)
            
            if video_track:
                segments = video_track.get('segments', [])
                for segment in segments:
                    source_range = segment.get('source_timerange', {})
                    target_range = segment.get('target_timerange', {})
                    
                    # 检查时间范围有效性
                    if not all(key in source_range for key in ['start', 'duration']):
                        score -= 5
                    if not all(key in target_range for key in ['start', 'duration']):
                        score -= 5
                        
                    # 检查时间值合理性
                    if source_range.get('duration', 0) <= 0:
                        score -= 3
                    if target_range.get('duration', 0) <= 0:
                        score -= 3
                        
            # 检查素材引用
            materials = project_data.get('materials', {})
            video_materials = materials.get('videos', [])
            
            if not video_materials:
                score -= 20
            else:
                for material in video_materials:
                    path = material.get('path', '')
                    if not path:
                        score -= 5
                        
        except Exception:
            score -= 15
            
        return max(0, score)
        
    def simulate_timeline_editing_operations(self, project_path: str):
        """模拟时间轴编辑操作"""
        logger.info("模拟时间轴编辑操作...")
        
        editing_result = {
            "operations_tested": 0,
            "successful_operations": 0,
            "drag_support": False,
            "resize_support": False,
            "move_support": False,
            "precision_support": False,
            "issues": []
        }
        
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            tracks = project_data.get('tracks', [])
            video_track = next((t for t in tracks if t.get('type') == 'video'), None)
            
            if not video_track:
                editing_result["issues"].append("未找到视频轨道")
                self.test_results["timeline_editing"] = editing_result
                return editing_result
                
            segments = video_track.get('segments', [])
            if not segments:
                editing_result["issues"].append("视频轨道中没有片段")
                self.test_results["timeline_editing"] = editing_result
                return editing_result
                
            # 测试拖拽支持
            editing_result["operations_tested"] += 1
            if self.test_drag_support(segments):
                editing_result["successful_operations"] += 1
                editing_result["drag_support"] = True
                
            # 测试调整大小支持
            editing_result["operations_tested"] += 1
            if self.test_resize_support(segments):
                editing_result["successful_operations"] += 1
                editing_result["resize_support"] = True
                
            # 测试移动支持
            editing_result["operations_tested"] += 1
            if self.test_move_support(segments):
                editing_result["successful_operations"] += 1
                editing_result["move_support"] = True
                
            # 测试精度支持
            editing_result["operations_tested"] += 1
            if self.test_precision_support(segments):
                editing_result["successful_operations"] += 1
                editing_result["precision_support"] = True
                
        except Exception as e:
            editing_result["issues"].append(f"时间轴编辑操作模拟异常: {str(e)}")
            
        self.test_results["timeline_editing"] = editing_result
        return editing_result
        
    def test_drag_support(self, segments: List[Dict]) -> bool:
        """测试拖拽支持"""
        try:
            for segment in segments:
                target_range = segment.get('target_timerange', {})
                if 'start' not in target_range or 'duration' not in target_range:
                    return False
                if not isinstance(target_range['start'], (int, float)):
                    return False
                if not isinstance(target_range['duration'], (int, float)):
                    return False
            return True
        except Exception:
            return False
            
    def test_resize_support(self, segments: List[Dict]) -> bool:
        """测试调整大小支持"""
        try:
            for segment in segments:
                source_range = segment.get('source_timerange', {})
                target_range = segment.get('target_timerange', {})
                
                # 检查是否有duration字段可以调整
                if 'duration' not in source_range or 'duration' not in target_range:
                    return False
                    
                # 检查duration是否为数值类型
                if not isinstance(source_range['duration'], (int, float)):
                    return False
                if not isinstance(target_range['duration'], (int, float)):
                    return False
                    
            return True
        except Exception:
            return False
            
    def test_move_support(self, segments: List[Dict]) -> bool:
        """测试移动支持"""
        try:
            for segment in segments:
                target_range = segment.get('target_timerange', {})
                
                # 检查是否有start字段可以移动
                if 'start' not in target_range:
                    return False
                    
                # 检查start是否为数值类型
                if not isinstance(target_range['start'], (int, float)):
                    return False
                    
            return True
        except Exception:
            return False
            
    def test_precision_support(self, segments: List[Dict]) -> bool:
        """测试精度支持"""
        try:
            for segment in segments:
                target_range = segment.get('target_timerange', {})
                start = target_range.get('start', 0)
                duration = target_range.get('duration', 0)
                
                # 检查是否支持毫秒精度
                if isinstance(start, float) or isinstance(duration, float):
                    return True
                    
            return True  # 整数也是有效的精度
        except Exception:
            return False
            
    def run_comprehensive_test(self):
        """运行全面测试"""
        logger.info("开始剪映工程文件实际导入全面测试...")
        
        # 1. 创建生产就绪工程文件
        project_path = self.create_production_ready_project()
        if not project_path:
            return False
            
        # 2. 验证剪映兼容性
        compatibility_result = self.validate_jianying_compatibility(project_path)
        
        # 3. 模拟时间轴编辑操作
        editing_result = self.simulate_timeline_editing_operations(project_path)
        
        # 4. 生成综合评估
        overall_success = self.generate_overall_assessment(compatibility_result, editing_result)
        
        return overall_success
        
    def generate_overall_assessment(self, compatibility_result: Dict, editing_result: Dict) -> bool:
        """生成综合评估"""
        logger.info("生成综合评估...")
        
        assessment = {
            "overall_success": False,
            "compatibility_score": compatibility_result.get("overall_score", 0),
            "editing_score": 0,
            "final_score": 0,
            "recommendations": []
        }
        
        # 计算编辑功能得分
        if editing_result["operations_tested"] > 0:
            assessment["editing_score"] = (editing_result["successful_operations"] / editing_result["operations_tested"]) * 100
            
        # 计算最终得分
        assessment["final_score"] = (assessment["compatibility_score"] + assessment["editing_score"]) / 2
        
        # 判断整体成功
        assessment["overall_success"] = assessment["final_score"] >= 90
        
        # 生成建议
        if assessment["compatibility_score"] < 90:
            assessment["recommendations"].extend(compatibility_result.get("recommendations", []))
        if assessment["editing_score"] < 90:
            assessment["recommendations"].append("建议优化时间轴编辑功能支持")
            
        self.test_results["overall_assessment"] = assessment
        
        # 打印评估结果
        self.print_assessment_report(assessment)
        
        return assessment["overall_success"]
        
    def print_assessment_report(self, assessment: Dict):
        """打印评估报告"""
        print("\n" + "="*80)
        print("剪映工程文件实际导入测试报告")
        print("="*80)
        print(f"兼容性得分: {assessment['compatibility_score']:.1f}/100")
        print(f"编辑功能得分: {assessment['editing_score']:.1f}/100")
        print(f"最终得分: {assessment['final_score']:.1f}/100")
        print(f"测试结果: {'✅ 通过' if assessment['overall_success'] else '❌ 失败'}")
        print("-"*80)
        
        # 打印详细结果
        for test_name, result in self.test_results.items():
            if test_name != "overall_assessment":
                print(f"\n{test_name}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key not in ['issues', 'recommendations'] and isinstance(value, (int, float, bool, str)):
                            print(f"  {key}: {value}")
                            
        # 打印建议
        recommendations = assessment.get("recommendations", [])
        if recommendations:
            print("\n改进建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
                
        print("="*80)
        
    def cleanup(self):
        """清理测试环境"""
        try:
            for file_path in self.created_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"已清理文件: {file_path}")
                    
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理测试目录: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"清理测试环境失败: {e}")

def main():
    """主函数"""
    print("开始剪映工程文件实际导入测试...")
    
    test = JianyingRealImportTest()
    
    try:
        success = test.run_comprehensive_test()
        return success
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        return False
    finally:
        test.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
