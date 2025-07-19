#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 快速启动脚本

提供一键启动功能，自动检测环境并选择最佳配置
"""

import os
import sys
import platform
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

class QuickStarter:
    """快速启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.system_info = self._detect_system()
        
    def _detect_system(self) -> Dict:
        """检测系统信息"""
        try:
            import psutil
            
            return {
                "platform": platform.system(),
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "cpu_count": psutil.cpu_count(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "has_gpu": self._check_gpu(),
                "has_docker": self._check_docker(),
                "has_conda": self._check_conda()
            }
        except ImportError:
            return {
                "platform": platform.system(),
                "memory_gb": 8.0,  # 默认假设
                "cpu_count": 4,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "has_gpu": False,
                "has_docker": False,
                "has_conda": False
            }
    
    def _check_gpu(self) -> bool:
        """检查GPU可用性"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _check_docker(self) -> bool:
        """检查Docker可用性"""
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_conda(self) -> bool:
        """检查Conda可用性"""
        try:
            result = subprocess.run(["conda", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def recommend_configuration(self) -> Dict:
        """推荐配置"""
        config = {
            "mode": "full",
            "quantization": "Q4_K_M",
            "max_memory": 7000,
            "deployment": "local",
            "install_method": "pip"
        }
        
        # 根据内存调整配置
        if self.system_info["memory_gb"] <= 4:
            config.update({
                "mode": "lite",
                "quantization": "Q2_K",
                "max_memory": 3800
            })
        elif self.system_info["memory_gb"] <= 6:
            config.update({
                "quantization": "Q4_K_M",
                "max_memory": 5000
            })
        else:
            config.update({
                "quantization": "Q5_K",
                "max_memory": 7000
            })
        
        # 根据可用工具调整安装方法
        if self.system_info["has_docker"]:
            config["deployment"] = "docker"
        elif self.system_info["has_conda"]:
            config["install_method"] = "conda"
        
        return config
    
    def show_system_info(self):
        """显示系统信息"""
        print("🖥️  系统信息")
        print("=" * 40)
        print(f"操作系统: {self.system_info['platform']}")
        print(f"内存: {self.system_info['memory_gb']:.1f}GB")
        print(f"CPU核心: {self.system_info['cpu_count']}")
        print(f"Python版本: {self.system_info['python_version']}")
        print(f"GPU支持: {'是' if self.system_info['has_gpu'] else '否'}")
        print(f"Docker可用: {'是' if self.system_info['has_docker'] else '否'}")
        print(f"Conda可用: {'是' if self.system_info['has_conda'] else '否'}")
        print()
    
    def show_recommended_config(self, config: Dict):
        """显示推荐配置"""
        print("💡 推荐配置")
        print("=" * 40)
        print(f"运行模式: {config['mode']}")
        print(f"量化级别: {config['quantization']}")
        print(f"内存限制: {config['max_memory']}MB")
        print(f"部署方式: {config['deployment']}")
        print(f"安装方法: {config['install_method']}")
        print()
    
    def quick_install(self, config: Dict) -> bool:
        """快速安装"""
        print("📦 开始快速安装...")
        
        try:
            if config["deployment"] == "docker":
                return self._install_docker(config)
            else:
                return self._install_local(config)
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False
    
    def _install_docker(self, config: Dict) -> bool:
        """Docker安装"""
        print("🐳 使用Docker安装...")
        
        # 构建Docker镜像
        target = "lite" if config["mode"] == "lite" else "production"
        cmd = [
            "docker", "build",
            "-f", "docker/Dockerfile",
            "--target", target,
            "-t", f"visionai-clipsmaster:{config['mode']}",
            "."
        ]
        
        print("构建Docker镜像...")
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ Docker镜像构建失败")
            return False
        
        print("✅ Docker镜像构建成功")
        
        # 创建启动脚本
        self._create_docker_start_script(config)
        
        return True
    
    def _install_local(self, config: Dict) -> bool:
        """本地安装"""
        print("🏠 使用本地安装...")
        
        # 创建虚拟环境
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            print("创建虚拟环境...")
            result = subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
            if result.returncode != 0:
                print("❌ 虚拟环境创建失败")
                return False
        
        # 确定pip路径
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"
        
        # 安装依赖
        print("安装Python依赖...")
        if config["mode"] == "lite":
            requirements_file = "requirements/requirements-lite.txt"
        else:
            requirements_file = "requirements/requirements.txt"
        
        result = subprocess.run([
            str(pip_path), "install", "-r", requirements_file
        ], cwd=self.project_root)
        
        if result.returncode != 0:
            print("❌ 依赖安装失败")
            return False
        
        print("✅ 依赖安装成功")
        
        # 创建启动脚本
        self._create_local_start_script(config, python_path)
        
        return True
    
    def _create_docker_start_script(self, config: Dict):
        """创建Docker启动脚本"""
        if platform.system() == "Windows":
            script_content = f"""@echo off
echo 启动VisionAI-ClipsMaster (Docker模式)
docker run -it --rm ^
    -p 8080:8080 ^
    -v "%cd%\\data:/home/visionai/data" ^
    -v "%cd%\\models:/home/visionai/models" ^
    -e VISIONAI_MODE={config['mode']} ^
    -e VISIONAI_MAX_MEMORY={config['max_memory']} ^
    visionai-clipsmaster:{config['mode']} web
"""
            script_path = self.project_root / "start_docker.bat"
        else:
            script_content = f"""#!/bin/bash
echo "启动VisionAI-ClipsMaster (Docker模式)"
docker run -it --rm \\
    -p 8080:8080 \\
    -v "$(pwd)/data:/home/visionai/data" \\
    -v "$(pwd)/models:/home/visionai/models" \\
    -e VISIONAI_MODE={config['mode']} \\
    -e VISIONAI_MAX_MEMORY={config['max_memory']} \\
    visionai-clipsmaster:{config['mode']} web
"""
            script_path = self.project_root / "start_docker.sh"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if platform.system() != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"✅ 启动脚本已创建: {script_path}")
    
    def _create_local_start_script(self, config: Dict, python_path: Path):
        """创建本地启动脚本"""
        if platform.system() == "Windows":
            script_content = f"""@echo off
echo 启动VisionAI-ClipsMaster (本地模式)
set VISIONAI_MODE={config['mode']}
set VISIONAI_MAX_MEMORY={config['max_memory']}
"{python_path}" src\\visionai_clipsmaster\\ui\\main_window.py
pause
"""
            script_path = self.project_root / "start_local.bat"
        else:
            script_content = f"""#!/bin/bash
echo "启动VisionAI-ClipsMaster (本地模式)"
export VISIONAI_MODE={config['mode']}
export VISIONAI_MAX_MEMORY={config['max_memory']}
"{python_path}" src/visionai_clipsmaster/ui/main_window.py
"""
            script_path = self.project_root / "start_local.sh"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if platform.system() != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"✅ 启动脚本已创建: {script_path}")
    
    def download_models(self, config: Dict) -> bool:
        """下载模型"""
        print("🤖 下载AI模型...")
        
        try:
            # 运行模型下载脚本
            if config["deployment"] == "docker":
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{self.project_root}/models:/home/visionai/models",
                    f"visionai-clipsmaster:{config['mode']}",
                    "download-models"
                ]
            else:
                # 使用本地Python
                if platform.system() == "Windows":
                    python_path = self.project_root / "venv" / "Scripts" / "python.exe"
                else:
                    python_path = self.project_root / "venv" / "bin" / "python"
                
                cmd = [
                    str(python_path),
                    "scripts/setup_models.py",
                    "--setup"
                ]
            
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ 模型下载成功")
                return True
            else:
                print("❌ 模型下载失败")
                return False
                
        except Exception as e:
            print(f"❌ 模型下载出错: {e}")
            return False
    
    def run_quick_start(self):
        """运行快速启动流程"""
        print("🚀 VisionAI-ClipsMaster 快速启动")
        print("=" * 50)
        print()
        
        # 显示系统信息
        self.show_system_info()
        
        # 获取推荐配置
        config = self.recommend_configuration()
        self.show_recommended_config(config)
        
        # 询问用户是否继续
        response = input("是否使用推荐配置进行安装? (Y/n): ").strip().lower()
        if response in ['n', 'no']:
            print("安装已取消")
            return False
        
        # 开始安装
        print("\n🔧 开始安装过程...")
        
        # 1. 快速安装
        if not self.quick_install(config):
            print("❌ 安装失败，请检查错误信息")
            return False
        
        # 2. 下载模型
        print("\n📥 下载模型文件...")
        download_response = input("是否现在下载AI模型? (Y/n): ").strip().lower()
        if download_response not in ['n', 'no']:
            if not self.download_models(config):
                print("⚠️  模型下载失败，可以稍后手动下载")
        
        # 3. 完成安装
        print("\n🎉 安装完成!")
        print("=" * 50)
        
        if config["deployment"] == "docker":
            print("启动方式:")
            if platform.system() == "Windows":
                print("  双击运行: start_docker.bat")
            else:
                print("  运行命令: ./start_docker.sh")
            print("  或手动运行: docker run -p 8080:8080 visionai-clipsmaster")
        else:
            print("启动方式:")
            if platform.system() == "Windows":
                print("  双击运行: start_local.bat")
            else:
                print("  运行命令: ./start_local.sh")
            print("  或手动激活环境后运行程序")
        
        print("\n访问地址: http://localhost:8080")
        print("文档地址: https://github.com/CKEN/VisionAI-ClipsMaster")
        
        return True

def main():
    """主函数"""
    try:
        starter = QuickStarter()
        success = starter.run_quick_start()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n用户取消安装")
        return 1
    except Exception as e:
        print(f"\n❌ 快速启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
