#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动恢复模块 - 简化版（UI演示用）
"""

import os
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

def _get_recovery_file_path():
    """获取恢复文件路径"""
    # 确保logs目录存在
    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir / "recovery_history.json"

def _load_history():
    """加载恢复历史"""
    try:
        recovery_file = _get_recovery_file_path()
        if recovery_file.exists():
            with open(recovery_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"已加载恢复历史记录: {len(data.get('error_types', []))} 个错误类型")
                return data
    except Exception as e:
        logger.error(f"加载恢复历史失败: {str(e)}")
    
    # 返回空数据
    return {"error_types": [], "recovery_attempts": []}

def _save_history(data):
    """保存恢复历史"""
    try:
        recovery_file = _get_recovery_file_path()
        with open(recovery_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("已保存恢复历史")
    except Exception as e:
        logger.error(f"保存恢复历史失败: {str(e)}")

def record_error(error_type, error_message, recovery_action=None):
    """记录错误"""
    # 加载现有历史
    history = _load_history()
    
    # 记录错误类型
    if error_type not in history["error_types"]:
        history["error_types"].append(error_type)
    
    # 记录恢复尝试
    history["recovery_attempts"].append({
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "error_message": error_message,
        "recovery_action": recovery_action
    })
    
    # 保存历史
    _save_history(history)
    logger.info(f"已记录错误: {error_type}")

def get_recovery_suggestions(error_type):
    """获取恢复建议"""
    suggestions = {
        "FileNotFoundError": [
            "检查文件路径是否正确",
            "确保文件存在",
            "尝试重新下载或生成文件"
        ],
        "PermissionError": [
            "以管理员身份运行程序",
            "检查文件权限设置",
            "关闭可能占用文件的其他程序"
        ],
        "ModuleNotFoundError": [
            "安装缺失的模块",
            "检查环境变量设置",
            "更新依赖项列表"
        ]
    }
    
    return suggestions.get(error_type, ["尝试重启程序", "检查日志文件", "联系技术支持"])

def init_recovery_system():
    """初始化自动恢复系统"""
    logger.info("初始化自动恢复系统")
    
    # 确保logs目录存在
    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 初始化恢复历史
    history = _load_history()
    if not history["error_types"]:
        logger.info("未发现历史错误记录")
    else:
        logger.info(f"已发现 {len(history['error_types'])} 种历史错误类型")
    
    logger.info("自动恢复系统初始化完成")

def get_recovery_report():
    """获取恢复历史报告"""
    history = _load_history()
    
    # 计算统计信息
    total_attempts = len(history.get("recovery_attempts", []))
    error_types = history.get("error_types", [])
    
    # 构建报告
    report = {
        "total_attempts": total_attempts,
        "error_types": error_types,
        "generated_at": datetime.now().isoformat()
    }
    
    return report 

def auto_heal(error_type, error_context=None):
    """自动修复错误
    
    根据错误类型和上下文尝试自动修复错误
    
    参数:
        error_type: 错误类型
        error_context: 错误上下文（可选）
        
    返回:
        bool: 是否成功修复
    """
    logger.info(f"尝试自动修复错误: {error_type}")
    
    # 记录修复尝试
    record_error(error_type, "触发自动修复", "auto_heal")
    
    # 错误类型特定修复
    if error_type == "FileNotFoundError":
        return _heal_file_not_found(error_context)
    elif error_type == "PermissionError":
        return _heal_permission_error(error_context)
    elif error_type == "ModuleNotFoundError":
        return _heal_module_not_found(error_context)
    elif error_type == "MemoryError":
        return _heal_memory_error(error_context)
    
    # 默认行为
    logger.warning(f"没有针对 {error_type} 的自动修复方法")
    return False

def _heal_file_not_found(context):
    """修复文件未找到错误"""
    if not context or "file_path" not in context:
        logger.warning("缺少文件路径，无法修复")
        return False
    
    file_path = context["file_path"]
    logger.info(f"尝试修复文件未找到错误: {file_path}")
    
    # 检查是否有备份文件
    backup_path = str(file_path) + ".bak"
    if os.path.exists(backup_path):
        try:
            # 从备份恢复
            shutil.copy2(backup_path, file_path)
            logger.info(f"已从备份恢复文件: {file_path}")
            return True
        except Exception as e:
            logger.error(f"从备份恢复失败: {str(e)}")
    
    # 创建默认空文件
    try:
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        logger.info(f"已创建空文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"创建空文件失败: {str(e)}")
    
    return False

def _heal_permission_error(context):
    """修复权限错误"""
    logger.info("尝试修复权限错误")
    # 权限错误通常需要用户干预
    return False

def _heal_module_not_found(context):
    """修复模块未找到错误"""
    if not context or "module_name" not in context:
        logger.warning("缺少模块名称，无法修复")
        return False
    
    module_name = context["module_name"]
    logger.info(f"尝试修复模块未找到错误: {module_name}")
    
    # 尝试使用pip安装模块
    try:
        import subprocess
        logger.info(f"尝试安装模块: {module_name}")
        subprocess.run([sys.executable, "-m", "pip", "install", module_name], 
                      capture_output=True, check=True)
        logger.info(f"模块安装成功: {module_name}")
        return True
    except Exception as e:
        logger.error(f"安装模块失败: {str(e)}")
    
    return False

def _heal_memory_error(context):
    """修复内存错误"""
    import gc
    logger.info("尝试修复内存错误")
    
    # 强制垃圾回收
    gc.collect()
    
    return False 