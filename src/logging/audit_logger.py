#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 合规性审计日志记录器

提供合规性事件的记录功能，确保日志的不可篡改性和完整性。
主要功能：
- 记录法律和合规事件
- 使用区块链式结构确保日志不可篡改
- 支持日志验证和完整性检查
- 支持多种日志存储格式（JSON, SQLite）
- 提供时间戳和加密哈希验证
"""

import os
import sys
import json
import time
import hashlib
import hmac
import sqlite3
import datetime
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from threading import Lock

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# 尝试导入项目日志模块
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("audit_logger")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("audit_logger")

# 审计日志文件目录
AUDIT_LOGS_DIR = PROJECT_ROOT / "logs" / "audit"
# 确保日志目录存在
AUDIT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# 设定常量
DEFAULT_SECRET_KEY = "VisionAI-ClipsMaster-Audit-Key"
HASH_ALGORITHM = 'sha256'  # 使用SHA-256算法
DATABASE_FILENAME = "audit_immutable.db"


class AuditLogger:
    """合规性审计日志记录器"""

    # 单例模式实例
    _instance = None
    _lock = Lock()  # 线程安全锁

    def __new__(cls, *args, **kwargs):
        """实现单例模式，确保全局只有一个记录器实例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuditLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, secret_key: str = None, storage_type: str = "both"):
        """
        初始化审计日志记录器
        
        Args:
            secret_key: 用于HMAC签名的密钥，为None时使用环境变量或默认密钥
            storage_type: 存储类型，可选值："json", "db", "both"
        """
        # 防止单例模式下重复初始化
        if getattr(self, '_initialized', False):
            return

        # 设置签名密钥
        self.secret_key = secret_key
        if not self.secret_key:
            self.secret_key = os.environ.get("AUDIT_SECRET_KEY", DEFAULT_SECRET_KEY)
        
        # 验证存储类型
        valid_types = ["json", "db", "both"]
        if storage_type not in valid_types:
            logger.warning(f"无效的存储类型: {storage_type}，使用默认值 'both'")
            storage_type = "both"
        self.storage_type = storage_type

        # 设置日志文件名（按年月日命名）
        now = datetime.datetime.now()
        self.date_prefix = now.strftime('%Y%m%d')
        self.json_log_file = AUDIT_LOGS_DIR / f"audit_{self.date_prefix}.json"
        self.db_file = AUDIT_LOGS_DIR / DATABASE_FILENAME
        
        # 初始化数据库（如果使用）
        if storage_type in ["db", "both"]:
            self._init_database()
        
        # 上一条日志的哈希值（区块链结构的前一块）
        self.last_hash = self._get_last_hash()
        
        # 创建会话ID
        self.session_id = str(uuid.uuid4())
        
        # 记录日志计数
        self.log_count = 0
        
        # 标记为已初始化
        self._initialized = True
        
        # 记录初始化事件
        self.log_system_event("INIT", "审计日志系统初始化")
        logger.info(f"审计日志记录器初始化完成，存储类型: {storage_type}")

    def _init_database(self) -> None:
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()
            
            # 创建审计日志表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                signature TEXT NOT NULL,
                session_id TEXT NOT NULL
            );
            ''')
            
            # 创建索引提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_logs(event_type);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON audit_logs(session_id);')
            
            conn.commit()
            conn.close()
            logger.info(f"审计数据库初始化完成: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"初始化审计数据库失败: {e}")
            raise

    def _get_last_hash(self) -> str:
        """
        获取最后一条日志的哈希值
        
        Returns:
            str: 最后一条日志的哈希值，如果没有则使用"0"（创世块）
        """
        # 默认哈希值（类似区块链的创世块）
        genesis_hash = "0" * 64
        
        if self.storage_type in ["db", "both"] and self.db_file.exists():
            try:
                conn = sqlite3.connect(str(self.db_file))
                cursor = conn.cursor()
                cursor.execute('SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1;')
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    return result[0]
            except sqlite3.Error as e:
                logger.error(f"从数据库获取最后哈希值失败: {e}")
        
        if self.storage_type in ["json", "both"] and self.json_log_file.exists():
            try:
                with open(self.json_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        pass  # 移动到最后一行
                    
                    # 读取最后一行并解析JSON
                    last_entry = json.loads(line.strip())
                    if 'hash' in last_entry:
                        return last_entry['hash']
            except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
                logger.error(f"从JSON文件获取最后哈希值失败: {e}")
        
        return genesis_hash

    def _compute_hash(self, data_str: str, prev_hash: str) -> str:
        """
        计算数据的哈希值
        
        采用区块链式结构，将当前数据与前一个哈希值组合后计算
        
        Args:
            data_str: 要计算哈希的数据字符串
            prev_hash: 前一个区块的哈希值
            
        Returns:
            str: 计算得到的哈希值
        """
        # 组合数据和前一个哈希值
        combined = f"{data_str}|{prev_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def _sign_data(self, data_hash: str) -> str:
        """
        使用HMAC对哈希值进行签名
        
        Args:
            data_hash: 数据哈希值
            
        Returns:
            str: HMAC签名（十六进制表示）
        """
        h = hmac.new(
            self.secret_key.encode('utf-8'),
            data_hash.encode('utf-8'),
            HASH_ALGORITHM
        )
        return h.hexdigest()

    def log_legal_event(self, event_type: str, detail: str) -> Dict[str, Any]:
        """
        记录关联法律事件
        
        Args:
            event_type: 事件类型
            detail: 详细信息
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        # 构造日志条目
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": event_type,
            "detail": detail,
            "hash": None,  # 稍后计算
            "previous_hash": self.last_hash,
            "signature": None,  # 稍后计算
            "session_id": self.session_id,
        }
        
        # 序列化数据并计算哈希
        data_str = json.dumps({k: v for k, v in entry.items() if k not in ['hash', 'signature']}, sort_keys=True)
        entry["hash"] = self._compute_hash(data_str, self.last_hash)
        
        # 签名
        entry["signature"] = self._sign_data(entry["hash"])
        
        # 更新最后的哈希值
        self.last_hash = entry["hash"]
        
        # 增加计数
        self.log_count += 1
        
        # 存储日志
        self._store_entry(entry)
        
        return entry

    def _store_entry(self, entry: Dict[str, Any]) -> None:
        """
        存储日志条目到相应的存储系统
        
        Args:
            entry: 日志条目
        """
        # JSON文件存储
        if self.storage_type in ["json", "both"]:
            try:
                with open(self.json_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except IOError as e:
                logger.error(f"写入JSON日志文件失败: {e}")
        
        # 数据库存储
        if self.storage_type in ["db", "both"]:
            try:
                conn = sqlite3.connect(str(self.db_file))
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO audit_logs 
                (timestamp, event_type, detail, hash, previous_hash, signature, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                ''', (
                    entry["timestamp"],
                    entry["type"],
                    entry["detail"],
                    entry["hash"],
                    entry["previous_hash"],
                    entry["signature"],
                    entry["session_id"]
                ))
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"写入数据库失败: {e}")

    def log_system_event(self, event_type: str, detail: str) -> Dict[str, Any]:
        """
        记录系统事件
        
        Args:
            event_type: 事件类型
            detail: 详细信息
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        return self.log_legal_event(f"SYSTEM_{event_type}", detail)

    def log_user_operation(self, operation: str, detail: str, user_id: str = None) -> Dict[str, Any]:
        """
        记录用户操作
        
        Args:
            operation: 操作类型
            detail: 详细信息
            user_id: 用户ID，为None时使用系统用户
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        user = user_id or os.environ.get('USERNAME', 'unknown')
        detail_with_user = f"User: {user}, {detail}"
        return self.log_legal_event(f"USER_{operation}", detail_with_user)

    def log_regulatory_event(self, regulation: str, action: str, detail: str) -> Dict[str, Any]:
        """
        记录监管相关事件
        
        Args:
            regulation: 法规名称（如"GDPR", "PIPL"等）
            action: 执行的操作
            detail: 详细信息
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        return self.log_legal_event(f"REGULATORY_{regulation}_{action}", detail)

    def log_content_filtered(self, content_type: str, filter_reason: str, detail: str) -> Dict[str, Any]:
        """
        记录内容过滤事件
        
        Args:
            content_type: 内容类型（如视频、音频、文本等）
            filter_reason: 过滤原因
            detail: 详细信息
            
        Returns:
            Dict[str, Any]: 记录的日志条目
        """
        return self.log_legal_event(f"FILTER_{content_type}", f"Reason: {filter_reason}, Detail: {detail}")

    def verify_log_integrity(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        验证日志完整性
        
        使用区块链式结构验证日志是否被篡改
        
        Args:
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: (是否完整, 问题日志列表)
        """
        issues = []
        
        # 验证数据库日志（如果启用）
        if self.storage_type in ["db", "both"] and self.db_file.exists():
            try:
                conn = sqlite3.connect(str(self.db_file))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建查询条件
                query = "SELECT * FROM audit_logs ORDER BY id ASC"
                cursor.execute(query)
                
                rows = cursor.fetchall()
                prev_hash = "0" * 64  # 创世块哈希
                
                for i, row in enumerate(rows):
                    row_dict = dict(row)
                    
                    # 验证前一个哈希是否正确链接
                    if row_dict["previous_hash"] != prev_hash:
                        issues.append({
                            "index": i,
                            "hash": row_dict["hash"],
                            "issue": "断链",
                            "expected_prev": prev_hash,
                            "actual_prev": row_dict["previous_hash"]
                        })
                    
                    # 验证哈希值是否正确
                    data_for_hash = {k: v for k, v in row_dict.items() 
                                    if k not in ['hash', 'signature', 'id']}
                    data_str = json.dumps(data_for_hash, sort_keys=True)
                    computed_hash = self._compute_hash(data_str, row_dict["previous_hash"])
                    
                    if computed_hash != row_dict["hash"]:
                        issues.append({
                            "index": i,
                            "hash": row_dict["hash"],
                            "issue": "哈希不匹配",
                            "computed_hash": computed_hash
                        })
                    
                    # 验证签名
                    computed_signature = self._sign_data(row_dict["hash"])
                    if computed_signature != row_dict["signature"]:
                        issues.append({
                            "index": i,
                            "hash": row_dict["hash"],
                            "issue": "签名不匹配",
                            "computed_signature": computed_signature
                        })
                    
                    # 更新前一个哈希
                    prev_hash = row_dict["hash"]
                
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"验证数据库日志完整性失败: {e}")
                issues.append({"issue": f"数据库错误: {str(e)}"})
        
        # 如果没有问题，则完整性验证通过
        return len(issues) == 0, issues

    def query_logs(self, event_type: Optional[str] = None, start_date: Optional[str] = None, 
                 end_date: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        查询日志记录
        
        Args:
            event_type: 事件类型过滤
            start_date: 开始日期（ISO格式）
            end_date: 结束日期（ISO格式）
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        results = []
        
        # 从数据库查询
        if self.storage_type in ["db", "both"] and self.db_file.exists():
            try:
                conn = sqlite3.connect(str(self.db_file))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 构建查询条件
                query = "SELECT * FROM audit_logs WHERE 1=1"
                params = []
                
                if event_type:
                    query += " AND event_type LIKE ?"
                    params.append(f"%{event_type}%")
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    results.append(dict(row))
                
                conn.close()
                
            except sqlite3.Error as e:
                logger.error(f"查询数据库日志失败: {e}")
        
        return results

    def export_logs(self, output_file: Optional[str] = None, format: str = "json") -> Optional[str]:
        """
        导出日志
        
        Args:
            output_file: 输出文件路径，为None时使用默认路径
            format: 导出格式，支持"json"和"csv"
            
        Returns:
            str: 导出文件路径，失败时返回None
        """
        # 设置默认输出文件
        if output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(AUDIT_LOGS_DIR / f"audit_export_{timestamp}.{format}")
        
        # 获取所有日志
        logs = self.query_logs(limit=10000)
        
        try:
            if format == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    if logs:
                        # 使用第一条日志的键作为表头
                        fieldnames = logs[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(logs)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return None
                
            logger.info(f"日志导出成功：{output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            return None

    def write_to_immutable_db(self, entry: Dict[str, Any]) -> bool:
        """
        将日志条目写入不可变存储
        
        此方法可以扩展为写入区块链或其他不可变存储
        
        Args:
            entry: 日志条目
            
        Returns:
            bool: 是否成功
        """
        try:
            # 当前实现仅记录到本地文件和数据库
            # 可以扩展为连接到区块链或其他不可变存储
            
            # 记录哈希到哈希链文件
            hash_chain_file = AUDIT_LOGS_DIR / "hash_chain.txt"
            with open(hash_chain_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry['timestamp']}|{entry['hash']}|{entry['previous_hash']}\n")
            
            return True
        except Exception as e:
            logger.error(f"写入不可变存储失败: {e}")
            return False
   
    
# 便捷函数
def get_audit_logger() -> AuditLogger:
    """
    获取审计日志记录器实例
    
    Returns:
        AuditLogger: 审计日志记录器实例
    """
    return AuditLogger()


def log_legal_event(event_type: str, detail: str) -> Dict[str, Any]:
    """
    记录法律事件的便捷函数
    
    Args:
        event_type: 事件类型
        detail: 详细信息
        
    Returns:
        Dict[str, Any]: 记录的日志条目
    """
    audit_logger = get_audit_logger()
    return audit_logger.log_legal_event(event_type, detail)


def verify_audit_integrity() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    验证审计日志完整性的便捷函数
    
    Returns:
        Tuple[bool, List[Dict[str, Any]]]: (是否完整, 问题日志列表)
    """
    audit_logger = get_audit_logger()
    return audit_logger.verify_log_integrity()


# 如果直接运行此脚本，执行简单的测试
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 审计日志记录器")
    parser.add_argument("--test", action="store_true", help="运行简单测试")
    parser.add_argument("--verify", action="store_true", help="验证日志完整性")
    parser.add_argument("--export", action="store_true", help="导出日志")
    args = parser.parse_args()
    
    logger.info("审计日志记录器测试")
    
    # 创建记录器实例
    audit_logger = get_audit_logger()
    
    if args.test:
        # 记录一些测试事件
        audit_logger.log_legal_event("TEST", "测试事件1")
        audit_logger.log_legal_event("TEST", "测试事件2")
        audit_logger.log_system_event("STARTUP", "系统启动")
        audit_logger.log_user_operation("LOGIN", "用户登录")
        audit_logger.log_regulatory_event("GDPR", "DATA_ACCESS", "用户请求数据访问")
        audit_logger.log_content_filtered("VIDEO", "INAPPROPRIATE", "不适当内容已过滤")
        
        logger.info("测试事件已记录")
    
    if args.verify:
        # 验证日志完整性
        success, issues = audit_logger.verify_log_integrity()
        if success:
            logger.info("✓ 日志完整性验证通过！")
        else:
            logger.warning(f"✗ 日志完整性验证失败，发现 {len(issues)} 个问题")
            for issue in issues:
                logger.warning(f"问题: {issue}")
    
    if args.export:
        # 导出日志
        export_path = audit_logger.export_logs()
        if export_path:
            logger.info(f"日志已导出至: {export_path}")
    
    # 如果没有提供任何参数，显示帮助信息
    if not (args.test or args.verify or args.export):
        parser.print_help() 