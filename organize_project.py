#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 项目结构组织脚本
将现有文件按照标准开源项目结构重新组织
"""

import os
import shutil
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
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def move_existing_files():
    """移动现有文件到正确位置"""
    
    # 文件移动映射
    file_moves = {
        # 源代码文件
        "VisionAI-ClipsMaster-Core/src/core/language_detector.py": "src/visionai_clipsmaster/core/language_detector.py",
        "VisionAI-ClipsMaster-Core/src/core/model_switcher.py": "src/visionai_clipsmaster/core/model_switcher.py",
        "VisionAI-ClipsMaster-Core/src/core/srt_parser.py": "src/visionai_clipsmaster/core/srt_parser.py",
        "VisionAI-ClipsMaster-Core/src/core/screenplay_engineer.py": "src/visionai_clipsmaster/core/screenplay_engineer.py",
        "VisionAI-ClipsMaster-Core/src/core/narrative_analyzer.py": "src/visionai_clipsmaster/core/narrative_analyzer.py",
        "VisionAI-ClipsMaster-Core/src/core/alignment_engineer.py": "src/visionai_clipsmaster/core/alignment_engineer.py",
        "VisionAI-ClipsMaster-Core/src/core/clip_generator.py": "src/visionai_clipsmaster/core/clip_generator.py",
        "VisionAI-ClipsMaster-Core/src/core/rhythm_analyzer.py": "src/visionai_clipsmaster/core/rhythm_analyzer.py",
        
        # 并发处理模块
        "VisionAI-ClipsMaster-Core/src/concurrent/worker_pool.py": "src/visionai_clipsmaster/concurrent/worker_pool.py",
        "VisionAI-ClipsMaster-Core/src/concurrent/resource_manager.py": "src/visionai_clipsmaster/concurrent/resource_manager.py",
        "VisionAI-ClipsMaster-Core/src/concurrent/batch_processor.py": "src/visionai_clipsmaster/concurrent/batch_processor.py",
        "VisionAI-ClipsMaster-Core/src/concurrent/progress_tracker.py": "src/visionai_clipsmaster/concurrent/progress_tracker.py",
        
        # 工具模块
        "VisionAI-ClipsMaster-Core/src/utils/file_utils.py": "src/visionai_clipsmaster/utils/file_utils.py",
        "VisionAI-ClipsMaster-Core/src/utils/log_handler.py": "src/visionai_clipsmaster/utils/logging_utils.py",
        
        # UI文件
        "simple_ui_fixed.py": "src/visionai_clipsmaster/ui/main_window.py",
        
        # 脚本文件
        "scripts/setup_models.py": "scripts/setup_models.py",
        "scripts/check_environment.py": "scripts/check_environment.py",
        "scripts/install.bat": "scripts/install.bat", 
        "scripts/install.sh": "scripts/install.sh",
        "scripts/quick_start.py": "scripts/quick_start.py",
        
        # 依赖文件
        "requirements/requirements.txt": "requirements/requirements.txt",
        "requirements/requirements-lite.txt": "requirements/requirements-lite.txt",
        "requirements/requirements-dev.txt": "requirements/requirements-dev.txt",
        "requirements/requirements-full.txt": "requirements/requirements-full.txt",
        
        # Docker文件
        "docker/Dockerfile": "docker/Dockerfile",
        "docker/docker-compose.yml": "docker/docker-compose.yml",
        "docker/entrypoint.sh": "docker/entrypoint.sh",
        
        # GitHub配置
        ".github/workflows/ci.yml": ".github/workflows/ci.yml",
        ".github/workflows/release.yml": ".github/workflows/release.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md": ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md": ".github/ISSUE_TEMPLATE/feature_request.md",
    }
    
    # 执行文件移动
    for source, destination in file_moves.items():
        if Path(source).exists():
            # 确保目标目录存在
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件
            shutil.copy2(source, destination)
            print(f"✓ 移动文件: {source} → {destination}")
        else:
            print(f"⚠ 文件不存在: {source}")

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
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# -*- coding: utf-8 -*-\n')
            f.write(f'"""{Path(init_file).parent.name} package"""\n')
        print(f"✓ 创建文件: {init_file}")

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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 创建占位文件: {file_path}")

def main():
    """主函数"""
    print("🚀 开始组织VisionAI-ClipsMaster项目结构...")
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
    
    print("\n" + "=" * 60)
    print("✅ 项目结构组织完成！")
    print("\n下一步:")
    print("1. 检查文件是否正确移动")
    print("2. 运行 Git 初始化命令")
    print("3. 提交代码到GitHub")

if __name__ == "__main__":
    main()
