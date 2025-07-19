#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常回滚管理器

提供在XML文件操作失败时的回滚机制，确保系统稳定性和数据一致性。
主要功能：
1. 文件操作前自动备份
2. 异常发生时恢复到原始状态
3. 支持多种文件格式的回滚（XML, JSON, SRT等）
4. 事务性操作支持
"""

import os
import sys
import shutil
import tempfile
import xml.etree.ElementTree as ET
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from functools import wraps
from datetime import datetime
import logging

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 配置日志
logger = get_logger("rollback_manager")


class LegalRollback:
    """XML操作的回滚机制类"""
    
    def __init__(self, original_xml: str):
        """
        初始化回滚对象
        
        Args:
            original_xml: 原始XML内容
        """
        self.backup = original_xml
        
    def restore(self, target_path: str = "output.xml"):
        """
        声明注入失败时恢复原始XML
        
        Args:
            target_path: 恢复目标文件路径，默认为"output.xml"
            
        Returns:
            bool: 恢复是否成功
        """
        logger.info(f"执行回滚操作，恢复到原始状态: {target_path}")
        
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(self.backup)
            logger.info(f"成功回滚到原始状态: {target_path}")
            return True
        except Exception as e:
            logger.error(f"回滚失败: {str(e)}")
            return False


class FileRollbackManager:
    """文件操作回滚管理器"""
    
    def __init__(self):
        """初始化文件回滚管理器"""
        self.backup_dir = os.path.join(tempfile.gettempdir(), "clipmaster_backup")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.backup_registry = {}  # 文件路径 -> 备份路径的映射
        self.logger = logger
        
    def backup_file(self, file_path: str) -> Optional[str]:
        """
        备份文件
        
        Args:
            file_path: 待备份文件路径
            
        Returns:
            Optional[str]: 备份文件路径，如果备份失败则返回None
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"文件不存在，无法备份: {file_path}")
                return None
                
            # 创建备份文件名，包含时间戳以避免冲突
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_filename = f"{filename}.{timestamp}.bak"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 复制文件
            shutil.copy2(file_path, backup_path)
            
            # 记录备份
            self.backup_registry[file_path] = backup_path
            self.logger.info(f"已备份文件: {file_path} -> {backup_path}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份文件失败: {str(e)}")
            return None
    
    def restore_file(self, file_path: str) -> bool:
        """
        从备份恢复文件
        
        Args:
            file_path: 要恢复的文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if file_path not in self.backup_registry:
                self.logger.warning(f"未找到文件的备份: {file_path}")
                return False
                
            backup_path = self.backup_registry[file_path]
            if not os.path.exists(backup_path):
                self.logger.error(f"备份文件已丢失: {backup_path}")
                return False
                
            # 恢复文件
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"已恢复文件: {backup_path} -> {file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"恢复文件失败: {str(e)}")
            return False
    
    def cleanup_backup(self, file_path: str = None, max_age_days: int = 7) -> int:
        """
        清理备份文件
        
        Args:
            file_path: 特定文件的备份，如果为None则清理所有过期备份
            max_age_days: 备份文件最大保留天数
            
        Returns:
            int: 清理的文件数量
        """
        try:
            count = 0
            now = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            if file_path:
                # 清理特定文件的备份
                if file_path in self.backup_registry:
                    backup_path = self.backup_registry[file_path]
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        count += 1
                    del self.backup_registry[file_path]
                    self.logger.info(f"已清理备份: {backup_path}")
            else:
                # 清理所有过期备份
                for filename in os.listdir(self.backup_dir):
                    file_path = os.path.join(self.backup_dir, filename)
                    # 检查文件是否过期
                    if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > max_age_seconds:
                        os.remove(file_path)
                        count += 1
                        # 更新注册表
                        for path, backup in list(self.backup_registry.items()):
                            if backup == file_path:
                                del self.backup_registry[path]
                                break
            
            return count
            
        except Exception as e:
            self.logger.error(f"清理备份失败: {str(e)}")
            return 0


class XMLRollbackManager:
    """XML文件操作回滚管理器"""
    
    def __init__(self):
        """初始化XML回滚管理器"""
        self.file_manager = FileRollbackManager()
        self.xml_backups = {}  # 文件路径 -> XML内容字符串的映射
        self.logger = logger
    
    def backup_xml_content(self, xml_path: str) -> bool:
        """
        备份XML文件内容
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            if not os.path.exists(xml_path):
                self.logger.warning(f"XML文件不存在: {xml_path}")
                return False
                
            # 读取XML文件内容
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
                
            # 保存内容备份
            self.xml_backups[xml_path] = xml_content
            self.logger.info(f"已备份XML内容: {xml_path}")
            
            # 同时创建文件备份
            self.file_manager.backup_file(xml_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"备份XML内容失败: {str(e)}")
            return False
    
    def restore_xml_content(self, xml_path: str) -> bool:
        """
        恢复XML文件内容
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            if xml_path not in self.xml_backups:
                self.logger.warning(f"未找到XML内容备份: {xml_path}")
                # 尝试从文件备份恢复
                return self.file_manager.restore_file(xml_path)
                
            # 从内存中恢复内容
            xml_content = self.xml_backups[xml_path]
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)
                
            self.logger.info(f"已恢复XML内容: {xml_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复XML内容失败: {str(e)}，尝试从文件备份恢复")
            # 作为后备，尝试从文件备份恢复
            return self.file_manager.restore_file(xml_path)
    
    def verify_xml(self, xml_path: str) -> bool:
        """
        验证XML文件是否有效
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            bool: XML是否有效
        """
        try:
            # 尝试解析XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            return True
        except Exception as e:
            self.logger.error(f"XML验证失败: {str(e)}")
            return False


# 装饰器：用于自动备份和恢复
def with_xml_rollback(func):
    """为XML操作函数添加自动回滚功能的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 找出XML文件路径参数
        xml_path = None
        for arg in args:
            if isinstance(arg, str) and arg.endswith(('.xml', '.fcpxml')):
                xml_path = arg
                break
        
        if xml_path is None:
            for key, value in kwargs.items():
                if key in ['xml_path', 'path', 'file_path'] and isinstance(value, str) and value.endswith(('.xml', '.fcpxml')):
                    xml_path = value
                    break
        
        if xml_path is None:
            logger.warning("无法找到XML文件路径参数，回滚功能将被禁用")
            return func(*args, **kwargs)
        
        # 初始化回滚管理器
        manager = XMLRollbackManager()
        
        # 备份XML文件
        if not manager.backup_xml_content(xml_path):
            logger.warning(f"无法备份XML文件，继续执行但不提供回滚保护: {xml_path}")
            return func(*args, **kwargs)
        
        try:
            # 执行原始函数
            result = func(*args, **kwargs)
            
            # 验证结果XML是否有效
            if not manager.verify_xml(xml_path):
                logger.error(f"生成的XML无效，执行回滚: {xml_path}")
                manager.restore_xml_content(xml_path)
                return False
            
            return result
            
        except Exception as e:
            # 发生异常时回滚
            logger.error(f"操作过程中发生异常，执行回滚: {str(e)}")
            logger.error(traceback.format_exc())
            manager.restore_xml_content(xml_path)
            raise
            
    return wrapper


# 创建单例回滚管理器
_xml_rollback_manager = XMLRollbackManager()
_file_rollback_manager = FileRollbackManager()

# 导出便捷函数
def backup_xml(xml_path: str) -> bool:
    """备份XML文件"""
    return _xml_rollback_manager.backup_xml_content(xml_path)

def restore_xml(xml_path: str) -> bool:
    """恢复XML文件"""
    return _xml_rollback_manager.restore_xml_content(xml_path)

def backup_file(file_path: str) -> Optional[str]:
    """备份任意文件"""
    return _file_rollback_manager.backup_file(file_path)

def restore_file(file_path: str) -> bool:
    """恢复任意文件"""
    return _file_rollback_manager.restore_file(file_path)

def cleanup_backups(max_age_days: int = 7) -> int:
    """清理过期备份"""
    return _file_rollback_manager.cleanup_backup(max_age_days=max_age_days)


if __name__ == "__main__":
    # 简单测试
    import argparse
    
    parser = argparse.ArgumentParser(description="XML回滚管理器工具")
    parser.add_argument("--backup", help="备份指定的XML文件")
    parser.add_argument("--restore", help="从备份恢复指定的XML文件")
    parser.add_argument("--verify", help="验证XML文件是否有效")
    parser.add_argument("--cleanup", action="store_true", help="清理过期备份")
    parser.add_argument("--days", type=int, default=7, help="备份文件保留天数")
    
    args = parser.parse_args()
    
    if args.backup:
        backup_xml(args.backup)
    elif args.restore:
        restore_xml(args.restore)
    elif args.verify:
        result = _xml_rollback_manager.verify_xml(args.verify)
        print(f"XML验证结果: {'有效' if result else '无效'}")
    elif args.cleanup:
        count = cleanup_backups(args.days)
        print(f"已清理{count}个过期备份文件")
    else:
        print("使用 --help 查看命令选项") 