#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全审计追踪模块

该模块提供安全审计追踪功能，记录和监控系统中的关键操作，
特别是敏感数据访问、模型参数调整以及日志查看等高风险操作。
支持详细的操作记录、安全存储和审计报告生成。
"""

import os
import sys
import json
import time
import hmac
import hashlib
import datetime
import logging
import traceback
import threading
from pathlib import Path
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import re
import csv

# 导入请求处理模块（如果在Web环境中使用）
try:
    from flask import request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    request = None

# 设置模块日志
logger = logging.getLogger(__name__)

class AuditLevel(str, Enum):
    """审计级别枚举"""
    LOW = "low"          # 低风险操作
    MEDIUM = "medium"    # 中风险操作
    HIGH = "high"        # 高风险操作
    CRITICAL = "critical"  # 关键风险操作

class AuditCategory(str, Enum):
    """审计类别枚举"""
    DATA_ACCESS = "data_access"           # 数据访问
    MODEL_OPERATION = "model_operation"   # 模型操作
    LOG_VIEW = "log_view"                 # 日志查看
    PARAMETER_CHANGE = "parameter_change" # 参数变更
    SYSTEM_CONFIG = "system_config"       # 系统配置
    EXPORT_OPERATION = "export_operation" # 导出操作
    USER_MANAGEMENT = "user_management"   # 用户管理
    SECURITY_EVENT = "security_event"     # 安全事件

class AuditTrail:
    """
    审计追踪类
    
    提供安全审计日志记录、存储和查询功能，确保系统操作可追溯性和合规性。
    """
    
    def __init__(self, log_dir: Optional[str] = None, 
                key: Optional[str] = None,
                enable_encryption: bool = True):
        """
        初始化审计追踪系统
        
        Args:
            log_dir: 审计日志存储目录，默认为 logs/audit
            key: 用于签名和验证的密钥，默认自动生成
            enable_encryption: 是否启用日志加密
        """
        # 设置日志目录
        self.log_dir = log_dir or os.path.join("logs", "audit")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 设置签名密钥
        self.key = key or os.environ.get("AUDIT_KEY", self._generate_default_key())
        
        # 启用加密
        self.enable_encryption = enable_encryption
        
        # 检查是否有线程本地存储
        self.thread_local = threading.local()
        
        # 初始化日志文件
        self.current_log_file = self._get_log_file_path()
        
        # 启动时记录系统信息
        self._log_system_startup()
    
    def _generate_default_key(self) -> str:
        """
        生成默认签名密钥
        
        Returns:
            生成的密钥
        """
        # 生成一个基于当前环境的唯一密钥
        base = f"VisionAI-ClipsMaster-{os.getpid()}-{time.time()}"
        return hashlib.sha256(base.encode()).hexdigest()
    
    def _get_log_file_path(self) -> str:
        """
        获取当前日志文件路径
        
        Returns:
            日志文件路径
        """
        # 按日期生成日志文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        return os.path.join(self.log_dir, f"audit-{today}.log")
    
    def _log_system_startup(self):
        """记录系统启动信息"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": AuditCategory.SYSTEM_CONFIG,
            "level": AuditLevel.MEDIUM,
            "action": "system_startup",
            "details": {
                "process_id": os.getpid(),
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
        self.secure_append(entry)
    
    def log_view_action(self, user, action):
        """
        记录查看操作审计日志
        
        Args:
            user: 用户对象或ID
            action: 操作类型
        """
        # 构造基本日志条目
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user.id if hasattr(user, 'id') else user,
            "action": action,
            "query_params": request.params if HAS_FLASK and request else {}
        }
        
        # 安全写入日志
        self.secure_append(entry)
        
        # 返回记录的条目，便于进一步处理
        return entry
    
    def log_data_access(self, user, data_type: str, resource_id: str, 
                      operation: str, extra_details: Dict[str, Any] = None):
        """
        记录数据访问操作
        
        Args:
            user: 用户对象或ID
            data_type: 数据类型（如 'video', 'subtitle', 'model'）
            resource_id: 资源标识符
            operation: 操作类型（如 'view', 'download', 'edit'）
            extra_details: 附加详情
        """
        # 确定审计级别
        level = self._determine_data_access_level(data_type, operation)
        
        # 构造详细日志条目
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": AuditCategory.DATA_ACCESS,
            "level": level,
            "user": user.id if hasattr(user, 'id') else user,
            "action": f"{operation}_{data_type}",
            "details": {
                "data_type": data_type,
                "resource_id": resource_id,
                "operation": operation,
                "client_ip": self._get_client_ip(),
                "user_agent": self._get_user_agent()
            }
        }
        
        # 添加额外详情
        if extra_details:
            entry["details"].update(extra_details)
        
        # 安全写入日志
        self.secure_append(entry)
    
    def log_model_operation(self, user, model_name: str, operation: str, 
                         parameters: Dict[str, Any] = None):
        """
        记录模型操作
        
        Args:
            user: 用户对象或ID
            model_name: 模型名称
            operation: 操作类型（如 'load', 'unload', 'inference'）
            parameters: 操作参数
        """
        # 构造日志条目
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": AuditCategory.MODEL_OPERATION,
            "level": AuditLevel.MEDIUM,
            "user": user.id if hasattr(user, 'id') else user,
            "action": f"{operation}_model",
            "details": {
                "model_name": model_name,
                "operation": operation,
                "parameters": parameters or {}
            }
        }
        
        # 安全写入日志
        self.secure_append(entry)
    
    def log_parameter_change(self, user, param_name: str, old_value: Any, 
                          new_value: Any, component: str = None):
        """
        记录参数变更
        
        Args:
            user: 用户对象或ID
            param_name: 参数名称
            old_value: 旧值
            new_value: 新值
            component: 组件名称
        """
        # 构造日志条目
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": AuditCategory.PARAMETER_CHANGE,
            "level": AuditLevel.HIGH,
            "user": user.id if hasattr(user, 'id') else user,
            "action": "parameter_change",
            "details": {
                "param_name": param_name,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "component": component
            }
        }
        
        # 安全写入日志
        self.secure_append(entry)
    
    def secure_append(self, entry: Dict[str, Any]):
        """
        安全地将审计条目追加到日志文件
        
        Args:
            entry: 审计日志条目
        """
        # 添加记录ID和签名
        entry_id = self._generate_entry_id()
        entry["id"] = entry_id
        
        # 计算条目签名
        entry_json = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        signature = self._sign_entry(entry_json)
        
        # 如果启用加密，则对内容进行加密
        if self.enable_encryption:
            encrypted_entry = self._encrypt_entry(entry_json)
            log_line = json.dumps({
                "id": entry_id,
                "encrypted": True,
                "data": encrypted_entry,
                "signature": signature
            })
        else:
            entry["signature"] = signature
            log_line = json.dumps(entry, ensure_ascii=False)
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.current_log_file), exist_ok=True)
        
        # 追加到日志文件
        with open(self.current_log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    def _generate_entry_id(self) -> str:
        """
        生成唯一的条目ID
        
        Returns:
            条目ID
        """
        # 使用时间戳和随机数组合生成唯一ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        random_part = os.urandom(4).hex()
        return f"{timestamp}-{random_part}"
    
    def _sign_entry(self, entry_json: str) -> str:
        """
        对日志条目生成签名
        
        Args:
            entry_json: 条目JSON字符串
            
        Returns:
            生成的签名
        """
        # 使用HMAC-SHA256生成签名
        h = hmac.new(
            self.key.encode(), 
            entry_json.encode(), 
            hashlib.sha256
        )
        return h.hexdigest()
    
    def _encrypt_entry(self, entry_json: str) -> str:
        """
        加密日志条目
        
        Args:
            entry_json: 条目JSON字符串
            
        Returns:
            加密后的数据
        """
        # 简单加密实现，实际应用中可使用更复杂的加密算法
        # 这里使用简单的base64编码模拟
        import base64
        return base64.b64encode(entry_json.encode()).decode()
    
    def _determine_data_access_level(self, data_type: str, operation: str) -> str:
        """
        根据数据类型和操作确定审计级别
        
        Args:
            data_type: 数据类型
            operation: 操作类型
            
        Returns:
            审计级别
        """
        # 敏感数据类型
        sensitive_types = ["subtitle", "video", "model", "parameter"]
        
        # 高风险操作
        high_risk_ops = ["download", "export", "delete", "modify"]
        
        # 确定级别
        if data_type in sensitive_types and operation in high_risk_ops:
            return AuditLevel.HIGH
        elif data_type in sensitive_types:
            return AuditLevel.MEDIUM
        elif operation in high_risk_ops:
            return AuditLevel.MEDIUM
        else:
            return AuditLevel.LOW
    
    def _get_client_ip(self) -> Optional[str]:
        """
        获取客户端IP
        
        Returns:
            客户端IP地址
        """
        if not HAS_FLASK or not request:
            return None
            
        # 尝试获取客户端IP
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        elif request.environ.get('HTTP_X_REAL_IP'):
            return request.environ['HTTP_X_REAL_IP']
        else:
            return request.remote_addr
    
    def _get_user_agent(self) -> Optional[str]:
        """
        获取用户代理字符串
        
        Returns:
            用户代理字符串
        """
        if not HAS_FLASK or not request:
            return None
            
        return request.user_agent.string if hasattr(request, 'user_agent') else None
    
    def search_logs(self, query: Dict[str, Any], 
                  start_date: Optional[datetime.datetime] = None,
                  end_date: Optional[datetime.datetime] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜索审计日志
        
        Args:
            query: 搜索条件
            start_date: 开始日期
            end_date: 结束日期
            limit: 结果数量限制
            
        Returns:
            匹配的日志条目列表
        """
        # 格式化日期
        if start_date is None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=30)
        if end_date is None:
            end_date = datetime.datetime.now()
        
        logger.info(f"搜索审计日志: {start_date} 至 {end_date}, 条件: {query}")
        
        # 获取所有日志文件
        log_files = []
        for file in Path(self.log_dir).glob("audit-*.log"):
            # 从文件名解析日期
            try:
                file_date_str = file.stem.split('-')[1]
                file_date = datetime.datetime.strptime(file_date_str, "%Y%m%d")
                # 检查日期是否在范围内
                if start_date.date() <= file_date.date() <= end_date.date():
                    log_files.append(file)
            except (IndexError, ValueError):
                # 文件名格式不匹配，跳过
                continue
        
        # 按日期排序
        log_files.sort()
        
        # 读取并过滤日志
        results = []
        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        # 解析日志行
                        log_entry = json.loads(line.strip())
                        
                        # 处理加密日志
                        if log_entry.get("encrypted", False):
                            # 实际应用中应解密日志内容
                            # 简化版本: 跳过加密日志
                            continue
                        
                        # 验证签名
                        if "signature" in log_entry:
                            entry_copy = log_entry.copy()
                            signature = entry_copy.pop("signature")
                            entry_json = json.dumps(entry_copy, ensure_ascii=False, sort_keys=True)
                            expected_signature = self._sign_entry(entry_json)
                            if signature != expected_signature:
                                logger.warning(f"日志条目签名无效: {log_entry.get('id', 'unknown')}")
                                continue
                        
                        # 检查时间戳是否在指定范围内
                        if "timestamp" in log_entry:
                            try:
                                entry_time = datetime.datetime.fromisoformat(log_entry["timestamp"].replace('Z', '+00:00'))
                                if not (start_date <= entry_time <= end_date):
                                    continue
                            except (ValueError, TypeError):
                                # 无效的时间戳格式，继续处理
                                pass
                        
                        # 检查是否匹配查询条件
                        matched = True
                        for key, value in query.items():
                            # 支持嵌套字段查询，如 "details.operation"
                            if "." in key:
                                parts = key.split(".")
                                current = log_entry
                                for part in parts:
                                    if part in current:
                                        current = current[part]
                                    else:
                                        matched = False
                                        break
                                if matched and current != value:
                                    matched = False
                            # 直接字段查询
                            elif key in log_entry:
                                # 支持正则表达式匹配
                                if isinstance(value, str) and value.startswith("regex:"):
                                    pattern = value[6:]
                                    if not re.search(pattern, str(log_entry[key]), re.IGNORECASE):
                                        matched = False
                                # 精确匹配
                                elif log_entry[key] != value:
                                    matched = False
                            else:
                                matched = False
                        
                        if matched:
                            results.append(log_entry)
                            if len(results) >= limit:
                                return results
                    except json.JSONDecodeError:
                        # 无效的JSON行，跳过
                        continue
        
        return results
    
    def export_logs(self, output_file: str, 
                  start_date: Optional[datetime.datetime] = None,
                  end_date: Optional[datetime.datetime] = None,
                  format: str = "json") -> bool:
        """
        导出审计日志
        
        Args:
            output_file: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
            format: 输出格式 ('json', 'csv')
            
        Returns:
            是否成功导出
        """
        # 查询所有日志
        logs = self.search_logs({}, start_date, end_date, limit=10000)
        
        if not logs:
            logger.warning("未找到需要导出的日志")
            return False
        
        try:
            if format.lower() == "json":
                # 导出为JSON格式
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == "csv":
                # 导出为CSV格式
                with open(output_file, "w", encoding="utf-8", newline="") as f:
                    # 分析所有条目，找出所有可能的字段
                    fieldnames = set()
                    for log in logs:
                        fieldnames.update(log.keys())
                    
                    # 添加一些通用字段
                    common_fields = ["id", "timestamp", "category", "level", "user", "action"]
                    # 确保通用字段排在最前面
                    fieldnames = [f for f in common_fields if f in fieldnames] + [f for f in fieldnames if f not in common_fields]
                    
                    # 创建CSV写入器
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # 写入数据
                    for log in logs:
                        # 处理可能的嵌套结构
                        flat_log = {}
                        for key, value in log.items():
                            if isinstance(value, dict):
                                # 简化处理：将字典转换为字符串
                                flat_log[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                flat_log[key] = value
                        writer.writerow(flat_log)
            
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
            
            logger.info(f"成功导出 {len(logs)} 条审计日志到 {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出审计日志失败: {e}")
            logger.debug(traceback.format_exc())
            return False

# 全局单例实例
_audit_trail_instance = None

def get_audit_trail() -> AuditTrail:
    """
    获取审计追踪实例（单例模式）
    
    Returns:
        AuditTrail实例
    """
    global _audit_trail_instance
    if _audit_trail_instance is None:
        _audit_trail_instance = AuditTrail()
    return _audit_trail_instance

# 便捷函数
def log_view_action(user, action):
    """
    记录查看操作审计日志
    
    Args:
        user: 用户对象或ID
        action: 操作类型
    """
    return get_audit_trail().log_view_action(user, action)

def log_data_access(user, data_type, resource_id, operation, **kwargs):
    """
    记录数据访问操作
    
    Args:
        user: 用户对象或ID
        data_type: 数据类型
        resource_id: 资源标识符
        operation: 操作类型
        **kwargs: 附加详情
    """
    return get_audit_trail().log_data_access(user, data_type, resource_id, operation, kwargs)

def log_model_operation(user, model_name, operation, parameters=None):
    """
    记录模型操作
    
    Args:
        user: 用户对象或ID
        model_name: 模型名称
        operation: 操作类型
        parameters: 操作参数
    """
    return get_audit_trail().log_model_operation(user, model_name, operation, parameters)

def log_parameter_change(user, param_name, old_value, new_value, component=None):
    """
    记录参数变更
    
    Args:
        user: 用户对象或ID
        param_name: 参数名称
        old_value: 旧值
        new_value: 新值
        component: 组件名称
    """
    return get_audit_trail().log_parameter_change(user, param_name, old_value, new_value, component)

# 审计日志装饰器
def audit_log(category: str, level: str = AuditLevel.MEDIUM):
    """
    审计日志装饰器
    
    用于自动记录函数调用的审计日志
    
    Args:
        category: 审计类别
        level: 审计级别
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取用户信息，假设第一个参数是用户或包含用户信息
            user = args[0] if args else kwargs.get('user', 'system')
            
            # 记录操作开始
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "category": category,
                "level": level,
                "user": user.id if hasattr(user, 'id') else user,
                "action": f"{func.__name__}_start",
                "details": {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            }
            audit_trail = get_audit_trail()
            audit_trail.secure_append(entry)
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 记录操作成功
                entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "category": category,
                    "level": level,
                    "user": user.id if hasattr(user, 'id') else user,
                    "action": f"{func.__name__}_success",
                    "details": {
                        "function": func.__name__,
                        "result": str(result)[:100]  # 限制结果长度
                    }
                }
                audit_trail.secure_append(entry)
                
                return result
                
            except Exception as e:
                # 记录操作失败
                entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "category": category,
                    "level": AuditLevel.HIGH,  # 错误提升到高级别
                    "user": user.id if hasattr(user, 'id') else user,
                    "action": f"{func.__name__}_error",
                    "details": {
                        "function": func.__name__,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                }
                audit_trail.secure_append(entry)
                
                # 重新抛出异常
                raise
        
        return wrapper
    
    return decorator 