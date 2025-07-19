#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster Windows项目结构组织脚本
专为Windows PowerShell环境优化
"""

import os
import shutil
import stat
from pathlib import Path

def create_directory_structure():
    """创建标准目录结构"""
    
    # 定义目录结构
    directories = [
        # 源代码目录
        "src/visionai_clipsmaster",
        "src/visionai_clipsmaster/core",
        "src/visionai_clipsmaster/models", 
        "src/visionai_clipsmaster/training",
        "src/visionai_clipsmaster/exporters",
        "src/visionai_clipsmaster/utils",
        "src/visionai_clipsmaster/concurrent",
        "src/visionai_clipsmaster/ui",
        "src/visionai_clipsmaster/ui/components",
        "src/visionai_clipsmaster/ui/assets",
        
        # 配置目录
        "configs",
        "configs/examples",
        
        # 模型目录
        "models",
        "models/mistral",
        "models/qwen", 
        "models/shared",
        "models/shared/vocabularies",
        
        # 数据目录
        "data",
        "data/examples",
        "data/input",
        "data/training", 
        "data/output",
        
        # 测试目录
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/performance",
        "tests/fixtures",
        "tests/fixtures/test_videos",
        "tests/fixtures/test_subtitles",
        
        # 文档目录
        "docs",
        "docs/installation",
        "docs/user_guide",
        "docs/developer_guide", 
        "docs/examples",
        "docs/assets",
        "docs/assets/images",
        "docs/assets/diagrams",
        
        # 脚本目录
        "scripts",
        
        # 工具目录
        "tools",
        "tools/ffmpeg",
        
        # Docker目录
        "docker",
        
        # GitHub配置
        ".github",
        ".github/workflows",
        ".github/ISSUE_TEMPLATE",
        
        # 示例目录
        "examples",
        "examples/basic_usage",
        "examples/advanced_usage",
        "examples/notebooks",
        
        # 日志目录
        "logs",
        
        # 依赖目录
        "requirements"
    ]
    
    # 创建所有目录
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✓ 创建目录: {directory}")
        except Exception as e:
            print(f"⚠ 创建目录失败 {directory}: {e}")

def safe_copy_file(source, destination):
    """安全地复制文件"""
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if source_path.exists():
            # 确保目标目录存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, dest_path)
            print(f"✓ 移动文件: {source} → {destination}")
            return True
        else:
            print(f"⚠ 源文件不存在: {source}")
            return False
    except Exception as e:
        print(f"❌ 文件复制失败 {source} → {destination}: {e}")
        return False

def move_existing_files():
    """移动现有文件到正确位置"""
    
    # 文件移动映射
    file_moves = {
        # 源代码文件 - 检查多个可能的位置
        "VisionAI-ClipsMaster-Core/src/core/language_detector.py": "src/visionai_clipsmaster/core/language_detector.py",
        "src/core/language_detector.py": "src/visionai_clipsmaster/core/language_detector.py",
        "language_detector.py": "src/visionai_clipsmaster/core/language_detector.py",
        
        "VisionAI-ClipsMaster-Core/src/core/model_switcher.py": "src/visionai_clipsmaster/core/model_switcher.py",
        "src/core/model_switcher.py": "src/visionai_clipsmaster/core/model_switcher.py",
        "model_switcher.py": "src/visionai_clipsmaster/core/model_switcher.py",
        
        # 并发处理模块
        "VisionAI-ClipsMaster-Core/src/concurrent/worker_pool.py": "src/visionai_clipsmaster/concurrent/worker_pool.py",
        "src/concurrent/worker_pool.py": "src/visionai_clipsmaster/concurrent/worker_pool.py",
        "worker_pool.py": "src/visionai_clipsmaster/concurrent/worker_pool.py",
        
        "VisionAI-ClipsMaster-Core/src/concurrent/resource_manager.py": "src/visionai_clipsmaster/concurrent/resource_manager.py",
        "src/concurrent/resource_manager.py": "src/visionai_clipsmaster/concurrent/resource_manager.py",
        "resource_manager.py": "src/visionai_clipsmaster/concurrent/resource_manager.py",
        
        "VisionAI-ClipsMaster-Core/src/concurrent/batch_processor.py": "src/visionai_clipsmaster/concurrent/batch_processor.py",
        "src/concurrent/batch_processor.py": "src/visionai_clipsmaster/concurrent/batch_processor.py",
        "batch_processor.py": "src/visionai_clipsmaster/concurrent/batch_processor.py",
        
        "VisionAI-ClipsMaster-Core/src/concurrent/progress_tracker.py": "src/visionai_clipsmaster/concurrent/progress_tracker.py",
        "src/concurrent/progress_tracker.py": "src/visionai_clipsmaster/concurrent/progress_tracker.py",
        "progress_tracker.py": "src/visionai_clipsmaster/concurrent/progress_tracker.py",
        
        # UI文件
        "simple_ui_fixed.py": "src/visionai_clipsmaster/ui/main_window.py",
        
        # 脚本文件
        "setup_models.py": "scripts/setup_models.py",
        "check_environment.py": "scripts/check_environment.py",
        "install.bat": "scripts/install.bat", 
        "install.sh": "scripts/install.sh",
        "quick_start.py": "scripts/quick_start.py",
        
        # 依赖文件
        "requirements.txt": "requirements/requirements.txt",
        "requirements-lite.txt": "requirements/requirements-lite.txt",
        "requirements-dev.txt": "requirements/requirements-dev.txt",
        "requirements-full.txt": "requirements/requirements-full.txt",
    }
    
    # 执行文件移动
    moved_count = 0
    for source, destination in file_moves.items():
        if safe_copy_file(source, destination):
            moved_count += 1
    
    print(f"\n📊 文件移动统计: 成功移动 {moved_count} 个文件")

def create_init_files():
    """创建必要的__init__.py文件"""
    
    init_files = [
        "src/__init__.py",
        "src/visionai_clipsmaster/__init__.py", 
        "src/visionai_clipsmaster/core/__init__.py",
        "src/visionai_clipsmaster/models/__init__.py",
        "src/visionai_clipsmaster/training/__init__.py",
        "src/visionai_clipsmaster/exporters/__init__.py",
        "src/visionai_clipsmaster/utils/__init__.py",
        "src/visionai_clipsmaster/concurrent/__init__.py",
        "src/visionai_clipsmaster/ui/__init__.py",
        "tests/__init__.py",
    ]
    
    for init_file in init_files:
        try:
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# -*- coding: utf-8 -*-\n')
                f.write(f'"""{Path(init_file).parent.name} package"""\n')
            print(f"✓ 创建文件: {init_file}")
        except Exception as e:
            print(f"❌ 创建文件失败 {init_file}: {e}")

def create_placeholder_files():
    """创建占位文件"""
    
    placeholder_files = [
        ("models/README.md", "# 模型文件目录\n\n请运行 `python scripts/setup_models.py --setup` 下载模型文件。\n"),
        ("data/README.md", "# 数据目录\n\n- `input/`: 输入文件\n- `output/`: 输出文件\n- `training/`: 训练数据\n- `examples/`: 示例文件\n"),
        ("logs/README.md", "# 日志目录\n\n程序运行日志将保存在此目录。\n"),
        ("tools/ffmpeg/README.md", "# FFmpeg工具\n\n请从 https://ffmpeg.org/download.html 下载FFmpeg并解压到此目录。\n"),
        ("data/.gitkeep", ""),
        ("logs/.gitkeep", ""),
        ("models/.gitkeep", ""),
        ("tools/.gitkeep", ""),
    ]
    
    for file_path, content in placeholder_files:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 创建占位文件: {file_path}")
        except Exception as e:
            print(f"❌ 创建占位文件失败 {file_path}: {e}")

def make_scripts_executable():
    """使脚本文件可执行（Windows兼容）"""
    script_files = [
        "scripts/install.sh",
        "scripts/git_setup.sh",
        "organize_project.py",
        "git_setup.sh"
    ]
    
    for script_file in script_files:
        try:
            if Path(script_file).exists():
                # Windows下设置文件权限
                current_permissions = os.stat(script_file).st_mode
                os.chmod(script_file, current_permissions | stat.S_IEXEC)
                print(f"✓ 设置可执行权限: {script_file}")
        except Exception as e:
            print(f"⚠ 设置权限失败 {script_file}: {e}")

def main():
    """主函数"""
    print("🚀 开始组织VisionAI-ClipsMaster项目结构 (Windows版本)...")
    print("=" * 60)
    
    # 1. 创建目录结构
    print("\n📁 创建目录结构...")
    create_directory_structure()
    
    # 2. 移动现有文件
    print("\n📦 移动现有文件...")
    move_existing_files()
    
    # 3. 创建__init__.py文件
    print("\n🐍 创建Python包文件...")
    create_init_files()
    
    # 4. 创建占位文件
    print("\n📄 创建占位文件...")
    create_placeholder_files()
    
    # 5. 设置脚本权限
    print("\n🔧 设置脚本权限...")
    make_scripts_executable()
    
    print("\n" + "=" * 60)
    print("✅ 项目结构组织完成！")
    print("\n📊 验证结果:")
    
    # 验证关键目录
    key_dirs = [
        "src/visionai_clipsmaster/core",
        "src/visionai_clipsmaster/concurrent", 
        "requirements",
        "scripts",
        "docker",
        ".github/workflows"
    ]
    
    for dir_path in key_dirs:
        if Path(dir_path).exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")
    
    print("\n🎯 下一步:")
    print("1. 检查文件是否正确移动")
    print("2. 运行 Git 初始化命令")
    print("3. 提交代码到GitHub")

if __name__ == "__main__":
    main()
