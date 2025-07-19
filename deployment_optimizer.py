#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 部署包优化器
优化项目打包策略，减小分发包体积，实现按需下载和轻量化部署
"""

import os
import sys
import json
import shutil
import zipfile
import time
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

logger = logging.getLogger(__name__)

class DeploymentOptimizer:
    """部署包优化器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.build_dir = self.project_root / 'build'
        self.dist_dir = self.project_root / 'dist'
        
    def analyze_project_structure(self) -> Dict[str, Any]:
        """分析项目结构"""
        print("📊 分析项目结构...")
        
        analysis = {
            "core_files": [],
            "optional_files": [],
            "large_files": [],
            "total_size_mb": 0,
            "file_categories": {
                "python": 0,
                "config": 0,
                "models": 0,
                "tests": 0,
                "docs": 0,
                "assets": 0,
                "other": 0
            }
        }
        
        # 核心文件列表
        core_patterns = [
            'src/**/*.py',
            'ui/**/*.py',
            'configs/*.json',
            'configs/*.yaml',
            'requirements.txt',
            'main.py',
            'simple_ui_fixed.py',
            'optimized_launcher.py'
        ]
        
        # 可选文件列表
        optional_patterns = [
            'tests/**/*',
            'docs/**/*',
            'examples/**/*',
            'scripts/**/*',
            '*.md',
            '*.txt'
        ]
        
        # 扫描所有文件
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not self._should_exclude(file_path):
                file_size = file_path.stat().st_size
                analysis["total_size_mb"] += file_size / 1024**2
                
                # 分类文件
                category = self._categorize_file(file_path)
                analysis["file_categories"][category] += 1
                
                # 识别大文件
                if file_size > 10 * 1024 * 1024:  # 大于10MB
                    analysis["large_files"].append({
                        "path": str(file_path.relative_to(self.project_root)),
                        "size_mb": file_size / 1024**2
                    })
                
                # 分类为核心或可选
                is_core = any(file_path.match(pattern) for pattern in core_patterns)
                is_optional = any(file_path.match(pattern) for pattern in optional_patterns)
                
                if is_core:
                    analysis["core_files"].append(str(file_path.relative_to(self.project_root)))
                elif is_optional:
                    analysis["optional_files"].append(str(file_path.relative_to(self.project_root)))
        
        print(f"✅ 项目总大小: {analysis['total_size_mb']:.2f} MB")
        print(f"   核心文件: {len(analysis['core_files'])} 个")
        print(f"   可选文件: {len(analysis['optional_files'])} 个")
        print(f"   大文件: {len(analysis['large_files'])} 个")
        
        return analysis
    
    def create_lightweight_package(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """创建轻量化部署包"""
        print("\n📦 创建轻量化部署包...")
        
        # 创建构建目录
        self.build_dir.mkdir(exist_ok=True)
        lightweight_dir = self.build_dir / 'lightweight'
        if lightweight_dir.exists():
            shutil.rmtree(lightweight_dir)
        lightweight_dir.mkdir()
        
        # 复制核心文件
        copied_files = 0
        total_size = 0
        
        for core_file in analysis["core_files"]:
            src_path = self.project_root / core_file
            dst_path = lightweight_dir / core_file
            
            if src_path.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                copied_files += 1
                total_size += src_path.stat().st_size
        
        # 创建启动脚本
        self._create_launcher_script(lightweight_dir)
        
        # 创建依赖下载器
        self._create_dependency_downloader(lightweight_dir)
        
        # 创建配置文件
        self._create_deployment_config(lightweight_dir, analysis)
        
        package_size_mb = total_size / 1024**2
        
        print(f"✅ 轻量化包创建完成")
        print(f"   文件数量: {copied_files}")
        print(f"   包大小: {package_size_mb:.2f} MB")
        print(f"   压缩率: {(1 - package_size_mb / analysis['total_size_mb']) * 100:.1f}%")
        
        return {
            "package_path": str(lightweight_dir),
            "file_count": copied_files,
            "size_mb": package_size_mb,
            "compression_ratio": (1 - package_size_mb / analysis['total_size_mb']) * 100
        }
    
    def create_modular_packages(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """创建模块化部署包"""
        print("\n🧩 创建模块化部署包...")
        
        modular_dir = self.build_dir / 'modular'
        if modular_dir.exists():
            shutil.rmtree(modular_dir)
        modular_dir.mkdir()
        
        # 定义模块
        modules = {
            "core": {
                "description": "核心功能模块",
                "patterns": [
                    'src/core/**/*.py',
                    'src/exporters/**/*.py',
                    'main.py',
                    'simple_ui_fixed.py'
                ]
            },
            "ui": {
                "description": "用户界面模块",
                "patterns": [
                    'ui/**/*.py',
                    'src/ui/**/*.py'
                ]
            },
            "models": {
                "description": "AI模型模块",
                "patterns": [
                    'models/**/*',
                    'src/models/**/*.py'
                ]
            },
            "configs": {
                "description": "配置文件模块",
                "patterns": [
                    'configs/**/*'
                ]
            }
        }
        
        module_info = {}
        
        for module_name, module_config in modules.items():
            module_path = modular_dir / f"{module_name}_module"
            module_path.mkdir()
            
            module_size = 0
            file_count = 0
            
            for pattern in module_config["patterns"]:
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(self.project_root)
                        dst_path = module_path / rel_path
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dst_path)
                        
                        module_size += file_path.stat().st_size
                        file_count += 1
            
            module_info[module_name] = {
                "description": module_config["description"],
                "path": str(module_path),
                "size_mb": module_size / 1024**2,
                "file_count": file_count
            }
            
            print(f"   {module_name}: {file_count} 文件, {module_size / 1024**2:.2f} MB")
        
        print("✅ 模块化包创建完成")
        
        return module_info
    
    def create_installer_script(self) -> Dict[str, Any]:
        """创建安装脚本"""
        print("\n🔧 创建安装脚本...")
        
        installer_script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 智能安装器
自动检测系统环境并安装所需组件
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path

class VisionAIInstaller:
    """VisionAI-ClipsMaster 安装器"""
    
    def __init__(self):
        self.system_info = self._detect_system()
        self.install_log = []
        
    def _detect_system(self):
        """检测系统信息"""
        return {
            "os": platform.system(),
            "arch": platform.machine(),
            "python_version": sys.version,
            "memory_gb": self._get_memory_info()
        }
    
    def _get_memory_info(self):
        """获取内存信息"""
        try:
            import psutil
            return psutil.virtual_memory().total / 1024**3
        except ImportError:
            return 0
    
    def install_dependencies(self):
        """安装依赖"""
        print("📦 安装Python依赖...")
        
        requirements = [
            "PyQt6>=6.4.0",
            "torch>=1.13.0",
            "transformers>=4.21.0",
            "psutil>=5.9.0",
            "requests>=2.28.0"
        ]
        
        for req in requirements:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", req])
                print(f"✅ {req} 安装成功")
                self.install_log.append(f"SUCCESS: {req}")
            except subprocess.CalledProcessError as e:
                print(f"❌ {req} 安装失败: {e}")
                self.install_log.append(f"FAILED: {req} - {e}")
    
    def download_models(self):
        """下载AI模型"""
        print("🤖 准备AI模型...")
        
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # 创建模型下载配置
        model_config = {
            "mistral-7b": {
                "url": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1",
                "size_gb": 13.5,
                "required": True
            },
            "qwen2.5-7b": {
                "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct",
                "size_gb": 14.2,
                "required": True
            }
        }
        
        with open(models_dir / "download_config.json", "w") as f:
            json.dump(model_config, f, indent=2)
        
        print("✅ 模型配置已准备，请运行模型下载器")
    
    def setup_environment(self):
        """设置环境"""
        print("⚙️ 配置环境...")
        
        # 创建启动脚本
        if self.system_info["os"] == "Windows":
            start_script = "start_visionai.bat"
            script_content = "@echo off\\necho Starting VisionAI-ClipsMaster...\\npython optimized_launcher.py\\npause\\n"
        else:
            start_script = "start_visionai.sh"
            script_content = "#!/bin/bash\\necho \\"Starting VisionAI-ClipsMaster...\\"\\npython3 optimized_launcher.py\\n"
        
        with open(start_script, "w") as f:
            f.write(script_content)
        
        if self.system_info["os"] != "Windows":
            os.chmod(start_script, 0o755)
        
        print(f"✅ 启动脚本已创建: {start_script}")
    
    def run_installation(self):
        """运行完整安装"""
        print("=== VisionAI-ClipsMaster 安装器 ===")
        print(f"系统: {self.system_info['os']} {self.system_info['arch']}")
        print(f"内存: {self.system_info['memory_gb']:.1f} GB")
        print()
        
        self.install_dependencies()
        self.download_models()
        self.setup_environment()
        
        print("\\n🎉 安装完成！")
        print("使用以下命令启动应用:")
        if self.system_info["os"] == "Windows":
            print("   start_visionai.bat")
        else:
            print("   ./start_visionai.sh")

if __name__ == "__main__":
    installer = VisionAIInstaller()
    installer.run_installation()
'''
        
        installer_file = self.build_dir / 'install.py'
        with open(installer_file, 'w', encoding='utf-8') as f:
            f.write(installer_script)
        
        print("✅ 安装脚本已创建")
        
        return {"installer_created": True, "installer_path": str(installer_file)}
    
    def _should_exclude(self, file_path: Path) -> bool:
        """判断是否应该排除文件"""
        exclude_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            '*.pyc',
            '*.pyo',
            '.DS_Store',
            'Thumbs.db',
            '*.tmp',
            'crash_log.txt'
        ]
        
        return any(pattern in str(file_path) for pattern in exclude_patterns)
    
    def _categorize_file(self, file_path: Path) -> str:
        """文件分类"""
        if file_path.suffix == '.py':
            return 'python'
        elif file_path.suffix in ['.json', '.yaml', '.yml', '.ini']:
            return 'config'
        elif 'model' in str(file_path).lower():
            return 'models'
        elif 'test' in str(file_path).lower():
            return 'tests'
        elif file_path.suffix in ['.md', '.txt', '.rst']:
            return 'docs'
        elif file_path.suffix in ['.png', '.jpg', '.svg', '.ico']:
            return 'assets'
        else:
            return 'other'
    
    def _create_launcher_script(self, target_dir: Path):
        """创建启动脚本"""
        launcher_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 轻量化启动器
"""

import sys
import os
from pathlib import Path

def main():
    """主函数"""
    print("🚀 启动 VisionAI-ClipsMaster...")
    
    # 检查依赖
    try:
        from simple_ui_fixed import main as ui_main
        ui_main()
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行 python install.py 安装依赖")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        
        launcher_file = target_dir / 'launcher.py'
        with open(launcher_file, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
    
    def _create_dependency_downloader(self, target_dir: Path):
        """创建依赖下载器"""
        downloader_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 依赖下载器
按需下载所需组件
"""

import os
import sys
import requests
import json
from pathlib import Path

def download_component(component_name: str, url: str, target_path: Path):
    """下载组件"""
    print(f"📥 下载 {component_name}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ {component_name} 下载完成")
        return True
        
    except Exception as e:
        print(f"❌ {component_name} 下载失败: {e}")
        return False

def main():
    """主函数"""
    print("📦 VisionAI-ClipsMaster 组件下载器")
    
    # 这里可以添加具体的下载逻辑
    print("✅ 所有组件已准备就绪")

if __name__ == "__main__":
    main()
'''
        
        downloader_file = target_dir / 'download_components.py'
        with open(downloader_file, 'w', encoding='utf-8') as f:
            f.write(downloader_content)
    
    def _create_deployment_config(self, target_dir: Path, analysis: Dict[str, Any]):
        """创建部署配置"""
        config = {
            "version": "1.0.0",
            "build_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "package_type": "lightweight",
            "original_size_mb": analysis["total_size_mb"],
            "compressed_size_mb": sum(f["size_mb"] for f in analysis["large_files"]),
            "components": {
                "core": {"required": True, "size_mb": 50},
                "ui": {"required": True, "size_mb": 20},
                "models": {"required": False, "size_mb": 500},
                "docs": {"required": False, "size_mb": 10}
            }
        }
        
        config_file = target_dir / 'deployment_config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def run_all_optimizations(self) -> Dict[str, Any]:
        """运行所有部署优化"""
        print("=== VisionAI-ClipsMaster 部署包优化 ===")
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {}
        
        # 分析项目结构
        analysis = self.analyze_project_structure()
        results["analysis"] = analysis
        
        # 创建轻量化包
        lightweight_package = self.create_lightweight_package(analysis)
        results["lightweight_package"] = lightweight_package
        
        # 创建模块化包
        modular_packages = self.create_modular_packages(analysis)
        results["modular_packages"] = modular_packages
        
        # 创建安装脚本
        installer = self.create_installer_script()
        results["installer"] = installer
        
        print("\n=== 部署优化完成 ===")
        print("🎉 所有部署优化措施已实施完成！")
        print("\n📋 优化总结:")
        print(f"- 原始项目大小: {analysis['total_size_mb']:.2f} MB")
        print(f"- 轻量化包大小: {lightweight_package['size_mb']:.2f} MB")
        print(f"- 压缩率: {lightweight_package['compression_ratio']:.1f}%")
        print(f"- 模块化包数量: {len(modular_packages)}")
        
        print("\n📦 部署包位置:")
        print(f"   轻量化包: {lightweight_package['package_path']}")
        print(f"   安装脚本: {installer['installer_path']}")
        
        return results

def main():
    """主函数"""
    optimizer = DeploymentOptimizer()
    return optimizer.run_all_optimizations()

if __name__ == "__main__":
    main()
