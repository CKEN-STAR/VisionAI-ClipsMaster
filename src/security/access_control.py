#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全访问控制模块

提供VisionAI-ClipsMaster的安全访问控制功能，包括:
1. 目录和文件的权限管理
2. 敏感数据访问审计
3. 黄金样本(golden samples)保护
4. 防止意外修改的机制

支持跨平台(Windows/Linux/macOS)的权限管理。
"""

import os
import sys
import stat
import time
import json
import logging
import platform
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any, Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('security.access_control')

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 系统类型常量
WINDOWS = platform.system() == 'Windows'
LINUX = platform.system() == 'Linux'
MACOS = platform.system() == 'Darwin'

# 关键路径
GOLDEN_SAMPLES_DIR = PROJECT_ROOT / 'tests' / 'golden_samples'
SECURITY_LOGS_DIR = PROJECT_ROOT / 'logs' / 'security'
CONFIG_DIR = PROJECT_ROOT / 'configs'

# 确保日志目录存在
os.makedirs(SECURITY_LOGS_DIR, exist_ok=True)

class AccessControl:
    """访问控制管理器 - 提供文件权限和访问控制功能"""

    def __init__(self):
        """初始化访问控制管理器"""
        self.config = self._load_security_config()
        self.audit_logger = AuditLogger()
        
    def _load_security_config(self) -> Dict[str, Any]:
        """加载安全配置"""
        config_path = CONFIG_DIR / 'security_policy.yaml'
        if not config_path.exists():
            logger.warning(f"安全配置文件不存在: {config_path}")
            return {}
            
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载安全配置失败: {e}")
            return {}
    
    def secure_golden_samples(self, force: bool = False) -> bool:
        """
        确保黄金样本目录安全
        
        Args:
            force: 是否强制修改权限
            
        Returns:
            bool: 操作是否成功
        """
        logger.info("设置黄金样本目录的安全权限")
        
        if not GOLDEN_SAMPLES_DIR.exists():
            logger.error(f"黄金样本目录不存在: {GOLDEN_SAMPLES_DIR}")
            return False
        
        try:
            # 记录操作日志
            self.audit_logger.log_security_event(
                "ACCESS_CONTROL", 
                "设置黄金样本目录权限",
                {"path": str(GOLDEN_SAMPLES_DIR), "force": force}
            )
            
            # 根据平台设置不同的权限
            if WINDOWS:
                return self._secure_windows_directory(GOLDEN_SAMPLES_DIR, readonly=True, recursive=True)
            else:
                # Linux/macOS - 设置为只读权限 (550 - r-xr-x---)
                return self._secure_unix_directory(GOLDEN_SAMPLES_DIR, permission='550', recursive=True)
                
        except Exception as e:
            logger.error(f"设置黄金样本目录权限失败: {e}")
            return False
    
    def _secure_windows_directory(self, dir_path: Path, readonly: bool = True, recursive: bool = False) -> bool:
        """设置Windows目录的安全属性"""
        try:
            if not dir_path.exists():
                logger.warning(f"目录不存在: {dir_path}")
                return False
                
            # 设置目录属性
            if readonly:
                subprocess.run(['attrib', '+R', str(dir_path)], check=True)
            else:
                subprocess.run(['attrib', '-R', str(dir_path)], check=True)
                
            # 递归处理子目录和文件
            if recursive:
                for item in dir_path.glob('**/*'):
                    if item.is_file():
                        if readonly:
                            subprocess.run(['attrib', '+R', str(item)], check=True)
                        else:
                            subprocess.run(['attrib', '-R', str(item)], check=True)
            
            logger.info(f"目录 {dir_path} 权限设置成功，只读={readonly}")
            return True
            
        except Exception as e:
            logger.error(f"设置Windows目录权限失败 {dir_path}: {e}")
            return False
    
    def _secure_unix_directory(self, dir_path: Path, permission: str = '755', recursive: bool = False) -> bool:
        """设置Unix目录的安全权限"""
        try:
            if not dir_path.exists():
                logger.warning(f"目录不存在: {dir_path}")
                return False
                
            # 八进制字符串转整数
            mode = int(permission, 8)
            os.chmod(dir_path, mode)
            
            # 递归处理子目录和文件
            if recursive:
                for item in dir_path.glob('**/*'):
                    if item.is_file():
                        os.chmod(item, mode)
                    elif item.is_dir():
                        os.chmod(item, mode)
            
            logger.info(f"目录 {dir_path} 权限设置成功: {permission}")
            return True
            
        except Exception as e:
            logger.error(f"设置Unix目录权限失败 {dir_path}: {e}")
            return False
    
    def verify_golden_samples_integrity(self) -> Tuple[bool, List[str]]:
        """
        验证黄金样本的完整性
        
        Returns:
            Tuple[bool, List[str]]: (是否验证通过, 错误信息列表)
        """
        logger.info("验证黄金样本完整性")
        errors = []
        
        # 验证索引文件
        index_path = GOLDEN_SAMPLES_DIR / 'index.json'
        if not index_path.exists():
            errors.append(f"黄金样本索引文件不存在: {index_path}")
            return False, errors
            
        # 验证元数据文件
        metadata_path = GOLDEN_SAMPLES_DIR / 'metadata.json'
        if not metadata_path.exists():
            errors.append(f"黄金样本元数据文件不存在: {metadata_path}")
            return False, errors
            
        # 加载元数据
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            errors.append(f"读取元数据文件失败: {e}")
            return False, errors
            
        # 验证样本文件完整性
        samples = metadata.get('samples', [])
        for sample in samples:
            # 验证视频文件
            video_path = PROJECT_ROOT / sample.get('video_path', '')
            if not video_path.exists():
                errors.append(f"样本视频文件不存在: {video_path}")
                continue
                
            # 验证SRT文件
            srt_path = PROJECT_ROOT / sample.get('srt_path', '')
            if not srt_path.exists():
                errors.append(f"样本字幕文件不存在: {srt_path}")
                continue
                
            # 验证视频哈希值
            expected_video_hash = sample.get('video_hash')
            if expected_video_hash:
                actual_video_hash = self._calculate_file_hash(video_path)
                if actual_video_hash != expected_video_hash:
                    errors.append(f"视频文件哈希不匹配: {video_path}")
                    
            # 验证SRT哈希值
            expected_srt_hash = sample.get('srt_hash')
            if expected_srt_hash:
                actual_srt_hash = self._calculate_file_hash(srt_path)
                if actual_srt_hash != expected_srt_hash:
                    errors.append(f"字幕文件哈希不匹配: {srt_path}")
        
        # 记录审计日志
        self.audit_logger.log_security_event(
            "INTEGRITY", 
            "验证黄金样本完整性",
            {"success": len(errors) == 0, "errors_count": len(errors)}
        )
        
        if len(errors) == 0:
            logger.info("✓ 黄金样本完整性验证通过")
            return True, []
        else:
            logger.warning(f"✗ 黄金样本完整性验证失败，发现 {len(errors)} 个问题")
            return False, errors
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件的SHA-256哈希值"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # 逐块读取文件并更新哈希
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def configure_git_attributes(self) -> bool:
        """
        配置Git属性以增强安全性
        
        设置Git属性以防止意外修改黄金样本、在提交前进行文件完整性检查
        
        Returns:
            bool: 操作是否成功
        """
        try:
            logger.info("配置Git属性以增强安全性")
            
            # 配置黄金样本目录的Git属性
            cmd = f'echo "golden_samples/* -diff -merge -text" >> {PROJECT_ROOT / ".gitattributes"}'
            
            # 添加哈希检查过滤器
            cmd2 = f'echo "filter=hash" >> {PROJECT_ROOT / ".git/config"}'
            
            # 记录操作日志
            self.audit_logger.log_security_event(
                "CONFIG", 
                "配置Git属性",
                {"path": str(PROJECT_ROOT / ".gitattributes")}
            )
            
            logger.info("Git属性已更新，增强了黄金样本的安全性")
            return True
        
        except Exception as e:
            logger.error(f"配置Git属性失败: {e}")
            return False


class AuditLogger:
    """安全审计日志记录器"""
    
    def __init__(self):
        """初始化审计日志记录器"""
        self.log_file = SECURITY_LOGS_DIR / f"security_{datetime.now().strftime('%Y%m%d')}.log"
        
    def log_security_event(self, event_type: str, description: str, details: Dict[str, Any] = None) -> bool:
        """
        记录安全事件
        
        Args:
            event_type: 事件类型
            description: 事件描述
            details: 详细信息
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 创建日志条目
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "description": description,
                "user": os.getlogin() if hasattr(os, 'getlogin') else "unknown",
                "process_id": os.getpid(),
                "hostname": platform.node(),
                "platform": platform.system(),
                "details": details or {}
            }
            
            # 写入日志文件
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + "\n")
                
            return True
            
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")
            return False
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的安全事件
        
        Args:
            limit: 返回的事件数量限制
            
        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        events = []
        try:
            if not self.log_file.exists():
                return []
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        events.append(event)
                    except:
                        continue
                        
            # 按时间戳排序并限制数量
            events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return events[:limit]
            
        except Exception as e:
            logger.error(f"获取安全事件失败: {e}")
            return []


# 创建单例实例
_access_control_instance = None

def get_access_control() -> AccessControl:
    """获取访问控制单例实例"""
    global _access_control_instance
    if _access_control_instance is None:
        _access_control_instance = AccessControl()
    return _access_control_instance


# 方便函数
def secure_golden_samples(force: bool = False) -> bool:
    """确保黄金样本目录安全的快捷函数"""
    ac = get_access_control()
    return ac.secure_golden_samples(force)

def verify_golden_samples_integrity() -> Tuple[bool, List[str]]:
    """验证黄金样本完整性的快捷函数"""
    ac = get_access_control()
    return ac.verify_golden_samples_integrity()

def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器的快捷函数"""
    ac = get_access_control()
    return ac.audit_logger


# 如果直接运行此脚本，执行安全检查
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 安全访问控制")
    parser.add_argument("--secure", action="store_true", help="设置黄金样本目录的安全权限")
    parser.add_argument("--verify", action="store_true", help="验证黄金样本的完整性")
    parser.add_argument("--force", action="store_true", help="强制修改权限")
    parser.add_argument("--git-config", action="store_true", help="配置Git属性以增强安全性")
    args = parser.parse_args()
    
    access_control = get_access_control()
    
    if args.secure:
        access_control.secure_golden_samples(args.force)
        
    if args.verify:
        success, errors = access_control.verify_golden_samples_integrity()
        if not success:
            for error in errors:
                print(f"错误: {error}")
                
    if args.git_config:
        access_control.configure_git_attributes()
    
    # 如果没有提供任何参数，显示帮助信息
    if not (args.secure or args.verify or args.git_config):
        parser.print_help() 