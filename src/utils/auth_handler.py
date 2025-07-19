#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户认证处理模块

提供用户身份验证、会话管理和访问权限控制功能。
支持JWT令牌验证、权限检查和用户会话跟踪。
"""

import os
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import threading

# JWT支持
try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False
    
# 配置日志
logger = logging.getLogger(__name__)

class AuthManager:
    """认证管理器
    
    处理用户认证、会话管理和访问权限控制。
    """
    
    def __init__(self):
        """初始化认证管理器"""
        self.sessions = {}  # 会话ID -> 用户数据
        self.users = {}     # 用户ID -> 用户数据
        self.tokens = {}    # 令牌 -> 会话ID
        self.project_permissions = {}  # 项目ID -> {用户ID: 权限}
        
        # JWT密钥
        self.jwt_secret = os.environ.get("JWT_SECRET", str(uuid.uuid4()))
        
        # 锁，用于线程安全操作
        self._lock = threading.RLock()
        
        # 加载用户数据
        self._load_user_data()
    
    def _load_user_data(self):
        """加载用户数据"""
        data_dir = Path("data/users")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            
        user_file = data_dir / "users.json"
        if not user_file.exists():
            # 创建默认用户
            default_user = {
                "id": str(uuid.uuid4()),
                "username": "default_user",
                "display_name": "默认用户",
                "email": "user@example.com",
                "is_admin": True,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            
            self.users[default_user["id"]] = default_user
            self._save_user_data()
            logger.info("已创建默认用户数据")
        else:
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    for user in user_data:
                        self.users[user["id"]] = user
                logger.info(f"已加载 {len(self.users)} 个用户")
            except Exception as e:
                logger.error(f"加载用户数据失败: {str(e)}")
    
    def _save_user_data(self):
        """保存用户数据"""
        try:
            data_dir = Path("data/users")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            user_file = data_dir / "users.json"
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(list(self.users.values()), f, ensure_ascii=False, indent=2)
            logger.debug("用户数据已保存")
        except Exception as e:
            logger.error(f"保存用户数据失败: {str(e)}")
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """验证用户凭据并创建会话
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            会话ID或None(验证失败)
        """
        # 简单演示，实际应用中应使用更安全的验证方式
        for user_id, user in self.users.items():
            if user.get("username") == username:
                # 在实际应用中应验证加密的密码
                # 这里简化为任何密码都能登录
                session_id = str(uuid.uuid4())
                
                with self._lock:
                    self.sessions[session_id] = {
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat(),
                        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                        "ip_address": "127.0.0.1"  # 在实际应用中获取真实IP
                    }
                    
                    # 更新用户最后登录时间
                    self.users[user_id]["last_login"] = datetime.now().isoformat()
                    self._save_user_data()
                
                logger.info(f"用户 {username} 已登录，会话ID: {session_id}")
                return session_id
        
        logger.warning(f"用户 {username} 认证失败")
        return None
    
    def create_token(self, session_id: str) -> Optional[str]:
        """为会话创建JWT令牌
        
        Args:
            session_id: 会话ID
            
        Returns:
            JWT令牌或None(创建失败)
        """
        if not HAS_JWT:
            logger.warning("JWT库未安装，无法创建令牌")
            return None
            
        if session_id not in self.sessions:
            logger.warning(f"无效的会话ID: {session_id}")
            return None
            
        try:
            user_id = self.sessions[session_id]["user_id"]
            user = self.users.get(user_id)
            
            if not user:
                logger.warning(f"会话 {session_id} 对应的用户不存在")
                return None
                
            # 创建令牌
            payload = {
                "sub": user_id,
                "username": user.get("username"),
                "is_admin": user.get("is_admin", False),
                "exp": int((datetime.now() + timedelta(hours=24)).timestamp()),
                "iat": int(datetime.now().timestamp()),
                "session_id": session_id
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
            
            with self._lock:
                self.tokens[token] = session_id
                
            logger.debug(f"已为会话 {session_id} 创建令牌")
            return token
            
        except Exception as e:
            logger.error(f"创建令牌失败: {str(e)}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            解码后的令牌数据或None(验证失败)
        """
        if not HAS_JWT:
            logger.warning("JWT库未安装，无法验证令牌")
            return None
            
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # 检查令牌是否已过期
            exp = payload.get("exp", 0)
            if exp < int(time.time()):
                logger.warning("令牌已过期")
                return None
                
            # 检查会话是否有效
            session_id = payload.get("session_id")
            if not session_id or session_id not in self.sessions:
                logger.warning(f"令牌对应的会话无效: {session_id}")
                return None
                
            return payload
            
        except jwt.PyJWTError as e:
            logger.warning(f"令牌验证失败: {str(e)}")
            return None
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户数据或None(用户不存在)
        """
        return self.users.get(user_id)
    
    def get_session_user(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话对应的用户
        
        Args:
            session_id: 会话ID
            
        Returns:
            用户数据或None(会话无效或用户不存在)
        """
        if session_id not in self.sessions:
            return None
            
        user_id = self.sessions[session_id]["user_id"]
        return self.get_user(user_id)
    
    def set_project_permission(self, project_id: str, user_id: str, permission: str = "read"):
        """设置用户对项目的权限
        
        Args:
            project_id: 项目ID
            user_id: 用户ID
            permission: 权限级别 (read, write, admin)
        """
        with self._lock:
            if project_id not in self.project_permissions:
                self.project_permissions[project_id] = {}
                
            self.project_permissions[project_id][user_id] = permission
            logger.debug(f"已设置用户 {user_id} 对项目 {project_id} 的权限: {permission}")
    
    def check_project_permission(self, project_id: str, user_id: str, required_permission: str = "read") -> bool:
        """检查用户是否具有项目的指定权限
        
        Args:
            project_id: 项目ID
            user_id: 用户ID
            required_permission: 所需权限级别 (read, write, admin)
            
        Returns:
            是否具有权限
        """
        # 如果用户不存在，无权限
        if user_id not in self.users:
            return False
            
        # 如果用户是管理员，有所有权限
        if self.users[user_id].get("is_admin", False):
            return True
            
        # 检查项目权限
        if project_id in self.project_permissions and user_id in self.project_permissions[project_id]:
            permission = self.project_permissions[project_id][user_id]
            
            # 权限等级: admin > write > read
            if required_permission == "read":
                return permission in ["read", "write", "admin"]
            elif required_permission == "write":
                return permission in ["write", "admin"]
            elif required_permission == "admin":
                return permission == "admin"
                
        return False
    
    def invalidate_session(self, session_id: str):
        """使会话失效
        
        Args:
            session_id: 会话ID
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                
                # 清理关联的令牌
                invalid_tokens = []
                for token, s_id in self.tokens.items():
                    if s_id == session_id:
                        invalid_tokens.append(token)
                
                for token in invalid_tokens:
                    if token in self.tokens:
                        del self.tokens[token]
                        
                logger.info(f"会话 {session_id} 已失效")
                
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        
        with self._lock:
            expired_sessions = []
            for session_id, session in self.sessions.items():
                expires_at = session.get("expires_at")
                if expires_at:
                    try:
                        expiry = datetime.fromisoformat(expires_at)
                        if expiry < now:
                            expired_sessions.append(session_id)
                    except ValueError:
                        pass
            
            # 移除过期会话
            for session_id in expired_sessions:
                self.invalidate_session(session_id)
                
            if expired_sessions:
                logger.info(f"已清理 {len(expired_sessions)} 个过期会话")

# 单例实例
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """获取认证管理器单例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

def get_current_user(session_id: str = None) -> Optional[Dict[str, Any]]:
    """获取当前用户
    
    Args:
        session_id: 会话ID (默认使用演示用户)
        
    Returns:
        用户数据
    """
    auth_manager = get_auth_manager()
    
    if session_id:
        return auth_manager.get_session_user(session_id)
    
    # 演示模式，返回第一个用户
    if auth_manager.users:
        return list(auth_manager.users.values())[0]
        
    return None

def verify_user_access(user: Dict[str, Any], project_id: str, required_permission: str = "read") -> bool:
    """验证用户是否有权访问项目
    
    Args:
        user: 用户数据
        project_id: 项目ID
        required_permission: 所需权限
        
    Returns:
        是否有权访问
    """
    if not user or not project_id:
        return False
        
    auth_manager = get_auth_manager()
    return auth_manager.check_project_permission(project_id, user.get("id"), required_permission)

def initialize_auth():
    """初始化认证系统"""
    auth_manager = get_auth_manager()
    logger.info("认证系统已初始化")

def cleanup_auth():
    """清理认证系统资源"""
    auth_manager = get_auth_manager()
    auth_manager.cleanup_expired_sessions()
    logger.info("认证系统资源已清理") 