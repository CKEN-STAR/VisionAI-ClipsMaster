#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试魔搭社区 (ModelScope) API连接
"""

import requests
import json

# 魔搭社区API配置
MODELSCOPE_API_URL = "https://api-inference.modelscope.cn/v1/chat/completions"
MODELSCOPE_API_KEY = "ms-e706a1e5-ad46-497f-966a-e20bdfaff22b"

# 测试模型
MODELS_TO_TEST = [
    "Qwen/Qwen3-235B-A22B-FP8",
    "deepseek-ai/DeepSeek-V3-0324",
    "Qwen/Qwen2.5-72B-Instruct",  # 备选模型
]

def test_modelscope_api(model_name):
    """测试魔搭社区API"""
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"API地址: {MODELSCOPE_API_URL}")
    print(f"{'='*60}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MODELSCOPE_API_KEY}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "你好，请回复'连接成功'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False
    }
    
    print(f"\n请求头: {json.dumps({k: v[:20]+'...' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")
    print(f"\n请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            MODELSCOPE_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 成功! 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"\n❌ 失败! 错误响应:")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

def test_siliconflow_api():
    """测试硅基流动API作为对比"""
    print(f"\n{'='*60}")
    print("对比测试: 硅基流动 API")
    print(f"{'='*60}")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    api_key = "sk-rovcxclyumgjbiihizlmrpgdnrkeyanohuvvdrkorryvqaat"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "Qwen/Qwen3-235B-A22B",
        "messages": [
            {"role": "user", "content": "你好，请回复'连接成功'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 硅基流动成功!")
            if "choices" in result:
                print(f"回复: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ 硅基流动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 硅基流动异常: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("魔搭社区 (ModelScope) API 连接测试")
    print("="*60)
    
    # 先测试硅基流动作为对比
    test_siliconflow_api()
    
    # 测试魔搭社区的各个模型
    for model in MODELS_TO_TEST:
        test_modelscope_api(model)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
