#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 快速打包脚本
一键创建完全自包含的整合包
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

def print_step(step_name, step_num=None, total_steps=None):
    """打印步骤信息"""
    if step_num and total_steps:
        print(f"\n{'='*60}")
        print(f"步骤 {step_num}/{total_steps}: {step_name}")
        print(f"{'='*60}")
    else:
        print(f"\n🔧 {step_name}")

def run_command(cmd, description="", check=True):
    """运行命令并处理错误"""
    print(f"执行: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return False

def main():
    """主打包流程"""
    project_root = Path(__file__).parent
    build_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🚀 VisionAI-ClipsMaster 整合包构建器")
    print(f"项目根目录: {project_root}")
    print(f"构建时间: {build_time}")
    
    # 步骤1: 检查环境
    print_step("检查构建环境", 1, 8)
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查主程序文件
    main_script = project_root / "simple_ui_fixed.py"
    if not main_script.exists():
        print(f"❌ 主程序文件不存在: {main_script}")
        return False
    print(f"✅ 主程序文件: {main_script}")
    
    # 步骤2: 安装打包依赖
    print_step("安装打包依赖", 2, 8)
    
    dependencies = ["pyinstaller>=5.0.0", "huggingface_hub>=0.16.0"]
    for dep in dependencies:
        if not run_command([sys.executable, "-m", "pip", "install", dep], 
                          f"安装 {dep}"):
            print(f"⚠️ {dep} 安装失败，继续尝试...")
    
    # 步骤3: 清理构建目录
    print_step("清理构建目录", 3, 8)
    
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    for dir_path in [build_dir, dist_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✅ 已清理: {dir_path}")
    
    # 步骤4: 创建PyInstaller规格文件
    print_step("创建PyInstaller规格文件", 4, 8)
    
    spec_file = project_root / "packaging" / "visionai_clipsmaster.spec"
    if not spec_file.exists():
        print(f"❌ 规格文件不存在: {spec_file}")
        return False
    print(f"✅ 使用规格文件: {spec_file}")
    
    # 步骤5: 构建可执行文件
    print_step("构建可执行文件", 5, 8)
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm", 
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir / "work"),
        str(spec_file)
    ]
    
    if not run_command(pyinstaller_cmd, "PyInstaller构建"):
        print("❌ 可执行文件构建失败")
        return False
    
    print("✅ 可执行文件构建完成")
    
    # 步骤6: 复制打包脚本和配置
    print_step("复制打包脚本和配置", 6, 8)
    
    package_dir = dist_dir / "VisionAI-ClipsMaster"
    if not package_dir.exists():
        print(f"❌ 打包目录不存在: {package_dir}")
        return False
    
    # 复制打包相关文件
    packaging_files = [
        ("scripts/deployment/model_path_manager.py", "model_path_manager.py"),
        ("scripts/deployment/startup_validator.py", "startup_validator.py"),
        ("scripts/deployment/launcher.py", "launcher.py"),
        ("scripts/deployment/启动VisionAI-ClipsMaster.bat", "启动VisionAI-ClipsMaster.bat"),
    ]
    
    for src, dst in packaging_files:
        src_path = project_root / src
        dst_path = package_dir / dst
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"✅ 已复制: {dst}")
        else:
            print(f"⚠️ 文件不存在: {src}")
    
    # 创建配置文件
    config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "1.0.1",
        "build_time": build_time,
        "self_contained": True,
        "first_run": True,
        "models_path": "models/downloaded",
        "temp_path": "temp",
        "logs_path": "logs",
        "data_path": "data"
    }
    
    config_file = package_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("✅ 配置文件已创建")
    
    # 创建必要目录
    required_dirs = ["models", "models/downloaded", "data", "logs", "temp"]
    for dir_name in required_dirs:
        dir_path = package_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录已创建: {dir_name}")
    
    # 步骤7: 创建说明文档
    print_step("创建说明文档", 7, 8)
    
    readme_content = f"""# VisionAI-ClipsMaster v1.0.1
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
VisionAI-ClipsMaster/
├── 启动VisionAI-ClipsMaster.bat    # 主启动文件
├── launcher.py                     # Python启动脚本
├── VisionAI-ClipsMaster.exe        # 主程序
├── models/                         # AI模型目录
├── configs/                        # 系统配置
├── data/                           # 数据目录
├── logs/                           # 日志文件
└── temp/                           # 临时文件
```

### 完全卸载
删除整个 `VisionAI-ClipsMaster` 文件夹即可完全卸载，
不会在系统其他位置留下任何文件。

### 构建信息
- 构建时间: {build_time}
- Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}
- 包含模型: Mistral-7B (英文), Qwen3-1.7B (中文)

### 技术支持
如遇问题，请查看 `logs/` 目录下的日志文件。
"""
    
    readme_file = package_dir / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ README文档已创建")
    
    # 步骤8: 计算包大小并完成
    print_step("完成打包", 8, 8)
    
    # 计算包大小
    total_size = 0
    file_count = 0
    for path in package_dir.rglob('*'):
        if path.is_file():
            total_size += path.stat().st_size
            file_count += 1
    
    size_mb = total_size / 1024 / 1024
    
    print(f"✅ 打包完成！")
    print(f"📁 整合包位置: {package_dir}")
    print(f"📊 包大小: {size_mb:.1f} MB")
    print(f"📄 文件数量: {file_count}")
    
    print(f"\n🎉 VisionAI-ClipsMaster 整合包构建成功！")
    print(f"\n使用说明:")
    print(f"1. 进入目录: {package_dir}")
    print(f"2. 双击运行: 启动VisionAI-ClipsMaster.bat")
    print(f"3. 首次运行会自动下载AI模型")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 构建成功完成！")
        else:
            print("\n❌ 构建失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断构建")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    input("\n按回车键退出...")
