"""
API安全防护系统

提供多层次的API安全保护，包括身份认证、访问控制、请求限流和数据校验
"""

from fastapi import Request, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import jwt
import os
import re
import ipaddress
import hmac
import hashlib
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta
from loguru import logger

# JWT配置
JWT_SECRET = os.getenv("JWT_SECRET", "visionai_secure_key_please_change_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60  # 24小时过期

# API密钥配置
API_KEYS = {
    "admin": {
        "key": os.getenv("ADMIN_API_KEY", "admin_dev_key"),
        "rate_limit": 100,  # 每分钟最大请求数
        "permissions": ["read", "write", "admin"]
    },
    "user": {
        "key": os.getenv("USER_API_KEY", "user_dev_key"),
        "rate_limit": 20,
        "permissions": ["read"]
    }
}

# IP黑名单和白名单
IP_BLACKLIST: Set[str] = set()
IP_WHITELIST: Set[str] = set()

# 敏感路径需要更高权限
PROTECTED_PATHS = {
    "/api/v1/admin": ["admin"],
    "/api/v1/batch": ["write", "admin"]
}

# IP地址封禁临时存储
blocked_ips: Dict[str, datetime] = {}

def create_jwt_token(user_id: str, permissions: List[str]) -> str:
    """
    创建JWT令牌
    
    Args:
        user_id: 用户标识
        permissions: 权限列表
        
    Returns:
        JWT令牌字符串
    """
    payload = {
        "sub": user_id,
        "permissions": permissions,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_api_key(api_key: str) -> Dict[str, Any]:
    """
    验证API密钥
    
    Args:
        api_key: API密钥字符串
        
    Returns:
        包含用户信息和权限的字典
    
    Raises:
        HTTPException: 如果API密钥无效
    """
    for user_id, user_info in API_KEYS.items():
        if hmac.compare_digest(api_key, user_info["key"]):
            return {
                "user_id": user_id,
                "permissions": user_info["permissions"],
                "rate_limit": user_info["rate_limit"]
            }
    
    # 未找到匹配的API密钥
    logger.warning(f"无效的API密钥尝试")
    raise HTTPException(status_code=401, detail="无效的API密钥")

def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址，处理代理情况
    
    Args:
        request: 请求对象
        
    Returns:
        客户端IP地址
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

# JWT身份验证
class JWTBearer(HTTPBearer):
    """JWT令牌验证"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(status_code=403, detail="未提供身份令牌")
        
        # 验证JWT令牌
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # 检查令牌是否过期
            if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="令牌已过期")
                
            # 将用户信息添加到请求状态
            user_data = {
                "user_id": payload.get("sub"),
                "permissions": payload.get("permissions", [])
            }
            request.state.user = user_data
            return user_data
            
        except jwt.PyJWTError as e:
            logger.warning(f"JWT验证失败: {str(e)}")
            raise HTTPException(status_code=401, detail="无效的身份令牌")

# API密钥身份验证
class APIKeyAuth:
    """API密钥验证"""
    
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error
    
    async def __call__(self, request: Request, x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
        if not x_api_key:
            if self.auto_error:
                raise HTTPException(status_code=403, detail="未提供API密钥")
            return None
        
        try:
            user_data = verify_api_key(x_api_key)
            request.state.user = user_data
            return user_data
        except HTTPException as e:
            if self.auto_error:
                raise e
            return None

# 权限验证
def check_permissions(required_permissions: List[str]):
    """
    权限验证依赖项
    
    Args:
        required_permissions: 所需权限列表
    """
    async def dependency(request: Request):
        user_data = getattr(request.state, "user", None)
        if not user_data:
            raise HTTPException(status_code=403, detail="未授权访问")
        
        user_permissions = user_data.get("permissions", [])
        
        # 检查是否有任何所需权限
        if not any(perm in user_permissions for perm in required_permissions):
            logger.warning(f"权限不足: {user_data.get('user_id')} 尝试访问 {request.url.path}")
            raise HTTPException(status_code=403, detail="权限不足")
        
        return True
    
    return dependency

# 令牌桶限流中间件
class RateLimiter(BaseHTTPMiddleware):
    """
    令牌桶限流中间件
    
    - 全局限流+基于IP的限流
    - 不同用户角色不同限流策略
    - 黑名单和白名单支持
    """
    
    def __init__(
        self, 
        app, 
        max_requests: int = 20, 
        window_seconds: int = 10,
        block_duration_minutes: int = 30
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_minutes = block_duration_minutes
        self.ip_buckets: Dict[str, List[float]] = {}
        self.user_buckets: Dict[str, List[float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = get_client_ip(request)
        
        # 检查IP是否在黑名单中
        if client_ip in IP_BLACKLIST:
            logger.warning(f"拒绝黑名单IP访问: {client_ip}")
            raise HTTPException(status_code=403, detail="IP已被封禁")
        
        # 检查IP是否在临时封禁列表中
        if client_ip in blocked_ips:
            block_until = blocked_ips[client_ip]
            if datetime.now() < block_until:
                remaining = (block_until - datetime.now()).total_seconds() // 60
                logger.warning(f"拒绝临时封禁IP访问: {client_ip}, 剩余 {remaining} 分钟")
                raise HTTPException(
                    status_code=429, 
                    detail=f"请求过于频繁，IP暂时被封禁，请在 {remaining:.0f} 分钟后重试"
                )
            else:
                # 封禁时间已过，移除IP
                del blocked_ips[client_ip]
        
        # 白名单IP不做限制
        if client_ip in IP_WHITELIST:
            return await call_next(request)
        
        # 获取当前时间
        now = time.time()
        
        # 基于IP的限流
        bucket = self.ip_buckets.setdefault(client_ip, [])
        bucket[:] = [t for t in bucket if now - t < self.window_seconds]
        
        # 判断是否超出限制
        if len(bucket) >= self.max_requests:
            # 记录频繁访问
            if len(bucket) >= self.max_requests * 2:
                # 如果超出两倍阈值，临时封禁IP
                blocked_ips[client_ip] = datetime.now() + timedelta(minutes=self.block_duration_minutes)
                logger.warning(f"IP {client_ip} 请求过于频繁，已临时封禁 {self.block_duration_minutes} 分钟")
                
            logger.warning(f"IP {client_ip} 请求过于频繁")
            raise HTTPException(
                status_code=429, 
                detail="请求过于频繁，请稍后再试"
            )
            
        # 记录本次请求时间
        bucket.append(now)
        
        # 基于用户的限流（如果已认证）
        user_data = getattr(request.state, "user", None)
        if user_data:
            user_id = user_data.get("user_id")
            user_rate_limit = user_data.get("rate_limit", self.max_requests)
            
            if user_id:
                user_bucket = self.user_buckets.setdefault(user_id, [])
                user_bucket[:] = [t for t in user_bucket if now - t < self.window_seconds]
                
                if len(user_bucket) >= user_rate_limit:
                    logger.warning(f"用户 {user_id} 请求过于频繁")
                    raise HTTPException(
                        status_code=429, 
                        detail="请求过于频繁，已超出API密钥限制"
                    )
                
                user_bucket.append(now)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制信息到响应头
        if client_ip in self.ip_buckets:
            requests_left = max(0, self.max_requests - len(self.ip_buckets[client_ip]))
            response.headers["X-RateLimit-Remaining"] = str(requests_left)
            response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))
        
        return response

# SQL注入防护中间件
class SQLInjectionGuard(BaseHTTPMiddleware):
    """SQL注入防护中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        # SQL注入攻击特征
        self.sql_patterns = [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
            r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
            r"((\%27)|(\'))union",
            r"exec\s+|\sexecute\s+|sp_executesql|xp_cmdshell",
            r";select\s+|;\s*insert|;\s*update|;\s*delete",
            r"\/\*|\*\/|\-\-\s+",
            r"((\%3C)|<)((\%2F)|\/)*[a-z0-9\%]+((\%3E)|>)",
            r"((\%3C)|<)((\%69)|i|(\%49))((\%6D)|m|(\%4D))((\%67)|g|(\%47))[^\n]+((\%3E)|>)",
            r"((\%3C)|<)[^\n]+((\%3E)|>)"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.sql_patterns]
    
    async def dispatch(self, request: Request, call_next):
        # 检查URL参数
        for param, value in request.query_params.items():
            for pattern in self.compiled_patterns:
                if pattern.search(value):
                    logger.warning(f"检测到URL参数中的SQL注入风险: {param}={value}")
                    raise HTTPException(status_code=400, detail="检测到非法请求内容")
        
        # 检查请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                body_str = body.decode("utf-8", errors="ignore")
                
                for pattern in self.compiled_patterns:
                    if pattern.search(body_str):
                        logger.warning(f"检测到请求体中的SQL注入风险")
                        raise HTTPException(status_code=400, detail="检测到非法请求内容")
            except Exception as e:
                # 如果无法解析请求体，继续处理请求
                pass
        
        return await call_next(request)

# 请求验证中间件
class RequestValidator(BaseHTTPMiddleware):
    """请求合法性验证中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # 高风险路径正则表达式
        self.sensitive_paths = [
            r"\/admin",
            r"\/config",
            r"\/users",
            r"\/security",
            r"\/auth"
        ]
        self.compiled_sensitive_paths = [re.compile(p, re.IGNORECASE) for p in self.sensitive_paths]
        
        # 已知的文件上传路径
        self.upload_paths = [
            r"\/upload",
            r"\/media"
        ]
        self.compiled_upload_paths = [re.compile(p, re.IGNORECASE) for p in self.upload_paths]
        
        # 允许的文件类型
        self.allowed_extensions = {'.mp4', '.avi', '.mov', '.srt', '.ass', '.txt'}
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 检查是否是敏感路径
        for pattern in self.compiled_sensitive_paths:
            if pattern.search(path):
                # 敏感路径需要确保JWT认证
                if not getattr(request.state, "user", None):
                    logger.warning(f"未认证访问敏感路径: {path}")
                    raise HTTPException(status_code=403, detail="需要认证才能访问此路径")
        
        # 检查文件上传请求
        if request.method == "POST":
            for pattern in self.compiled_upload_paths:
                if pattern.search(path):
                    content_type = request.headers.get("content-type", "")
                    
                    # 如果是文件上传请求，检查文件类型限制
                    if content_type.startswith("multipart/form-data"):
                        form = await request.form()
                        for field_name, field_value in form.items():
                            if hasattr(field_value, "filename"):
                                filename = field_value.filename
                                if filename:
                                    ext = os.path.splitext(filename)[1].lower()
                                    if ext not in self.allowed_extensions:
                                        logger.warning(f"拒绝上传不允许的文件类型: {ext}")
                                        raise HTTPException(
                                            status_code=400, 
                                            detail=f"不支持的文件类型: {ext}，仅允许 {', '.join(self.allowed_extensions)}"
                                        )
        
        # 处理请求
        return await call_next(request)

# CORS头添加中间件
class CORSMiddleware(BaseHTTPMiddleware):
    """CORS头添加中间件"""
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        # 处理请求
        response = await call_next(request)
        
        # 获取请求的Origin头
        origin = request.headers.get("origin", "*")
        
        # 如果允许所有源，或者请求的源在允许列表中
        if "*" in self.allowed_origins or origin in self.allowed_origins:
            # 添加CORS头
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
            response.headers["Access-Control-Max-Age"] = "86400"  # 24小时
        
        return response

# 日志记录中间件
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 记录请求信息
        client_ip = get_client_ip(request)
        start_time = time.time()
        
        # 处理请求前的日志
        logger.info(f"收到请求: {request.method} {request.url.path} 来自 {client_ip}")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求处理完成: {request.method} {request.url.path} "
                f"状态码: {response.status_code} "
                f"处理时间: {process_time:.3f}s"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # 记录错误信息
            logger.error(
                f"请求处理出错: {request.method} {request.url.path} "
                f"错误: {str(e)}"
            )
            # 重新抛出异常，让后续的错误处理中间件处理
            raise 