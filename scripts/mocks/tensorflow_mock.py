#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TensorFlow模拟模块
用于在没有安装TensorFlow的环境中提供基本的GPU检测功能
"""

class MockConfig:
    """模拟TensorFlow配置类"""
    
    class Experimental:
        """模拟实验性功能"""
        
        @staticmethod
        def list_physical_devices(device_type='GPU'):
            """模拟列出物理设备"""
            if device_type == 'GPU':
                # 返回空列表，表示没有GPU
                return []
            return []
    
    experimental = Experimental()

# 模拟TensorFlow配置
config = MockConfig()

def __getattr__(name):
    """处理其他属性访问"""
    if name == 'config':
        return config
    raise AttributeError(f"module 'tensorflow_mock' has no attribute '{name}'")
