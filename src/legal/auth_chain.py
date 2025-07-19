#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 用户授权链验证模块

提供用户授权链验证功能，确保用户遵守协议并拥有内容权限。
主要功能：
1. 验证用户是否签署了最新的EULA
2. 验证用户是否拥有素材的使用权限
3. 维护上传内容的权限证明链
4. 用户权限审核与记录

支持中英文双语验证，中文模型立即启用，英文配置保留但不激活。
"""

import os
import sys
import json
import time
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# 导入相关模块
try:
    from src.utils.log_handler import get_module_logger
    from src.logging.audit_logger import log_legal_event
    from src.security.access_control import get_audit_logger
except ImportError:
    # 基本日志设置（如果无法导入日志处理器）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def get_module_logger(name):
        return logging.getLogger(name)
    
    def log_legal_event(event_type, detail):
        logger = logging.getLogger("legal.audit")
        logger.info(f"{event_type}: {detail}")
        return {"status": "logged"}
    
    def get_audit_logger():
        return logging.getLogger("security.audit")

# 配置日志
logger = get_module_logger("legal.auth_chain")

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
LEGAL_DIR = PROJECT_ROOT / "configs" / "legal"
USER_DATA_DIR = DATA_DIR / "users"
CONTENT_CERTS_DIR = DATA_DIR / "content_certificates"

# 确保目录存在
for dir_path in [DATA_DIR, LEGAL_DIR, USER_DATA_DIR, CONTENT_CERTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 异常类定义
class AuthorizationError(Exception):
    """授权错误：用户未获得适当授权"""
    pass

class ContentError(Exception):
    """内容错误：内容不符合要求或不被允许"""
    pass

class CopyrightError(Exception):
    """版权错误：缺少内容权限证明"""
    pass

class EULAError(Exception):
    """EULA错误：用户未签署EULA"""
    pass

# 授权链验证器
class AuthorizationChain:
    """
    用户授权链验证器
    
    管理用户授权链验证，确保合法使用软件和内容
    """
    
    def __init__(self):
        """初始化授权链验证器"""
        self.eula_versions = self._load_eula_versions()
        self.current_eula_version = self._get_current_eula_version()
        self.content_certificates = self._load_content_certificates()
        
        # 初始化连接到审计日志系统
        try:
            self.audit_logger = get_audit_logger()
        except:
            self.audit_logger = None
        
        logger.info(f"授权链验证器初始化完成，当前EULA版本: {self.current_eula_version}")
    
    def _load_eula_versions(self) -> Dict[str, Dict[str, Any]]:
        """
        加载所有EULA版本信息
        
        Returns:
            Dict: EULA版本信息字典
        """
        versions_file = LEGAL_DIR / "eula_versions.json"
        
        if not versions_file.exists():
            # 创建默认版本文件
            default_versions = {
                "1.0.0": {
                    "version": "1.0.0",
                    "date": datetime.datetime.now().isoformat(),
                    "path": "eula_1.0.0.md",
                    "status": "active"
                }
            }
            
            with open(versions_file, "w", encoding="utf-8") as f:
                json.dump(default_versions, f, ensure_ascii=False, indent=2)
            
            # 创建默认EULA文件
            default_eula_path = LEGAL_DIR / "eula_1.0.0.md"
            if not default_eula_path.exists():
                with open(default_eula_path, "w", encoding="utf-8") as f:
                    f.write("# VisionAI-ClipsMaster 用户协议 v1.0.0\n\n")
                    f.write("## 1. 所有权\n用户保留原始内容所有权。\n\n")
                    f.write("## 2. 数据处理\n原始素材处理后立即删除。\n\n")
                    f.write("## 3. AI伦理规范\n禁止生成非法或侵权内容。\n\n")
                    f.write("## 4. 数据删除权\n用户有权要求删除个人数据（GDPR第17条被遗忘权）。\n\n")
                    f.write("## 5. 合规要求\n符合中国《生成式AI服务管理暂行办法》的要求。\n")
            
            return default_versions
        
        try:
            with open(versions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载EULA版本信息失败: {e}")
            return {}
    
    def _get_current_eula_version(self) -> str:
        """
        获取当前活跃的EULA版本
        
        Returns:
            str: 当前EULA版本号
        """
        active_versions = [
            version for version, info in self.eula_versions.items()
            if info.get("status") == "active"
        ]
        
        return active_versions[-1] if active_versions else "1.0.0"
    
    def _load_content_certificates(self) -> Dict[str, Set[str]]:
        """
        加载内容权限证明数据
        
        Returns:
            Dict: 用户ID到内容哈希集合的映射
        """
        certificates = {}
        
        try:
            # 遍历用户证书目录
            for user_file in CONTENT_CERTS_DIR.glob("*.json"):
                user_id = user_file.stem
                
                with open(user_file, "r", encoding="utf-8") as f:
                    user_certs = json.load(f)
                
                # 存储内容哈希集合
                certificates[user_id] = set(user_certs.get("content_hashes", []))
        except Exception as e:
            logger.error(f"加载内容权限证明数据失败: {e}")
        
        return certificates
    
    def _save_content_certificate(self, user_id: str, content_hash: str) -> bool:
        """
        保存内容权限证明
        
        Args:
            user_id: 用户ID
            content_hash: 内容哈希值
            
        Returns:
            bool: 操作是否成功
        """
        user_cert_file = CONTENT_CERTS_DIR / f"{user_id}.json"
        
        try:
            # 加载现有证书或创建新证书
            if user_cert_file.exists():
                with open(user_cert_file, "r", encoding="utf-8") as f:
                    user_certs = json.load(f)
            else:
                user_certs = {
                    "user_id": user_id,
                    "content_hashes": [],
                    "last_updated": ""
                }
            
            # 更新证书
            if content_hash not in user_certs["content_hashes"]:
                user_certs["content_hashes"].append(content_hash)
            
            user_certs["last_updated"] = datetime.datetime.now().isoformat()
            
            # 保存证书
            with open(user_cert_file, "w", encoding="utf-8") as f:
                json.dump(user_certs, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的集合
            if user_id not in self.content_certificates:
                self.content_certificates[user_id] = set()
            
            self.content_certificates[user_id].add(content_hash)
            
            return True
        
        except Exception as e:
            logger.error(f"保存内容权限证明失败: {e}")
            return False
    
    def check_eula_signed(self, user_id: str) -> bool:
        """
        检查用户是否签署了最新的EULA
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否签署了最新EULA
        """
        # 检查用户EULA签署记录
        user_eula_file = USER_DATA_DIR / f"{user_id}_eula.json"
        
        if not user_eula_file.exists():
            logger.warning(f"用户 {user_id} 没有EULA签署记录")
            return False
        
        try:
            with open(user_eula_file, "r", encoding="utf-8") as f:
                signed_data = json.load(f)
            
            signed_version = signed_data.get("version", "")
            signed_date = signed_data.get("signed_date", "")
            
            # 检查签署的是否为最新版本
            if signed_version == self.current_eula_version:
                # 记录审计事件
                log_legal_event("EULA_CHECK", f"用户 {user_id} 已签署最新EULA版本 {signed_version}")
                return True
            else:
                logger.warning(f"用户 {user_id} 签署的EULA版本 {signed_version} 不是最新版本 {self.current_eula_version}")
                return False
                
        except Exception as e:
            logger.error(f"检查用户EULA签署状态失败: {e}")
            return False
    
    def sign_eula(self, user_id: str) -> Dict[str, Any]:
        """
        为用户签署最新版本的EULA
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 签署结果
        """
        # 构建签署记录
        signed_data = {
            "user_id": user_id,
            "version": self.current_eula_version,
            "signed_date": datetime.datetime.now().isoformat(),
            "ip_address": "127.0.0.1",  # 实际应用中应获取真实IP
            "status": "accepted"
        }
        
        # 保存签署记录
        user_eula_file = USER_DATA_DIR / f"{user_id}_eula.json"
        
        try:
            with open(user_eula_file, "w", encoding="utf-8") as f:
                json.dump(signed_data, f, ensure_ascii=False, indent=2)
            
            # 记录审计日志
            log_legal_event(
                "EULA_SIGNED", 
                f"用户 {user_id} 签署EULA版本 {self.current_eula_version}"
            )
            
            logger.info(f"用户 {user_id} 成功签署EULA版本 {self.current_eula_version}")
            
            return {
                "success": True,
                "user_id": user_id,
                "version": self.current_eula_version,
                "signed_date": signed_data["signed_date"]
            }
            
        except Exception as e:
            logger.error(f"保存用户EULA签署记录失败: {e}")
            
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }
    
    def get_upload_certificates(self, user_id: str) -> List[str]:
        """
        获取用户的上传权限证明列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 内容哈希列表
        """
        return list(self.content_certificates.get(user_id, set()))
    
    def register_content_ownership(self, user_id: str, content_hash: str, proof_type: str = "self_declaration") -> Dict[str, Any]:
        """
        注册内容所有权/使用权
        
        Args:
            user_id: 用户ID
            content_hash: 内容哈希值
            proof_type: 证明类型（self_declaration/license/purchase）
            
        Returns:
            Dict: 注册结果
        """
        # 验证用户是否签署EULA
        if not self.check_eula_signed(user_id):
            return {
                "success": False,
                "user_id": user_id,
                "content_hash": content_hash,
                "error": "用户未签署最新EULA"
            }
        
        # 保存内容权限证明
        if self._save_content_certificate(user_id, content_hash):
            # 记录审计日志
            log_legal_event(
                "CONTENT_OWNERSHIP", 
                f"用户 {user_id} 注册内容 {content_hash[:8]} 的{proof_type}权限"
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "content_hash": content_hash,
                "proof_type": proof_type,
                "registered_date": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "user_id": user_id,
                "content_hash": content_hash,
                "error": "注册内容权限失败"
            }
    
    def validate_authorization_chain(self, user_id: str, content_hash: str) -> Dict[str, Any]:
        """
        验证授权链
        
        检查用户是否签署EULA以及是否拥有内容的使用权
        
        Args:
            user_id: 用户ID
            content_hash: 内容哈希值
            
        Returns:
            Dict: 验证结果
        """
        result = {
            "user_id": user_id,
            "content_hash": content_hash,
            "eula_signed": False,
            "content_authorized": False,
            "success": False
        }
        
        # 检查用户是否签署协议
        if not self.check_eula_signed(user_id):
            result["error"] = "用户未签署最新协议"
            log_legal_event("AUTH_CHAIN", f"验证失败: 用户 {user_id} 未签署最新EULA")
            return result
        
        result["eula_signed"] = True
        
        # 检查素材上传权限
        upload_records = self.get_upload_certificates(user_id)
        if content_hash not in upload_records:
            result["error"] = "未找到素材权限证明"
            log_legal_event("AUTH_CHAIN", f"验证失败: 用户 {user_id} 没有内容 {content_hash[:8]} 的权限证明")
            return result
        
        result["content_authorized"] = True
        result["success"] = True
        
        # 记录审计日志
        log_legal_event("AUTH_CHAIN", f"验证成功: 用户 {user_id} 对内容 {content_hash[:8]} 的授权有效")
        
        return result


# 实例化授权链验证器（单例模式）
_auth_chain_instance = None

def get_auth_chain() -> AuthorizationChain:
    """
    获取授权链验证器实例（单例模式）
    
    Returns:
        AuthorizationChain: 授权链验证器实例
    """
    global _auth_chain_instance
    
    if _auth_chain_instance is None:
        _auth_chain_instance = AuthorizationChain()
    
    return _auth_chain_instance


# 便捷函数
def validate_authorization_chain(user_id: str, content_hash: str) -> Dict[str, Any]:
    """
    验证用户授权链
    
    检查用户是否签署EULA以及是否拥有内容的使用权
    
    Args:
        user_id: 用户ID
        content_hash: 内容哈希值
        
    Returns:
        Dict: 验证结果
        
    Raises:
        AuthorizationError: 用户未签署最新协议
        CopyrightError: 未找到素材权限证明
    """
    auth_chain = get_auth_chain()
    
    # 检查用户协议签署记录
    if not auth_chain.check_eula_signed(user_id):
        raise AuthorizationError("用户未签署最新协议")
    
    # 验证素材上传授权
    upload_records = auth_chain.get_upload_certificates(user_id)
    if content_hash not in upload_records:
        raise CopyrightError("未找到素材权限证明")
    
    # 记录审计日志
    log_legal_event("AUTHORIZATION", f"用户 {user_id} 通过对内容 {content_hash[:8]} 的授权链验证")
    
    return {
        "user_id": user_id,
        "content_hash": content_hash,
        "eula_signed": True,
        "content_authorized": True,
        "success": True
    }

def check_eula_signed(user_id: str) -> bool:
    """
    检查用户是否签署了最新的EULA
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 是否签署了最新EULA
    """
    auth_chain = get_auth_chain()
    return auth_chain.check_eula_signed(user_id)

def sign_eula(user_id: str) -> Dict[str, Any]:
    """
    为用户签署最新版本的EULA
    
    Args:
        user_id: 用户ID
        
    Returns:
        Dict: 签署结果
    """
    auth_chain = get_auth_chain()
    return auth_chain.sign_eula(user_id)

def register_content_ownership(user_id: str, content_hash: str, proof_type: str = "self_declaration") -> Dict[str, Any]:
    """
    注册内容所有权/使用权
    
    Args:
        user_id: 用户ID
        content_hash: 内容哈希值
        proof_type: 证明类型（self_declaration/license/purchase）
        
    Returns:
        Dict: 注册结果
    """
    auth_chain = get_auth_chain()
    return auth_chain.register_content_ownership(user_id, content_hash, proof_type)

def get_upload_certificates(user_id: str) -> List[str]:
    """
    获取用户的上传权限证明列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        List[str]: 内容哈希列表
    """
    auth_chain = get_auth_chain()
    return auth_chain.get_upload_certificates(user_id)


# 直接运行时的测试代码
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 用户授权链验证")
    parser.add_argument("--sign-eula", type=str, help="签署EULA (需要用户ID)")
    parser.add_argument("--check-eula", type=str, help="检查EULA签署状态 (需要用户ID)")
    parser.add_argument("--register", type=str, nargs=2, help="注册内容所有权 (用户ID 内容哈希)")
    parser.add_argument("--validate", type=str, nargs=2, help="验证授权链 (用户ID 内容哈希)")
    parser.add_argument("--get-certs", type=str, help="获取用户上传证书 (需要用户ID)")
    
    args = parser.parse_args()
    
    if args.sign_eula:
        result = sign_eula(args.sign_eula)
        print(f"签署EULA结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    elif args.check_eula:
        signed = check_eula_signed(args.check_eula)
        print(f"用户 {args.check_eula} EULA签署状态: {'已签署' if signed else '未签署'}")
        
    elif args.register:
        user_id, content_hash = args.register
        result = register_content_ownership(user_id, content_hash)
        print(f"注册内容所有权结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    elif args.validate:
        user_id, content_hash = args.validate
        try:
            result = validate_authorization_chain(user_id, content_hash)
            print(f"授权链验证结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"授权链验证失败: {e}")
            
    elif args.get_certs:
        certs = get_upload_certificates(args.get_certs)
        print(f"用户 {args.get_certs} 上传证书: {certs}")
        
    else:
        parser.print_help() 