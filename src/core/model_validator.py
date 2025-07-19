import hashlib
import os
from loguru import logger
from src.utils.exceptions import ModelCorruptionError, PermissionError

def load_hash_from_db(model_path: str) -> str:
    """从数据库或本地配置加载模型期望哈希（占位实现）"""
    # TODO: 实际项目中应从数据库或配置文件获取
    hash_db = {
        "models/qwen/quantized/Q4_K_M.gguf": "abc123...",
        "models/mistral/quantized/Q4_K_M.gguf": "def456..."
    }
    return hash_db.get(model_path, "")

def calculate_file_hash(model_path: str, algo: str = "sha256") -> str:
    """计算文件哈希值"""
    h = hashlib.new(algo)
    with open(model_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def check_file_permissions(model_path: str):
    """检查文件权限，确保可读"""
    if not os.access(model_path, os.R_OK):
        raise PermissionError(f"模型文件不可读: {model_path}")

def auto_repair_model(model_path: str) -> bool:
    """自动修复模型文件（占位实现，可扩展为重新下载分片等）"""
    logger.warning(f"尝试自动修复模型: {model_path}")
    # TODO: 实现自动修复逻辑，如重新下载分片
    return False

def validate_model_integrity(model_path: str):
    """完整性校验，自动修复并二次校验"""
    expected_hash = load_hash_from_db(model_path)
    actual_hash = calculate_file_hash(model_path)
    if actual_hash != expected_hash:
        logger.error(f"模型哈希校验失败: {model_path}")
        repaired = auto_repair_model(model_path)
        if repaired:
            actual_hash = calculate_file_hash(model_path)
            if actual_hash != expected_hash:
                raise ModelCorruptionError(f"模型修复后哈希仍不匹配: {model_path}")
        else:
            raise ModelCorruptionError(f"模型校验失败: {model_path}")
    check_file_permissions(model_path)
    logger.info(f"模型完整性校验通过: {model_path}") 