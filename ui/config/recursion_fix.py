"""
递归深度修复模块
解决递归深度超出问题
"""

import sys
import threading

# 默认递归限制
DEFAULT_RECURSION_LIMIT = 3000
THREAD_STACK_SIZE = 8 * 1024 * 1024  # 8MB

def increase_recursion_limit(limit: int = DEFAULT_RECURSION_LIMIT) -> bool:
    """
    增加递归深度限制
    
    Args:
        limit: 新的递归限制
        
    Returns:
        是否成功设置
    """
    try:
        current_limit = sys.getrecursionlimit()
        
        if limit > current_limit:
            sys.setrecursionlimit(limit)
            print(f"[OK] 递归限制已从 {current_limit} 增加到 {limit}")
        else:
            print(f"[INFO] 当前递归限制 {current_limit} 已足够，无需调整")
        
        return True
        
    except Exception as e:
        print(f"[WARN] 设置递归限制失败: {e}")
        return False

def set_thread_stack_size(size: int = THREAD_STACK_SIZE) -> bool:
    """
    设置线程栈大小
    
    Args:
        size: 栈大小（字节）
        
    Returns:
        是否成功设置
    """
    try:
        threading.stack_size(size)
        print(f"[OK] 线程栈大小已设置为 {size // (1024*1024)}MB")
        return True
        
    except Exception as e:
        print(f"[WARN] 设置线程栈大小失败: {e}")
        return False

def get_recursion_info() -> dict:
    """获取递归相关信息"""
    try:
        return {
            'current_limit': sys.getrecursionlimit(),
            'default_limit': DEFAULT_RECURSION_LIMIT,
            'thread_stack_size': threading.stack_size() if hasattr(threading, 'stack_size') else None,
            'platform': sys.platform
        }
    except Exception as e:
        print(f"[WARN] 获取递归信息失败: {e}")
        return {}

def apply_recursion_fixes() -> bool:
    """应用所有递归相关修复"""
    try:
        success = True
        
        # 增加递归限制
        if not increase_recursion_limit():
            success = False
        
        # 设置线程栈大小
        if not set_thread_stack_size():
            success = False
        
        if success:
            print("[OK] 递归修复应用完成")
        else:
            print("[WARN] 部分递归修复应用失败")
        
        return success
        
    except Exception as e:
        print(f"[WARN] 应用递归修复失败: {e}")
        return False

def check_recursion_safety() -> bool:
    """检查递归安全性"""
    try:
        current_limit = sys.getrecursionlimit()
        
        # 检查是否有足够的递归深度
        if current_limit < 1000:
            print(f"[WARN] 递归限制过低: {current_limit}")
            return False
        
        # 测试递归调用
        def test_recursion(depth=0):
            if depth > 100:  # 测试100层递归
                return True
            return test_recursion(depth + 1)
        
        result = test_recursion()
        if result:
            print("[OK] 递归安全性检查通过")
            return True
        else:
            print("[WARN] 递归安全性检查失败")
            return False
            
    except RecursionError:
        print("[WARN] 递归深度不足")
        return False
    except Exception as e:
        print(f"[WARN] 递归安全性检查异常: {e}")
        return False

# 自动应用修复
def auto_fix_recursion():
    """自动修复递归问题"""
    try:
        if not check_recursion_safety():
            apply_recursion_fixes()
    except Exception as e:
        print(f"[WARN] 自动递归修复失败: {e}")

__all__ = [
    'increase_recursion_limit',
    'set_thread_stack_size', 
    'get_recursion_info',
    'apply_recursion_fixes',
    'check_recursion_safety',
    'auto_fix_recursion'
]
