#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 系统测试 - 阶段一：基础环境验证
测试环境：使用系统Python解释器 C:\\Users\\13075\\AppData\\Local\\Programs\\Python\\Python313\\python.exe
内存限制：3.8GB峰值内存
硬件环境：纯CPU推理模式
"""

import os
import sys
import json
import yaml
import subprocess
import importlib
import time
from pathlib import Path
from datetime import datetime
import psutil
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stage1_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Stage1EnvironmentValidator:
    """阶段一：基础环境验证器"""
    
    def __init__(self):
        self.test_results = {
            "stage": "基础环境验证",
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        self.core_path = Path("VisionAI-ClipsMaster-Core")
        
    def log_test_result(self, test_name, status, details=None, warning=None):
        """记录测试结果"""
        self.test_results["tests"][test_name] = {
            "status": status,
            "details": details or "",
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results["summary"]["total_tests"] += 1
        if status == "PASS":
            self.test_results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.test_results["summary"]["failed"] += 1
        if warning:
            self.test_results["summary"]["warnings"] += 1
            
    def test_python_interpreter(self):
        """测试Python解释器版本和路径"""
        logger.info("测试Python解释器...")
        try:
            python_path = sys.executable
            python_version = sys.version
            
            # 检查是否使用系统Python
            expected_path = r"C:\\Users\\13075\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"
            
            details = f"Python路径: {python_path}\nPython版本: {python_version}"
            
            if expected_path.lower() in python_path.lower():
                self.log_test_result("Python解释器", "PASS", details)
                logger.info("✓ 使用正确的系统Python解释器")
            else:
                warning = f"当前使用: {python_path}, 建议使用: {expected_path}"
                self.log_test_result("Python解释器", "PASS", details, warning)
                logger.warning(f"⚠ {warning}")
                
        except Exception as e:
            self.log_test_result("Python解释器", "FAIL", f"错误: {str(e)}")
            logger.error(f"✗ Python解释器测试失败: {e}")
            
    def test_core_dependencies(self):
        """测试核心依赖包"""
        logger.info("测试核心依赖包...")
        
        # 核心依赖列表
        core_deps = [
            "torch", "transformers", "huggingface_hub", "yaml", 
            "cv2", "numpy", "pandas", "psutil", "PyQt6",
            "jieba", "spacy", "langdetect", "tqdm"
        ]
        
        failed_deps = []
        passed_deps = []
        
        for dep in core_deps:
            try:
                if dep == "yaml":
                    import yaml
                elif dep == "cv2":
                    import cv2
                elif dep == "PyQt6":
                    import PyQt6
                else:
                    importlib.import_module(dep)
                passed_deps.append(dep)
                logger.info(f"✓ {dep} 导入成功")
            except ImportError as e:
                failed_deps.append(f"{dep}: {str(e)}")
                logger.error(f"✗ {dep} 导入失败: {e}")
                
        if not failed_deps:
            self.log_test_result("核心依赖包", "PASS", f"成功导入: {', '.join(passed_deps)}")
        else:
            self.log_test_result("核心依赖包", "FAIL", 
                               f"失败: {'; '.join(failed_deps)}\n成功: {', '.join(passed_deps)}")
                               
    def test_config_files(self):
        """测试配置文件完整性"""
        logger.info("测试配置文件...")
        
        config_files = [
            "configs/model_config.yaml",
            "configs/active_model.yaml", 
            "configs/clip_settings.json",
            "configs/security_policy.json",
            "configs/export_policy.yaml"
        ]
        
        results = []
        for config_file in config_files:
            config_path = self.core_path / config_file
            try:
                if config_path.exists():
                    if config_file.endswith('.yaml'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    elif config_file.endswith('.json'):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                    results.append(f"✓ {config_file}")
                    logger.info(f"✓ {config_file} 验证通过")
                else:
                    results.append(f"✗ {config_file} 不存在")
                    logger.error(f"✗ {config_file} 不存在")
            except Exception as e:
                results.append(f"✗ {config_file}: {str(e)}")
                logger.error(f"✗ {config_file} 解析失败: {e}")
                
        if all("✓" in result for result in results):
            self.log_test_result("配置文件", "PASS", "\n".join(results))
        else:
            self.log_test_result("配置文件", "FAIL", "\n".join(results))
            
    def test_ffmpeg_tools(self):
        """测试FFmpeg工具链"""
        logger.info("测试FFmpeg工具链...")
        
        ffmpeg_path = self.core_path / "tools" / "ffmpeg" / "bin"
        tools = ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]
        
        results = []
        for tool in tools:
            tool_path = ffmpeg_path / tool
            if tool_path.exists():
                try:
                    # 测试工具版本
                    result = subprocess.run([str(tool_path), "-version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_line = result.stdout.split('\n')[0]
                        results.append(f"✓ {tool}: {version_line}")
                        logger.info(f"✓ {tool} 可用")
                    else:
                        results.append(f"✗ {tool}: 执行失败")
                        logger.error(f"✗ {tool} 执行失败")
                except subprocess.TimeoutExpired:
                    results.append(f"✗ {tool}: 超时")
                    logger.error(f"✗ {tool} 执行超时")
                except Exception as e:
                    results.append(f"✗ {tool}: {str(e)}")
                    logger.error(f"✗ {tool} 错误: {e}")
            else:
                results.append(f"✗ {tool}: 文件不存在")
                logger.error(f"✗ {tool} 文件不存在")
                
        if all("✓" in result for result in results):
            self.log_test_result("FFmpeg工具链", "PASS", "\n".join(results))
        else:
            self.log_test_result("FFmpeg工具链", "FAIL", "\n".join(results))

    def test_chinese_encoding(self):
        """测试中文字体和编码支持"""
        logger.info("测试中文编码支持...")

        try:
            # 测试中文字符串处理
            test_chinese = "这是一个中文测试字符串"
            encoded = test_chinese.encode('utf-8')
            decoded = encoded.decode('utf-8')

            # 测试文件读写
            test_file = Path("test_chinese_encoding.txt")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_chinese)

            with open(test_file, 'r', encoding='utf-8') as f:
                read_content = f.read()

            test_file.unlink()  # 删除测试文件

            if read_content == test_chinese:
                self.log_test_result("中文编码支持", "PASS",
                                   f"UTF-8编码测试通过: {test_chinese}")
                logger.info("✓ 中文编码支持正常")
            else:
                self.log_test_result("中文编码支持", "FAIL",
                                   f"编码不一致: 原始={test_chinese}, 读取={read_content}")
                logger.error("✗ 中文编码测试失败")

        except Exception as e:
            self.log_test_result("中文编码支持", "FAIL", f"错误: {str(e)}")
            logger.error(f"✗ 中文编码测试异常: {e}")

    def test_memory_constraints(self):
        """测试内存约束设置"""
        logger.info("测试内存约束...")

        try:
            # 获取系统内存信息
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            available_memory_gb = memory.available / (1024**3)

            # 检查是否满足4GB设备要求
            target_memory_limit = 3.8  # GB

            details = f"总内存: {total_memory_gb:.2f}GB\n可用内存: {available_memory_gb:.2f}GB\n目标限制: {target_memory_limit}GB"

            if available_memory_gb >= target_memory_limit:
                self.log_test_result("内存约束", "PASS", details)
                logger.info(f"✓ 内存充足，可用 {available_memory_gb:.2f}GB")
            else:
                warning = f"可用内存不足，建议释放内存后重试"
                self.log_test_result("内存约束", "PASS", details, warning)
                logger.warning(f"⚠ {warning}")

        except Exception as e:
            self.log_test_result("内存约束", "FAIL", f"错误: {str(e)}")
            logger.error(f"✗ 内存检查失败: {e}")

    def test_directory_structure(self):
        """测试目录结构完整性"""
        logger.info("测试目录结构...")

        required_dirs = [
            "src/core",
            "src/training",
            "src/nlp",
            "src/exporters",
            "configs",
            "data/training",
            "tools/ffmpeg"
        ]

        results = []
        for dir_path in required_dirs:
            full_path = self.core_path / dir_path
            if full_path.exists() and full_path.is_dir():
                results.append(f"✓ {dir_path}")
                logger.info(f"✓ {dir_path} 存在")
            else:
                results.append(f"✗ {dir_path} 缺失")
                logger.error(f"✗ {dir_path} 缺失")

        if all("✓" in result for result in results):
            self.log_test_result("目录结构", "PASS", "\n".join(results))
        else:
            self.log_test_result("目录结构", "FAIL", "\n".join(results))

    def run_all_tests(self):
        """运行所有阶段一测试"""
        logger.info("=" * 60)
        logger.info("开始阶段一：基础环境验证测试")
        logger.info("=" * 60)

        start_time = time.time()

        # 执行所有测试
        self.test_python_interpreter()
        self.test_core_dependencies()
        self.test_config_files()
        self.test_ffmpeg_tools()
        self.test_chinese_encoding()
        self.test_memory_constraints()
        self.test_directory_structure()

        # 计算总耗时
        end_time = time.time()
        duration = end_time - start_time

        # 更新测试结果
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["duration_seconds"] = duration
        self.test_results["success_rate"] = (
            self.test_results["summary"]["passed"] /
            self.test_results["summary"]["total_tests"] * 100
            if self.test_results["summary"]["total_tests"] > 0 else 0
        )

        # 生成报告
        self.generate_report()

        return self.test_results

    def generate_report(self):
        """生成测试报告"""
        logger.info("=" * 60)
        logger.info("阶段一测试报告")
        logger.info("=" * 60)

        summary = self.test_results["summary"]
        logger.info(f"总测试数: {summary['total_tests']}")
        logger.info(f"通过: {summary['passed']}")
        logger.info(f"失败: {summary['failed']}")
        logger.info(f"警告: {summary['warnings']}")
        logger.info(f"成功率: {self.test_results['success_rate']:.1f}%")
        logger.info(f"耗时: {self.test_results['duration_seconds']:.2f}秒")

        # 保存详细报告
        report_file = f"stage1_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        logger.info(f"详细报告已保存至: {report_file}")

        # 判断是否通过
        if self.test_results["success_rate"] >= 80:
            logger.info("🎉 阶段一测试通过！可以进入下一阶段")
            return True
        else:
            logger.error("❌ 阶段一测试未通过，请修复问题后重试")
            return False

def main():
    """主函数"""
    try:
        validator = Stage1EnvironmentValidator()
        result = validator.run_all_tests()

        # 返回退出码
        if result["success_rate"] >= 80:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(2)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
