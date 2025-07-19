#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证分层压缩策略

验证压缩配置并运行测试
"""

import os
import sys
import argparse
import subprocess
import yaml
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VerifyScript")

def run_command(cmd, cwd=None):
    """运行命令并返回输出"""
    logger.info(f"执行命令: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd or project_root,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        raise

def verify_config():
    """验证压缩配置"""
    logger.info("验证压缩配置文件...")
    
    config_path = os.path.join(project_root, "configs", "compression_layers.yaml")
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        logger.error(f"找不到配置文件: {config_path}")
        return False
    
    # 使用layered_cli验证配置
    try:
        from src.compression.layered_cli import verify_config as verify_config_func
        
        # 创建一个参数对象
        class Args:
            def __init__(self, config):
                self.config = config
        
        args = Args(config_path)
        
        # 验证配置
        result = verify_config_func(args)
        if result != 0:
            logger.error("配置验证失败")
            return False
        
        logger.info("配置验证成功")
        return True
    
    except ImportError:
        logger.warning("无法导入验证模块，尝试直接使用YAML解析验证")
        
        try:
            # 加载YAML配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查基本结构
            if not isinstance(config, dict) or "compression_policy" not in config:
                logger.error("配置文件格式错误，缺少compression_policy节点")
                return False
            
            policies = config["compression_policy"]
            if not isinstance(policies, dict):
                logger.error("compression_policy必须是字典")
                return False
            
            # 检查必要的策略类型
            required_types = ["model_weights", "default"]
            for res_type in required_types:
                if res_type not in policies:
                    logger.error(f"缺少必要的策略类型: {res_type}")
                    return False
            
            logger.info(f"配置验证成功，包含 {len(policies)} 个策略类型")
            return True
            
        except Exception as e:
            logger.error(f"配置解析失败: {e}")
            return False

def run_layered_test():
    """运行分层压缩测试"""
    logger.info("运行分层压缩测试...")
    
    test_script = os.path.join(project_root, "src", "compression", "test_layered.py")
    
    # 检查测试脚本是否存在
    if not os.path.exists(test_script):
        logger.error(f"找不到测试脚本: {test_script}")
        return False
    
    # 运行测试
    try:
        cmd = f"{sys.executable} {test_script}"
        run_command(cmd)
        logger.info("测试执行成功")
        return True
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return False

def validate_yq_config():
    """使用yq命令验证配置"""
    logger.info("使用yq验证配置...")
    
    config_path = os.path.join(project_root, "configs", "compression_layers.yaml")
    
    # 检查yq命令是否可用
    try:
        run_command("yq --version")
    except:
        logger.warning("yq命令不可用，跳过此验证步骤")
        return True
    
    # 使用yq验证配置
    try:
        # 提取配置内容并显示
        cmd = f"yq eval '.compression_policy' {config_path}"
        result = run_command(cmd)
        
        # 输出配置摘要
        logger.info("压缩策略配置摘要:")
        policies = yaml.safe_load(result)
        for res_type, policy in policies.items():
            algorithm = policy.get("algorithm", "unknown")
            level = policy.get("level", "N/A")
            auto_compress = "yes" if policy.get("auto_compress", False) else "no"
            threshold = policy.get("threshold_mb", "N/A")
            
            logger.info(f"  {res_type}: 算法={algorithm} (级别{level}), "
                      f"自动压缩={auto_compress}, 阈值={threshold}MB")
        
        return True
        
    except Exception as e:
        logger.error(f"yq验证失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="验证分层压缩策略")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试执行")
    parser.add_argument("--yq-check", action="store_true", help="使用yq命令验证配置")
    args = parser.parse_args()
    
    success = True
    
    # 验证配置
    if not verify_config():
        logger.error("配置验证失败")
        success = False
    
    # 使用yq验证配置(可选)
    if args.yq_check and success:
        if not validate_yq_config():
            logger.warning("yq验证失败，但继续执行")
    
    # 运行测试(除非指定跳过)
    if not args.skip_tests and success:
        if not run_layered_test():
            logger.error("测试执行失败")
            success = False
    
    if success:
        logger.info("验证成功! ✓")
        return 0
    else:
        logger.error("验证失败! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 