#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级模型加载演示

此示例展示了如何在实际应用中使用按需加载引擎和适配器，
包括自动语言检测、模型切换和内存优化等功能。
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
from src.core.on_demand_loader import OnDemandLoader, ModelLoadRequest
from src.core.model_loader_adapter import ModelLoaderAdapter
from src.utils.memory_guard import MemoryGuard
from src.utils.memory_manager import MemoryManager
from src.utils.device_manager import HybridDevice

def print_separator(title=""):
    """打印分隔线"""
    width = 60
    print("\n" + "=" * width)
    if title:
        print(f"{title.center(width)}")
        print("-" * width)

def print_model_info(info: Dict[str, Any]):
    """打印模型信息"""
    if not info:
        print("无模型信息")
        return
        
    print(f"模型名称: {info.get('name', 'N/A')}")
    print(f"语言: {info.get('language', 'N/A')}")
    print(f"量化等级: {info.get('quantization', 'N/A')}")
    print(f"已加载: {'是' if info.get('loaded', False) else '否'}")
    print(f"内存估计: {info.get('memory_estimate_gb', 0):.2f} GB")
    
    # 打印状态信息
    state = info.get("state", {})
    if state:
        print("\n状态信息:")
        print(f"  加载次数: {state.get('load_count', 0)}")
        last_used = state.get('last_used', 0)
        if last_used:
            print(f"  最后使用: {time.ctime(last_used)}")

def print_memory_info(memory_manager: MemoryManager):
    """打印内存使用信息"""
    mem_info = memory_manager.get_memory_usage()
    
    print(f"系统内存总量: {mem_info['total_mb']:.2f} MB")
    print(f"可用内存: {mem_info['available_mb']:.2f} MB")
    print(f"使用率: {mem_info['percent']:.2f}%")
    print(f"进程内存使用: {mem_info['process_rss_mb']:.2f} MB")
    print(f"内存峰值: {mem_info['peak_mb']:.2f} MB")

def simulate_inference(text: str):
    """模拟推理过程"""
    print(f"\n输入文本: \"{text}\"")
    print("模拟推理中...")
    time.sleep(1)  # 模拟推理延迟
    
    # 生成模拟回复
    if "你好" in text or "早上好" in text:
        return "你好！有什么我可以帮助你的吗？"
    elif "hello" in text.lower() or "good morning" in text.lower():
        return "Hello! How can I assist you today?"
    else:
        return "我已经理解了您的输入，正在处理中..."

def main():
    parser = argparse.ArgumentParser(description="高级模型加载演示")
    parser.add_argument("--config-dir", default="configs/models", help="模型配置目录")
    parser.add_argument("--model-dir", default="models", help="模型文件目录")
    parser.add_argument("--cache-dir", default=".cache/models", help="模型缓存目录")
    args = parser.parse_args()
    
    print_separator("初始化组件")
    
    # 初始化内存守卫
    memory_guard = MemoryGuard(
        low_memory_threshold=0.8,  # 80%内存使用率触发警告
        enable_monitoring=True     # 启用内存监控
    )
    
    # 初始化内存管理器
    memory_manager = MemoryManager(min_required_memory=1.0)  # 最小需要1GB内存
    
    # 初始化设备管理器
    device_manager = HybridDevice()
    
    # 打印设备信息
    device_info = device_manager.get_device_info()
    print(f"当前设备: {device_info.get('current_device', 'unknown')}")
    print(f"可用设备: {[d.value for d in device_info.get('available_devices', [])]}")
    
    # 初始化按需加载引擎
    loader = OnDemandLoader(
        config_dir=args.config_dir,
        model_dir=args.model_dir,
        cache_dir=args.cache_dir,
        memory_guard=memory_guard,
        device_manager=device_manager,
        memory_manager=memory_manager
    )
    
    # 创建适配器
    adapter = ModelLoaderAdapter(on_demand_loader=loader)
    
    print_separator("可用模型")
    
    # 显示所有可用模型
    available_models = adapter.get_available_models()
    for model in available_models:
        install_status = "已安装" if model['installed'] else "未安装"
        print(f"- {model['name']} ({model['language']}): {install_status}, "
              f"内存需求: {model['memory_gb']:.2f}GB")
    
    print_separator("内存状态")
    print_memory_info(memory_manager)
    
    # 测试文本
    test_texts = [
        "你好，这是一段中文测试文本，用于测试语言检测和模型切换功能。",
        "Hello, this is an English test text for language detection and model switching.",
        "早上好，今天天气真不错！",
        "Good morning! The weather is nice today!"
    ]
    
    # 测试语言检测和模型切换
    for i, text in enumerate(test_texts):
        print_separator(f"测试 {i+1}: 语言检测与模型切换")
        
        # 检测语言并切换模型
        language = adapter.detect_and_switch(text)
        print(f"检测到语言: {language}")
        
        # 获取当前模型信息
        model_info = adapter.get_active_model_info()
        print_model_info(model_info)
        
        # 模拟推理
        if model_info and model_info.get("loaded", False):
            response = simulate_inference(text)
            print(f"模型回复: \"{response}\"")
        else:
            print("模型未加载，无法进行推理")
        
        # 打印内存状态
        print("\n当前内存状态:")
        print_memory_info(memory_manager)
        
        # 暂停一下，让用户观察
        time.sleep(1)
    
    print_separator("清理资源")
    
    # 卸载所有模型
    adapter.unload_all_models()
    
    # 再次打印内存状态
    print("\n清理后内存状态:")
    print_memory_info(memory_manager)
    
    print("\n演示完成!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 