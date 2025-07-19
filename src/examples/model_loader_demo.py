#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
按需加载引擎使用示例

该示例演示如何使用OnDemandLoader进行模型的动态加载和切换。
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入按需加载引擎
from src.core.on_demand_loader import OnDemandLoader, ModelLoadRequest

def model_callback(model_name: str):
    """模型加载后的回调函数"""
    logger.info(f"模型 {model_name} 已准备就绪，可以开始使用")

def print_model_info(info: Dict[str, Any]):
    """打印模型信息"""
    print("\n" + "-" * 50)
    print(f"模型名称: {info.get('name', 'N/A')}")
    print(f"语言: {info.get('language', 'N/A')}")
    print(f"量化等级: {info.get('quantization', 'N/A')}")
    print(f"已加载: {'是' if info.get('loaded', False) else '否'}")
    print(f"内存估计: {info.get('memory_estimate_gb', 0):.2f} GB")
    print("-" * 50 + "\n")

def main():
    logger.info("启动按需加载引擎测试...")
    
    # 创建按需加载引擎实例
    loader = OnDemandLoader(
        config_dir="configs/models",
        model_dir="models",
        cache_dir=".cache/models"
    )
    
    # 显示所有可用模型
    logger.info("检测到以下可用模型:")
    available_models = loader.get_available_models()
    
    for model in available_models:
        print(f"- {model['name']} ({model['language']}): "
              f"{'已安装' if model['installed'] else '未安装'}, "
              f"内存需求: {model['memory_gb']:.2f}GB")
    
    # 尝试加载中文模型
    logger.info("\n尝试加载中文模型...")
    
    zh_model = loader.get_model_for_language("zh")
    if zh_model:
        # 创建加载请求
        request = ModelLoadRequest(
            model_name=zh_model,
            language="zh",
            callback=model_callback
        )
        
        # 加载模型
        success = loader.load_model(request)
        
        if success:
            # 获取模型信息
            model_info = loader.get_model_info(zh_model)
            print_model_info(model_info)
            
            # 模拟使用模型
            logger.info("模拟使用中文模型进行推理...")
            time.sleep(2)  # 模拟推理过程
            
            logger.info("中文推理完成")
        else:
            logger.error("中文模型加载失败")
    else:
        logger.error("未找到中文模型")
    
    # 尝试自动检测并切换语言
    test_text_en = "Hello, this is an English text sample for language detection."
    logger.info(f"\n尝试自动检测文本语言: \"{test_text_en}\"")
    
    detected_lang = loader.auto_detect_and_switch(test_text_en)
    logger.info(f"检测到语言: {detected_lang}")
    
    # 获取当前活动模型信息
    active_model_info = loader.get_model_info()
    if active_model_info:
        print_model_info(active_model_info)
    else:
        logger.warning("当前无活动模型")
    
    # 注意：英文模型应显示为未安装状态
    
    # 清理资源
    logger.info("\n清理资源...")
    # 卸载模型
    if zh_model:
        loader.unload_model(zh_model)
        logger.info(f"已卸载模型: {zh_model}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 