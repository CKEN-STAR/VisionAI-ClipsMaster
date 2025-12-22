#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试云端AI引擎 - 验证魔搭社区错误提示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.cloud_ai_engine import CloudAIEngine, CloudPlatform, CloudModel

# API密钥
MODELSCOPE_API_KEY = "ms-e706a1e5-ad46-497f-966a-e20bdfaff22b"
SILICONFLOW_API_KEY = "sk-rovcxclyumgjbiihizlmrpgdnrkeyanohuvvdrkorryvqaat"

def test_cloud_engine():
    """使用CloudAIEngine测试两个平台"""
    
    print("\n" + "="*60)
    print("测试1: 硅基流动 (SiliconFlow)")
    print("="*60)
    
    try:
        engine = CloudAIEngine()
        engine.configure(CloudPlatform.SILICONFLOW, CloudModel.QWEN3, SILICONFLOW_API_KEY)
        result = engine.test_connection()
        
        if result.get("success"):
            print("✅ 硅基流动连接成功!")
        else:
            print(f"❌ 硅基流动连接失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 硅基流动异常: {e}")
    
    print("\n" + "="*60)
    print("测试2: 魔搭社区 (ModelScope)")
    print("="*60)
    
    try:
        engine = CloudAIEngine()
        engine.configure(CloudPlatform.MODELSCOPE, CloudModel.QWEN3, MODELSCOPE_API_KEY)
        result = engine.test_connection()
        
        if result.get("success"):
            print("✅ 魔搭社区连接成功!")
        else:
            print(f"❌ 魔搭社区连接失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 魔搭社区异常: {e}")
        # 这里应该显示友好的错误提示

if __name__ == "__main__":
    print("="*60)
    print("云端AI引擎连接测试")
    print("="*60)
    
    test_cloud_engine()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
