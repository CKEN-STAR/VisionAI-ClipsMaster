#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试GPU加速优化功能
"""

import time
from src.training.zh_trainer import ZhTrainer
from src.core.gpu_accelerator import get_gpu_accelerator

def test_gpu_optimization():
    """测试GPU加速优化"""
    
    print('=== GPU加速功能测试 ===')
    
    # 测试GPU加速器
    print('\n1. 测试GPU加速器初始化...')
    gpu_accelerator = get_gpu_accelerator()
    
    print(f'可用后端: {gpu_accelerator.available_backends}')
    print(f'活跃后端: {gpu_accelerator.active_backend}')
    print(f'GPU信息: {gpu_accelerator.gpus_info}')
    
    # 测试训练器的GPU支持
    print('\n2. 测试训练器GPU支持...')
    
    # CPU模式训练器
    cpu_trainer = ZhTrainer(use_gpu=False)
    print(f'CPU训练器GPU加速器: {cpu_trainer.gpu_accelerator}')
    
    # GPU模式训练器
    gpu_trainer = ZhTrainer(use_gpu=True)
    print(f'GPU训练器GPU加速器: {gpu_trainer.gpu_accelerator}')
    
    # 测试推理性能
    print('\n3. 测试推理性能...')
    
    test_texts = [
        "小明在公园里散步。",
        "今天天气很好。",
        "他看到了一只小猫。",
        "猫咪很可爱。",
        "他决定拍照留念。"
    ]
    
    # CPU推理测试
    print('\nCPU推理测试:')
    cpu_start = time.time()
    cpu_results = []
    for text in test_texts:
        result = cpu_trainer.quick_inference_test(text)
        cpu_results.append(result)
        print(f'  {text} -> {result}')
    cpu_time = time.time() - cpu_start
    print(f'CPU总耗时: {cpu_time:.3f}秒')
    
    # GPU推理测试（如果可用）
    if gpu_trainer.gpu_accelerator and gpu_trainer.gpu_accelerator.active_backend:
        print('\nGPU推理测试:')
        gpu_start = time.time()
        gpu_results = []
        for text in test_texts:
            result = gpu_trainer.accelerated_inference(text)
            gpu_results.append(result)
            print(f'  {text} -> {result}')
        gpu_time = time.time() - gpu_start
        print(f'GPU总耗时: {gpu_time:.3f}秒')
        
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        print(f'加速比: {speedup:.2f}x')
    else:
        print('\nGPU不可用，跳过GPU推理测试')
    
    # 性能基准测试
    print('\n4. 性能基准测试...')
    benchmark_results = gpu_trainer.benchmark_inference_performance(test_texts)
    print(f'基准测试结果: {benchmark_results}')
    
    # GPU加速器性能测试
    print('\n5. GPU加速器性能测试...')
    try:
        gpu_benchmark = gpu_accelerator.benchmark_performance()
        print(f'GPU加速器基准测试: {gpu_benchmark}')
    except Exception as e:
        print(f'GPU加速器基准测试失败: {e}')
    
    print('\n=== GPU加速功能测试完成 ===')
    
    return {
        "gpu_available": gpu_trainer.gpu_accelerator is not None,
        "active_backend": gpu_trainer.gpu_accelerator.active_backend if gpu_trainer.gpu_accelerator else None,
        "benchmark_results": benchmark_results
    }

if __name__ == "__main__":
    result = test_gpu_optimization()
    print(f'\n最终结果: {result}')
