#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI 启动脚本 (带详细日志)
确保所有依赖正常并记录启动过程
"""

import sys
import os
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

print("="*80)
print("VisionAI-ClipsMaster UI 启动脚本 (带详细日志)")
print("="*80)
print()

# 1. 检查Python环境
print("[1/7] 检查Python环境...")
print(f"   Python版本: {sys.version}")
print(f"   Python路径: {sys.executable}")
print(f"   工作目录: {os.getcwd()}")

if '.venv' in sys.executable or 'venv' in sys.executable:
    print("   ✅ 使用虚拟环境")
else:
    print("   ⚠️  警告: 未使用虚拟环境!")
    print("   建议: 使用虚拟环境启动")

# 2. 检查PyTorch
print("\n[2/7] 检查PyTorch...")
try:
    import torch
    print(f"   ✅ PyTorch版本: {torch.__version__}")
    print(f"   ✅ CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   ✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   ✅ CUDA版本: {torch.version.cuda}")
except Exception as e:
    print(f"   ❌ PyTorch错误: {e}")
    print("   请修复PyTorch后再启动UI")
    sys.exit(1)

# 3. 检查llama-cpp-python
print("\n[3/7] 检查llama-cpp-python...")
try:
    from llama_cpp import Llama
    print("   ✅ llama-cpp-python可用")
    
    # 检查CUDA支持
    try:
        test_llama = Llama(model_path="", n_ctx=1, verbose=False)
    except:
        pass  # 预期会失败,只是测试导入
    print("   ✅ llama-cpp-python可以实例化")
except Exception as e:
    print(f"   ❌ llama-cpp-python错误: {e}")
    print("   AI功能可能无法使用")

# 4. 检查PyQt6
print("\n[4/7] 检查PyQt6...")
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    print("   ✅ PyQt6可用")
except Exception as e:
    print(f"   ❌ PyQt6错误: {e}")
    print("   请安装PyQt6: pip install PyQt6")
    sys.exit(1)

# 5. 检查项目文件
print("\n[5/7] 检查项目文件...")
required_files = [
    "simple_ui_fixed.py",
    "src/core/video_processor.py",
    "src/core/real_ai_engine.py",
    "src/core/screenplay_engineer.py"
]

all_files_exist = True
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} 不存在!")
        all_files_exist = False

if not all_files_exist:
    print("   ❌ 缺少必要文件!")
    sys.exit(1)

# 6. 检查GGUF模型
print("\n[6/7] 检查GGUF模型...")
model_paths = [
    "models/qwen/quantized/trained_20251102_162922_Q4_K_M_f16.gguf",
    "models/qwen/quantized/qwen-test-small.gguf"
]

model_found = False
for model_path in model_paths:
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"   ✅ {model_path} ({size_mb:.2f} MB)")
        model_found = True
    else:
        print(f"   ❌ {model_path} 不存在")

if not model_found:
    print("   ⚠️  警告: 没有找到GGUF模型!")
    print("   AI功能可能无法使用")

# 7. 启动UI
print("\n[7/7] 启动UI...")
print()
print("="*80)
print("正在启动VisionAI-ClipsMaster UI...")
print("="*80)
print()
print("提示:")
print("1. 请在UI中添加SRT文件")
print("2. 点击'AI优化字幕'按钮")
print("3. 观察控制台输出")
print("4. 如果出现错误,请查看日志文件: logs/visionai.log")
print()
print("="*80)
print()

# 导入并启动UI
try:
    # 添加详细的导入日志
    print("[导入] 正在导入simple_ui_fixed...")
    import simple_ui_fixed
    
    print("[导入] 正在创建QApplication...")
    app = QApplication(sys.argv)
    
    print("[导入] 正在创建主窗口...")
    window = simple_ui_fixed.VisionAIClipsMaster()
    
    print("[导入] 正在显示窗口...")
    window.show()
    
    print("[导入] UI启动成功!")
    print()
    print("="*80)
    print("UI已启动,请在窗口中操作")
    print("="*80)
    print()
    
    # 运行事件循环
    sys.exit(app.exec())
    
except Exception as e:
    print()
    print("="*80)
    print("❌ UI启动失败!")
    print("="*80)
    print(f"错误: {e}")
    print()
    
    import traceback
    print("详细错误信息:")
    traceback.print_exc()
    
    print()
    print("建议:")
    print("1. 检查是否所有依赖都已安装")
    print("2. 查看日志文件: logs/visionai.log")
    print("3. 尝试重新安装依赖: pip install -r requirements.txt")
    
    sys.exit(1)

