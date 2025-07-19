#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 功能验证器
验证体积优化后的核心功能完整性
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

class FunctionValidator:
    def __init__(self):
        self.project_root = Path(".")
        self.test_results = {
            "validation_time": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "UNKNOWN",
            "critical_issues": [],
            "warnings": []
        }
    
    def log_test(self, test_name, status, message="", details=None):
        """记录测试结果"""
        self.test_results["tests"][test_name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        
        if status == "FAIL":
            self.test_results["critical_issues"].append(f"{test_name}: {message}")
        elif status == "WARN":
            self.test_results["warnings"].append(f"{test_name}: {message}")
    
    def test_critical_files(self):
        """测试关键文件存在性"""
        print("\n🔍 测试1: 关键文件完整性")
        
        critical_files = {
            "simple_ui_fixed.py": "主UI文件",
            "src/core": "核心模块目录",
            "configs/model_config.yaml": "模型配置文件",
            "tools/ffmpeg/bin/ffmpeg.exe": "FFmpeg可执行文件",
            "requirements.txt": "依赖清单"
        }
        
        all_exist = True
        missing_files = []
        
        for file_path, description in critical_files.items():
            if os.path.exists(file_path):
                self.log_test(f"文件存在_{file_path}", "PASS", f"{description} 存在")
            else:
                self.log_test(f"文件存在_{file_path}", "FAIL", f"{description} 缺失")
                missing_files.append(file_path)
                all_exist = False
        
        if all_exist:
            self.log_test("关键文件完整性", "PASS", "所有关键文件都存在")
        else:
            self.log_test("关键文件完整性", "FAIL", f"缺失文件: {', '.join(missing_files)}")
        
        return all_exist
    
    def test_ui_import(self):
        """测试UI模块导入"""
        print("\n🖥️ 测试2: UI模块导入")
        
        try:
            # 测试PyQt6导入
            import PyQt6
            self.log_test("PyQt6导入", "PASS", f"PyQt6版本: {PyQt6.QtCore.PYQT_VERSION_STR}")
            
            # 测试主UI文件语法
            with open("simple_ui_fixed.py", "r", encoding="utf-8") as f:
                ui_content = f.read()
            
            # 简单语法检查
            compile(ui_content, "simple_ui_fixed.py", "exec")
            self.log_test("UI文件语法", "PASS", "UI文件语法正确")
            
            return True
            
        except ImportError as e:
            self.log_test("PyQt6导入", "FAIL", f"PyQt6导入失败: {e}")
            return False
        except SyntaxError as e:
            self.log_test("UI文件语法", "FAIL", f"UI文件语法错误: {e}")
            return False
        except Exception as e:
            self.log_test("UI模块测试", "FAIL", f"未知错误: {e}")
            return False
    
    def test_ffmpeg_functionality(self):
        """测试FFmpeg功能"""
        print("\n🎬 测试3: FFmpeg功能")
        
        ffmpeg_path = "tools/ffmpeg/bin/ffmpeg.exe"
        
        if not os.path.exists(ffmpeg_path):
            self.log_test("FFmpeg存在性", "FAIL", "FFmpeg可执行文件不存在")
            return False
        
        try:
            # 测试FFmpeg版本
            result = subprocess.run([ffmpeg_path, "-version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.log_test("FFmpeg版本", "PASS", version_line)
                
                # 测试基本功能
                test_cmd = [ffmpeg_path, "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", 
                           "-t", "1", "-f", "null", "-"]
                
                test_result = subprocess.run(test_cmd, capture_output=True, timeout=30)
                
                if test_result.returncode == 0:
                    self.log_test("FFmpeg功能", "PASS", "FFmpeg基本功能正常")
                    return True
                else:
                    self.log_test("FFmpeg功能", "FAIL", "FFmpeg功能测试失败")
                    return False
            else:
                self.log_test("FFmpeg版本", "FAIL", f"FFmpeg版本检查失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_test("FFmpeg测试", "FAIL", "FFmpeg测试超时")
            return False
        except Exception as e:
            self.log_test("FFmpeg测试", "FAIL", f"FFmpeg测试异常: {e}")
            return False
    
    def test_core_modules(self):
        """测试核心模块"""
        print("\n⚙️ 测试4: 核心模块")
        
        core_modules = [
            "src/core/model_switcher.py",
            "src/core/language_detector.py", 
            "src/core/srt_parser.py",
            "src/core/screenplay_engineer.py",
            "src/core/clip_generator.py"
        ]
        
        all_modules_ok = True
        
        for module_path in core_modules:
            if os.path.exists(module_path):
                try:
                    # 检查Python语法
                    with open(module_path, "r", encoding="utf-8") as f:
                        module_content = f.read()
                    
                    compile(module_content, module_path, "exec")
                    self.log_test(f"模块语法_{os.path.basename(module_path)}", "PASS", "语法正确")
                    
                except SyntaxError as e:
                    self.log_test(f"模块语法_{os.path.basename(module_path)}", "FAIL", f"语法错误: {e}")
                    all_modules_ok = False
                except Exception as e:
                    self.log_test(f"模块检查_{os.path.basename(module_path)}", "FAIL", f"检查失败: {e}")
                    all_modules_ok = False
            else:
                self.log_test(f"模块存在_{os.path.basename(module_path)}", "FAIL", "模块文件不存在")
                all_modules_ok = False
        
        if all_modules_ok:
            self.log_test("核心模块完整性", "PASS", "所有核心模块都正常")
        else:
            self.log_test("核心模块完整性", "FAIL", "部分核心模块有问题")
        
        return all_modules_ok
    
    def test_config_files(self):
        """测试配置文件"""
        print("\n📋 测试5: 配置文件")
        
        config_files = {
            "configs/model_config.yaml": "模型配置",
            "configs/clip_settings.json": "剪辑设置",
            "configs/export_policy.yaml": "导出策略"
        }
        
        all_configs_ok = True
        
        for config_path, description in config_files.items():
            if os.path.exists(config_path):
                try:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        import yaml
                        with open(config_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    elif config_path.endswith('.json'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    
                    self.log_test(f"配置文件_{os.path.basename(config_path)}", "PASS", f"{description} 格式正确")
                    
                except Exception as e:
                    self.log_test(f"配置文件_{os.path.basename(config_path)}", "FAIL", f"{description} 格式错误: {e}")
                    all_configs_ok = False
            else:
                self.log_test(f"配置文件_{os.path.basename(config_path)}", "WARN", f"{description} 文件不存在")
        
        return all_configs_ok
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n💾 测试6: 内存使用")
        
        try:
            import psutil
            
            # 获取当前进程内存使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb < 100:  # 验证脚本本身应该很轻量
                self.log_test("验证器内存使用", "PASS", f"内存使用: {memory_mb:.1f}MB")
            else:
                self.log_test("验证器内存使用", "WARN", f"内存使用较高: {memory_mb:.1f}MB")
            
            # 检查系统可用内存
            available_memory_gb = psutil.virtual_memory().available / 1024 / 1024 / 1024
            
            if available_memory_gb >= 4:
                self.log_test("系统内存", "PASS", f"可用内存: {available_memory_gb:.1f}GB")
            else:
                self.log_test("系统内存", "WARN", f"可用内存不足: {available_memory_gb:.1f}GB")
            
            return True
            
        except ImportError:
            self.log_test("内存测试", "WARN", "psutil未安装，跳过内存测试")
            return True
        except Exception as e:
            self.log_test("内存测试", "FAIL", f"内存测试失败: {e}")
            return False
    
    def test_disk_space(self):
        """测试磁盘空间"""
        print("\n💿 测试7: 磁盘空间")
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_gb = free / 1024 / 1024 / 1024
            
            if free_gb >= 2:
                self.log_test("磁盘空间", "PASS", f"可用空间: {free_gb:.1f}GB")
            else:
                self.log_test("磁盘空间", "WARN", f"磁盘空间不足: {free_gb:.1f}GB")
            
            return True
            
        except Exception as e:
            self.log_test("磁盘空间测试", "FAIL", f"磁盘空间检查失败: {e}")
            return False
    
    def run_validation(self):
        """运行完整验证"""
        print("🚀 开始VisionAI-ClipsMaster功能验证")
        print(f"📁 项目目录: {self.project_root.absolute()}")
        print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 执行所有测试
        tests = [
            self.test_critical_files,
            self.test_ui_import,
            self.test_ffmpeg_functionality,
            self.test_core_modules,
            self.test_config_files,
            self.test_memory_usage,
            self.test_disk_space
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(f"测试异常_{test_func.__name__}", "FAIL", f"测试执行异常: {e}")
        
        # 计算总体状态
        pass_rate = passed_tests / total_tests
        
        if pass_rate >= 0.9:
            self.test_results["overall_status"] = "PASS"
            status_msg = f"验证通过 ({passed_tests}/{total_tests})"
        elif pass_rate >= 0.7:
            self.test_results["overall_status"] = "WARN"
            status_msg = f"部分通过 ({passed_tests}/{total_tests})"
        else:
            self.test_results["overall_status"] = "FAIL"
            status_msg = f"验证失败 ({passed_tests}/{total_tests})"
        
        print(f"\n📊 验证结果: {status_msg}")
        
        if self.test_results["critical_issues"]:
            print("\n❌ 关键问题:")
            for issue in self.test_results["critical_issues"]:
                print(f"  • {issue}")
        
        if self.test_results["warnings"]:
            print("\n⚠️ 警告:")
            for warning in self.test_results["warnings"]:
                print(f"  • {warning}")
        
        # 保存验证报告
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 验证报告已保存: {report_file}")
        
        return self.test_results["overall_status"] == "PASS"

def main():
    validator = FunctionValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print("\n🎉 所有验证通过，系统功能正常!")
            sys.exit(0)
        else:
            print("\n⚠️ 验证发现问题，请检查报告")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ 用户中断验证")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
