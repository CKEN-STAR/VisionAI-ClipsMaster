#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备ID生成模块

提供硬件指纹采集功能，用于唯一标识设备。
这个模块为VisionAI-ClipsMaster的其他组件提供设备识别能力。
"""

import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 导入硬件指纹模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from tests.device_compatibility.hardware_fingerprint import get_hardware_id, get_detailed_hardware_fingerprint
from tests.device_compatibility.hardware_fingerprint_simple import get_hardware_id as get_simple_hardware_id

# 设置日志
logger = logging.getLogger("device_id")

class DeviceIdentifier:
    """设备标识符类，管理硬件指纹和设备ID"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化设备标识符
        
        Args:
            cache_dir: 缓存目录路径，默认为None（使用默认目录）
        """
        if cache_dir is None:
            self.cache_dir = Path.home() / ".visionai" / "device"
        else:
            self.cache_dir = Path(cache_dir)
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存文件路径
        self.cache_file = self.cache_dir / "device_id.json"
        
        # 设备ID和详细信息
        self.device_id = None
        self.device_info = None
        
    def get_device_id(self, force_refresh: bool = False) -> str:
        """
        获取设备ID
        
        Args:
            force_refresh: 是否强制刷新，不使用缓存
            
        Returns:
            str: 设备ID（SHA256哈希）
        """
        # 如果已经加载且不需要强制刷新，直接返回
        if self.device_id is not None and not force_refresh:
            return self.device_id
        
        # 尝试从缓存加载
        if not force_refresh and self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache_data = json.load(f)
                self.device_id = cache_data.get("device_id")
                if self.device_id:
                    logger.debug(f"从缓存加载设备ID: {self.device_id[:8]}...")
                    return self.device_id
            except Exception as e:
                logger.warning(f"读取设备ID缓存失败: {e}")
        
        # 如果缓存无效或需要刷新，生成新的设备ID
        try:
            logger.debug("正在生成设备ID...")
            # 使用完整的硬件指纹生成器
            self.device_id = get_hardware_id()
            
            # 保存到缓存
            with open(self.cache_file, "w") as f:
                json.dump({"device_id": self.device_id}, f)
                
            logger.debug(f"生成并缓存设备ID: {self.device_id[:8]}...")
            return self.device_id
            
        except Exception as e:
            # 如果完整的硬件指纹生成失败，尝试使用简化版
            logger.warning(f"生成完整硬件指纹失败: {e}，尝试使用简化版...")
            try:
                self.device_id = get_simple_hardware_id()
                
                # 保存到缓存
                with open(self.cache_file, "w") as f:
                    json.dump({"device_id": self.device_id}, f)
                    
                logger.debug(f"生成并缓存简化设备ID: {self.device_id[:8]}...")
                return self.device_id
                
            except Exception as e2:
                # 如果简化版也失败，使用备用方法
                logger.error(f"生成简化硬件指纹失败: {e2}，使用备用方法...")
                import platform
                import uuid
                
                # 使用主机名和MAC地址
                backup_id = hashlib.sha256(
                    (platform.node() + str(uuid.getnode())).encode()
                ).hexdigest()
                
                self.device_id = backup_id
                return self.device_id
    
    def get_device_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取详细的设备信息
        
        Args:
            force_refresh: 是否强制刷新，不使用缓存
            
        Returns:
            Dict[str, Any]: 设备详细信息
        """
        # 如果已经加载且不需要强制刷新，直接返回
        if self.device_info is not None and not force_refresh:
            return self.device_info
        
        # 缓存文件路径
        info_cache_file = self.cache_dir / "device_info.json"
        
        # 尝试从缓存加载
        if not force_refresh and info_cache_file.exists():
            try:
                with open(info_cache_file, "r") as f:
                    self.device_info = json.load(f)
                logger.debug("从缓存加载设备详细信息")
                return self.device_info
            except Exception as e:
                logger.warning(f"读取设备详细信息缓存失败: {e}")
        
        # 如果缓存无效或需要刷新，收集设备信息
        try:
            logger.debug("正在收集设备详细信息...")
            self.device_info = get_detailed_hardware_fingerprint(verbose=False)
            
            # 保存到缓存
            with open(info_cache_file, "w") as f:
                json.dump(self.device_info, f, indent=2)
                
            logger.debug("设备详细信息已收集并缓存")
            return self.device_info
            
        except Exception as e:
            # 如果收集失败，返回简化的信息
            logger.error(f"收集设备详细信息失败: {e}")
            
            import platform
            
            self.device_info = {
                "hardware_id": self.get_device_id(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "system": platform.system(),
                "version": platform.version()
            }
            
            return self.device_info
    
    def save_device_info(self, file_path: str) -> bool:
        """
        将设备信息保存到文件
        
        Args:
            file_path: 保存路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            info = self.get_device_info()
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
                
            logger.info(f"设备信息已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存设备信息失败: {e}")
            return False


# 全局实例，简化使用
_device_identifier = None

def get_device_identifier() -> DeviceIdentifier:
    """
    获取设备标识符实例（单例模式）
    
    Returns:
        DeviceIdentifier: 设备标识符实例
    """
    global _device_identifier
    
    if _device_identifier is None:
        _device_identifier = DeviceIdentifier()
        
    return _device_identifier


def get_device_id() -> str:
    """
    获取设备ID（简单接口）
    
    Returns:
        str: 设备ID
    """
    return get_device_identifier().get_device_id()


def get_device_info() -> Dict[str, Any]:
    """
    获取详细设备信息（简单接口）
    
    Returns:
        Dict[str, Any]: 设备详细信息
    """
    return get_device_identifier().get_device_info()


def save_device_report(file_path: Optional[str] = None) -> str:
    """
    生成并保存设备报告
    
    Args:
        file_path: 保存路径，如果为None则使用默认路径
        
    Returns:
        str: 报告文件路径
    """
    if file_path is None:
        file_path = os.path.join("reports", "device_report.json")
        
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 保存设备信息
    get_device_identifier().save_device_info(file_path)
    
    return file_path


def is_mobile_device() -> bool:
    """判断当前设备是否为移动设备
    
    通过分析设备特征判断当前运行环境是否为移动设备，例如手机、平板等
    
    Returns:
        bool: 是否为移动设备
    """
    import platform
    
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # 检测ARM架构（通常用于移动设备）
    if 'arm' in machine:
        return True
        
    # 检测Android系统
    if 'android' in system:
        return True
        
    # 检测iOS设备特征
    if system == 'darwin' and ('iphone' in machine.lower() or 'ipad' in machine.lower()):
        return True
    
    # 检测特定环境变量（可由测试框架设置）
    if os.environ.get("VISIONAI_MOBILE_DEVICE", "false").lower() == "true":
        return True
        
    return False


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 获取并打印设备ID
    device_id = get_device_id()
    print(f"设备ID: {device_id}")
    
    # 保存设备报告
    report_path = save_device_report()
    print(f"设备报告已保存到: {report_path}") 