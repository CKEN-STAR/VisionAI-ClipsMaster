#!/usr/bin/env python3
"""
依赖测试脚本 - 验证所有关键依赖是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def test_numpy():
    """测试numpy"""
    try:
        import numpy as np
        print(f"✅ numpy {np.__version__} - 正常")
        
        # 测试基本功能
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.sum() == 15
        print(f"   └─ 基本数组操作正常")
        return True
    except Exception as e:
        print(f"❌ numpy 测试失败: {e}")
        return False

def test_torch():
    """测试PyTorch和CUDA"""
    try:
        import torch
        print(f"✅ torch {torch.__version__} - 正常")
        
        # 测试CUDA
        if torch.cuda.is_available():
            print(f"   ├─ CUDA可用: {torch.cuda.get_device_name(0)}")
            print(f"   ├─ CUDA版本: {torch.version.cuda}")
            
            # 测试GPU张量操作
            x = torch.randn(3, 3).cuda()
            y = torch.randn(3, 3).cuda()
            z = x + y
            print(f"   └─ GPU张量操作正常")
        else:
            print(f"   └─ CUDA不可用（仅CPU模式）")
        
        return True
    except Exception as e:
        print(f"❌ torch 测试失败: {e}")
        return False

def test_transformers():
    """测试transformers库"""
    try:
        import transformers
        print(f"✅ transformers {transformers.__version__} - 正常")
        return True
    except Exception as e:
        print(f"❌ transformers 测试失败: {e}")
        return False

def test_gguf():
    """测试gguf库"""
    try:
        import gguf
        # gguf可能没有__version__属性，尝试获取
        try:
            version = gguf.__version__
        except AttributeError:
            version = "已安装（版本未知）"
        print(f"✅ gguf {version} - 正常")

        # 测试基本功能
        from gguf import GGUFWriter
        print(f"   └─ GGUFWriter 可用")
        return True
    except Exception as e:
        print(f"❌ gguf 测试失败: {e}")
        return False

def test_protobuf():
    """测试protobuf"""
    try:
        import google.protobuf
        print(f"✅ protobuf {google.protobuf.__version__} - 正常")
        return True
    except Exception as e:
        print(f"❌ protobuf 测试失败: {e}")
        return False

def test_sentencepiece():
    """测试sentencepiece"""
    try:
        import sentencepiece
        print(f"✅ sentencepiece {sentencepiece.__version__} - 正常")
        return True
    except Exception as e:
        print(f"❌ sentencepiece 测试失败: {e}")
        return False

def test_llama_cpp_converter():
    """测试llama.cpp转换脚本"""
    try:
        llama_cpp_path = project_root / "llama.cpp" / "convert_hf_to_gguf.py"
        if not llama_cpp_path.exists():
            print(f"❌ llama.cpp转换脚本不存在: {llama_cpp_path}")
            return False
        
        # 尝试导入转换脚本需要的模块
        import numpy
        import sentencepiece
        import transformers
        import gguf
        
        print(f"✅ llama.cpp转换脚本依赖完整")
        print(f"   └─ 脚本路径: {llama_cpp_path}")
        return True
    except Exception as e:
        print(f"❌ llama.cpp转换脚本测试失败: {e}")
        return False

def test_model_converter():
    """测试ModelConverter类"""
    try:
        from models.converters.model_converter import ModelConverter
        print(f"✅ ModelConverter 导入成功")
        
        # 创建实例
        converter = ModelConverter()
        print(f"   └─ ModelConverter 实例化成功")
        return True
    except Exception as e:
        print(f"❌ ModelConverter 测试失败: {e}")
        return False

def test_pyqt6():
    """测试PyQt6"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QT_VERSION_STR
        print(f"✅ PyQt6 {QT_VERSION_STR} - 正常")
        return True
    except Exception as e:
        print(f"❌ PyQt6 测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("VisionAI-ClipsMaster 依赖测试")
    print("=" * 60)
    print()
    
    tests = [
        ("核心数值库", test_numpy),
        ("PyTorch深度学习框架", test_torch),
        ("Transformers模型库", test_transformers),
        ("GGUF格式支持", test_gguf),
        ("Protobuf序列化", test_protobuf),
        ("SentencePiece分词器", test_sentencepiece),
        ("llama.cpp转换工具", test_llama_cpp_converter),
        ("模型转换器", test_model_converter),
        ("PyQt6界面库", test_pyqt6),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n测试: {name}")
        print("-" * 60)
        result = test_func()
        results.append((name, result))
        print()
    
    # 汇总结果
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统依赖完整，功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查相关依赖。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

