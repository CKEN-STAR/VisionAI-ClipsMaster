#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试数据管理与清理
创建测试数据、执行测试后的完整清理工作
"""

import os
import sys
import json
import time
import traceback
import tempfile
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TestDataManagementSuite:
    """测试数据管理套件"""
    
    def __init__(self):
        self.test_results = {}
        self.created_files = []
        self.created_dirs = []
        self.temp_dirs = []
        
    def create_test_data(self) -> Dict[str, Any]:
        """创建测试数据"""
        print("\n=== 创建测试数据 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 创建中英文测试字幕文件
            test_data = self.create_subtitle_test_data()
            results["details"]["subtitle_files"] = test_data["subtitle_files"]
            
            # 创建训练数据
            training_data = self.create_training_test_data()
            results["details"]["training_files"] = training_data["training_files"]
            
            # 创建配置文件
            config_data = self.create_config_test_data()
            results["details"]["config_files"] = config_data["config_files"]
            
            # 创建模拟视频文件
            video_data = self.create_video_test_data()
            results["details"]["video_files"] = video_data["video_files"]
            
            total_files = (len(test_data["subtitle_files"]) + 
                          len(training_data["training_files"]) + 
                          len(config_data["config_files"]) + 
                          len(video_data["video_files"]))
            
            results["details"]["total_files_created"] = total_files
            print(f"✓ 测试数据创建完成，共创建 {total_files} 个文件")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"创建测试数据失败: {str(e)}"
            print(f"✗ 创建测试数据失败: {e}")
        
        return results
    
    def create_subtitle_test_data(self) -> Dict[str, List[str]]:
        """创建字幕测试数据"""
        subtitle_files = []
        
        # 英文字幕
        english_srt = """1
00:00:01,000 --> 00:00:03,000
Hello, this is an English test subtitle.

2
00:00:03,500 --> 00:00:05,500
This is the second English subtitle line.

3
00:00:06,000 --> 00:00:08,000
And this is the third English line.
"""
        
        # 中文字幕
        chinese_srt = """1
00:00:01,000 --> 00:00:03,000
你好，这是一个中文测试字幕。

2
00:00:03,500 --> 00:00:05,500
这是第二行中文字幕。

3
00:00:06,000 --> 00:00:08,000
这是第三行中文字幕。
"""
        
        # 创建测试目录
        test_dir = self.create_temp_dir("subtitle_test")
        
        # 保存英文字幕
        en_file = os.path.join(test_dir, "test_english.srt")
        with open(en_file, 'w', encoding='utf-8') as f:
            f.write(english_srt)
        subtitle_files.append(en_file)
        self.created_files.append(en_file)
        
        # 保存中文字幕
        zh_file = os.path.join(test_dir, "test_chinese.srt")
        with open(zh_file, 'w', encoding='utf-8') as f:
            f.write(chinese_srt)
        subtitle_files.append(zh_file)
        self.created_files.append(zh_file)
        
        print(f"✓ 创建字幕测试文件: {len(subtitle_files)} 个")
        return {"subtitle_files": subtitle_files}
    
    def create_training_test_data(self) -> Dict[str, List[str]]:
        """创建训练测试数据"""
        training_files = []
        
        # 创建训练数据目录
        training_dir = self.create_temp_dir("training_test")
        
        # 英文训练数据
        en_training_data = {
            "original_subtitles": [
                "Hello, how are you today?",
                "I am fine, thank you very much.",
                "What are you doing this weekend?"
            ],
            "viral_subtitles": [
                "Hey! What's up today?",
                "I'm amazing, thanks!",
                "Weekend plans? Tell me!"
            ]
        }
        
        en_file = os.path.join(training_dir, "en_training_data.json")
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump(en_training_data, f, ensure_ascii=False, indent=2)
        training_files.append(en_file)
        self.created_files.append(en_file)
        
        # 中文训练数据
        zh_training_data = {
            "original_subtitles": [
                "你好，今天怎么样？",
                "我很好，谢谢你。",
                "这个周末你打算做什么？"
            ],
            "viral_subtitles": [
                "嗨！今天咋样？",
                "我超棒的，谢啦！",
                "周末计划？快说说！"
            ]
        }
        
        zh_file = os.path.join(training_dir, "zh_training_data.json")
        with open(zh_file, 'w', encoding='utf-8') as f:
            json.dump(zh_training_data, f, ensure_ascii=False, indent=2)
        training_files.append(zh_file)
        self.created_files.append(zh_file)
        
        print(f"✓ 创建训练测试文件: {len(training_files)} 个")
        return {"training_files": training_files}
    
    def create_config_test_data(self) -> Dict[str, List[str]]:
        """创建配置测试数据"""
        config_files = []
        
        # 创建配置目录
        config_dir = self.create_temp_dir("config_test")
        
        # 测试模型配置
        model_config = {
            "available_models": [
                {
                    "name": "test-mistral-7b",
                    "language": "en",
                    "quantization": "Q4_K_M",
                    "memory_requirement_mb": 3200
                },
                {
                    "name": "test-qwen2.5-7b",
                    "language": "zh",
                    "quantization": "Q4_K_M",
                    "memory_requirement_mb": 2800
                }
            ],
            "memory_management": {
                "max_memory_mb": 3800,
                "enable_dynamic_loading": True
            }
        }
        
        config_file = os.path.join(config_dir, "test_model_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, ensure_ascii=False, indent=2)
        config_files.append(config_file)
        self.created_files.append(config_file)
        
        print(f"✓ 创建配置测试文件: {len(config_files)} 个")
        return {"config_files": config_files}
    
    def create_video_test_data(self) -> Dict[str, List[str]]:
        """创建视频测试数据（模拟文件）"""
        video_files = []
        
        # 创建视频目录
        video_dir = self.create_temp_dir("video_test")
        
        # 创建模拟视频文件（空文件，仅用于测试）
        video_names = ["test_video_1.mp4", "test_video_2.mp4", "test_video_3.avi"]
        
        for video_name in video_names:
            video_file = os.path.join(video_dir, video_name)
            # 创建空文件模拟视频
            with open(video_file, 'w') as f:
                f.write("# Mock video file for testing")
            video_files.append(video_file)
            self.created_files.append(video_file)
        
        print(f"✓ 创建视频测试文件: {len(video_files)} 个")
        return {"video_files": video_files}
    
    def create_temp_dir(self, prefix: str) -> str:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp(prefix=f"{prefix}_")
        self.temp_dirs.append(temp_dir)
        self.created_dirs.append(temp_dir)
        return temp_dir
    
    def verify_test_data(self) -> Dict[str, Any]:
        """验证测试数据"""
        print("\n=== 验证测试数据 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 验证文件存在性
            existing_files = []
            missing_files = []
            
            for file_path in self.created_files:
                if os.path.exists(file_path):
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            results["details"]["existing_files"] = len(existing_files)
            results["details"]["missing_files"] = len(missing_files)
            results["details"]["total_files"] = len(self.created_files)
            
            # 验证目录存在性
            existing_dirs = []
            missing_dirs = []
            
            for dir_path in self.created_dirs:
                if os.path.exists(dir_path):
                    existing_dirs.append(dir_path)
                else:
                    missing_dirs.append(dir_path)
            
            results["details"]["existing_dirs"] = len(existing_dirs)
            results["details"]["missing_dirs"] = len(missing_dirs)
            results["details"]["total_dirs"] = len(self.created_dirs)
            
            # 验证文件内容
            content_verification = self.verify_file_contents()
            results["details"]["content_verification"] = content_verification
            
            if len(missing_files) == 0 and len(missing_dirs) == 0:
                print(f"✓ 测试数据验证通过: {len(existing_files)} 文件, {len(existing_dirs)} 目录")
            else:
                results["status"] = "partial_failure"
                print(f"⚠ 测试数据验证部分失败: 缺失 {len(missing_files)} 文件, {len(missing_dirs)} 目录")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"验证测试数据失败: {str(e)}"
            print(f"✗ 验证测试数据失败: {e}")
        
        return results
    
    def verify_file_contents(self) -> Dict[str, Any]:
        """验证文件内容"""
        verification_results = {}
        
        for file_path in self.created_files:
            try:
                if file_path.endswith('.srt'):
                    # 验证SRT文件格式
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '-->' in content and content.strip():
                            verification_results[file_path] = "valid_srt"
                        else:
                            verification_results[file_path] = "invalid_srt"
                
                elif file_path.endswith('.json'):
                    # 验证JSON文件格式
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)  # 尝试解析JSON
                        verification_results[file_path] = "valid_json"
                
                else:
                    # 其他文件类型
                    if os.path.getsize(file_path) > 0:
                        verification_results[file_path] = "non_empty"
                    else:
                        verification_results[file_path] = "empty"
            
            except Exception as e:
                verification_results[file_path] = f"error: {str(e)}"
        
        return verification_results
    
    def cleanup_test_data(self) -> Dict[str, Any]:
        """清理测试数据"""
        print("\n=== 清理测试数据 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 清理文件
            cleaned_files = 0
            failed_files = []
            
            for file_path in self.created_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned_files += 1
                except Exception as e:
                    failed_files.append({"file": file_path, "error": str(e)})
            
            # 清理目录
            cleaned_dirs = 0
            failed_dirs = []
            
            for dir_path in self.created_dirs:
                try:
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path)
                        cleaned_dirs += 1
                except Exception as e:
                    failed_dirs.append({"dir": dir_path, "error": str(e)})
            
            # 清理临时目录
            for temp_dir in self.temp_dirs:
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                except Exception:
                    pass  # 忽略临时目录清理错误
            
            results["details"]["cleaned_files"] = cleaned_files
            results["details"]["failed_files"] = len(failed_files)
            results["details"]["cleaned_dirs"] = cleaned_dirs
            results["details"]["failed_dirs"] = len(failed_dirs)
            results["details"]["total_files"] = len(self.created_files)
            results["details"]["total_dirs"] = len(self.created_dirs)
            
            if len(failed_files) == 0 and len(failed_dirs) == 0:
                print(f"✓ 测试数据清理完成: {cleaned_files} 文件, {cleaned_dirs} 目录")
            else:
                results["status"] = "partial_failure"
                print(f"⚠ 测试数据清理部分失败: 失败 {len(failed_files)} 文件, {len(failed_dirs)} 目录")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"清理测试数据失败: {str(e)}"
            print(f"✗ 清理测试数据失败: {e}")
        
        return results
    
    def cleanup_test_reports(self) -> Dict[str, Any]:
        """清理测试报告文件"""
        print("\n=== 清理测试报告 ===")
        results = {"status": "success", "details": {}}
        
        try:
            # 查找所有测试报告文件
            report_patterns = [
                "*_test_report_*.json",
                "*_test_*.json",
                "test_*_report.json"
            ]
            
            report_files = []
            for pattern in report_patterns:
                report_files.extend(glob.glob(pattern))
            
            # 清理报告文件
            cleaned_reports = 0
            failed_reports = []
            
            for report_file in report_files:
                try:
                    if os.path.exists(report_file):
                        os.remove(report_file)
                        cleaned_reports += 1
                        print(f"  清理报告: {report_file}")
                except Exception as e:
                    failed_reports.append({"file": report_file, "error": str(e)})
            
            results["details"]["cleaned_reports"] = cleaned_reports
            results["details"]["failed_reports"] = len(failed_reports)
            results["details"]["total_reports"] = len(report_files)
            
            if len(failed_reports) == 0:
                print(f"✓ 测试报告清理完成: {cleaned_reports} 个报告文件")
            else:
                results["status"] = "partial_failure"
                print(f"⚠ 测试报告清理部分失败: 失败 {len(failed_reports)} 个文件")
            
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"清理测试报告失败: {str(e)}"
            print(f"✗ 清理测试报告失败: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始VisionAI-ClipsMaster测试数据管理")
        print("=" * 60)
        
        all_results = {}
        
        # 执行各项测试
        test_methods = [
            ("create_test_data", self.create_test_data),
            ("verify_test_data", self.verify_test_data),
            ("cleanup_test_data", self.cleanup_test_data),
            ("cleanup_test_reports", self.cleanup_test_reports)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                all_results[test_name] = result
            except Exception as e:
                all_results[test_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                print(f"✗ {test_name} 执行异常: {e}")
        
        return all_results

def main():
    """主函数"""
    test_suite = TestDataManagementSuite()
    
    # 运行测试
    results = test_suite.run_all_tests()
    
    # 生成最终报告
    report_file = f"test_data_management_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 测试数据管理报告已生成: {report_file}")
    
    # 统计测试结果
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
    
    print(f"\n📈 测试统计:")
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {successful_tests}")
    print(f"失败测试: {total_tests - successful_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
