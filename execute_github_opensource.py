#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster GitHub开源执行脚本
自动化执行开源准备工作
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubOpenSourceExecutor:
    def __init__(self, source_dir=".", target_base="VisionAI-ClipsMaster-opensource"):
        self.source_dir = Path(source_dir).resolve()
        self.target_base = Path(target_base).resolve()
        self.backup_dir = Path(f"{source_dir}-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
    def create_backup(self):
        """创建项目备份"""
        logger.info("📦 创建项目备份...")
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            # 复制项目，排除.git目录
            shutil.copytree(
                self.source_dir, 
                self.backup_dir,
                ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '*.log')
            )
            logger.info(f"✅ 备份完成: {self.backup_dir}")
            return True
        except Exception as e:
            logger.error(f"❌ 备份失败: {e}")
            return False
    
    def create_clean_structure(self):
        """创建清理后的项目结构"""
        logger.info("🧹 创建清理后的项目结构...")
        
        # 定义仓库结构
        repos = {
            'main': {
                'name': 'VisionAI-ClipsMaster',
                'dirs': ['src', 'ui', 'configs', 'docs', 'scripts'],
                'files': ['requirements.txt', 'README.md', 'LICENSE', 'simple_ui_fixed.py'],
                'size_limit_mb': 100
            },
            'tools': {
                'name': 'VisionAI-ClipsMaster-Tools', 
                'dirs': ['tools', 'bin'],
                'files': [],
                'size_limit_mb': 1000
            },
            'models': {
                'name': 'VisionAI-ClipsMaster-Models',
                'dirs': ['models', 'llama.cpp'],
                'files': [],
                'size_limit_mb': 500
            },
            'testdata': {
                'name': 'VisionAI-ClipsMaster-TestData',
                'dirs': ['data', 'examples/compressed', 'tests/test_data'],
                'files': [],
                'size_limit_mb': 1000
            }
        }
        
        # 创建各个仓库目录
        for repo_key, repo_info in repos.items():
            repo_path = self.target_base / repo_info['name']
            
            try:
                # 创建目录
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                repo_path.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"📁 创建仓库: {repo_info['name']}")
                
                # 复制目录
                for dir_name in repo_info['dirs']:
                    source_path = self.source_dir / dir_name
                    target_path = repo_path / dir_name
                    
                    if source_path.exists():
                        if source_path.is_dir():
                            shutil.copytree(source_path, target_path, 
                                          ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log', '.git'))
                        else:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_path, target_path)
                        logger.info(f"  ✅ 复制目录: {dir_name}")
                    else:
                        logger.warning(f"  ⚠️ 目录不存在: {dir_name}")
                
                # 复制文件
                for file_name in repo_info['files']:
                    source_file = self.source_dir / file_name
                    target_file = repo_path / file_name
                    
                    if source_file.exists():
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
                        logger.info(f"  ✅ 复制文件: {file_name}")
                    else:
                        logger.warning(f"  ⚠️ 文件不存在: {file_name}")
                
                # 创建基础文件
                self._create_repo_files(repo_path, repo_key, repo_info)
                
            except Exception as e:
                logger.error(f"❌ 创建仓库 {repo_info['name']} 失败: {e}")
                return False
        
        return True
    
    def _create_repo_files(self, repo_path, repo_key, repo_info):
        """为每个仓库创建基础文件"""
        
        # 创建.gitignore
        gitignore_content = self._get_gitignore_content(repo_key)
        with open(repo_path / '.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        
        # 创建README.md
        readme_content = self._get_readme_content(repo_key, repo_info)
        with open(repo_path / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 为需要Git LFS的仓库创建.gitattributes
        if repo_key in ['tools', 'models', 'testdata']:
            gitattributes_content = self._get_gitattributes_content(repo_key)
            with open(repo_path / '.gitattributes', 'w', encoding='utf-8') as f:
                f.write(gitattributes_content)
    
    def _get_gitignore_content(self, repo_key):
        """获取.gitignore内容"""
        base_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 环境
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 操作系统
.DS_Store
Thumbs.db

# 项目特定
logs/
*.log
test_output/
benchmark_results/
cache/
temp/
tmp/
outputs/
reports/
*.backup
*.bak
"""
        
        if repo_key == 'main':
            base_gitignore += """
# 大文件 (在独立仓库中)
models/
tools/
data/
bin/
*.bin
*.safetensors
*.gguf
*.pt
*.pth
*.h5
*.onnx
*.exe
*.zip
*.7z
"""
        
        return base_gitignore
    
    def _get_gitattributes_content(self, repo_key):
        """获取.gitattributes内容"""
        if repo_key == 'tools':
            return """*.exe filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.dll filter=lfs diff=lfs merge=lfs -text
"""
        elif repo_key == 'models':
            return """*.bin filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.gguf filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
"""
        elif repo_key == 'testdata':
            return """*.mp4 filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
"""
        return ""
    
    def _get_readme_content(self, repo_key, repo_info):
        """获取README.md内容"""
        if repo_key == 'main':
            return """# VisionAI-ClipsMaster

基于本地大语言模型的短剧视频重混工具

## 🚀 快速开始

### 安装
```bash
# 1. 克隆主仓库
git clone https://github.com/CKEN/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载工具 (可选)
git clone https://github.com/CKEN/VisionAI-ClipsMaster-Tools.git tools

# 4. 下载模型 (可选)
git clone https://github.com/CKEN/VisionAI-ClipsMaster-Models.git models

# 5. 运行
python simple_ui_fixed.py
```

## 📦 仓库架构

- **主仓库**: 核心代码和文档
- **工具仓库**: FFmpeg等二进制工具
- **模型仓库**: AI模型文件
- **测试数据仓库**: 测试数据和示例

## 🔧 特性

- 双模型架构 (Mistral-7B + Qwen2.5-7B)
- 4GB内存设备支持
- 自动字幕重构
- 剪映项目文件导出

## 📄 许可证

MIT License
"""
        else:
            return f"""# {repo_info['name']}

VisionAI-ClipsMaster项目的{repo_info['name']}组件

## 说明

这是VisionAI-ClipsMaster项目的一部分，包含{repo_key}相关文件。

## 使用方法

请参考主仓库的说明文档：
https://github.com/CKEN/VisionAI-ClipsMaster

## 许可证

MIT License
"""
    
    def initialize_git_repos(self):
        """初始化Git仓库"""
        logger.info("🔧 初始化Git仓库...")
        
        repos = [
            'VisionAI-ClipsMaster',
            'VisionAI-ClipsMaster-Tools', 
            'VisionAI-ClipsMaster-Models',
            'VisionAI-ClipsMaster-TestData'
        ]
        
        for repo_name in repos:
            repo_path = self.target_base / repo_name
            if not repo_path.exists():
                logger.warning(f"⚠️ 仓库目录不存在: {repo_name}")
                continue
            
            try:
                os.chdir(repo_path)
                
                # 初始化Git
                subprocess.run(['git', 'init'], check=True, capture_output=True)
                subprocess.run(['git', 'branch', '-M', 'main'], check=True, capture_output=True)
                
                # 配置Git LFS (如果需要)
                if repo_name != 'VisionAI-ClipsMaster':
                    subprocess.run(['git', 'lfs', 'install'], check=True, capture_output=True)
                    subprocess.run(['git', 'add', '.gitattributes'], check=True, capture_output=True)
                    subprocess.run(['git', 'commit', '-m', 'Setup: Add Git LFS configuration'], 
                                 check=True, capture_output=True)
                
                # 添加.gitignore
                subprocess.run(['git', 'add', '.gitignore'], check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', 'Setup: Add .gitignore'], 
                             check=True, capture_output=True)
                
                # 添加所有文件
                subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', f'Initial commit: {repo_name}'], 
                             check=True, capture_output=True)
                
                logger.info(f"✅ Git仓库初始化完成: {repo_name}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Git操作失败 {repo_name}: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ 初始化仓库失败 {repo_name}: {e}")
                return False
        
        return True
    
    def generate_setup_script(self):
        """生成安装脚本"""
        logger.info("📝 生成安装脚本...")
        
        setup_script = """#!/bin/bash
# VisionAI-ClipsMaster 安装脚本

echo "🚀 VisionAI-ClipsMaster 安装脚本"

# 检查Git
if ! command -v git &> /dev/null; then
    echo "❌ 请先安装 Git"
    exit 1
fi

# 检查Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo "⚠️ 建议安装 Git LFS 以支持大文件下载"
fi

# 克隆主仓库
echo "📦 克隆主仓库..."
git clone https://github.com/CKEN/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 询问是否下载工具
read -p "是否下载工具仓库 (FFmpeg等)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 下载工具仓库..."
    git clone https://github.com/CKEN/VisionAI-ClipsMaster-Tools.git tools
fi

# 询问是否下载模型
read -p "是否下载模型仓库? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 下载模型仓库..."
    git clone https://github.com/CKEN/VisionAI-ClipsMaster-Models.git models
fi

# 询问是否下载测试数据
read -p "是否下载测试数据仓库? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 下载测试数据仓库..."
    git clone https://github.com/CKEN/VisionAI-ClipsMaster-TestData.git testdata
fi

echo "✅ 安装完成!"
echo "🚀 运行: python simple_ui_fixed.py"
"""
        
        setup_file = self.target_base / 'setup.sh'
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_script)
        
        # 设置执行权限
        os.chmod(setup_file, 0o755)
        logger.info(f"✅ 安装脚本已生成: {setup_file}")
    
    def execute_full_process(self):
        """执行完整的开源准备流程"""
        logger.info("🚀 开始VisionAI-ClipsMaster GitHub开源准备")
        logger.info("=" * 60)
        
        steps = [
            ("创建备份", self.create_backup),
            ("创建清理结构", self.create_clean_structure),
            ("初始化Git仓库", self.initialize_git_repos),
            ("生成安装脚本", self.generate_setup_script)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n🔄 执行步骤: {step_name}")
            if not step_func():
                logger.error(f"❌ 步骤失败: {step_name}")
                return False
            logger.info(f"✅ 步骤完成: {step_name}")
        
        logger.info("\n🎉 开源准备完成!")
        logger.info(f"📁 输出目录: {self.target_base}")
        logger.info("📋 下一步:")
        logger.info("   1. 在GitHub创建对应的仓库")
        logger.info("   2. 添加远程仓库地址")
        logger.info("   3. 推送到GitHub")
        
        return True

def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster GitHub开源执行器")
    print("=" * 50)
    
    # 确认执行
    response = input("是否开始执行开源准备? (y/n): ")
    if response.lower() != 'y':
        print("❌ 操作已取消")
        return False
    
    # 执行开源准备
    executor = GitHubOpenSourceExecutor()
    return executor.execute_full_process()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
