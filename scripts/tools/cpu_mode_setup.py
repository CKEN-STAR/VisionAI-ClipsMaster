"""
CPU模式强制设置
在导入任何PyTorch相关模块之前设置环境变量，确保在无GPU设备上正常运行
"""

import os
import sys

def setup_cpu_mode():
    """设置CPU模式环境变量"""
    # 强制禁用CUDA
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TORCH_USE_CUDA_DSA'] = '0'
    
    # 设置线程数（适配低配设备）
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['MKL_NUM_THREADS'] = '4'
    os.environ['NUMEXPR_NUM_THREADS'] = '4'
    
    # PyTorch内存优化
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # 禁用一些可能导致问题的功能
    os.environ['TORCH_CUDNN_V8_API_ENABLED'] = '0'
    os.environ['TORCH_CUDNN_V8_API_LRU_CACHE_LIMIT'] = '0'
    
    print("[OK] CPU模式环境已设置")

def check_torch_cpu():
    """检查PyTorch是否正确使用CPU"""
    try:
        import torch
        device = torch.device('cpu')
        
        # 测试基本操作
        x = torch.randn(2, 2, device=device)
        y = torch.randn(2, 2, device=device)
        z = torch.mm(x, y)
        
        print(f"[OK] PyTorch CPU模式测试成功")
        print(f"[INFO] PyTorch版本: {torch.__version__}")
        print(f"[INFO] CUDA可用: {torch.cuda.is_available()}")
        print(f"[INFO] 设备: {device}")
        
        return True
    except Exception as e:
        print(f"[ERROR] PyTorch CPU模式测试失败: {e}")
        return False

def setup_memory_optimization():
    """设置内存优化"""
    import gc
    
    # 启用垃圾回收
    gc.enable()
    
    # 设置垃圾回收阈值（更频繁的垃圾回收）
    gc.set_threshold(700, 10, 10)
    
    print("[OK] 内存优化设置完成")

# 在模块导入时自动执行
if __name__ == "__main__":
    setup_cpu_mode()
    setup_memory_optimization()
    check_torch_cpu()
else:
    # 作为模块导入时也执行设置
    setup_cpu_mode()
