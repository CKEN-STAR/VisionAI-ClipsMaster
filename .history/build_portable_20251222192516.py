#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 便携版打包脚本
安全地创建可移植整合包，不影响现有项目

使用方法:
    python build_portable.py

输出:
    dist/VisionAI-ClipsMaster-Portable/  - 完整的便携版目录
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "dist" / "VisionAI-ClipsMaster-Portable"
BACKUP_DIR = PROJECT_ROOT / "dist" / "backup"

def print_header(msg):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {msg}")
    print("=" * 60)

def print_step(step, msg):
    """打印步骤"""
    print(f"\n[{step}] {msg}")

def check_environment():
    """检查打包环境"""
    print_header("检查打包环境")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("  请运行: pip install pyinstaller")
        return False
    
    # 检查spec文件
    spec_file = PROJECT_ROOT / "visionai_portable.spec"
    if not spec_file.exists():
        print(f"✗ 找不到spec文件: {spec_file}")
        return False
    print(f"✓ Spec文件存在: {spec_file}")
    
    # 检查主程序
    main_file = PROJECT_ROOT / "simple_ui_fixed.py"
    if not main_file.exists():
        print(f"✗ 找不到主程序: {main_file}")
        return False
    print(f"✓ 主程序存在: {main_file}")
    
    # 检查关键目录
    required_dirs = ['configs', 'src', 'ui', 'tools/ffmpeg']
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            print(f"✗ 缺少目录: {dir_name}")
            return False
        print(f"✓ 目录存在: {dir_name}")
    
    return True

def backup_existing():
    """备份现有的打包结果"""
    print_step(1, "备份现有打包结果")
    
    if OUTPUT_DIR.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"portable_backup_{timestamp}"
        
        print(f"  备份到: {backup_path}")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(OUTPUT_DIR), str(backup_path))
        print("  ✓ 备份完成")
    else:
        print("  无需备份（目录不存在）")

def run_pyinstaller():
    """运行PyInstaller打包"""
    print_step(2, "运行PyInstaller打包")
    
    spec_file = PROJECT_ROOT / "visionai_portable.spec"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"  命令: {' '.join(cmd)}")
    print("  正在打包，请稍候...")
    print("-" * 40)
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    
    if result.returncode != 0:
        print("  ✗ PyInstaller打包失败")
        return False
    
    print("-" * 40)
    print("  ✓ PyInstaller打包完成")
    return True

def create_additional_files():
    """创建额外的配置文件"""
    print_step(3, "创建额外文件")
    
    if not OUTPUT_DIR.exists():
        print("  ✗ 输出目录不存在")
        return False
    
    # 创建启动脚本
    start_script = OUTPUT_DIR / "启动VisionAI.bat"
    start_script.write_text('''@echo off
chcp 65001 >nul
echo ========================================
echo   VisionAI-ClipsMaster 便携版
echo ========================================
echo.
echo 正在启动...
cd /d "%~dp0"
VisionAI-ClipsMaster.exe
pause
''', encoding='utf-8')
    print(f"  ✓ 创建启动脚本: {start_script.name}")
    
    # 创建说明文件
    readme = OUTPUT_DIR / "使用说明.txt"
    readme.write_text(f'''VisionAI-ClipsMaster 便携版
============================

版本: v1.2.0
打包时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

使用方法:
---------
1. 双击 "启动VisionAI.bat" 或直接运行 "VisionAI-ClipsMaster.exe"
2. 首次运行可能需要较长时间加载

目录说明:
---------
- VisionAI-ClipsMaster.exe  主程序
- _internal/                 程序依赖文件
- configs/                   配置文件（可自定义）
- models/                    AI模型目录
- tools/ffmpeg/              视频处理工具

注意事项:
---------
1. 请勿删除 _internal 目录中的任何文件
2. 模型文件需要单独下载放入 models 目录
3. 如遇问题，请查看控制台输出的错误信息

云端AI模式:
---------
本版本支持云端AI模式，无需本地模型即可使用AI功能：
1. 在设置中选择"云端模式"
2. 配置API密钥（支持SiliconFlow、ModelScope等）
3. 即可使用云端AI进行字幕优化

技术支持:
---------
如有问题，请联系开发者
''', encoding='utf-8')
    print(f"  ✓ 创建说明文件: {readme.name}")
    
    # 创建必要的空目录
    dirs_to_create = [
        'models/qwen/quantized',
        'logs',
        'output',
        'temp',
        'exports',
    ]
    
    for dir_name in dirs_to_create:
        dir_path = OUTPUT_DIR / "_internal" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # 创建.gitkeep保持目录
        (dir_path / ".gitkeep").touch()
    print(f"  ✓ 创建必要目录结构")
    
    return True

def verify_package():
    """验证打包结果"""
    print_step(4, "验证打包结果")
    
    if not OUTPUT_DIR.exists():
        print("  ✗ 输出目录不存在")
        return False
    
    # 检查主程序
    exe_file = OUTPUT_DIR / "VisionAI-ClipsMaster.exe"
    if not exe_file.exists():
        print("  ✗ 主程序不存在")
        return False
    print(f"  ✓ 主程序: {exe_file.name} ({exe_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 检查内部目录
    internal_dir = OUTPUT_DIR / "_internal"
    if not internal_dir.exists():
        print("  ✗ _internal目录不存在")
        return False
    
    # 统计文件
    total_files = sum(1 for _ in OUTPUT_DIR.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file())
    
    print(f"  ✓ 总文件数: {total_files}")
    print(f"  ✓ 总大小: {total_size / 1024 / 1024:.1f} MB")
    
    # 检查关键文件
    key_paths = [
        "_internal/configs",
        "_internal/tools/ffmpeg/bin/ffmpeg.exe",
    ]
    
    for path in key_paths:
        full_path = OUTPUT_DIR / path
        if full_path.exists():
            print(f"  ✓ {path}")
        else:
            print(f"  ⚠ 缺少: {path}")
    
    return True

def main():
    """主函数"""
    print_header("VisionAI-ClipsMaster 便携版打包工具")
    print(f"项目目录: {PROJECT_ROOT}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    # 检查环境
    if not check_environment():
        print("\n✗ 环境检查失败，请修复后重试")
        return 1
    
    # 备份现有结果
    backup_existing()
    
    # 运行打包
    if not run_pyinstaller():
        print("\n✗ 打包失败")
        return 1
    
    # 创建额外文件
    if not create_additional_files():
        print("\n⚠ 创建额外文件时出现问题")
    
    # 验证结果
    if not verify_package():
        print("\n⚠ 验证时发现问题")
    
    print_header("打包完成")
    print(f"\n便携版位置: {OUTPUT_DIR}")
    print("\n可以将整个目录复制到其他设备使用")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
