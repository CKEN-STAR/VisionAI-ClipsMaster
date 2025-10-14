"""
模拟的TensorFlow模块
用于在没有安装TensorFlow的环境中提供基本功能
"""

# 添加 __path__ 属性，避免导入错误
__path__ = []

class DLPack:
    @staticmethod
    def from_dlpack(*args, **kwargs):
        """模拟from_dlpack函数"""
        return None
        
    @staticmethod
    def to_dlpack(*args, **kwargs):
        """模拟to_dlpack函数"""
        return None

class Experimental:
    """模拟的experimental模块"""
    def __init__(self):
        self.dlpack = DLPack()

# 暴露主要模块接口
experimental = Experimental()

def is_tensor(obj):
    """检查对象是否为张量
    
    Args:
        obj: 要检查的对象
    
    Returns:
        bool: 是否为张量
    """
    # 在模拟模块中总是返回False
    # 这是一个简单的实现实际TensorFlow中会检查对象类型
    return False

def __getattr__(name):
    """处理所有未定义的属性访问"""
    print(f"访问了TensorFlow模拟模块中未实现的属性: {name}")
    return lambda *args, **kwargs: None

