#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 环境检查脚本

检查系统环境、依赖安装、模型文件等是否正确配置
"""

import os
import sys
import platform
import subprocess
import importlib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "system": {},
            "python": {},
            "dependencies": {},
            "models": {},
            "tools": {},
            "overall": {"status": "unknown", "score": 0}
        }
        
    def check_system_info(self) -> Dict:
        """检查系统信息"""
        print("🖥️  检查系统信息...")
        
        try:
            import psutil
            
            # 基本系统信息
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            }
            
            # 内存信息
            memory = psutil.virtual_memory()
            system_info.update({
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent
            })
            
            # CPU信息
            system_info.update({
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_freq_max": psutil.cpu_freq().max if psutil.cpu_freq() else "Unknown"
            })
            
            # 磁盘信息
            disk = psutil.disk_usage(str(self.project_root))
            system_info.update({
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2)
            })
            
            self.results["system"] = system_info
            
            # 评估系统配置
            score = 0
            issues = []
            
            if system_info["memory_total_gb"] >= 8:
                score += 30
            elif system_info["memory_total_gb"] >= 4:
                score += 20
                issues.append("内存较少，建议使用轻量化模式")
            else:
                score += 10
                issues.append("内存不足，可能影响性能")
                
            if system_info["cpu_count"] >= 4:
                score += 20
            elif system_info["cpu_count"] >= 2:
                score += 15
            else:
                score += 5
                issues.append("CPU核心数较少")
                
            if system_info["disk_free_gb"] >= 20:
                score += 20
            elif system_info["disk_free_gb"] >= 10:
                score += 15
                issues.append("磁盘空间较少")
            else:
                score += 5
                issues.append("磁盘空间不足")
                
            print(f"   ✓ 系统: {system_info['system']} {system_info['release']}")
            print(f"   ✓ 内存: {system_info['memory_total_gb']:.1f}GB")
            print(f"   ✓ CPU: {system_info['cpu_count']} 核心")
            print(f"   ✓ 磁盘: {system_info['disk_free_gb']:.1f}GB 可用")
            
            if issues:
                for issue in issues:
                    print(f"   ⚠️  {issue}")
                    
            return {"score": score, "issues": issues}
            
        except ImportError:
            print("   ⚠️  psutil未安装，无法获取详细系统信息")
            return {"score": 50, "issues": ["无法获取详细系统信息"]}
        except Exception as e:
            print(f"   ❌ 系统信息检查失败: {e}")
            return {"score": 0, "issues": [f"系统检查失败: {e}"]}
            
    def check_python_environment(self) -> Dict:
        """检查Python环境"""
        print("🐍 检查Python环境...")
        
        python_info = {
            "version": sys.version,
            "version_info": sys.version_info,
            "executable": sys.executable,
            "platform": sys.platform,
            "prefix": sys.prefix
        }
        
        self.results["python"] = python_info
        
        score = 0
        issues = []
        
        # 检查Python版本
        if sys.version_info >= (3, 10):
            score += 30
        elif sys.version_info >= (3, 8):
            score += 25
            issues.append("建议升级到Python 3.10+")
        else:
            score += 0
            issues.append("Python版本过低，需要3.8+")
            
        # 检查虚拟环境
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            score += 20
            print("   ✓ 运行在虚拟环境中")
        else:
            score += 10
            issues.append("建议使用虚拟环境")
            
        print(f"   ✓ Python版本: {python_info['version_info'].major}.{python_info['version_info'].minor}.{python_info['version_info'].micro}")
        print(f"   ✓ 可执行文件: {python_info['executable']}")
        
        if issues:
            for issue in issues:
                print(f"   ⚠️  {issue}")
                
        return {"score": score, "issues": issues}
        
    def check_dependencies(self) -> Dict:
        """检查依赖包"""
        print("📦 检查依赖包...")
        
        # 核心依赖列表
        core_dependencies = [
            "numpy", "pandas", "pyyaml", "psutil", "jieba", "langdetect",
            "opencv-python", "pysrt", "loguru", "tqdm", "rich", "pydantic",
            "requests", "click"
        ]
        
        # 可选依赖列表
        optional_dependencies = [
            "torch", "transformers", "scipy", "scikit-learn", "matplotlib",
            "plotly", "spacy", "nltk"
        ]
        
        installed = {}
        missing_core = []
        missing_optional = []
        
        # 检查核心依赖
        for package in core_dependencies:
            try:
                module = importlib.import_module(package.replace("-", "_"))
                version = getattr(module, "__version__", "unknown")
                installed[package] = version
                print(f"   ✓ {package}: {version}")
            except ImportError:
                missing_core.append(package)
                print(f"   ❌ {package}: 未安装")
                
        # 检查可选依赖
        for package in optional_dependencies:
            try:
                module = importlib.import_module(package.replace("-", "_"))
                version = getattr(module, "__version__", "unknown")
                installed[package] = version
                print(f"   ✓ {package}: {version} (可选)")
            except ImportError:
                missing_optional.append(package)
                print(f"   ⚠️  {package}: 未安装 (可选)")
                
        self.results["dependencies"] = {
            "installed": installed,
            "missing_core": missing_core,
            "missing_optional": missing_optional
        }
        
        # 计算分数
        total_core = len(core_dependencies)
        installed_core = total_core - len(missing_core)
        score = int((installed_core / total_core) * 70)
        
        # 可选依赖加分
        if len(missing_optional) < len(optional_dependencies) / 2:
            score += 10
            
        issues = []
        if missing_core:
            issues.append(f"缺少核心依赖: {', '.join(missing_core)}")
        if len(missing_optional) > len(optional_dependencies) / 2:
            issues.append("缺少较多可选依赖，部分功能可能受限")
            
        return {"score": score, "issues": issues}
        
    def check_models(self) -> Dict:
        """检查模型文件"""
        print("🤖 检查模型文件...")
        
        models_dir = self.project_root / "models"
        found_models = {}
        issues = []
        
        if not models_dir.exists():
            print("   ❌ 模型目录不存在")
            return {"score": 0, "issues": ["模型目录不存在"]}
            
        # 检查模型目录
        model_types = ["mistral-7b", "qwen2.5-7b"]
        
        for model_type in model_types:
            model_dir = models_dir / model_type
            if model_dir.exists():
                # 查找模型文件
                model_files = list(model_dir.glob("*.gguf")) + list(model_dir.glob("*.bin"))
                if model_files:
                    config_file = model_dir / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            found_models[model_type] = {
                                "files": [f.name for f in model_files],
                                "config": config
                            }
                            print(f"   ✓ {model_type}: {config.get('quantization', 'unknown')} ({config.get('size_gb', 'unknown')}GB)")
                        except Exception as e:
                            found_models[model_type] = {"files": [f.name for f in model_files], "config": None}
                            print(f"   ⚠️  {model_type}: 文件存在但配置损坏")
                            issues.append(f"{model_type} 配置文件损坏")
                    else:
                        found_models[model_type] = {"files": [f.name for f in model_files], "config": None}
                        print(f"   ⚠️  {model_type}: 文件存在但缺少配置")
                        issues.append(f"{model_type} 缺少配置文件")
                else:
                    print(f"   ❌ {model_type}: 目录存在但无模型文件")
                    issues.append(f"{model_type} 无模型文件")
            else:
                print(f"   ❌ {model_type}: 目录不存在")
                issues.append(f"{model_type} 目录不存在")
                
        self.results["models"] = found_models
        
        # 计算分数
        score = len(found_models) * 25  # 每个模型25分
        if len(found_models) == len(model_types):
            score += 20  # 完整性奖励
            
        if not found_models:
            issues.append("未找到任何模型文件，请运行 python scripts/setup_models.py --setup")
            
        return {"score": score, "issues": issues}
        
    def check_external_tools(self) -> Dict:
        """检查外部工具"""
        print("🔧 检查外部工具...")
        
        tools = {
            "ffmpeg": "视频处理",
            "git": "版本控制"
        }
        
        found_tools = {}
        issues = []
        
        for tool, description in tools.items():
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    found_tools[tool] = version_line
                    print(f"   ✓ {tool}: {version_line}")
                else:
                    print(f"   ❌ {tool}: 未安装 ({description})")
                    issues.append(f"{tool} 未安装")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"   ❌ {tool}: 未安装 ({description})")
                issues.append(f"{tool} 未安装")
                
        self.results["tools"] = found_tools
        
        # 计算分数
        score = len(found_tools) * 15  # 每个工具15分
        
        if "ffmpeg" not in found_tools:
            issues.append("FFmpeg是视频处理的必需工具")
            
        return {"score": score, "issues": issues}
        
    def run_comprehensive_check(self) -> Dict:
        """运行综合检查"""
        print("🔍 VisionAI-ClipsMaster 环境检查")
        print("=" * 50)
        
        # 运行各项检查
        system_result = self.check_system_info()
        python_result = self.check_python_environment()
        deps_result = self.check_dependencies()
        models_result = self.check_models()
        tools_result = self.check_external_tools()
        
        # 计算总分
        total_score = (
            system_result["score"] * 0.2 +
            python_result["score"] * 0.2 +
            deps_result["score"] * 0.3 +
            models_result["score"] * 0.2 +
            tools_result["score"] * 0.1
        )
        
        # 收集所有问题
        all_issues = []
        for result in [system_result, python_result, deps_result, models_result, tools_result]:
            all_issues.extend(result.get("issues", []))
            
        # 确定整体状态
        if total_score >= 80:
            status = "excellent"
            status_text = "优秀"
            status_emoji = "🎉"
        elif total_score >= 60:
            status = "good"
            status_text = "良好"
            status_emoji = "✅"
        elif total_score >= 40:
            status = "fair"
            status_text = "一般"
            status_emoji = "⚠️"
        else:
            status = "poor"
            status_text = "较差"
            status_emoji = "❌"
            
        self.results["overall"] = {
            "status": status,
            "score": round(total_score, 1),
            "issues": all_issues
        }
        
        # 输出结果
        print("\n" + "=" * 50)
        print(f"{status_emoji} 环境检查结果")
        print("=" * 50)
        print(f"总体评分: {total_score:.1f}/100 ({status_text})")
        
        if all_issues:
            print(f"\n发现 {len(all_issues)} 个问题:")
            for i, issue in enumerate(all_issues, 1):
                print(f"  {i}. {issue}")
                
        # 给出建议
        print(f"\n💡 建议:")
        if status == "excellent":
            print("  环境配置优秀，可以正常使用所有功能！")
        elif status == "good":
            print("  环境配置良好，可以正常使用大部分功能。")
            print("  建议解决上述问题以获得更好的体验。")
        elif status == "fair":
            print("  环境配置基本可用，但建议优化配置。")
            print("  请优先解决核心依赖和模型文件问题。")
        else:
            print("  环境配置存在较多问题，可能影响正常使用。")
            print("  请按照上述问题列表逐一解决。")
            
        if "未找到任何模型文件" in str(all_issues):
            print("\n📥 下载模型:")
            print("  python scripts/setup_models.py --setup")
            
        if "ffmpeg" in str(all_issues):
            print("\n🔧 安装FFmpeg:")
            print("  Windows: 下载 https://ffmpeg.org/download.html")
            print("  Ubuntu: sudo apt install ffmpeg")
            print("  macOS: brew install ffmpeg")
            
        return self.results

def main():
    """主函数"""
    checker = EnvironmentChecker()
    results = checker.run_comprehensive_check()
    
    # 保存结果到文件
    results_file = Path("environment_check_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 详细结果已保存到: {results_file}")
    
    # 返回退出码
    if results["overall"]["score"] >= 60:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
