#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交互沙盒隔离器示例

演示如何使用交互沙盒隔离器安全地执行用户代码。
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sandbox_example")

from src.realtime.sandbox import (
    InteractionSandbox,
    initialize_interaction_sandbox,
    get_interaction_sandbox,
    DockerSandbox,
    SubprocessSandbox
)

# 测试代码示例
SAFE_CODE = """
import math
import random

# 计算圆周率到指定精度
def estimate_pi(iterations):
    inside_circle = 0
    total_points = 0
    
    for _ in range(iterations):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1:
            inside_circle += 1
        total_points += 1
    
    return 4 * inside_circle / total_points

# 计算并打印圆周率近似值
pi_estimate = estimate_pi(10000)
print(f"圆周率近似值: {pi_estimate}")
print(f"与math.pi的差异: {abs(pi_estimate - math.pi)}")
"""

UNSAFE_CODE = """
import os
import sys
import subprocess

# 尝试列出目录内容
print("尝试列出当前目录:")
try:
    files = os.listdir('.')
    print(files)
except Exception as e:
    print(f"列出目录失败: {e}")

# 尝试执行系统命令
print("\\n尝试执行系统命令:")
try:
    output = subprocess.check_output(['ls', '-la'])
    print(output)
except Exception as e:
    print(f"执行命令失败: {e}")

# 尝试读取文件
print("\\n尝试读取文件:")
try:
    with open('/etc/passwd', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"读取文件失败: {e}")
"""

RESOURCE_INTENSIVE_CODE = """
# 尝试分配大量内存
print("尝试分配大量内存...")
try:
    # 尝试分配约500MB的内存
    big_list = [0] * (64 * 1024 * 1024)
    print(f"成功分配内存: {len(big_list)} 元素")
except Exception as e:
    print(f"内存分配失败: {e}")

# 尝试进行大量计算
print("\\n尝试进行大量计算...")
try:
    result = 0
    for i in range(10000000):
        result += i
    print(f"计算结果: {result}")
except Exception as e:
    print(f"计算失败: {e}")
"""

INFINITE_LOOP_CODE = """
# 无限循环
print("开始无限循环...")
while True:
    pass
"""

async def test_docker_sandbox():
    """测试Docker沙盒"""
    logger.info("=== 测试Docker沙盒 ===")
    
    try:
        # 创建Docker沙盒
        sandbox = DockerSandbox(timeout=10)
        
        # 执行安全代码
        logger.info("执行安全代码...")
        result = await sandbox.execute(SAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行不安全代码
        logger.info("\n执行不安全代码...")
        result = await sandbox.execute(UNSAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行资源密集型代码
        logger.info("\n执行资源密集型代码...")
        result = await sandbox.execute(RESOURCE_INTENSIVE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行无限循环代码（应该超时）
        logger.info("\n执行无限循环代码（应该超时）...")
        result = await sandbox.execute(INFINITE_LOOP_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 清理沙盒资源
        await sandbox.cleanup()
        
    except Exception as e:
        logger.error(f"Docker沙盒测试出错: {str(e)}")

async def test_subprocess_sandbox():
    """测试子进程沙盒"""
    logger.info("=== 测试子进程沙盒 ===")
    
    try:
        # 创建子进程沙盒
        sandbox = SubprocessSandbox(timeout=10)
        
        # 执行安全代码
        logger.info("执行安全代码...")
        result = await sandbox.execute(SAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行不安全代码
        logger.info("\n执行不安全代码...")
        result = await sandbox.execute(UNSAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行资源密集型代码
        logger.info("\n执行资源密集型代码...")
        result = await sandbox.execute(RESOURCE_INTENSIVE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行无限循环代码（应该超时）
        logger.info("\n执行无限循环代码（应该超时）...")
        result = await sandbox.execute(INFINITE_LOOP_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 清理沙盒资源
        await sandbox.cleanup()
        
    except Exception as e:
        logger.error(f"子进程沙盒测试出错: {str(e)}")

async def test_interaction_sandbox():
    """测试交互沙盒隔离器"""
    logger.info("=== 测试交互沙盒隔离器 ===")
    
    try:
        # 初始化交互沙盒隔离器
        sandbox = await initialize_interaction_sandbox(timeout=10)
        
        # 获取沙盒单例
        singleton = get_interaction_sandbox()
        logger.info(f"单例检查: {sandbox is singleton}")
        
        # 执行安全代码
        logger.info("执行安全代码...")
        result = await sandbox.safe_execute(SAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行不安全代码
        logger.info("\n执行不安全代码...")
        result = await sandbox.safe_execute(UNSAFE_CODE)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 执行复杂数学计算
        logger.info("\n执行复杂数学计算...")
        math_code = """
import numpy as np
import math

# 创建一个矩阵
matrix = np.random.rand(100, 100)
# 计算行列式
det = np.linalg.det(matrix)
print(f"矩阵行列式: {det}")
# 计算特征值
eigenvalues = np.linalg.eigvals(matrix)
print(f"特征值前5个: {eigenvalues[:5]}")
        """
        
        result = await sandbox.safe_execute(math_code)
        logger.info(f"执行结果：成功 = {result['success']}")
        logger.info(f"标准输出：\n{result['stdout']}")
        if result['stderr']:
            logger.info(f"标准错误：\n{result['stderr']}")
        
        # 清理沙盒资源
        await sandbox.cleanup()
        
    except Exception as e:
        logger.error(f"交互沙盒隔离器测试出错: {str(e)}")

async def main():
    """主函数"""
    logger.info("开始交互沙盒隔离器示例")
    
    try:
        # 测试Docker沙盒
        await test_docker_sandbox()
        
        # 测试子进程沙盒
        await test_subprocess_sandbox()
        
        # 测试交互沙盒隔离器
        await test_interaction_sandbox()
        
        logger.info("示例执行完成")
    except Exception as e:
        logger.error(f"示例执行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 