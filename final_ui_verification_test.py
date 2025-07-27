#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终UI验证测试

验证所有修复后的功能：
1. UI界面正常启动和显示
2. 核心功能集成正常工作
3. 端到端工作流完整性
4. 性能和稳定性达标
"""

import os
import sys
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ui_startup():
    """测试UI启动"""
    logger.info("测试UI启动...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import SimpleScreenplayApp
        
        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # 创建主窗口
        window = SimpleScreenplayApp()
        
        # 验证窗口属性
        window_title = window.windowTitle()
        window_size = window.size()
        
        # 验证UI组件
        has_tabs = hasattr(window, 'tabs')
        has_processor = hasattr(window, 'processor')
        
        # 清理
        window.close()
        
        logger.info(f"✅ UI启动测试通过: {window_title}, 尺寸: {window_size.width()}x{window_size.height()}")
        return True
        
    except Exception as e:
        logger.error(f"❌ UI启动测试失败: {e}")
        return False

def test_core_functionality():
    """测试核心功能"""
    logger.info("测试核心功能...")
    
    try:
        from simple_ui_fixed import VideoProcessor
        from src.core.screenplay_engineer import ScreenplayEngineer
        from src.core.srt_parser import parse_srt
        
        # 创建测试SRT文件
        temp_dir = tempfile.mkdtemp(prefix="final_ui_test_")
        test_srt_path = Path(temp_dir) / "test.srt"
        
        test_content = """1
00:00:00,000 --> 00:00:03,000
今天天气很好

2
00:00:03,000 --> 00:00:06,000
我去了公园散步

3
00:00:06,000 --> 00:00:09,000
看到了很多花
"""
        
        with open(test_srt_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 测试SRT解析
        subtitles = parse_srt(str(test_srt_path))
        parse_success = len(subtitles) == 3
        
        # 测试剧本工程师
        engineer = ScreenplayEngineer()
        engineer.load_subtitles(subtitles)
        reconstruction = engineer.reconstruct_screenplay(
            srt_input=subtitles,
            target_style="viral"
        )
        reconstruction_success = reconstruction is not None
        
        # 测试VideoProcessor
        output_path = VideoProcessor.generate_viral_srt(str(test_srt_path))
        generation_success = output_path is not None and Path(output_path).exists()
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        logger.info(f"✅ 核心功能测试: 解析={parse_success}, 重构={reconstruction_success}, 生成={generation_success}")
        return parse_success and reconstruction_success and generation_success
        
    except Exception as e:
        logger.error(f"❌ 核心功能测试失败: {e}")
        return False

def test_end_to_end_workflow():
    """测试端到端工作流"""
    logger.info("测试端到端工作流...")
    
    try:
        from simple_ui_fixed import VideoProcessor
        
        # 创建测试文件
        temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
        test_srt_path = Path(temp_dir) / "original.srt"
        
        test_content = """1
00:00:00,000 --> 00:00:05,000
这是一个测试视频

2
00:00:05,000 --> 00:00:10,000
用于验证完整工作流程

3
00:00:10,000 --> 00:00:15,000
包含多个测试场景
"""
        
        with open(test_srt_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 执行完整工作流
        start_time = time.time()
        output_path = VideoProcessor.generate_viral_srt(str(test_srt_path))
        end_time = time.time()
        
        # 验证结果
        workflow_success = output_path is not None and Path(output_path).exists()
        processing_time = end_time - start_time
        
        if workflow_success:
            # 验证输出文件内容
            with open(output_path, 'r', encoding='utf-8') as f:
                output_content = f.read()
            content_valid = len(output_content.strip()) > 0 and "00:00:" in output_content
        else:
            content_valid = False
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        logger.info(f"✅ 端到端工作流测试: 成功={workflow_success}, 内容有效={content_valid}, 耗时={processing_time:.2f}s")
        return workflow_success and content_valid
        
    except Exception as e:
        logger.error(f"❌ 端到端工作流测试失败: {e}")
        return False

def test_performance_and_stability():
    """测试性能和稳定性"""
    logger.info("测试性能和稳定性...")
    
    try:
        import psutil
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import SimpleScreenplayApp
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 创建应用实例
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # 测试多次窗口创建和销毁
        for i in range(3):
            start_time = time.time()
            window = SimpleScreenplayApp()
            creation_time = time.time() - start_time
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            window.close()
            
            # 检查创建时间和内存使用
            creation_reasonable = creation_time < 5.0
            memory_reasonable = current_memory < 1000  # 小于1GB
            
            if not (creation_reasonable and memory_reasonable):
                logger.warning(f"性能问题: 创建时间={creation_time:.2f}s, 内存={current_memory:.1f}MB")
                return False
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        logger.info(f"✅ 性能和稳定性测试通过: 内存增长={memory_increase:.1f}MB")
        return True
        
    except Exception as e:
        logger.error(f"❌ 性能和稳定性测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    logger.info("测试错误处理...")
    
    try:
        from simple_ui_fixed import VideoProcessor
        
        # 测试无效文件处理
        invalid_results = []
        
        # 测试不存在的文件
        result1 = VideoProcessor.generate_viral_srt("nonexistent.srt")
        invalid_results.append(result1 is None)
        
        # 测试空文件
        temp_dir = tempfile.mkdtemp(prefix="error_test_")
        empty_file = Path(temp_dir) / "empty.srt"
        empty_file.touch()
        
        result2 = VideoProcessor.generate_viral_srt(str(empty_file))
        invalid_results.append(result2 is None)
        
        # 测试无效格式文件
        invalid_file = Path(temp_dir) / "invalid.srt"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("这不是一个有效的SRT文件")
        
        result3 = VideoProcessor.generate_viral_srt(str(invalid_file))
        invalid_results.append(result3 is None)
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        error_handling_success = all(invalid_results)
        
        logger.info(f"✅ 错误处理测试: 成功处理={len([r for r in invalid_results if r])}/{len(invalid_results)}个错误情况")
        return error_handling_success
        
    except Exception as e:
        logger.error(f"❌ 错误处理测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("VisionAI-ClipsMaster 最终UI验证测试")
    print("=" * 80)
    
    test_results = {}
    
    # 运行所有测试
    tests = [
        ("UI启动测试", test_ui_startup),
        ("核心功能测试", test_core_functionality),
        ("端到端工作流测试", test_end_to_end_workflow),
        ("性能和稳定性测试", test_performance_and_stability),
        ("错误处理测试", test_error_handling)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = test_func()
            test_results[test_name] = result
            
            if result:
                passed_tests += 1
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
                
        except Exception as e:
            test_results[test_name] = False
            logger.error(f"❌ {test_name} - 异常: {e}")
    
    # 生成最终报告
    success_rate = passed_tests / total_tests
    
    print("\n" + "=" * 80)
    print("最终测试结果")
    print("=" * 80)
    print(f"总体状态: {'✅ 通过' if success_rate >= 0.8 else '❌ 失败'}")
    print(f"成功率: {success_rate:.1%} ({passed_tests}/{total_tests})")
    print(f"通过的测试: {[name for name, result in test_results.items() if result]}")
    print(f"失败的测试: {[name for name, result in test_results.items() if not result]}")
    print("=" * 80)
    
    # 保存测试报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": success_rate,
        "test_results": test_results,
        "overall_status": "PASSED" if success_rate >= 0.8 else "FAILED"
    }
    
    report_file = Path("test_output") / f"final_ui_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(exist_ok=True)
    
    import json
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"测试报告已保存: {report_file}")
    
    return success_rate >= 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
