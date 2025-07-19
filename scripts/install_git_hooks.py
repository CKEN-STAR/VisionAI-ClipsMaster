#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git钩子安装脚本

该脚本用于设置Git钩子，确保在提交前验证黄金样本的完整性，
防止意外修改黄金样本。
"""

import os
import sys
import stat
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GIT_HOOKS_DIR = PROJECT_ROOT / '.git' / 'hooks'

# 确保Git钩子目录存在
if not GIT_HOOKS_DIR.exists():
    print(f"错误: Git钩子目录不存在 {GIT_HOOKS_DIR}")
    print("请确保这是一个有效的Git仓库。")
    sys.exit(1)

# pre-commit钩子内容
PRE_COMMIT_HOOK = """#!/usr/bin/env python
import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
REPO_ROOT = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                        text=True).strip())

# 检查是否修改了黄金样本目录中的文件
def check_golden_samples_changes():
    # 获取暂存区中的更改
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                            capture_output=True, text=True)
    changed_files = result.stdout.splitlines()
    
    # 检查是否有黄金样本目录中的文件
    golden_changes = [f for f in changed_files if f.startswith('tests/golden_samples/')]
    
    if golden_changes:
        print("警告: 检测到黄金样本目录中的文件有更改:")
        for f in golden_changes:
            print(f"  - {f}")
        
        # 执行黄金样本完整性检查
        print("\\n正在验证黄金样本完整性...")
        sys.path.insert(0, str(REPO_ROOT))
        
        try:
            from src.security.access_control import verify_golden_samples_integrity
            success, errors = verify_golden_samples_integrity()
            
            if not success:
                print("\\n错误: 黄金样本完整性验证失败。")
                for error in errors:
                    print(f"  - {error}")
                
                print("\\n所有黄金样本的修改都需要通过正式流程处理。")
                print("请使用 'python -m tests.golden_samples.manage_golden' 工具进行管理。")
                return False
        except ImportError:
            print("警告: 无法导入验证模块，跳过完整性检查。")
    
    return True

# 执行钩子
if __name__ == "__main__":
    try:
        if not check_golden_samples_changes():
            print("\\n提交已中止。请解决上述问题后重试。")
            sys.exit(1)
            
        sys.exit(0)
    except Exception as e:
        print(f"执行Git钩子时出错: {e}")
        # 出错时允许提交继续，避免阻塞开发
        sys.exit(0)
"""

# pre-push钩子内容
PRE_PUSH_HOOK = """#!/usr/bin/env python
import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
REPO_ROOT = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], 
                                        text=True).strip())

# 执行黄金样本完整性检查
def verify_golden_samples():
    print("正在验证黄金样本完整性...")
    sys.path.insert(0, str(REPO_ROOT))
    
    try:
        from src.security.access_control import verify_golden_samples_integrity
        success, errors = verify_golden_samples_integrity()
        
        if not success:
            print("\\n错误: 黄金样本完整性验证失败。")
            for error in errors:
                print(f"  - {error}")
            
            user_input = input("\\n黄金样本完整性验证失败。是否仍然继续推送? (y/N): ")
            return user_input.lower() == 'y'
    except ImportError:
        print("警告: 无法导入验证模块，跳过完整性检查。")
    
    return True

# 执行钩子
if __name__ == "__main__":
    try:
        if not verify_golden_samples():
            print("\\n推送已中止。请解决上述问题后重试。")
            sys.exit(1)
            
        sys.exit(0)
    except Exception as e:
        print(f"执行Git钩子时出错: {e}")
        # 出错时允许推送继续，避免阻塞开发
        sys.exit(0)
"""

def install_hook(hook_name, content):
    """安装Git钩子"""
    hook_path = GIT_HOOKS_DIR / hook_name
    
    # 写入钩子文件
    with open(hook_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 设置为可执行文件
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    
    print(f"已安装 {hook_name} 钩子")

def main():
    """主函数"""
    print("安装 Git 钩子...")
    
    # 安装 pre-commit 钩子
    install_hook('pre-commit', PRE_COMMIT_HOOK)
    
    # 安装 pre-push 钩子
    install_hook('pre-push', PRE_PUSH_HOOK)
    
    print("Git 钩子安装完成！")
    print("这些钩子将在提交和推送前验证黄金样本的完整性。")

if __name__ == "__main__":
    main() 