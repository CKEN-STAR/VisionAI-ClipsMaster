#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强模块测试脚本
Test Script for Enhanced Modules

验证修复后的功能是否正常工作
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_enhanced_language_detector():
    """测试增强语言检测器"""
    print("🔍 测试增强语言检测器...")
    
    try:
        from src.core.enhanced_language_detector import EnhancedLanguageDetector
        
        detector = EnhancedLanguageDetector()
        
        # 测试用例
        test_cases = [
            ("Hello world, this is a test.", "en"),
            ("你好世界，这是一个测试。", "zh"),
            ("今天天气很好，我去了公园散步", "zh"),
            ("The weather is nice today, I went to the park", "en"),
            ("霸道总裁的秘密终于曝光了！", "zh"),
            ("SHOCKING! The CEO's secret is finally revealed!", "en")
        ]
        
        success_count = 0
        for text, expected in test_cases:
            detected = detector.detect_language(text)
            is_correct = detected == expected
            status = "✅" if is_correct else "❌"
            print(f"  {status} '{text[:30]}...' -> {detected} (期望: {expected})")
            
            if is_correct:
                success_count += 1
                
        accuracy = success_count / len(test_cases) * 100
        print(f"  📊 准确率: {accuracy:.1f}% ({success_count}/{len(test_cases)})")
        
        return accuracy >= 80  # 80%以上算通过
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_enhanced_model_switcher():
    """测试增强模型切换器"""
    print("🤖 测试增强模型切换器...")
    
    try:
        from src.core.enhanced_model_switcher import EnhancedModelSwitcher
        
        switcher = EnhancedModelSwitcher()
        
        # 测试模型切换
        print("  🔄 测试中文模型切换...")
        zh_result = switcher.switch_to_language("zh")
        print(f"    中文模型切换: {'✅' if zh_result else '❌'}")
        
        print("  🔄 测试英文模型切换...")
        en_result = switcher.switch_to_language("en")
        print(f"    英文模型切换: {'✅' if en_result else '❌'}")
        
        # 测试内容生成
        print("  📝 测试内容生成...")
        zh_content = switcher.generate_viral_content("今天发生了一件有趣的事情")
        en_content = switcher.generate_viral_content("Something interesting happened today")
        
        zh_success = zh_content.get("success", False)
        en_success = en_content.get("success", False)
        
        print(f"    中文内容生成: {'✅' if zh_success else '❌'}")
        print(f"    英文内容生成: {'✅' if en_success else '❌'}")
        
        if zh_success:
            print(f"    中文生成结果: {zh_content.get('generated_text', '')[:50]}...")
        if en_success:
            print(f"    英文生成结果: {en_content.get('generated_text', '')[:50]}...")
            
        # 获取模型状态
        status = switcher.get_model_status()
        print(f"  📊 模型状态获取: {'✅' if status else '❌'}")
        
        return zh_result and en_result and zh_success and en_success
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_enhanced_screenplay_engineer():
    """测试增强剧本工程师"""
    print("📝 测试增强剧本工程师...")
    
    try:
        from src.core.enhanced_screenplay_engineer import EnhancedScreenplayEngineer
        
        engineer = EnhancedScreenplayEngineer()
        
        # 创建测试SRT内容
        test_srt = """1
00:00:00,000 --> 00:00:03,000
林晓雨匆忙走进公司大楼

2
00:00:03,000 --> 00:00:06,000
她今天要面试一家顶级投资公司

3
00:00:06,000 --> 00:00:09,000
电梯门打开，一个高大的身影走了出来

4
00:00:09,000 --> 00:00:12,000
那是公司的CEO，陈墨轩

5
00:00:12,000 --> 00:00:15,000
两人的目光在电梯前相遇"""

        # 测试剧情分析
        print("  🔍 测试剧情结构分析...")
        analysis = engineer.analyze_plot_structure(test_srt)
        analysis_success = "error" not in analysis
        print(f"    剧情分析: {'✅' if analysis_success else '❌'}")
        
        if analysis_success:
            print(f"    检测语言: {analysis.get('language', 'unknown')}")
            print(f"    字幕数量: {analysis.get('total_subtitles', 0)}")
            print(f"    剧情类型: {analysis.get('genre', 'unknown')}")
            
        # 测试爆款生成
        print("  🎯 测试爆款版本生成...")
        viral_result = engineer.generate_viral_version(test_srt, "zh")
        viral_success = viral_result.get("success", False)
        print(f"    爆款生成: {'✅' if viral_success else '❌'}")
        
        if viral_success:
            viral_subtitles = viral_result.get("subtitles", [])
            print(f"    爆款字幕数: {len(viral_subtitles)}")
            print(f"    压缩比: {viral_result.get('compression_ratio', 0):.2f}")
            print(f"    质量分数: {viral_result.get('quality_metrics', {}).get('overall_score', 0):.2f}")
            
            if viral_subtitles:
                print(f"    示例爆款文本: {viral_subtitles[0].get('text', '')[:30]}...")
                
        return analysis_success and viral_success
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_enhanced_sync_engine():
    """测试增强同步引擎"""
    print("⚡ 测试增强同步引擎...")
    
    try:
        from src.core.enhanced_sync_engine import EnhancedSyncEngine
        
        sync_engine = EnhancedSyncEngine()
        
        # 创建测试数据
        test_subtitles = [
            {"start_time": 0.0, "end_time": 3.0, "text": "测试字幕1"},
            {"start_time": 3.0, "end_time": 6.0, "text": "测试字幕2"},
            {"start_time": 6.0, "end_time": 9.0, "text": "测试字幕3"}
        ]
        
        test_video_shots = [
            {"start": 0.0, "end": 3.5, "shot_id": 1},
            {"start": 3.5, "end": 6.5, "shot_id": 2},
            {"start": 6.5, "end": 9.5, "shot_id": 3}
        ]
        
        # 测试字幕映射
        print("  🎯 测试字幕映射...")
        mapped_shot = sync_engine.map_subtitle_to_shot(test_subtitles[0], test_video_shots)
        mapping_success = mapped_shot is not None
        print(f"    字幕映射: {'✅' if mapping_success else '❌'}")
        
        # 测试同步精度计算
        print("  📊 测试同步精度计算...")
        accuracy_result = sync_engine.calculate_sync_accuracy(test_subtitles, test_video_shots)
        accuracy_success = "mapping_success_rate" in accuracy_result
        print(f"    精度计算: {'✅' if accuracy_success else '❌'}")
        
        if accuracy_success:
            success_rate = accuracy_result["mapping_success_rate"]
            avg_error = accuracy_result["average_sync_error"]
            print(f"    映射成功率: {success_rate:.1%}")
            print(f"    平均误差: {avg_error:.3f}秒")
            print(f"    容忍度内比例: {accuracy_result.get('within_tolerance_rate', 0):.1%}")
            
        return mapping_success and accuracy_success
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def test_enhanced_workflow_manager():
    """测试增强工作流管理器"""
    print("🔄 测试增强工作流管理器...")
    
    try:
        from src.core.enhanced_workflow_manager import EnhancedWorkflowManager
        
        # 创建测试SRT文件
        test_srt_content = """1
00:00:00,000 --> 00:00:03,000
测试字幕内容

2
00:00:03,000 --> 00:00:06,000
这是一个测试"""

        test_srt_path = "test_input.srt"
        with open(test_srt_path, 'w', encoding='utf-8') as f:
            f.write(test_srt_content)
            
        # 创建工作流管理器
        def progress_callback(current, total, message):
            print(f"    进度: {current}/{total} - {message}")
            
        workflow_manager = EnhancedWorkflowManager(progress_callback=progress_callback)
        
        # 测试完整工作流
        print("  🎬 测试完整工作流...")
        result = workflow_manager.process_complete_workflow(
            video_path="test_video.mp4",
            srt_path=test_srt_path,
            output_path="test_output.mp4",
            language="zh"
        )
        
        workflow_success = result.get("success", False)
        print(f"    工作流执行: {'✅' if workflow_success else '❌'}")
        
        if workflow_success:
            print(f"    处理时长: {result.get('total_duration', 0):.2f}秒")
            print(f"    完成步骤: {result.get('steps_completed', 0)}")
            print(f"    输出文件: {result.get('viral_srt_path', 'N/A')}")
        else:
            print(f"    错误信息: {result.get('error', '未知错误')}")
            
        # 清理测试文件
        try:
            Path(test_srt_path).unlink()
        except:
            pass
            
        return workflow_success
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 VisionAI-ClipsMaster 增强模块综合测试")
    print("=" * 60)
    
    test_results = {}
    
    # 运行各项测试
    test_functions = [
        ("语言检测器", test_enhanced_language_detector),
        ("模型切换器", test_enhanced_model_switcher),
        ("剧本工程师", test_enhanced_screenplay_engineer),
        ("同步引擎", test_enhanced_sync_engine),
        ("工作流管理器", test_enhanced_workflow_manager)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n{test_name} 测试:")
        start_time = time.time()
        
        try:
            result = test_func()
            test_results[test_name] = result
            duration = time.time() - start_time
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  结果: {status} (耗时: {duration:.2f}秒)")
        except Exception as e:
            test_results[test_name] = False
            print(f"  结果: ❌ 异常 - {e}")
            
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    pass_rate = passed_tests / total_tests * 100
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
        
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 通过 ({pass_rate:.1f}%)")
    
    if pass_rate >= 80:
        print("🎉 测试通过！增强模块工作正常。")
        return True
    else:
        print("⚠️ 测试未完全通过，部分功能可能存在问题。")
        return False

def main():
    """主函数"""
    success = run_comprehensive_test()
    
    # 保存测试报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"enhanced_modules_test_report_{timestamp}.json"
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_success": success,
        "python_version": sys.version,
        "test_environment": "enhanced_modules"
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 测试报告已保存: {report_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
