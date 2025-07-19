#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 部署包生成器
创建适合4GB内存设备的轻量化部署包
"""

import os
import shutil
import json
import zipfile
from pathlib import Path
from datetime import datetime
import argparse

class DeploymentPackageCreator:
    def __init__(self, source_dir=".", output_dir="deployment_packages"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 部署包配置
        self.packages = {
            "lite": {
                "name": "VisionAI-ClipsMaster-Lite",
                "description": "核心运行时包 (≤200MB)",
                "target_size": "200MB",
                "includes": [
                    "src/",
                    "configs/",
                    "ui/",
                    "requirements.txt",
                    "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
                    "VisionAI-ClipsMaster-Core/requirements.txt"
                ],
                "excludes": [
                    "models/",
                    "tools/ffmpeg/",
                    "examples/",
                    "tests/",
                    "docs/"
                ]
            },
            "standard": {
                "name": "VisionAI-ClipsMaster-Standard", 
                "description": "标准包含FFmpeg (≤600MB)",
                "target_size": "600MB",
                "includes": [
                    "src/",
                    "configs/",
                    "ui/",
                    "tools/ffmpeg/bin/",
                    "requirements.txt",
                    "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
                    "VisionAI-ClipsMaster-Core/requirements.txt",
                    "README.md",
                    "LICENSE"
                ],
                "excludes": [
                    "models/",
                    "examples/",
                    "tests/",
                    "docs/",
                    "tools/ffmpeg/*.zip"
                ]
            },
            "complete": {
                "name": "VisionAI-ClipsMaster-Complete",
                "description": "完整包含量化模型 (≤1GB)",
                "target_size": "1GB", 
                "includes": [
                    "src/",
                    "configs/",
                    "ui/",
                    "tools/ffmpeg/bin/",
                    "models/*/quantized/*.gguf",
                    "models/configs/",
                    "requirements.txt",
                    "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
                    "VisionAI-ClipsMaster-Core/requirements.txt",
                    "README.md",
                    "LICENSE",
                    "docs/USER_MANUAL.md"
                ],
                "excludes": [
                    "models/*/base/",
                    "examples/",
                    "tests/",
                    "tools/ffmpeg/*.zip"
                ]
            }
        }
    
    def get_dir_size(self, path):
        """计算目录大小"""
        total = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, FileNotFoundError):
            pass
        return total
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def copy_with_pattern(self, source_root, dest_root, pattern):
        """根据模式复制文件"""
        source_path = source_root / pattern
        
        if source_path.exists():
            if source_path.is_file():
                dest_path = dest_root / pattern
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                return source_path.stat().st_size
            elif source_path.is_dir():
                dest_path = dest_root / pattern
                if not dest_path.exists():
                    shutil.copytree(source_path, dest_path)
                    return self.get_dir_size(source_path)
        else:
            # 处理通配符模式
            copied_size = 0
            for match in source_root.glob(pattern):
                if match.is_file():
                    rel_path = match.relative_to(source_root)
                    dest_path = dest_root / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(match, dest_path)
                    copied_size += match.stat().st_size
                elif match.is_dir():
                    rel_path = match.relative_to(source_root)
                    dest_path = dest_root / rel_path
                    if not dest_path.exists():
                        shutil.copytree(match, dest_path)
                        copied_size += self.get_dir_size(match)
            return copied_size
        
        return 0
    
    def create_package(self, package_type, compress=True):
        """创建指定类型的部署包"""
        if package_type not in self.packages:
            raise ValueError(f"未知的包类型: {package_type}")
        
        config = self.packages[package_type]
        package_name = config["name"]
        
        print(f"\n🚀 创建 {package_name} 部署包...")
        print(f"📝 描述: {config['description']}")
        print(f"🎯 目标大小: {config['target_size']}")
        
        # 创建临时目录
        temp_dir = self.output_dir / f"temp_{package_name}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        package_dir = temp_dir / package_name
        package_dir.mkdir()
        
        # 复制包含的文件
        total_size = 0
        copied_files = []
        
        for include_pattern in config["includes"]:
            print(f"📁 复制: {include_pattern}")
            size = self.copy_with_pattern(self.source_dir, package_dir, include_pattern)
            if size > 0:
                total_size += size
                copied_files.append(include_pattern)
        
        # 创建启动脚本
        self.create_startup_scripts(package_dir)
        
        # 创建安装说明
        self.create_installation_guide(package_dir, package_type)
        
        # 创建包信息文件
        package_info = {
            "package_name": package_name,
            "package_type": package_type,
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "description": config["description"],
            "target_size": config["target_size"],
            "actual_size": self.format_size(total_size),
            "actual_size_bytes": total_size,
            "included_files": copied_files,
            "requirements": {
                "python": ">=3.8",
                "memory": "4GB RAM",
                "storage": "1GB available space"
            }
        }
        
        with open(package_dir / "package_info.json", 'w', encoding='utf-8') as f:
            json.dump(package_info, f, indent=2, ensure_ascii=False)
        
        print(f"📦 包大小: {self.format_size(total_size)}")
        
        # 压缩包
        if compress:
            zip_path = self.output_dir / f"{package_name}-v1.0.0.zip"
            print(f"🗜️ 压缩到: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            compressed_size = zip_path.stat().st_size
            print(f"📦 压缩后大小: {self.format_size(compressed_size)}")
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return zip_path, compressed_size
        else:
            # 移动到最终位置
            final_dir = self.output_dir / package_name
            if final_dir.exists():
                shutil.rmtree(final_dir)
            shutil.move(package_dir, final_dir)
            shutil.rmtree(temp_dir)
            
            return final_dir, total_size
    
    def create_startup_scripts(self, package_dir):
        """创建启动脚本"""
        # Windows 启动脚本
        windows_script = """@echo off
echo VisionAI-ClipsMaster 启动中...
cd /d "%~dp0"

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 启动程序
echo 启动VisionAI-ClipsMaster...
if exist "VisionAI-ClipsMaster-Core\\\\1imple_ui_fixed.py" (
    python VisionAI-ClipsMaster-Core\\\\1imple_ui_fixed.py
) else (
    python src\\\\1ain.py
)

pause
"""
        
        with open(package_dir / "start.bat", 'w', encoding='utf-8') as f:
            f.write(windows_script)
        
        # Linux/Mac 启动脚本
        unix_script = """#!/bin/bash
echo "VisionAI-ClipsMaster 启动中..."
cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 安装依赖
echo "安装依赖包..."
pip3 install -r requirements.txt

# 启动程序
echo "启动VisionAI-ClipsMaster..."
if [ -f "VisionAI-ClipsMaster-Core/simple_ui_fixed.py" ]; then
    python3 VisionAI-ClipsMaster-Core/simple_ui_fixed.py
else
    python3 src/main.py
fi
"""
        
        with open(package_dir / "start.sh", 'w', encoding='utf-8') as f:
            f.write(unix_script)
        
        # 设置执行权限
        os.chmod(package_dir / "start.sh", 0o755)
    
    def create_installation_guide(self, package_dir, package_type):
        """创建安装说明"""
        guide = f"""# VisionAI-ClipsMaster 安装指南

## 系统要求
- Python 3.8 或更高版本
- 4GB RAM (推荐 8GB)
- 1GB 可用存储空间
- Windows 10/11, macOS 10.14+, 或 Linux

## 快速开始

### Windows
1. 双击 `start.bat` 启动程序
2. 首次运行会自动安装依赖包
3. 等待程序启动完成

### Linux/macOS
1. 打开终端，进入程序目录
2. 运行: `./start.sh`
3. 首次运行会自动安装依赖包

### 手动安装
如果自动安装失败，请手动执行：
```bash
pip install -r requirements.txt
python VisionAI-ClipsMaster-Core/simple_ui_fixed.py
```

## 包类型说明
- **Lite**: 仅核心代码，需要单独下载模型和FFmpeg
- **Standard**: 包含FFmpeg，需要单独下载模型
- **Complete**: 包含所有必要组件，可直接使用

## 故障排除
1. **Python未找到**: 请安装Python 3.8+并添加到PATH
2. **依赖安装失败**: 尝试使用国内镜像源
3. **内存不足**: 关闭其他程序释放内存

## 获取帮助
- GitHub: https://github.com/CKEN/VisionAI-ClipsMaster
- 文档: 查看docs目录下的详细文档
"""
        
        with open(package_dir / "INSTALL.md", 'w', encoding='utf-8') as f:
            f.write(guide)
    
    def create_all_packages(self, compress=True):
        """创建所有类型的部署包"""
        print("🎯 VisionAI-ClipsMaster 部署包生成器")
        print("=" * 50)
        
        results = {}
        
        for package_type in self.packages.keys():
            try:
                path, size = self.create_package(package_type, compress)
                results[package_type] = {
                    "path": str(path),
                    "size": self.format_size(size),
                    "size_bytes": size,
                    "success": True
                }
            except Exception as e:
                print(f"❌ 创建 {package_type} 包失败: {e}")
                results[package_type] = {
                    "error": str(e),
                    "success": False
                }
        
        # 生成总结报告
        report_file = self.output_dir / "deployment_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 部署包创建完成！")
        print(f"📄 详细报告: {report_file}")
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 部署包生成器")
    parser.add_argument("--type", choices=["lite", "standard", "complete", "all"],
                       default="all", help="要创建的包类型")
    parser.add_argument("--no-compress", action="store_true",
                       help="不压缩，保留目录结构")
    parser.add_argument("--source", default=".", help="源代码目录")
    parser.add_argument("--output", default="deployment_packages", help="输出目录")
    
    args = parser.parse_args()
    
    creator = DeploymentPackageCreator(args.source, args.output)
    
    if args.type == "all":
        creator.create_all_packages(not args.no_compress)
    else:
        creator.create_package(args.type, not args.no_compress)

if __name__ == "__main__":
    main()
