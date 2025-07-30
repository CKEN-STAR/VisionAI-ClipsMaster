#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 完全自包含整合包构建器
创建开箱即用的独立可执行整合包
"""

import os
import sys
import shutil
import subprocess
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

# 添加当前目录到路径
sys.path.append(str(Path(__file__).parent))
from build_config import PackagingConfig, ModelDownloadManager

class PackageBuilder:
    """整合包构建器"""
    
    def __init__(self):
        self.config = PackagingConfig(str(Path(__file__).parent.parent))
        self.model_manager = ModelDownloadManager(self.config.package_dir)
        
    def clean_build_dirs(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = [self.config.build_dir, self.config.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   已清理: {dir_path}")
        
        # 重新创建目录
        self.config.package_dir.mkdir(parents=True, exist_ok=True)
        print("✅ 构建目录清理完成")
    
    def install_dependencies(self):
        """安装打包依赖"""
        print("📦 安装打包依赖...")
        
        dependencies = [
            "pyinstaller>=5.0.0",
            "huggingface_hub>=0.16.0",
            "auto-py-to-exe",  # 可选的GUI工具
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"   ✅ 已安装: {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ 安装失败: {dep} - {e}")
                return False
        
        print("✅ 打包依赖安装完成")
        return True
    
    def create_pyinstaller_spec(self):
        """创建PyInstaller规格文件"""
        print("📝 创建PyInstaller规格文件...")
        
        spec_config = self.config.get_pyinstaller_spec()
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{spec_config["script"]}'],
    pathex=['{self.config.project_root}'],
    binaries=[],
    datas={spec_config["datas"]},
    hiddenimports={spec_config["hidden_imports"]},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks={spec_config["runtime_hooks"]},
    excludes={spec_config["excludes"]},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 收集所有transformers和torch相关文件
for module in {spec_config["collect_all"]}:
    a.datas += collect_data_files(module)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{spec_config["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={str(spec_config["console"]).lower()},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{spec_config["name"]}',
)
'''
        
        spec_file = self.config.build_dir / f"{self.config.package_name}.spec"
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✅ 规格文件已创建: {spec_file}")
        return spec_file
    
    def build_executable(self, spec_file: Path):
        """使用PyInstaller构建可执行文件"""
        print("🔨 构建可执行文件...")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath", str(self.config.dist_dir),
            "--workpath", str(self.config.build_dir / "work"),
            str(spec_file)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 可执行文件构建完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def create_model_management_scripts(self):
        """创建模型管理脚本"""
        print("📜 创建模型管理脚本...")
        
        # 创建模型下载器
        downloader_script = self.config.package_dir / "model_downloader.py"
        with open(downloader_script, 'w', encoding='utf-8') as f:
            f.write(self.model_manager.create_model_downloader_script())
        
        # 创建启动脚本
        startup_script = self.config.package_dir / "start.py"
        with open(startup_script, 'w', encoding='utf-8') as f:
            f.write(self.model_manager.create_startup_script())
        
        # 创建批处理启动文件（Windows）
        batch_script = self.config.package_dir / "启动VisionAI-ClipsMaster.bat"
        batch_content = f'''@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo VisionAI-ClipsMaster 正在启动...
python start.py
pause
'''
        with open(batch_script, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        print("✅ 模型管理脚本创建完成")
    
    def create_configuration_files(self):
        """创建配置文件"""
        print("⚙️ 创建配置文件...")
        
        # 创建模型配置
        models_config = {
            "download_on_startup": True,
            "models_directory": "models/downloaded",
            "available_models": self.model_manager.model_configs,
            "auto_cleanup": False,
            "max_cache_size_gb": 20
        }
        
        config_file = self.config.package_dir / "models" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(models_config, f, indent=2, ensure_ascii=False)
        
        # 创建应用配置
        app_config = {
            "app_name": "VisionAI-ClipsMaster",
            "version": self.config.version,
            "self_contained": True,
            "models_path": "models/downloaded",
            "temp_path": "temp",
            "logs_path": "logs",
            "data_path": "data"
        }
        
        app_config_file = self.config.package_dir / "config.json"
        with open(app_config_file, 'w', encoding='utf-8') as f:
            json.dump(app_config, f, indent=2, ensure_ascii=False)
        
        print("✅ 配置文件创建完成")
    
    def create_readme_and_docs(self):
        """创建说明文档"""
        print("📚 创建说明文档...")
        
        readme_content = f'''# VisionAI-ClipsMaster v{self.config.version}
## 完全自包含整合包

### 快速开始
1. 双击 `启动VisionAI-ClipsMaster.bat` 启动程序
2. 首次运行会自动下载AI模型（需要网络连接）
3. 模型下载完成后即可开始使用

### 系统要求
- Windows 10/11 (64位)
- 内存: 4GB以上
- 硬盘空间: 15GB以上（包含AI模型）
- 网络连接（首次运行下载模型）

### 目录结构
```
VisionAI-ClipsMaster-v{self.config.version}/
├── 启动VisionAI-ClipsMaster.bat    # 主启动文件
├── start.py                        # Python启动脚本
├── model_downloader.py             # 模型下载器
├── {self.config.package_name}.exe  # 主程序
├── models/                         # AI模型目录
│   ├── config.json                # 模型配置
│   └── downloaded/                # 下载的模型文件
├── configs/                       # 系统配置
├── data/                          # 数据目录
├── logs/                          # 日志文件
└── temp/                          # 临时文件
```

### 完全卸载
删除整个 `VisionAI-ClipsMaster-v{self.config.version}` 文件夹即可完全卸载，
不会在系统其他位置留下任何文件。

### 技术支持
如遇问题，请查看 `logs/` 目录下的日志文件。
'''
        
        readme_file = self.config.package_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print("✅ 说明文档创建完成")
    
    def optimize_package_size(self):
        """优化整合包大小"""
        print("🗜️ 优化整合包大小...")
        
        # 删除不必要的文件
        unnecessary_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo", 
            "**/tests",
            "**/test_*",
            "**/.git*",
            "**/docs",
            "**/*.md",
            "**/examples",
        ]
        
        for pattern in unnecessary_patterns:
            for path in self.config.package_dir.glob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
        
        print("✅ 包大小优化完成")
    
    def create_final_package(self):
        """创建最终的分发包"""
        print("📦 创建最终分发包...")
        
        # 创建压缩包
        zip_file = self.config.dist_dir / f"{self.config.package_name}-v{self.config.version}.zip"
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.config.package_dir.rglob('*'):
                if file_path.is_file():
                    arc_name = file_path.relative_to(self.config.package_dir.parent)
                    zf.write(file_path, arc_name)
        
        print(f"✅ 分发包已创建: {zip_file}")
        print(f"📊 包大小: {zip_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        return zip_file
    
    def build(self):
        """执行完整的构建流程"""
        print(f"🚀 开始构建 {self.config.package_name} v{self.config.version}")
        print("=" * 60)
        
        try:
            # 1. 清理构建目录
            self.clean_build_dirs()
            
            # 2. 安装依赖
            if not self.install_dependencies():
                return False
            
            # 3. 创建PyInstaller规格文件
            spec_file = self.create_pyinstaller_spec()
            
            # 4. 构建可执行文件
            if not self.build_executable(spec_file):
                return False
            
            # 5. 创建模型管理脚本
            self.create_model_management_scripts()
            
            # 6. 创建配置文件
            self.create_configuration_files()
            
            # 7. 创建说明文档
            self.create_readme_and_docs()
            
            # 8. 优化包大小
            self.optimize_package_size()
            
            # 9. 创建最终分发包
            final_package = self.create_final_package()
            
            print("=" * 60)
            print("🎉 构建完成！")
            print(f"📁 整合包位置: {self.config.package_dir}")
            print(f"📦 分发包位置: {final_package}")
            print("\n使用说明:")
            print("1. 解压分发包到任意目录")
            print("2. 双击 '启动VisionAI-ClipsMaster.bat' 即可使用")
            
            return True
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    builder = PackageBuilder()
    success = builder.build()
    
    if not success:
        print("\n构建失败，请检查错误信息")
        sys.exit(1)
    
    print("\n构建成功！")
    input("按回车键退出...")
