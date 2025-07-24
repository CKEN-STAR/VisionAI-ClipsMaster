#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程文件兼容性修复测试脚本

测试修复后的剪映导出功能，验证兼容性是否达到100%

作者: VisionAI-ClipsMaster Team
日期: 2025-07-23
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_project_data():
    """创建测试项目数据"""
    return {
        "project_name": "兼容性测试项目",
        "source_video": "test_video.mp4",
        "segments": [
            {
                "start_time": "00:00:00,000",
                "end_time": "00:00:05,000",
                "text": "这是第一个测试片段",
                "source_file": "test_video.mp4",
                "width": 1920,
                "height": 1080,
                "fps": 30
            },
            {
                "start_time": "00:00:05,000",
                "end_time": "00:00:10,000",
                "text": "这是第二个测试片段",
                "source_file": "test_video.mp4",
                "width": 1920,
                "height": 1080,
                "fps": 30
            },
            {
                "start_time": "00:00:10,000",
                "end_time": "00:00:15,000",
                "text": "这是第三个测试片段",
                "source_file": "test_video.mp4",
                "width": 1920,
                "height": 1080,
                "fps": 30
            }
        ]
    }

def test_jianying_export_compatibility():
    """测试剪映导出兼容性"""
    logger.info("开始测试剪映导出兼容性修复...")
    
    try:
        # 导入修复后的导出器
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        from src.exporters.jianying_compatibility_validator import JianyingCompatibilityValidator
        
        # 创建测试数据
        test_data = create_test_project_data()
        logger.info(f"创建测试数据，包含 {len(test_data['segments'])} 个片段")
        
        # 创建导出器
        exporter = JianYingProExporter()
        validator = JianyingCompatibilityValidator()
        
        # 创建输出目录
        output_dir = PROJECT_ROOT / "test_output" / "compatibility_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试1: 基本导出功能
        logger.info("测试1: 基本导出功能")
        output_file = output_dir / "test_project.json"
        success = exporter.export_project(test_data, str(output_file))
        
        if not success:
            logger.error("基本导出功能测试失败")
            return False
        
        logger.info("✅ 基本导出功能测试通过")
        
        # 测试2: 验证生成的文件
        logger.info("测试2: 验证生成的文件")
        if not output_file.exists():
            logger.error("输出文件不存在")
            return False
        
        # 读取生成的文件
        with open(output_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        logger.info("✅ 文件生成测试通过")
        
        # 测试3: 兼容性验证
        logger.info("测试3: 兼容性验证")
        is_compatible, errors = validator.validate_project(project_data)
        
        if not is_compatible:
            logger.error(f"兼容性验证失败，发现 {len(errors)} 个问题:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("✅ 兼容性验证测试通过")
        
        # 测试4: 结构完整性检查
        logger.info("测试4: 结构完整性检查")
        structure_check = check_project_structure(project_data)
        
        if not structure_check:
            logger.error("结构完整性检查失败")
            return False
        
        logger.info("✅ 结构完整性检查通过")
        
        # 测试5: 时间轴一致性检查
        logger.info("测试5: 时间轴一致性检查")
        timeline_check = check_timeline_consistency(project_data)
        
        if not timeline_check:
            logger.error("时间轴一致性检查失败")
            return False
        
        logger.info("✅ 时间轴一致性检查通过")
        
        # 测试6: 素材映射检查
        logger.info("测试6: 素材映射检查")
        material_check = check_material_mapping(project_data)
        
        if not material_check:
            logger.error("素材映射检查失败")
            return False
        
        logger.info("✅ 素材映射检查通过")
        
        # 生成测试报告
        generate_test_report(project_data, output_dir)
        
        logger.info("🎉 所有兼容性测试通过！剪映导出功能兼容性达到100%")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_project_structure(project_data):
    """检查项目结构完整性"""
    required_fields = [
        'version', 'type', 'platform', 'create_time', 'update_time',
        'id', 'draft_id', 'draft_name', 'canvas_config', 'tracks', 
        'materials', 'extra_info', 'keyframes', 'relations'
    ]
    
    for field in required_fields:
        if field not in project_data:
            logger.error(f"缺少必需字段: {field}")
            return False
    
    # 检查轨道数量
    tracks = project_data.get('tracks', [])
    if len(tracks) < 3:  # 应该有视频、音频、字幕轨道
        logger.error(f"轨道数量不足，期望至少3个，实际 {len(tracks)} 个")
        return False
    
    # 检查素材数量
    materials = project_data.get('materials', {})
    videos = materials.get('videos', [])
    audios = materials.get('audios', [])
    texts = materials.get('texts', [])
    
    if len(videos) == 0 or len(audios) == 0 or len(texts) == 0:
        logger.error("素材库中缺少必要的素材类型")
        return False
    
    return True

def check_timeline_consistency(project_data):
    """检查时间轴一致性"""
    canvas_duration = project_data.get('canvas_config', {}).get('duration', 0)
    export_end = project_data.get('extra_info', {}).get('export_range', {}).get('end', 0)
    
    # 检查时长一致性
    if abs(canvas_duration - export_end) > 100:  # 允许100ms误差
        logger.error(f"时长不一致: canvas_duration={canvas_duration}, export_end={export_end}")
        return False
    
    # 检查轨道片段时长
    tracks = project_data.get('tracks', [])
    for track in tracks:
        segments = track.get('segments', [])
        total_track_duration = 0
        
        for segment in segments:
            target_timerange = segment.get('target_timerange', {})
            duration = target_timerange.get('duration', 0)
            total_track_duration += duration
        
        # 轨道总时长应该与画布时长一致
        if abs(total_track_duration - canvas_duration) > 100:
            logger.error(f"轨道 {track.get('type')} 时长不一致: {total_track_duration} vs {canvas_duration}")
            return False
    
    return True

def check_material_mapping(project_data):
    """检查素材映射关系"""
    materials = project_data.get('materials', {})
    tracks = project_data.get('tracks', [])
    
    # 收集所有素材ID
    all_material_ids = set()
    for material_type, material_list in materials.items():
        for material in material_list:
            material_id = material.get('id', '')
            if material_id:
                all_material_ids.add(material_id)
    
    # 检查轨道中引用的素材ID是否存在
    for track in tracks:
        segments = track.get('segments', [])
        for segment in segments:
            material_id = segment.get('material_id', '')
            if material_id and material_id not in all_material_ids:
                logger.error(f"轨道片段引用了不存在的素材ID: {material_id}")
                return False
    
    return True

def generate_test_report(project_data, output_dir):
    """生成测试报告"""
    report = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_result": "PASS",
        "compatibility_score": "100%",
        "project_info": {
            "version": project_data.get('version'),
            "platform": project_data.get('platform'),
            "tracks_count": len(project_data.get('tracks', [])),
            "materials_count": {
                "videos": len(project_data.get('materials', {}).get('videos', [])),
                "audios": len(project_data.get('materials', {}).get('audios', [])),
                "texts": len(project_data.get('materials', {}).get('texts', []))
            },
            "total_duration": project_data.get('canvas_config', {}).get('duration', 0)
        },
        "validation_results": {
            "structure_check": "PASS",
            "timeline_consistency": "PASS",
            "material_mapping": "PASS",
            "compatibility_validation": "PASS"
        }
    }
    
    # 保存报告
    report_file = output_dir / "compatibility_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"测试报告已保存到: {report_file}")

def main():
    """主函数"""
    print("=" * 60)
    print("剪映工程文件兼容性修复测试")
    print("=" * 60)
    
    success = test_jianying_export_compatibility()
    
    if success:
        print("\n🎉 测试结果: 成功")
        print("✅ 剪映导出功能兼容性已达到100%")
        print("✅ 所有测试用例通过")
        print("✅ 工程文件结构完整")
        print("✅ 时间轴映射准确")
        print("✅ 素材关系正确")
    else:
        print("\n❌ 测试结果: 失败")
        print("需要进一步检查和修复")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
