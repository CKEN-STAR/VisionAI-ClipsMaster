#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模拟训练代码备份
备份当前的模拟训练实现，以便在需要时恢复
"""

import os
import shutil
import time
from datetime import datetime

def backup_simulation_code():
    """备份当前的模拟训练代码"""
    print("💾 备份当前模拟训练代码...")
    
    backup_dir = f"backup_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 需要备份的文件
    files_to_backup = [
        "src/training/zh_trainer.py",
        "src/training/en_trainer.py", 
        "src/training/trainer.py",
        "src/training/model_fine_tuner.py"
    ]
    
    backed_up_files = []
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            backed_up_files.append(file_path)
            print(f"  ✅ 已备份: {file_path}")
        else:
            print(f"  ⚠️ 文件不存在: {file_path}")
    
    print(f"📁 备份完成，保存在: {backup_dir}")
    print(f"📊 共备份 {len(backed_up_files)} 个文件")
    
    return backup_dir, backed_up_files

if __name__ == "__main__":
    backup_simulation_code()
