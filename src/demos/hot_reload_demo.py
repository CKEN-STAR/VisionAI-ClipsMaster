#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热重载监听器演示脚本

展示如何使用热重载监听器监控配置文件变更并自动应用新配置
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# 导入热重载监听器
from src.config import (
    ConfigWatcher,
    get_config_watcher,
    watch_config,
    get_config
)

# 导入日志工具
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("hot_reload_demo")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("hot_reload_demo")

# 配置文件路径
CONFIG_DIR = os.path.join(root_dir, "configs")
TEST_CONFIG_PATH = os.path.join(CONFIG_DIR, "hot_reload_test.json")
TEST_CONFIG_YAML_PATH = os.path.join(CONFIG_DIR, "hot_reload_test.yaml")


def create_test_config():
    """创建测试配置文件"""
    # 创建JSON测试配置
    json_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "1.0.0",
        "last_updated": datetime.datetime.now().isoformat(),
        "settings": {
            "language": "auto",
            "theme": "dark",
            "auto_save": True,
            "save_interval": 5
        }
    }
    
    # 创建YAML测试配置
    yaml_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "1.0.0",
        "last_updated": datetime.datetime.now().isoformat(),
        "features": {
            "auto_reload": True,
            "check_interval": 2,
            "notify_changes": True
        }
    }
    
    # 写入JSON配置文件
    with open(TEST_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_config, f, indent=2, ensure_ascii=False)
    
    # 写入YAML配置文件
    try:
        import yaml
        with open(TEST_CONFIG_YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_config, f, allow_unicode=True, sort_keys=False)
    except (ImportError, Exception) as e:
        logger.error(f"写入YAML配置失败: {e}")
    
    logger.info(f"创建了测试配置文件: {TEST_CONFIG_PATH}, {TEST_CONFIG_YAML_PATH}")


def json_config_callback(config):
    """JSON配置文件变更回调函数"""
    logger.info("JSON配置已更新:")
    logger.info(f"  应用名称: {config.get('app_name')}")
    logger.info(f"  版本: {config.get('version')}")
    logger.info(f"  最后更新: {config.get('last_updated')}")
    
    settings = config.get('settings', {})
    logger.info("  设置:")
    for key, value in settings.items():
        logger.info(f"    {key}: {value}")


def yaml_config_callback(config):
    """YAML配置文件变更回调函数"""
    logger.info("YAML配置已更新:")
    logger.info(f"  应用名称: {config.get('app_name')}")
    logger.info(f"  版本: {config.get('version')}")
    logger.info(f"  最后更新: {config.get('last_updated')}")
    
    features = config.get('features', {})
    logger.info("  功能:")
    for key, value in features.items():
        logger.info(f"    {key}: {value}")


def update_test_config():
    """更新测试配置文件"""
    # 更新JSON配置
    try:
        if os.path.exists(TEST_CONFIG_PATH):
            with open(TEST_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 修改值
            config['last_updated'] = datetime.datetime.now().isoformat()
            config['settings']['theme'] = 'light' if config['settings'].get('theme') == 'dark' else 'dark'
            
            # 写回文件
            with open(TEST_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"已更新JSON配置文件: {TEST_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"更新JSON配置文件失败: {e}")
    
    # 更新YAML配置
    try:
        import yaml
        if os.path.exists(TEST_CONFIG_YAML_PATH):
            with open(TEST_CONFIG_YAML_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 修改值
            config['last_updated'] = datetime.datetime.now().isoformat()
            config['features']['check_interval'] += 1
            
            # 写回文件
            with open(TEST_CONFIG_YAML_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            logger.info(f"已更新YAML配置文件: {TEST_CONFIG_YAML_PATH}")
    except Exception as e:
        logger.error(f"更新YAML配置文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="热重载监听器演示")
    parser.add_argument("--auto-update", action="store_true", help="自动更新配置")
    parser.add_argument("--update-interval", type=int, default=5, help="更新间隔（秒）")
    args = parser.parse_args()
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    print("配置热重载监听器演示")
    print("-" * 50)
    
    # 创建测试配置文件
    create_test_config()
    
    # 获取配置监视器
    watcher = get_config_watcher()
    watcher.start()
    
    # 注册回调
    watch_config(TEST_CONFIG_PATH, json_config_callback)
    watch_config(TEST_CONFIG_YAML_PATH, yaml_config_callback)
    
    print(f"\n监控配置文件: \n- {TEST_CONFIG_PATH}\n- {TEST_CONFIG_YAML_PATH}")
    
    if args.auto_update:
        print(f"\n每 {args.update_interval} 秒自动更新配置...")
    else:
        print("\n请手动修改配置文件内容以查看热重载效果...")
    
    print("\n按 Ctrl+C 停止演示")
    print("-" * 50)
    
    try:
        update_count = 0
        while True:
            if args.auto_update:
                # 等待指定间隔
                time.sleep(args.update_interval)
                
                # 更新配置
                update_test_config()
                update_count += 1
                
                # 最多更新5次
                if update_count >= 5:
                    print("\n已完成5次配置更新，演示结束")
                    break
            else:
                # 手动更新模式，只是等待
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，演示结束")
    finally:
        # 停止监控
        watcher.stop()
        print("\n已停止配置监控")


if __name__ == "__main__":
    main() 