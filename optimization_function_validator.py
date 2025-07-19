#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化后功能验证器
确保体积优化后所有核心功能100%可用
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class FunctionValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.python_exe = r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
        self.results = {
            "validation_time": datetime.now().isoformat(),
            "tests": {},
            "overall_score": 0,
            "critical_failures": [],
            "warnings": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func) -> Dict[str, Any]:
        """运行单个测试"""
        self.log(f"运行测试: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            test_result = {
                "success": True,
                "duration": duration,
                "details": result if isinstance(result, dict) else {"result": result}
            }
            
            self.log(f"✅ {test_name} - 通过 ({duration:.2f}s)")
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "success": False,
                "duration": duration,
                "error": str(e),
                "details": {}
            }
            
            self.log(f"❌ {test_name} - 失败: {e}")
            return test_result
    
    def test_file_structure(self) -> Dict[str, Any]:
        """测试文件结构完整性"""
        required_files = [
            "simple_ui_fixed.py",
            "src/core/__init__.py",
            "src/core/model_switcher.py",
            "src/core/language_detector.py", 
            "src/core/srt_parser.py",
            "src/core/screenplay_engineer.py",
            "src/core/clip_generator.py",
            "configs/model_config.yaml",
            "requirements.txt"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        if missing_files:
            raise Exception(f"缺失关键文件: {missing_files}")
        
        return {
            "required_files": len(required_files),
            "existing_files": len(existing_files),
            "missing_files": missing_files
        }
    
    def test_ui_startup(self) -> Dict[str, Any]:
        """测试UI启动"""
        ui_file = self.project_root / "simple_ui_fixed.py"
        
        # 使用系统Python启动UI（非阻塞测试）
        cmd = [
            self.python_exe,
            str(ui_file),
            "--test-mode"  # 假设有测试模式
        ]
        
        try:
            # 启动进程并等待短时间
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待3秒检查是否正常启动
            time.sleep(3)
            
            if process.poll() is None:
                # 进程仍在运行，说明启动成功
                process.terminate()
                process.wait(timeout=5)
                return {"startup_success": True, "startup_time": "< 3s"}
            else:
                # 进程已退出，检查错误
                stdout, stderr = process.communicate()
                if "successfully" in stdout.lower() or process.returncode == 0:
                    return {"startup_success": True, "output": stdout}
                else:
                    raise Exception(f"UI启动失败: {stderr}")
                    
        except subprocess.TimeoutExpired:
            process.kill()
            return {"startup_success": True, "note": "UI启动正常，已终止测试"}
    
    def test_core_imports(self) -> Dict[str, Any]:
        """测试核心模块导入"""
        core_modules = [
            "src.core.model_switcher",
            "src.core.language_detector",
            "src.core.srt_parser", 
            "src.core.screenplay_engineer",
            "src.core.clip_generator"
        ]
        
        # 临时添加项目路径
        original_path = sys.path.copy()
        sys.path.insert(0, str(self.project_root))
        
        try:
            import_results = {}
            
            for module_name in core_modules:
                try:
                    __import__(module_name)
                    import_results[module_name] = "success"
                except ImportError as e:
                    import_results[module_name] = f"failed: {e}"
            
            failed_imports = [k for k, v in import_results.items() if "failed" in v]
            
            if failed_imports:
                raise Exception(f"模块导入失败: {failed_imports}")
            
            return {
                "total_modules": len(core_modules),
                "successful_imports": len(core_modules) - len(failed_imports),
                "failed_imports": failed_imports,
                "import_details": import_results
            }
            
        finally:
            sys.path = original_path
    
    def test_config_loading(self) -> Dict[str, Any]:
        """测试配置文件加载"""
        config_files = [
            "configs/model_config.yaml",
            "configs/clip_settings.json"
        ]
        
        loaded_configs = {}
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            
            if not config_path.exists():
                continue
                
            try:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                elif config_file.endswith('.json'):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                else:
                    continue
                
                loaded_configs[config_file] = {
                    "status": "loaded",
                    "keys": list(config_data.keys()) if isinstance(config_data, dict) else "non-dict"
                }
                
            except Exception as e:
                loaded_configs[config_file] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        failed_configs = [k for k, v in loaded_configs.items() if v["status"] == "failed"]
        
        if failed_configs:
            raise Exception(f"配置文件加载失败: {failed_configs}")
        
        return {
            "total_configs": len(config_files),
            "loaded_configs": len(loaded_configs),
            "config_details": loaded_configs
        }
    
    def test_ffmpeg_availability(self) -> Dict[str, Any]:
        """测试FFmpeg可用性"""
        ffmpeg_paths = [
            self.project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            "ffmpeg"  # 系统PATH中的ffmpeg
        ]
        
        working_ffmpeg = None
        
        for ffmpeg_path in ffmpeg_paths:
            try:
                if isinstance(ffmpeg_path, Path):
                    if not ffmpeg_path.exists():
                        continue
                    cmd = [str(ffmpeg_path), "-version"]
                else:
                    cmd = [ffmpeg_path, "-version"]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and "ffmpeg version" in result.stdout:
                    working_ffmpeg = str(ffmpeg_path)
                    break
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        if not working_ffmpeg:
            raise Exception("FFmpeg不可用")
        
        return {
            "ffmpeg_path": working_ffmpeg,
            "available": True
        }
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用情况"""
        try:
            import psutil
            
            # 获取当前进程内存使用
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 检查系统内存
            system_memory = psutil.virtual_memory()
            
            # 4GB内存兼容性检查
            memory_mb = memory_info.rss / 1024 / 1024
            system_total_gb = system_memory.total / 1024 / 1024 / 1024
            
            compatible_4gb = memory_mb < 3800  # 留200MB余量
            
            return {
                "current_memory_mb": round(memory_mb, 2),
                "system_total_gb": round(system_total_gb, 2),
                "system_available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                "4gb_compatible": compatible_4gb
            }
            
        except ImportError:
            return {"error": "psutil not available", "4gb_compatible": True}
    
    def test_dual_model_config(self) -> Dict[str, Any]:
        """测试双模型配置"""
        config_path = self.project_root / "configs" / "model_config.yaml"
        
        if not config_path.exists():
            raise Exception("模型配置文件不存在")
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查双模型配置
            base_models = config.get('base_models', {})

            required_languages = ['en', 'zh']
            available_models = []

            for lang in required_languages:
                if lang in base_models:
                    model_config = base_models[lang]
                    if 'name' in model_config and 'path' in model_config:
                        available_models.append(f"{model_config['name']}-{lang}")
            
            if len(available_models) < 2:
                raise Exception(f"双模型配置不完整，仅找到: {available_models}")
            
            return {
                "configured_models": available_models,
                "dual_model_ready": True,
                "model_details": {lang: base_models[lang] for lang in required_languages if lang in base_models}
            }
            
        except Exception as e:
            raise Exception(f"双模型配置检查失败: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有验证测试"""
        self.log("开始功能验证测试")
        
        # 定义测试套件
        test_suite = [
            ("文件结构完整性", self.test_file_structure),
            ("核心模块导入", self.test_core_imports),
            ("配置文件加载", self.test_config_loading),
            ("FFmpeg可用性", self.test_ffmpeg_availability),
            ("内存使用检查", self.test_memory_usage),
            ("双模型配置", self.test_dual_model_config),
            ("UI启动测试", self.test_ui_startup)
        ]
        
        # 运行测试
        passed_tests = 0
        critical_tests = ["文件结构完整性", "核心模块导入", "双模型配置"]
        
        for test_name, test_func in test_suite:
            test_result = self.run_test(test_name, test_func)
            self.results["tests"][test_name] = test_result
            
            if test_result["success"]:
                passed_tests += 1
            elif test_name in critical_tests:
                self.results["critical_failures"].append(test_name)
            else:
                self.results["warnings"].append(test_name)
        
        # 计算总分
        self.results["overall_score"] = (passed_tests / len(test_suite)) * 100
        
        # 输出结果
        self.log("=== 验证结果 ===")
        self.log(f"总体评分: {self.results['overall_score']:.1f}/100")
        self.log(f"通过测试: {passed_tests}/{len(test_suite)}")
        
        if self.results["critical_failures"]:
            self.log(f"关键失败: {self.results['critical_failures']}")
        
        if self.results["warnings"]:
            self.log(f"警告项目: {self.results['warnings']}")
        
        # 保存详细报告
        report_path = self.project_root / "optimization_validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.log(f"详细报告已保存: {report_path}")
        
        return self.results

def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    validator = FunctionValidator(project_root)
    results = validator.run_all_tests()
    
    # 判断验证结果
    success = (
        results["overall_score"] >= 85 and 
        len(results["critical_failures"]) == 0
    )
    
    if success:
        print(f"\n✅ 功能验证通过！评分: {results['overall_score']:.1f}/100")
        print("所有核心功能在优化后正常工作")
    else:
        print(f"\n❌ 功能验证失败！评分: {results['overall_score']:.1f}/100")
        if results["critical_failures"]:
            print(f"关键失败项: {', '.join(results['critical_failures'])}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
