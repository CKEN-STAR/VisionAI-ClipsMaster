#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试依赖管理
验证所有必需依赖可正确导入，可选依赖有优雅的fallback
"""

import sys
import importlib
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_core_dependencies():
    """测试核心依赖"""
    print("=" * 60)
    print("测试1: 核心依赖检查")
    print("=" * 60)

    core_deps = [
        ("PyQt6", "UI框架"),
        ("numpy", "数值计算"),
        ("cv2", "视频处理"),
        ("jieba", "中文分词"),
        ("psutil", "系统监控"),
        ("yaml", "配置文件"),
        ("requests", "网络请求"),
    ]

    # 可能有环境问题的依赖（单独测试）
    env_sensitive_deps = [
        ("torch", "深度学习框架"),
        ("transformers", "模型库"),
    ]

    failed = []
    warnings = []

    # 测试核心依赖
    for module_name, description in core_deps:
        try:
            importlib.import_module(module_name)
            print(f"✓ {module_name:20s} - {description}")
        except ImportError as e:
            print(f"✗ {module_name:20s} - {description} (失败)")
            failed.append(module_name)

    # 测试环境敏感依赖（允许失败）
    for module_name, description in env_sensitive_deps:
        try:
            importlib.import_module(module_name)
            print(f"✓ {module_name:20s} - {description}")
        except Exception as e:
            print(f"⚠ {module_name:20s} - {description} (环境问题，跳过)")
            warnings.append(f"{module_name}: {str(e)[:50]}")

    if failed:
        print(f"\n✗ 核心依赖缺失: {', '.join(failed)}")
        assert False, f"核心依赖缺失: {failed}"
    else:
        print("\n✓ 核心依赖正常")

    if warnings:
        print(f"⚠ 环境警告: {len(warnings)}个")

    print()


def test_optional_dependencies():
    """测试可选依赖的fallback"""
    print("=" * 60)
    print("测试2: 可选依赖fallback检查")
    print("=" * 60)

    optional_deps = [
        ("pynvml", "GPU监控"),
        ("modelscope", "模型下载"),
        ("bitsandbytes", "量化工具"),
    ]

    for module_name, description in optional_deps:
        try:
            importlib.import_module(module_name)
            print(f"✓ {module_name:20s} - {description} (已安装)")
        except Exception as e:
            # 允许任何异常（包括DLL加载失败）
            error_msg = str(e)[:50] if str(e) else "未知错误"
            print(f"⚠ {module_name:20s} - {description} (不可用: {error_msg}...)")

    print("\n✓ 可选依赖检查完成")
    print()


def test_nvidia_ml_py():
    """测试nvidia-ml-py替代pynvml"""
    print("=" * 60)
    print("测试3: nvidia-ml-py检查")
    print("=" * 60)
    
    try:
        import pynvml
        print(f"✓ pynvml已导入")
        
        # 检查是否有弃用警告
        if hasattr(pynvml, '__version__'):
            print(f"✓ 使用nvidia-ml-py版本: {pynvml.__version__}")
        else:
            print(f"⚠ 使用已弃用的pynvml，建议升级到nvidia-ml-py")
        
        # 测试基本功能
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            print(f"✓ 检测到 {device_count} 个GPU设备")
            pynvml.nvmlShutdown()
        except Exception as e:
            print(f"⚠ GPU检测失败（可能没有NVIDIA GPU）: {e}")
    
    except ImportError:
        print(f"⚠ pynvml/nvidia-ml-py未安装，GPU监控功能不可用")
    
    print()


def test_gptq_fallback():
    """测试GPTQ量化的fallback"""
    print("=" * 60)
    print("测试4: GPTQ量化fallback检查")
    print("=" * 60)
    
    from src.core.gptq_quantizer import HAS_AUTO_GPTQ
    
    if HAS_AUTO_GPTQ:
        print("✓ auto-gptq已安装，GPTQ量化功能可用")
    else:
        print("⚠ auto-gptq未安装，GPTQ量化功能不可用（使用fallback）")
    
    # 验证代码有优雅的fallback
    try:
        from src.core.gptq_quantizer import GPTQQuantizer
        print("✓ GPTQQuantizer类可正常导入")
    except ImportError as e:
        print(f"✗ GPTQQuantizer导入失败: {e}")
        assert False, "GPTQQuantizer应该有fallback机制"
    
    print()


def test_enhanced_device_manager():
    """测试增强设备管理器的依赖处理"""
    print("=" * 60)
    print("测试5: 增强设备管理器依赖检查")
    print("=" * 60)
    
    try:
        from src.utils.enhanced_device_manager import NVML_AVAILABLE, TORCH_AVAILABLE
        
        print(f"✓ TORCH可用: {TORCH_AVAILABLE}")
        print(f"✓ NVML可用: {NVML_AVAILABLE}")
        
        # 即使依赖不可用，模块也应该能导入
        from src.utils.enhanced_device_manager import EnhancedDeviceManager
        print("✓ EnhancedDeviceManager可正常导入")
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        assert False, "EnhancedDeviceManager应该有fallback机制"
    
    print()


def test_requirements_file():
    """测试requirements.txt格式"""
    print("=" * 60)
    print("测试6: requirements.txt格式检查")
    print("=" * 60)
    
    req_file = project_root / "requirements.txt"
    
    if not req_file.exists():
        print("✗ requirements.txt不存在")
        assert False, "requirements.txt文件缺失"
    
    with open(req_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用nvidia-ml-py而非pynvml
    if "nvidia-ml-py" in content:
        print("✓ 使用推荐的nvidia-ml-py")
    else:
        print("⚠ 未找到nvidia-ml-py")
    
    if "pynvml" in content and "nvidia-ml-py" not in content:
        print("✗ 仍在使用已弃用的pynvml")
        assert False, "应该使用nvidia-ml-py替代pynvml"
    
    # 检查auto-gptq是否标记为可选
    if "# auto-gptq" in content or "auto-gptq" not in content:
        print("✓ auto-gptq已标记为可选或移除")
    else:
        print("⚠ auto-gptq应该标记为可选依赖")
    
    print("✓ requirements.txt格式检查通过")
    print()


def test_optional_requirements_file():
    """测试requirements-optional.txt存在性"""
    print("=" * 60)
    print("测试7: requirements-optional.txt检查")
    print("=" * 60)
    
    opt_req_file = project_root / "requirements-optional.txt"
    
    if opt_req_file.exists():
        print(f"✓ requirements-optional.txt存在")
        with open(opt_req_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"✓ 包含 {len(lines)} 行配置")
    else:
        print("⚠ requirements-optional.txt不存在（建议创建）")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("依赖管理测试套件")
    print("=" * 60 + "\n")
    
    try:
        test_core_dependencies()
        test_optional_dependencies()
        test_nvidia_ml_py()
        test_gptq_fallback()
        test_enhanced_device_manager()
        test_requirements_file()
        test_optional_requirements_file()
        
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

