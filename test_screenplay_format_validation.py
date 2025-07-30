#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本重构结果格式验证测试
验证修复后的剧本重构功能返回正确的标准化格式
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_screenplay_format_validation():
    """测试剧本重构结果格式验证"""
    print("=" * 60)
    print("剧本重构结果格式验证测试")
    print("=" * 60)
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        from src.core.srt_parser import SRTParser
        
        # 创建测试数据
        test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是一个关于爱情的故事

2
00:00:03,000 --> 00:00:05,000
男主角是一个普通的上班族

3
00:00:05,000 --> 00:00:07,000
女主角是一个美丽的画家

4
00:00:07,000 --> 00:00:10,000
他们在咖啡厅相遇了

5
00:00:10,000 --> 00:00:12,000
这是命运的安排吗？"""
        
        # 保存测试文件
        test_file = "test_format_validation.srt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_srt_content)
        
        print("✓ 测试SRT文件创建成功")
        
        # 解析SRT文件
        parser = SRTParser()
        subtitles = parser.parse_srt_file(test_file)
        print(f"✓ SRT解析成功，共解析到 {len(subtitles)} 条字幕")
        
        # 创建剧本工程师
        engineer = ScreenplayEngineer()
        print("✓ 剧本工程师初始化成功")
        
        # 测试剧本重构
        reconstructed = engineer.reconstruct_screenplay(subtitles)
        print(f"✓ 剧本重构完成，生成 {len(reconstructed)} 个片段")
        
        # 验证返回格式
        format_valid = True
        format_errors = []
        
        # 1. 检查返回类型
        if not isinstance(reconstructed, list):
            format_valid = False
            format_errors.append(f"返回类型错误：期望 list，实际 {type(reconstructed)}")
        else:
            print("✓ 返回类型正确：list")
        
        # 2. 检查每个片段的格式
        required_fields = ["start", "end", "text", "duration"]
        
        for i, segment in enumerate(reconstructed):
            if not isinstance(segment, dict):
                format_valid = False
                format_errors.append(f"片段{i+1}类型错误：期望 dict，实际 {type(segment)}")
                continue
                
            # 检查必需字段
            for field in required_fields:
                if field not in segment:
                    format_valid = False
                    format_errors.append(f"片段{i+1}缺少字段：{field}")
                    continue
                    
                # 检查字段类型
                if field in ["start", "end", "duration"]:
                    if not isinstance(segment[field], (int, float)):
                        format_valid = False
                        format_errors.append(f"片段{i+1}字段{field}类型错误：期望 number，实际 {type(segment[field])}")
                elif field == "text":
                    if not isinstance(segment[field], str):
                        format_valid = False
                        format_errors.append(f"片段{i+1}字段{field}类型错误：期望 str，实际 {type(segment[field])}")
        
        # 3. 检查时间逻辑
        for i, segment in enumerate(reconstructed):
            if isinstance(segment, dict) and "start" in segment and "end" in segment:
                if segment["start"] >= segment["end"]:
                    format_valid = False
                    format_errors.append(f"片段{i+1}时间逻辑错误：start({segment['start']}) >= end({segment['end']})")
                    
                if "duration" in segment:
                    expected_duration = segment["end"] - segment["start"]
                    actual_duration = segment["duration"]
                    if abs(expected_duration - actual_duration) > 0.1:  # 允许0.1秒误差
                        format_valid = False
                        format_errors.append(f"片段{i+1}时长计算错误：期望{expected_duration:.2f}，实际{actual_duration:.2f}")
        
        # 输出验证结果
        if format_valid:
            print("✅ 格式验证通过：所有片段格式正确")
            
            # 显示格式化的结果示例
            print("\n格式化结果示例：")
            for i, segment in enumerate(reconstructed[:3]):  # 只显示前3个
                print(f"  片段{i+1}:")
                print(f"    start: {segment['start']:.2f}")
                print(f"    end: {segment['end']:.2f}")
                print(f"    duration: {segment['duration']:.2f}")
                print(f"    text: '{segment['text']}'")
                print()
                
            # 保存格式验证结果
            validation_result = {
                "status": "success",
                "total_segments": len(reconstructed),
                "format_valid": True,
                "sample_segments": reconstructed[:3],
                "validation_time": __import__('datetime').datetime.now().isoformat()
            }
            
            with open("test_output/screenplay_format_validation.json", "w", encoding="utf-8") as f:
                json.dump(validation_result, f, ensure_ascii=False, indent=2)
                
            print("✅ 格式验证结果已保存到 test_output/screenplay_format_validation.json")
            
        else:
            print("❌ 格式验证失败：")
            for error in format_errors:
                print(f"  - {error}")
                
            # 保存错误信息
            validation_result = {
                "status": "failed",
                "format_valid": False,
                "errors": format_errors,
                "validation_time": __import__('datetime').datetime.now().isoformat()
            }
            
            with open("test_output/screenplay_format_validation.json", "w", encoding="utf-8") as f:
                json.dump(validation_result, f, ensure_ascii=False, indent=2)
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✓ 测试文件清理完成")
        
        return format_valid
        
    except Exception as e:
        print(f"❌ 格式验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """测试边缘情况"""
    print("\n" + "=" * 60)
    print("边缘情况测试")
    print("=" * 60)
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        engineer = ScreenplayEngineer()
        
        # 测试空输入
        result = engineer.reconstruct_screenplay([])
        if isinstance(result, list) and len(result) == 0:
            print("✅ 空输入测试通过")
        else:
            print(f"❌ 空输入测试失败：期望空列表，实际 {result}")
            
        # 测试单个字幕
        single_subtitle = [{
            "id": 1,
            "start_time": 1.0,
            "end_time": 3.0,
            "duration": 2.0,
            "text": "单个测试字幕"
        }]
        
        result = engineer.reconstruct_screenplay(single_subtitle)
        if isinstance(result, list) and len(result) > 0:
            print("✅ 单个字幕测试通过")
        else:
            print(f"❌ 单个字幕测试失败：{result}")
            
        return True
        
    except Exception as e:
        print(f"❌ 边缘情况测试失败: {e}")
        return False

def main():
    """主函数"""
    print("VisionAI-ClipsMaster 剧本重构格式验证测试")
    print("测试时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 确保输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    # 执行测试
    format_test_passed = test_screenplay_format_validation()
    edge_test_passed = test_edge_cases()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if format_test_passed and edge_test_passed:
        print("🎉 所有测试通过！剧本重构功能格式正确")
        return True
    else:
        print("❌ 部分测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
