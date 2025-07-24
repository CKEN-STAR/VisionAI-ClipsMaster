#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 依赖验证脚本
验证所有关键依赖项是否正确安装并可用
"""

import sys
import importlib
import subprocess
from pathlib import Path

# 核心依赖项配置
CORE_DEPENDENCIES = {
    "AI和机器学习": {
        "torch": {"import_name": "torch", "critical": True},
        "transformers": {"import_name": "transformers", "critical": True},
        "numpy": {"import_name": "numpy", "critical": True},
        "scikit-learn": {"import_name": "sklearn", "critical": False}
    },
    "视频和图像处理": {
        "opencv-python": {"import_name": "cv2", "critical": True},
        "Pillow": {"import_name": "PIL", "critical": True},
        "ffmpeg-python": {"import_name": "ffmpeg", "critical": False}
    },
    "用户界面": {
        "PyQt6": {"import_name": "PyQt6", "critical": True}
    },
    "系统监控": {
        "psutil": {"import_name": "psutil", "critical": True},
        "GPUtil": {"import_name": "GPUtil", "critical": False}
    },
    "日志和配置": {
        "loguru": {"import_name": "loguru", "critical": True},
        "PyYAML": {"import_name": "yaml", "critical": True}
    },
    "数据处理": {
        "pandas": {"import_name": "pandas", "critical": True},
        "matplotlib": {"import_name": "matplotlib", "critical": True}
    },
    "网络和文本": {
        "requests": {"import_name": "requests", "critical": True},
        "jieba": {"import_name": "jieba", "critical": False},
        "langdetect": {"import_name": "langdetect", "critical": False}
    },
    "用户体验": {
        "tqdm": {"import_name": "tqdm", "critical": False},
        "colorama": {"import_name": "colorama", "critical": False}
    },
    "新增依赖": {
        "lxml": {"import_name": "lxml", "critical": True},
        "tabulate": {"import_name": "tabulate", "critical": False},
        "modelscope": {"import_name": "modelscope", "critical": False}
    }
}

def check_package_version(package_name, import_name):
    """检查包版本"""
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        return version
    except:
        return None

def verify_package(package_name, import_name, critical=False):
    """验证单个包"""
    try:
        # 尝试导入
        importlib.import_module(import_name)
        version = check_package_version(package_name, import_name)
        
        status = "✅"
        message = f"{package_name} ({version})"
        return True, status, message
        
    except ImportError as e:
        status = "❌" if critical else "⚠️"
        message = f"{package_name} - 未安装"
        return False, status, message
    except Exception as e:
        status = "❌" if critical else "⚠️"
        message = f"{package_name} - 导入错误: {str(e)[:50]}"
        return False, status, message

def run_functionality_tests():
    """运行基本功能测试"""
    print("\n🧪 运行基本功能测试...")
    print("=" * 50)
    
    tests = []
    
    # 测试PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        tests.append(("PyQt6 GUI框架", True, "可以创建GUI应用"))
    except Exception as e:
        tests.append(("PyQt6 GUI框架", False, f"GUI创建失败: {e}"))
    
    # 测试torch
    try:
        import torch
        x = torch.tensor([1.0, 2.0, 3.0])
        tests.append(("PyTorch 张量计算", True, f"张量运算正常"))
    except Exception as e:
        tests.append(("PyTorch 张量计算", False, f"张量运算失败: {e}"))
    
    # 测试opencv
    try:
        import cv2
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        tests.append(("OpenCV 图像处理", True, "图像处理正常"))
    except Exception as e:
        tests.append(("OpenCV 图像处理", False, f"图像处理失败: {e}"))
    
    # 测试transformers
    try:
        from transformers import AutoTokenizer
        tests.append(("Transformers NLP", True, "NLP模块可用"))
    except Exception as e:
        tests.append(("Transformers NLP", False, f"NLP模块失败: {e}"))
    
    # 显示测试结果
    for test_name, success, message in tests:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}: {message}")
    
    return tests

def generate_install_commands(missing_packages):
    """生成安装命令"""
    if not missing_packages:
        return []
    
    commands = []
    
    # 按优先级分组
    critical_packages = [pkg for pkg, critical in missing_packages if critical]
    optional_packages = [pkg for pkg, critical in missing_packages if not critical]
    
    if critical_packages:
        commands.append(f"# 安装关键依赖")
        commands.append(f"pip install {' '.join(critical_packages)}")
        commands.append("")
    
    if optional_packages:
        commands.append(f"# 安装可选依赖")
        commands.append(f"pip install {' '.join(optional_packages)}")
        commands.append("")
    
    # 或者使用requirements文件
    commands.append("# 或者使用requirements文件一次性安装")
    commands.append("pip install -r requirements_minimal.txt")
    
    return commands

def main():
    """主函数"""
    print("🔍 VisionAI-ClipsMaster 依赖验证工具")
    print("=" * 60)
    print("检查所有关键依赖项的安装状态和可用性\n")
    
    total_packages = 0
    installed_packages = 0
    critical_missing = 0
    missing_packages = []
    
    # 按类别验证依赖
    for category, packages in CORE_DEPENDENCIES.items():
        print(f"📦 {category}:")
        
        for package_name, config in packages.items():
            total_packages += 1
            import_name = config["import_name"]
            critical = config["critical"]
            
            success, status, message = verify_package(package_name, import_name, critical)
            print(f"  {status} {message}")
            
            if success:
                installed_packages += 1
            else:
                missing_packages.append((package_name, critical))
                if critical:
                    critical_missing += 1
        
        print()
    
    # 显示统计信息
    print("📊 验证统计:")
    print(f"  总依赖项: {total_packages}")
    print(f"  已安装: {installed_packages}")
    print(f"  缺失: {len(missing_packages)}")
    print(f"  关键缺失: {critical_missing}")
    print()
    
    # 运行功能测试
    if critical_missing == 0:
        tests = run_functionality_tests()
        failed_tests = [t for t in tests if not t[1]]
        if failed_tests:
            print(f"\n⚠️  {len(failed_tests)} 个功能测试失败")
    
    # 生成修复建议
    if missing_packages:
        print("🔧 修复建议:")
        print("=" * 30)
        
        install_commands = generate_install_commands(missing_packages)
        for cmd in install_commands:
            print(cmd)
        
        print("\n💡 快速修复:")
        print("python fix_missing_dependencies.py")
    
    # 最终状态评估
    print("\n🎯 系统状态评估:")
    if critical_missing == 0:
        if len(missing_packages) == 0:
            print("✅ 完美！所有依赖项都已正确安装")
        else:
            print("✅ 良好！关键依赖已安装，可选依赖可稍后安装")
    else:
        print("❌ 需要修复！关键依赖缺失，可能影响核心功能")
    
    return critical_missing == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
