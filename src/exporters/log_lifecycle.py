#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志生命周期管理整合模块

整合日志轮换、清理和存档功能，提供全面的日志生命周期管理。
与现有日志系统集成，确保日志文件不会无限增长。
"""

import os
import sys
import time
import threading
import datetime
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_temp_log_directory, get_archived_logs_directory, clean_old_logs
from src.exporters.log_rotator import LogRotator, LogRotationManager, get_log_rotation_manager, setup_standard_log_rotation
from src.exporters.log_writer import get_realtime_logger
from src.exporters.structured_logger import get_structured_logger
from src.exporters.log_fingerprint import fingerprint_log_file, process_active_logs, generate_log_summary
from src.exporters.log_crypto import encrypt_file, encrypt_archived_logs, check_crypto_available

# 模块日志记录器
logger = get_module_logger("log_lifecycle")

class LogLifecycleManager:
    """
    日志生命周期管理器
    
    提供日志文件的完整生命周期管理，包括创建、轮换、归档和清理。
    """
    
    def __init__(self, auto_setup: bool = True):
        """
        初始化日志生命周期管理器
        
        Args:
            auto_setup: 是否自动配置日志管理
        """
        # 获取日志轮换管理器
        self.rotation_manager = get_log_rotation_manager()
        
        # 定期清理线程
        self.cleanup_thread = None
        self.stop_event = threading.Event()
        
        # 指纹生成配置
        self.fingerprint_enabled = True
        self.auto_fingerprint = False
        self.fingerprint_interval = 86400  # 默认每天生成一次指纹
        self.last_fingerprint_time = 0
        
        # 归档加密配置
        self.encryption_enabled = True
        
        # 自动配置
        if auto_setup:
            self.setup()
            
    def setup(self) -> None:
        """设置标准日志管理"""
        # 配置标准日志轮换
        setup_standard_log_rotation()
        
        # 启动定期清理
        self.start_periodic_cleanup()
        
        # 配置指纹生成（可选）
        if self.auto_fingerprint:
            self.schedule_fingerprint_generation()
        
        # 检查加密功能可用性
        if self.encryption_enabled:
            self.encryption_enabled = check_crypto_available()
            if not self.encryption_enabled:
                logger.warning("加密功能不可用，已禁用日志归档加密")
        
        logger.info("日志生命周期管理已配置")
        
    def start_periodic_cleanup(self, 
                              interval_days: int = 1, 
                              retention_days: int = 30) -> None:
        """
        启动定期清理线程
        
        Args:
            interval_days: 清理间隔（天）
            retention_days: 日志保留时间（天）
        """
        if self.cleanup_thread is not None and self.cleanup_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(interval_days, retention_days),
            daemon=True,
            name="LogCleanupThread"
        )
        self.cleanup_thread.start()
        logger.info(f"已启动定期日志清理（间隔: {interval_days}天, 保留: {retention_days}天）")
        
    def stop_periodic_cleanup(self) -> None:
        """停止定期清理线程"""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            return
            
        self.stop_event.set()
        self.cleanup_thread.join(timeout=5.0)
        logger.info("日志清理线程已停止")
        
    def _cleanup_loop(self, interval_days: int, retention_days: int) -> None:
        """清理线程主循环"""
        while not self.stop_event.is_set():
            try:
                # 执行清理
                deleted_count = self.cleanup_old_logs(retention_days)
                logger.info(f"定期日志清理已完成，删除了 {deleted_count} 个过期日志文件")
                
                # 等待下一次清理
                # 将天数转换为秒
                interval_seconds = interval_days * 86400
                
                # 分段睡眠，以便能够及时响应停止信号
                for _ in range(int(interval_seconds / 10)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"日志清理线程发生错误: {str(e)}")
                # 出错后等待一段时间再重试
                time.sleep(3600)  # 1小时
                
    def cleanup_old_logs(self, max_age_days: int = 30) -> int:
        """
        清理所有过期日志
        
        Args:
            max_age_days: 日志保留最大天数
            
        Returns:
            已删除的文件数量
        """
        # 使用log_path模块的清理功能
        deleted_count = clean_old_logs(max_age_days)
        
        # 清理备份目录中的旧文件
        backup_deleted = self._cleanup_old_backups(max_age_days)
        
        return deleted_count + backup_deleted
        
    def _cleanup_old_backups(self, max_age_days: int) -> int:
        """清理过期的备份文件"""
        import time
        
        log_dir = get_log_directory()
        deleted_count = 0
        
        # 计算截止时间
        cutoff_time = time.time() - (max_age_days * 86400)
        
        # 查找所有备份目录
        backup_dirs = []
        backup_dirs.append(log_dir / "backups")
        
        # 遍历子目录寻找更多备份目录
        for subdir in log_dir.glob("**/backups"):
            backup_dirs.append(subdir)
            
        # 清理所有备份目录
        for backup_dir in backup_dirs:
            if not backup_dir.exists():
                continue
                
            for backup_file in backup_dir.glob("*"):
                if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_time:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.debug(f"删除过期备份文件: {backup_file}")
                    except Exception as e:
                        logger.warning(f"无法删除备份文件 {backup_file}: {e}")
                        
        return deleted_count
        
    def archive_logs(self, 
                    target_dir: Optional[Union[str, Path]] = None, 
                    days_to_archive: int = 30,
                    encrypt_archives: bool = True) -> Optional[Dict[str, Any]]:
        """
        归档日志文件
        
        将超过指定天数的日志文件归档到指定目录，并进行加密保护
        
        Args:
            target_dir: 归档目标目录
            days_to_archive: 归档超过多少天的日志
            encrypt_archives: 是否启用归档加密
            
        Returns:
            归档结果信息
        """
        # 检查加密功能是否可用
        encryption_available = self.encryption_enabled and check_crypto_available()
        
        # 如果要求加密但不可用，记录警告
        if encrypt_archives and not encryption_available:
            logger.warning("加密功能不可用，将以未加密方式归档")
            encrypt_archives = False
        
        # 默认归档目录
        if target_dir is None:
            if encrypt_archives:
                target_dir = get_archived_logs_directory()
            else:
                target_dir = get_log_directory() / "archives" / "plain"
        else:
            target_dir = Path(target_dir)
            
        # 确保目录存在
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志目录
        log_dir = get_log_directory()
        
        # 创建归档文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 计算截止时间
        cutoff_time = time.time() - (days_to_archive * 86400)
        
        # 查找所有符合条件的日志文件
        log_files = []
        for log_file in log_dir.glob("**/*"):
            if (log_file.is_file() and
                log_file.stat().st_mtime < cutoff_time and
                not str(log_file).startswith(str(target_dir)) and
                not log_file.name.endswith(".enc")):  # 排除已加密文件
                log_files.append(log_file)
                
        if not log_files:
            logger.info("没有符合归档条件的日志文件")
            return {"status": "no_files", "count": 0}
        
        archive_results = {
            "timestamp": timestamp,
            "encrypted": encrypt_archives,
            "total_files": len(log_files),
            "processed_files": 0,
            "archived_files": [],
            "encrypted_files": [],
            "errors": []
        }
        
        # 处理每个日志文件
        for log_file in log_files:
            try:
                # 计算相对路径，保持目录结构
                rel_path = log_file.relative_to(log_dir)
                target_subdir = target_dir / rel_path.parent
                target_subdir.mkdir(parents=True, exist_ok=True)
                
                # 目标文件路径
                target_file = target_subdir / f"{log_file.stem}_{timestamp}{log_file.suffix}"
                
                # 先将文件复制到归档目录
                shutil.copy2(log_file, target_file)
                archive_results["archived_files"].append(str(target_file))
                
                # 如果需要加密
                if encrypt_archives:
                    encrypted_file = encrypt_file(
                        target_file, 
                        output_path=target_file.with_suffix(target_file.suffix + ".enc"),
                        delete_original=True
                    )
                    if encrypted_file:
                        archive_results["encrypted_files"].append(str(encrypted_file))
                        logger.debug(f"已加密归档日志: {encrypted_file}")
                    else:
                        archive_results["errors"].append({
                            "file": str(target_file),
                            "error": "加密失败"
                        })
                        logger.error(f"无法加密日志文件 {target_file}")
                
                # 删除原始日志文件
                log_file.unlink()
                archive_results["processed_files"] += 1
                
            except Exception as e:
                logger.error(f"处理日志文件 {log_file} 时出错: {str(e)}")
                archive_results["errors"].append({
                    "file": str(log_file),
                    "error": str(e)
                })
        
        # 记录归档结果
        logger.info(f"日志归档完成: 处理了 {archive_results['processed_files']} 个文件, "
                   f"加密 {len(archive_results['encrypted_files'])} 个文件, "
                   f"错误 {len(archive_results['errors'])} 个")
        
        return archive_results
        
    def encrypt_archived_logs(self, days: int = 30) -> Dict[str, Any]:
        """
        加密归档日志
        
        对已归档但未加密的日志文件进行加密处理
        
        Args:
            days: 处理几天前的日志
            
        Returns:
            加密结果信息
        """
        if not self.encryption_enabled:
            logger.warning("加密功能已禁用，无法加密归档日志")
            return {"status": "encryption_disabled"}
            
        # 检查加密功能是否可用
        if not check_crypto_available():
            logger.error("加密功能不可用，无法加密归档日志")
            return {"status": "encryption_unavailable"}
            
        # 执行加密
        try:
            results = encrypt_archived_logs(days)
            
            # 统计结果
            status = {
                "status": "success",
                "total": len(results),
                "success": sum(1 for v in results.values() if not v.startswith("错误") and not v == "加密失败"),
                "failed": sum(1 for v in results.values() if v.startswith("错误") or v == "加密失败"),
                "details": results
            }
            
            logger.info(f"归档日志加密完成: 总计 {status['total']} 个文件, "
                       f"成功 {status['success']} 个, 失败 {status['failed']} 个")
            
            return status
        except Exception as e:
            logger.error(f"归档日志加密过程中出错: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
        
    def get_log_stats(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        生成所有日志文件的统计信息，包括大小、数量、时间范围等
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_size": 0,
            "file_count": 0,
            "error_logs": 0,
            "newest_log": None,
            "oldest_log": None,
            "fingerprinted_logs": 0,
            "encrypted_logs": 0,
            "fingerprint_enabled": self.fingerprint_enabled,
            "encryption_enabled": self.encryption_enabled,
            "detailed_logs": []
        }
        
        # 日志目录
        log_dir = get_log_directory()
        
        oldest_time = time.time()
        newest_time = 0
        oldest_file = None
        newest_file = None
        
        # 遍历所有日志文件
        for log_file in log_dir.glob("**/*"):
            if not log_file.is_file():
                continue
                
            # 更新总计数
            stats["file_count"] += 1
            
            # 获取文件大小
            file_size = log_file.stat().st_size
            stats["total_size"] += file_size
            
            # 检查最旧/最新文件
            file_mtime = log_file.stat().st_mtime
            if file_mtime < oldest_time:
                oldest_time = file_mtime
                oldest_file = log_file
                
            if file_mtime > newest_time:
                newest_time = file_mtime
                newest_file = log_file
                
            # 检查是否是指纹版本
            is_fingerprinted = "fingerprinted" in log_file.name
            if is_fingerprinted:
                stats["fingerprinted_logs"] += 1
                
            # 检查是否是加密版本
            is_encrypted = log_file.name.endswith(".enc")
            if is_encrypted:
                stats["encrypted_logs"] += 1
                
            # 获取日志摘要
            try:
                summary = generate_log_summary(log_file)
                stats["detailed_logs"].append(summary)
            except Exception as e:
                stats["error_logs"] += 1
                stats["detailed_logs"].append({"summary_error": str(e)})
            
        # 更新最旧/最新文件
        if oldest_file is not None:
            stats["oldest_log"] = {
                "path": str(oldest_file.relative_to(log_dir)),
                "time": datetime.datetime.fromtimestamp(oldest_time).isoformat(),
                "age_days": (time.time() - oldest_time) / 86400
            }
            
        if newest_file is not None:
            stats["newest_log"] = {
                "path": str(newest_file.relative_to(log_dir)),
                "time": datetime.datetime.fromtimestamp(newest_time).isoformat()
            }
            
        # 添加人类可读的总大小
        stats["total_size_human"] = self._format_size(stats["total_size"])
        
        return stats
    
    def _format_size(self, size_bytes: int) -> str:
        """将字节大小格式化为人类可读的形式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
            
    def shutdown(self) -> None:
        """关闭日志生命周期管理器"""
        # 停止清理线程
        self.stop_event.set()
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
            
        # 停止指纹生成线程
        if hasattr(self, 'fingerprint_thread') and self.fingerprint_thread and self.fingerprint_thread.is_alive():
            self.fingerprint_thread.join(timeout=5.0)
            
        # 关闭轮换管理器
        self.rotation_manager.shutdown()
        
        logger.info("日志生命周期管理器已关闭")

    def schedule_fingerprint_generation(self, interval_seconds: int = None) -> None:
        """
        安排定期生成日志指纹
        
        Args:
            interval_seconds: 指纹生成间隔（秒）
        """
        if interval_seconds is not None:
            self.fingerprint_interval = interval_seconds
            
        # 创建线程
        self.fingerprint_thread = threading.Thread(
            target=self._fingerprint_loop,
            daemon=True,
            name="LogFingerprintThread"
        )
        self.fingerprint_thread.start()
        logger.info(f"已安排定期日志指纹生成（间隔: {self.fingerprint_interval}秒）")
    
    def _fingerprint_loop(self) -> None:
        """日志指纹生成线程主循环"""
        while not self.stop_event.is_set():
            try:
                # 检查是否需要生成指纹
                now = time.time()
                if now - self.last_fingerprint_time >= self.fingerprint_interval:
                    # 生成日志指纹
                    results = process_active_logs()
                    self.last_fingerprint_time = now
                    logger.info(f"定期日志指纹生成已完成，处理了 {len(results)} 个日志文件")
                
                # 等待一段时间
                # 分段睡眠，以便能够及时响应停止信号
                for _ in range(min(60, int(self.fingerprint_interval / 10))):
                    if self.stop_event.is_set():
                        break
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"日志指纹生成线程发生错误: {str(e)}")
                # 出错后等待一段时间再重试
                time.sleep(3600)  # 1小时
    
    def generate_fingerprints_now(self, output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
        """
        立即为活动日志生成指纹
        
        Args:
            output_dir: 输出目录
            
        Returns:
            处理结果字典
        """
        if not self.fingerprint_enabled:
            logger.warning("日志指纹功能已禁用")
            return {}
            
        try:
            results = process_active_logs(output_dir)
            self.last_fingerprint_time = time.time()
            return results
        except Exception as e:
            logger.error(f"生成日志指纹时出错: {str(e)}")
            return {"error": str(e)}


# 全局日志生命周期管理器
_lifecycle_manager = None

def get_log_lifecycle_manager() -> LogLifecycleManager:
    """
    获取全局日志生命周期管理器
    
    Returns:
        日志生命周期管理器实例
    """
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = LogLifecycleManager()
    return _lifecycle_manager

def init_log_lifecycle() -> None:
    """初始化日志生命周期管理"""
    manager = get_log_lifecycle_manager()
    # 配置已经在构造函数中完成
    
def shutdown_log_lifecycle() -> None:
    """关闭日志生命周期管理"""
    global _lifecycle_manager
    if _lifecycle_manager is not None:
        _lifecycle_manager.shutdown()
        _lifecycle_manager = None


if __name__ == "__main__":
    # 测试代码
    
    # 初始化日志生命周期管理
    manager = LogLifecycleManager()
    
    # 获取日志统计信息
    stats = manager.get_log_stats()
    
    print("日志统计信息:")
    print(f"总文件数: {stats['file_count']}")
    print(f"总大小: {stats['total_size_human']}")
    print(f"指纹日志: {stats['fingerprinted_logs']}")
    print(f"加密日志: {stats['encrypted_logs']}")
    
    if stats.get('oldest_log'):
        print(f"最旧文件: {stats['oldest_log']['path']}, 时间: {stats['oldest_log']['time']}")
        print(f"文件年龄: {stats['oldest_log']['age_days']:.1f} 天")
        
    if stats.get('newest_log'):
        print(f"最新文件: {stats['newest_log']['path']}, 时间: {stats['newest_log']['time']}")
    
    # 测试日志加密归档
    print("\n测试日志归档加密...")
    result = manager.archive_logs(days_to_archive=30, encrypt_archives=True)
    print(f"归档结果: 处理了 {result.get('processed_files', 0)} 个文件")
    print(f"加密文件数: {len(result.get('encrypted_files', []))}")
    
    # 关闭管理器
    manager.shutdown()
    print("测试完成") 