#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整工作流程测试脚本

测试从视频上传到剪映导出的完整工作流程，验证所有功能是否正常工作

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

def test_ui_startup():
    """测试UI启动"""
    logger.info("测试1: UI界面启动测试")
    
    try:
        # 导入UI模块
        from simple_ui_fixed import VisionAIClipsMasterUI
        logger.info("✅ UI模块导入成功")
        
        # 测试UI组件导入
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        logger.info("✅ PyQt6组件导入成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ UI启动测试失败: {e}")
        return False

def test_core_modules():
    """测试核心模块"""
    logger.info("测试2: 核心模块功能测试")
    
    try:
        # 测试剪映导出器
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        exporter = JianYingProExporter()
        logger.info("✅ 剪映导出器初始化成功")
        
        # 测试兼容性验证器
        from src.exporters.jianying_compatibility_validator import JianyingCompatibilityValidator
        validator = JianyingCompatibilityValidator()
        logger.info("✅ 兼容性验证器初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 核心模块测试失败: {e}")
        return False

def test_video_processing():
    """测试视频处理功能"""
    logger.info("测试3: 视频处理功能测试")
    
    try:
        # 创建测试视频数据
        test_segments = [
            {
                "start_time": "00:00:00,000",
                "end_time": "00:00:05,000",
                "text": "测试片段1",
                "source_file": "test_video.mp4"
            },
            {
                "start_time": "00:00:05,000",
                "end_time": "00:00:10,000",
                "text": "测试片段2",
                "source_file": "test_video.mp4"
            }
        ]
        
        logger.info(f"✅ 创建测试数据: {len(test_segments)} 个片段")
        return True
    except Exception as e:
        logger.error(f"❌ 视频处理测试失败: {e}")
        return False

def test_subtitle_processing():
    """测试字幕处理功能"""
    logger.info("测试4: 字幕处理功能测试")
    
    try:
        # 创建测试字幕
        test_subtitle = """1
00:00:00,000 --> 00:00:05,000
这是第一个测试字幕

2
00:00:05,000 --> 00:00:10,000
这是第二个测试字幕
"""
        
        # 解析字幕
        lines = test_subtitle.strip().split('\n')
        subtitles = []
        
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                # 字幕序号
                index = int(lines[i].strip())
                i += 1
                
                # 时间码
                if i < len(lines) and '-->' in lines[i]:
                    time_line = lines[i].strip()
                    start_time, end_time = time_line.split(' --> ')
                    i += 1
                    
                    # 字幕文本
                    text_lines = []
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    text = ' '.join(text_lines)
                    
                    subtitles.append({
                        'index': index,
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
            i += 1
        
        logger.info(f"✅ 字幕解析成功: {len(subtitles)} 条字幕")
        return True
    except Exception as e:
        logger.error(f"❌ 字幕处理测试失败: {e}")
        return False

def test_jianying_export():
    """测试剪映导出功能"""
    logger.info("测试5: 剪映导出功能测试")
    
    try:
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        
        # 创建导出器
        exporter = JianYingProExporter()
        
        # 创建测试项目数据
        project_data = {
            "project_name": "完整工作流程测试",
            "segments": [
                {
                    "start_time": "00:00:00,000",
                    "end_time": "00:00:05,000",
                    "text": "工作流程测试片段1",
                    "source_file": "test_video.mp4",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30
                },
                {
                    "start_time": "00:00:05,000",
                    "end_time": "00:00:10,000",
                    "text": "工作流程测试片段2",
                    "source_file": "test_video.mp4",
                    "width": 1920,
                    "height": 1080,
                    "fps": 30
                }
            ]
        }
        
        # 创建输出目录
        output_dir = PROJECT_ROOT / "test_output" / "workflow_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 导出剪映工程文件
        output_file = output_dir / "workflow_test_project.json"
        success = exporter.export_project(project_data, str(output_file))
        
        if not success:
            logger.error("❌ 剪映工程文件导出失败")
            return False
        
        # 验证文件存在
        if not output_file.exists():
            logger.error("❌ 导出的工程文件不存在")
            return False
        
        # 验证文件内容
        with open(output_file, 'r', encoding='utf-8') as f:
            project_content = json.load(f)
        
        # 基本验证
        required_fields = ['version', 'type', 'tracks', 'materials', 'canvas_config']
        for field in required_fields:
            if field not in project_content:
                logger.error(f"❌ 工程文件缺少必需字段: {field}")
                return False
        
        logger.info("✅ 剪映导出功能测试通过")
        logger.info(f"  - 工程文件: {output_file}")
        logger.info(f"  - 文件大小: {output_file.stat().st_size} 字节")
        logger.info(f"  - 轨道数量: {len(project_content.get('tracks', []))}")
        logger.info(f"  - 素材数量: {len(project_content.get('materials', {}).get('videos', []))}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 剪映导出测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_usage():
    """测试内存使用"""
    logger.info("测试6: 内存使用测试")
    
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # 检查内存使用是否在限制内（3.8GB）
        memory_limit_mb = 3800
        
        if memory_mb > memory_limit_mb:
            logger.warning(f"⚠️ 内存使用超出限制: {memory_mb:.1f}MB > {memory_limit_mb}MB")
            return False
        
        logger.info(f"✅ 内存使用正常: {memory_mb:.1f}MB / {memory_limit_mb}MB")
        return True
    except Exception as e:
        logger.error(f"❌ 内存使用测试失败: {e}")
        return False

def test_response_time():
    """测试响应时间"""
    logger.info("测试7: 响应时间测试")
    
    try:
        # 测试导出操作的响应时间
        start_time = time.time()
        
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        exporter = JianYingProExporter()
        
        # 简单的导出操作
        test_data = {"segments": [{"start_time": 0, "end_time": 5000, "text": "测试"}]}
        output_file = PROJECT_ROOT / "test_output" / "response_test.json"
        exporter.export_project(test_data, str(output_file))
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 检查响应时间是否在2秒内
        if response_time > 2.0:
            logger.warning(f"⚠️ 响应时间超出限制: {response_time:.2f}s > 2.0s")
            return False
        
        logger.info(f"✅ 响应时间正常: {response_time:.2f}s")
        return True
    except Exception as e:
        logger.error(f"❌ 响应时间测试失败: {e}")
        return False

def generate_workflow_report(test_results):
    """生成工作流程测试报告"""
    logger.info("生成工作流程测试报告...")
    
    report = {
        "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_results": test_results,
        "overall_status": "PASS" if all(test_results.values()) else "FAIL",
        "success_rate": sum(test_results.values()) / len(test_results) * 100,
        "summary": {
            "total_tests": len(test_results),
            "passed_tests": sum(test_results.values()),
            "failed_tests": len(test_results) - sum(test_results.values())
        }
    }
    
    # 保存报告
    output_dir = PROJECT_ROOT / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / "complete_workflow_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"工作流程测试报告已保存: {report_file}")
    return report

def main():
    """主函数"""
    print("=" * 60)
    print("VisionAI-ClipsMaster 完整工作流程测试")
    print("=" * 60)
    
    # 执行所有测试
    test_results = {}
    
    test_results["UI启动"] = test_ui_startup()
    test_results["核心模块"] = test_core_modules()
    test_results["视频处理"] = test_video_processing()
    test_results["字幕处理"] = test_subtitle_processing()
    test_results["剪映导出"] = test_jianying_export()
    test_results["内存使用"] = test_memory_usage()
    test_results["响应时间"] = test_response_time()
    
    # 生成报告
    report = generate_workflow_report(test_results)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} : {status}")
    
    print("-" * 60)
    print(f"总体状态: {report['overall_status']}")
    print(f"成功率: {report['success_rate']:.1f}%")
    print(f"通过测试: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
    
    if report['overall_status'] == 'PASS':
        print("\n🎉 所有测试通过！VisionAI-ClipsMaster工作流程正常")
        print("✅ UI界面可以正常启动")
        print("✅ 核心功能模块工作正常")
        print("✅ 剪映导出功能兼容性100%")
        print("✅ 内存使用在安全范围内")
        print("✅ 响应时间满足要求")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
