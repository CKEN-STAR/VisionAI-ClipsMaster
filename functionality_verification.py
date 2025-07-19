#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 功能完整性验证器
验证清理后所有核心功能是否正常工作
"""

import os
import sys
import importlib
import traceback
from pathlib import Path
import json
from datetime import datetime

class FunctionalityVerifier:
    def __init__(self):
        self.project_root = Path(".")
        self.verification_results = []
        self.critical_modules = [
            # 双模型系统
            "src.core.intelligent_model_selector",
            "src.core.language_detector", 
            "src.core.model_switcher",
            "src.core.enhanced_model_loader",
            
            # 剧本重构和字幕生成
            "src.core.screenplay_engineer",
            "src.core.enhanced_subtitle_reconstructor",
            "src.core.srt_parser",
            "src.core.ai_viral_transformer",
            
            # 视频切割拼接功能
            "src.core.clip_generator",
            "src.core.alignment_engineer",
            "src.core.video_processor",
            
            # UI界面和用户交互
            "ui.main_window",
            "ui.screenplay_app",
            "VisionAI-ClipsMaster-Core.simple_ui_fixed",
            
            # 训练投喂机制
            "src.training.trainer",
            "src.training.zh_trainer",
            "src.training.en_trainer",
            
            # 剪映工程文件导出
            "src.exporters.jianying_pro_exporter",
            "src.export.jianying_exporter",
            "src.exporters.timeline_converter"
        ]
        
        self.core_files = [
            # 配置文件
            "configs/model_config.yaml",
            "requirements.txt",
            "VisionAI-ClipsMaster-Core/requirements.txt",
            
            # 核心工具
            "tools/ffmpeg/bin/ffmpeg.exe",
            "tools/ffmpeg/bin/ffprobe.exe",
            "tools/ffmpeg/bin/ffplay.exe",
            
            # 主要入口点
            "VisionAI-ClipsMaster-Core/simple_ui_fixed.py"
        ]
    
    def log_result(self, test_name, status, details="", error=None):
        """记录验证结果"""
        result = {
            "test_name": test_name,
            "status": status,  # PASS, FAIL, SKIP
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.verification_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
        if error:
            print(f"   错误: {error}")
    
    def verify_file_existence(self):
        """验证核心文件是否存在"""
        print("\n🔍 验证核心文件存在性...")
        
        for file_path in self.core_files:
            path = self.project_root / file_path
            if path.exists():
                size = path.stat().st_size if path.is_file() else "目录"
                self.log_result(f"文件存在: {file_path}", "PASS", f"大小: {size}")
            else:
                self.log_result(f"文件存在: {file_path}", "FAIL", "文件不存在")
    
    def verify_module_imports(self):
        """验证关键模块是否可以正常导入"""
        print("\n🔍 验证模块导入...")
        
        # 添加项目路径到sys.path
        project_paths = [
            str(self.project_root),
            str(self.project_root / "src"),
            str(self.project_root / "ui"),
            str(self.project_root / "VisionAI-ClipsMaster-Core"),
            str(self.project_root / "VisionAI-ClipsMaster-Core" / "src")
        ]
        
        for path in project_paths:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        for module_name in self.critical_modules:
            try:
                # 尝试导入模块
                module = importlib.import_module(module_name)
                
                # 检查模块是否有主要类或函数
                if hasattr(module, '__all__'):
                    exports = module.__all__
                elif hasattr(module, '__dict__'):
                    exports = [name for name in dir(module) if not name.startswith('_')]
                else:
                    exports = []
                
                self.log_result(f"模块导入: {module_name}", "PASS", 
                              f"导出: {len(exports)} 个对象")
                
            except ImportError as e:
                self.log_result(f"模块导入: {module_name}", "FAIL", 
                              f"导入失败", e)
            except Exception as e:
                self.log_result(f"模块导入: {module_name}", "FAIL", 
                              f"未知错误", e)
    
    def verify_ffmpeg_functionality(self):
        """验证FFmpeg功能"""
        print("\n🔍 验证FFmpeg功能...")
        
        ffmpeg_path = self.project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
        if not ffmpeg_path.exists():
            self.log_result("FFmpeg可执行性", "FAIL", "FFmpeg不存在")
            return
        
        try:
            import subprocess
            result = subprocess.run([str(ffmpeg_path), "-version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                self.log_result("FFmpeg可执行性", "PASS", version_info)
            else:
                self.log_result("FFmpeg可执行性", "FAIL", 
                              f"返回码: {result.returncode}")
        except Exception as e:
            self.log_result("FFmpeg可执行性", "FAIL", "执行失败", e)
    
    def verify_ui_components(self):
        """验证UI组件"""
        print("\n🔍 验证UI组件...")
        
        try:
            # 尝试导入PyQt6
            import PyQt6
            self.log_result("PyQt6依赖", "PASS", f"版本: {PyQt6.QtCore.PYQT_VERSION_STR}")
        except ImportError as e:
            self.log_result("PyQt6依赖", "FAIL", "PyQt6未安装", e)
        
        # 检查UI文件
        ui_files = [
            "ui/main_window.py",
            "ui/screenplay_app.py",
            "VisionAI-ClipsMaster-Core/simple_ui_fixed.py"
        ]
        
        for ui_file in ui_files:
            path = self.project_root / ui_file
            if path.exists():
                self.log_result(f"UI文件: {ui_file}", "PASS", f"大小: {path.stat().st_size}")
            else:
                self.log_result(f"UI文件: {ui_file}", "FAIL", "文件不存在")
    
    def verify_model_configs(self):
        """验证模型配置"""
        print("\n🔍 验证模型配置...")
        
        config_file = self.project_root / "configs" / "model_config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # 检查关键配置项
                required_keys = ['models', 'quantization', 'memory_limits']
                missing_keys = [key for key in required_keys if key not in config]
                
                if not missing_keys:
                    self.log_result("模型配置文件", "PASS", 
                                  f"包含 {len(config)} 个配置项")
                else:
                    self.log_result("模型配置文件", "FAIL", 
                                  f"缺少配置项: {missing_keys}")
                    
            except Exception as e:
                self.log_result("模型配置文件", "FAIL", "解析失败", e)
        else:
            self.log_result("模型配置文件", "FAIL", "配置文件不存在")
    
    def verify_directory_structure(self):
        """验证目录结构完整性"""
        print("\n🔍 验证目录结构...")
        
        required_dirs = [
            "src/core",
            "src/exporters", 
            "src/training",
            "ui",
            "configs",
            "tools/ffmpeg/bin",
            "VisionAI-ClipsMaster-Core/src"
        ]
        
        for dir_path in required_dirs:
            path = self.project_root / dir_path
            if path.exists() and path.is_dir():
                file_count = len(list(path.rglob("*.py")))
                self.log_result(f"目录结构: {dir_path}", "PASS", 
                              f"包含 {file_count} 个Python文件")
            else:
                self.log_result(f"目录结构: {dir_path}", "FAIL", "目录不存在")
    
    def verify_dependencies(self):
        """验证依赖包"""
        print("\n🔍 验证依赖包...")
        
        critical_packages = [
            "PyQt6",
            "yaml", 
            "numpy",
            "torch",
            "transformers"
        ]
        
        for package in critical_packages:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', '未知版本')
                self.log_result(f"依赖包: {package}", "PASS", f"版本: {version}")
            except ImportError:
                self.log_result(f"依赖包: {package}", "FAIL", "包未安装")
    
    def generate_verification_report(self):
        """生成验证报告"""
        total_tests = len(self.verification_results)
        passed_tests = len([r for r in self.verification_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.verification_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.verification_results if r["status"] == "SKIP"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "verification_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "success_rate": round(success_rate, 2)
            },
            "detailed_results": self.verification_results
        }
        
        report_file = self.project_root / "functionality_verification_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 功能验证完成！")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ({success_rate:.1f}%)")
        print(f"失败: {failed_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"详细报告: {report_file}")
        
        # 评估整体状态
        if success_rate >= 90:
            print("🎉 功能完整性验证: 优秀")
        elif success_rate >= 75:
            print("✅ 功能完整性验证: 良好")
        elif success_rate >= 60:
            print("⚠️ 功能完整性验证: 一般")
        else:
            print("❌ 功能完整性验证: 需要修复")
        
        return report
    
    def run_verification(self):
        """运行完整验证"""
        print("🎯 VisionAI-ClipsMaster 功能完整性验证")
        print("=" * 50)
        
        # 执行各项验证
        self.verify_file_existence()
        self.verify_directory_structure()
        self.verify_module_imports()
        self.verify_ffmpeg_functionality()
        self.verify_ui_components()
        self.verify_model_configs()
        self.verify_dependencies()
        
        # 生成报告
        return self.generate_verification_report()

def main():
    """主函数"""
    verifier = FunctionalityVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main()
