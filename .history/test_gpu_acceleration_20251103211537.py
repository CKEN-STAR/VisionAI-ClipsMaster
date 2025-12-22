"""
测试GPU加速是否正常工作
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gpu_support():
    """测试GPU支持"""
    print("=" * 60)
    print("🔍 测试1: 检查llama-cpp-python的GPU支持")
    print("=" * 60)
    
    try:
        from llama_cpp import llama_cpp
        gpu_support = llama_cpp.llama_supports_gpu_offload()
        print(f"✅ GPU offload support: {gpu_support}")
        
        if not gpu_support:
            print("❌ GPU支持未启用!")
            return False
    except Exception as e:
        print(f"❌ 检查GPU支持失败: {e}")
        return False
    
    print()
    return True

def test_ai_engine_gpu():
    """测试AI引擎的GPU配置"""
    print("=" * 60)
    print("🔍 测试2: 检查AI引擎的GPU配置")
    print("=" * 60)
    
    try:
        from src.core.real_ai_engine import RealAIEngine
        
        # 初始化AI引擎
        print("正在初始化AI引擎...")
        engine = RealAIEngine()
        
        # 检查设备配置
        print(f"✅ AI引擎设备: {engine.device}")
        print(f"✅ CUDA可用: {engine.cuda_available}")
        
        if engine.device != "cuda":
            print("⚠️ AI引擎未使用GPU!")
            return False
            
    except Exception as e:
        print(f"❌ 测试AI引擎失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True

def test_model_loading():
    """测试模型加载时的GPU配置"""
    print("=" * 60)
    print("🔍 测试3: 测试模型加载(GPU加速)")
    print("=" * 60)
    
    try:
        from llama_cpp import Llama
        import os
        
        # 查找可用的GGUF模型
        model_paths = [
            "models/qwen/quantized/qwen-test-small.gguf",
            "models/qwen/quantized/trained_qwen_q4.gguf",
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            print("⚠️ 未找到GGUF模型文件,跳过模型加载测试")
            return True
        
        print(f"正在加载模型: {model_path}")
        print("配置: n_gpu_layers=-1 (所有层使用GPU)")
        
        # 使用GPU加速配置
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_gpu_layers=-1,  # 所有层使用GPU
            n_threads=4,
            verbose=True
        )
        
        print("✅ 模型加载成功!")
        
        # 测试推理
        print("\n测试推理...")
        response = model("你好", max_tokens=10)
        print(f"✅ 推理成功: {response}")
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    return True

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🚀 GPU加速测试套件")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试1: GPU支持
    results.append(("GPU支持检查", test_gpu_support()))
    
    # 测试2: AI引擎GPU配置
    results.append(("AI引擎GPU配置", test_ai_engine_gpu()))
    
    # 测试3: 模型加载
    results.append(("模型加载(GPU)", test_model_loading()))
    
    # 总结
    print("=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r for _, r in results)
    
    print()
    if all_passed:
        print("🎉 所有测试通过! GPU加速已成功启用!")
    else:
        print("⚠️ 部分测试失败,请检查配置")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

