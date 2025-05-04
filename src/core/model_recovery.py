"""
模型恢复模块

负责处理模型加载、使用过程中的错误和异常，提供自动修复和恢复机制：
1. 模型加载失败恢复
2. 推理过程中的异常处理
3. 模型量化动态调整
4. 针对中文模型的特殊优化
"""

import os
import sys
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from loguru import logger
from src.utils.exceptions import ModelLoadError, ModelCorruptionError, MemoryOverflowError, ErrorCode


class ModelRecovery:
    """模型恢复专家类"""
    
    def __init__(self):
        """初始化模型恢复系统"""
        self.recovery_stats = {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "model_types": {}
        }
        self.model_config_dir = os.path.join("configs", "models")
        self.models_dir = "models"
        self.recovery_attempts = {}  # 记录每个模型的恢复尝试次数
        self.max_recovery_attempts = 3  # 最大恢复尝试次数
    
    def _get_model_paths(self, model_name: str) -> Dict[str, str]:
        """
        获取模型相关路径
        
        Args:
            model_name: 模型名称
            
        Returns:
            包含模型路径信息的字典
        """
        # 获取模型配置文件路径
        config_file = os.path.join(
            self.model_config_dir, 
            "available_models", 
            f"{model_name}.yaml"
        )
        
        # 从名称推断模型路径
        if "zh" in model_name:
            model_type = "qwen"
            language = "zh"
        else:
            model_type = "mistral"
            language = "en"
        
        # 构建路径
        model_dir = os.path.join(self.models_dir, model_type)
        base_dir = os.path.join(model_dir, "base")
        quantized_dir = os.path.join(model_dir, "quantized")
        finetuned_dir = os.path.join(model_dir, "finetuned")
        
        return {
            "config_file": config_file,
            "model_dir": model_dir,
            "base_dir": base_dir,
            "quantized_dir": quantized_dir,
            "finetuned_dir": finetuned_dir,
            "model_type": model_type,
            "language": language
        }
    
    def verify_model_files(self, model_name: str) -> Tuple[bool, List[str]]:
        """
        验证模型文件完整性
        
        Args:
            model_name: 模型名称
            
        Returns:
            Tuple[bool, List[str]]: 验证是否通过，错误信息列表
        """
        paths = self._get_model_paths(model_name)
        config_file = paths["config_file"]
        errors = []
        
        # 检查配置文件是否存在
        if not os.path.exists(config_file):
            errors.append(f"模型配置文件不存在: {config_file}")
            return False, errors
        
        # 读取配置文件获取模型文件路径
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            model_path = config.get("path", "")
            if not model_path:
                errors.append(f"配置文件中未指定模型路径: {config_file}")
                return False, errors
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                errors.append(f"模型文件不存在: {model_path}")
                return False, errors
                
            # 简单检查文件大小
            file_size = os.path.getsize(model_path)
            if file_size < 1000000:  # 1MB
                errors.append(f"模型文件过小，可能已损坏: {model_path} ({file_size} 字节)")
                return False, errors
            
            logger.info(f"模型 {model_name} 验证通过")
            return True, []
        except Exception as e:
            errors.append(f"验证模型时发生错误: {str(e)}")
            return False, errors
    
    def fix_model_config(self, model_name: str, issues: List[str] = None) -> bool:
        """
        修复模型配置问题
        
        Args:
            model_name: 模型名称
            issues: 发现的问题列表
            
        Returns:
            是否成功修复
        """
        paths = self._get_model_paths(model_name)
        config_file = paths["config_file"]
        
        if not os.path.exists(config_file):
            logger.warning(f"无法修复不存在的配置文件: {config_file}")
            return False
        
        try:
            import yaml
            # 读取当前配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 修复常见问题
            modified = False
            
            # 1. 修复路径问题
            if "path" not in config or not os.path.exists(config.get("path", "")):
                # 尝试找到合适的模型文件
                model_files = []
                search_dirs = [
                    paths["quantized_dir"],
                    paths["finetuned_dir"],
                    paths["base_dir"]
                ]
                
                for search_dir in search_dirs:
                    if os.path.exists(search_dir):
                        for file in os.listdir(search_dir):
                            if file.endswith((".bin", ".gguf", ".safetensors", ".pth")):
                                model_files.append(os.path.join(search_dir, file))
                
                if model_files:
                    # 选择最大的文件作为模型文件
                    model_files.sort(key=lambda f: os.path.getsize(f), reverse=True)
                    config["path"] = model_files[0]
                    logger.info(f"已更新模型路径为: {config['path']}")
                    modified = True
            
            # 2. 确保量化配置正确
            if "quantization" not in config:
                # 根据语言和可能的模型大小设置默认量化级别
                if paths["language"] == "zh":
                    config["quantization"] = "Q4_K_M"  # 中文模型默认量化级别
                else:
                    config["quantization"] = "Q5_K_M"  # 英文模型默认量化级别
                logger.info(f"已设置默认量化级别: {config['quantization']}")
                modified = True
            
            # 3. 确保其他必要配置存在
            if "context_size" not in config:
                config["context_size"] = 4096  # 默认上下文大小
                modified = True
            
            if "threads" not in config:
                import multiprocessing
                config["threads"] = max(1, multiprocessing.cpu_count() - 1)  # 默认线程数
                modified = True
            
            # 保存修改后的配置
            if modified:
                # 先备份原配置
                backup_file = f"{config_file}.bak"
                shutil.copy2(config_file, backup_file)
                
                # 保存新配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                logger.info(f"已修复模型 {model_name} 的配置文件")
                return True
            else:
                logger.info(f"模型 {model_name} 的配置文件无需修复")
                return True
                
        except Exception as e:
            logger.error(f"修复模型配置时发生错误: {e}")
            return False
    
    def recover_model_loading_error(self, model_name: str, error: Exception) -> bool:
        """
        处理模型加载错误
        
        Args:
            model_name: 模型名称
            error: 捕获的异常
            
        Returns:
            是否成功恢复
        """
        self.recovery_stats["attempts"] += 1
        model_type = "zh" if "zh" in model_name else "en"
        self.recovery_stats["model_types"][model_type] = self.recovery_stats["model_types"].get(model_type, 0) + 1
        
        # 记录此模型的恢复尝试次数
        self.recovery_attempts[model_name] = self.recovery_attempts.get(model_name, 0) + 1
        
        # 如果超过最大尝试次数，放弃恢复
        if self.recovery_attempts[model_name] > self.max_recovery_attempts:
            logger.warning(f"模型 {model_name} 恢复尝试次数已达上限 ({self.max_recovery_attempts})，不再尝试")
            self.recovery_stats["failures"] += 1
            return False
        
        logger.info(f"开始恢复模型 {model_name}，错误类型: {type(error).__name__}")
        
        # 根据错误类型选择恢复策略
        if isinstance(error, MemoryOverflowError) or "memory" in str(error).lower():
            return self._recover_from_memory_error(model_name)
        elif isinstance(error, ModelCorruptionError) or "corrupt" in str(error).lower():
            return self._recover_from_corruption(model_name)
        else:
            # 默认恢复方法
            return self._general_model_recovery(model_name, error)
    
    def _recover_from_memory_error(self, model_name: str) -> bool:
        """
        处理内存不足导致的模型加载错误
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否成功恢复
        """
        logger.info(f"尝试解决模型 {model_name} 的内存问题")
        paths = self._get_model_paths(model_name)
        config_file = paths["config_file"]
        
        try:
            import yaml
            # 读取当前配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 降低量化精度以减少内存占用
            current_quant = config.get("quantization", "")
            new_quant = None
            
            # 量化级别降级策略
            if current_quant in ["float16", "float32", "F16", "F32"]:
                new_quant = "Q5_K_M"  # 从浮点降级到5位量化
            elif current_quant in ["Q8_0", "Q6_K", "Q5_K", "Q5_K_M"]:
                new_quant = "Q4_K_M"  # 从高精度量化降级到4位量化
            elif current_quant in ["Q4_K", "Q4_K_M"]:
                new_quant = "Q3_K_M"  # 从4位量化降级到3位量化
            elif current_quant in ["Q3_K", "Q3_K_M"]:
                new_quant = "Q2_K"    # 从3位量化降级到2位量化
            else:
                new_quant = "Q2_K"    # 最低量化级别
            
            # 应用新的量化设置
            if new_quant and new_quant != current_quant:
                # 备份原配置
                backup_file = f"{config_file}.bak"
                shutil.copy2(config_file, backup_file)
                
                # 更新量化设置
                config["quantization"] = new_quant
                logger.info(f"将模型 {model_name} 的量化级别从 {current_quant} 降级为 {new_quant}")
                
                # 保存新配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                # 降低线程数
                if "threads" in config and config["threads"] > 1:
                    config["threads"] = max(1, config["threads"] - 1)
                    logger.info(f"将模型 {model_name} 的线程数降低到 {config['threads']}")
                
                # 降低批处理大小
                if "batch_size" in config and config["batch_size"] > 1:
                    config["batch_size"] = max(1, config["batch_size"] // 2)
                    logger.info(f"将模型 {model_name} 的批处理大小降低到 {config['batch_size']}")
                
                # 保存更新后的配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                self.recovery_stats["successes"] += 1
                return True
            else:
                logger.warning(f"模型 {model_name} 已经使用最低量化级别，无法进一步降低")
                self.recovery_stats["failures"] += 1
                return False
                
        except Exception as e:
            logger.error(f"处理内存错误时发生异常: {e}")
            self.recovery_stats["failures"] += 1
            return False
    
    def _recover_from_corruption(self, model_name: str) -> bool:
        """
        处理模型文件损坏问题
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否成功恢复
        """
        logger.info(f"尝试修复损坏的模型文件: {model_name}")
        paths = self._get_model_paths(model_name)
        
        try:
            import yaml
            # 读取当前配置
            with open(paths["config_file"], 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            current_model_path = config.get("path", "")
            
            if current_model_path and os.path.exists(current_model_path):
                # 备份损坏的模型文件
                corrupt_backup = f"{current_model_path}.corrupt"
                try:
                    shutil.move(current_model_path, corrupt_backup)
                    logger.info(f"已将损坏的模型文件备份为: {corrupt_backup}")
                except Exception as move_error:
                    logger.warning(f"备份损坏模型文件失败: {move_error}")
            
            # 寻找备用模型文件
            backup_files = []
            search_dirs = [
                paths["quantized_dir"], 
                paths["finetuned_dir"], 
                paths["base_dir"]
            ]
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for file in os.listdir(search_dir):
                        if file.endswith((".bin", ".gguf", ".safetensors", ".pth")) and file != os.path.basename(corrupt_backup):
                            backup_files.append(os.path.join(search_dir, file))
            
            if backup_files:
                # 选择备用模型文件
                backup_files.sort(key=lambda f: os.path.getsize(f), reverse=True)
                new_model_path = backup_files[0]
                
                # 更新配置
                config["path"] = new_model_path
                logger.info(f"已切换到备用模型文件: {new_model_path}")
                
                # 保存更新后的配置
                with open(paths["config_file"], 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                self.recovery_stats["successes"] += 1
                return True
            else:
                logger.error(f"未找到可用的备用模型文件")
                self.recovery_stats["failures"] += 1
                return False
                
        except Exception as e:
            logger.error(f"修复损坏模型时发生错误: {e}")
            self.recovery_stats["failures"] += 1
            return False
    
    def _general_model_recovery(self, model_name: str, error: Exception) -> bool:
        """
        通用模型恢复策略
        
        Args:
            model_name: 模型名称
            error: 原始错误
            
        Returns:
            是否成功恢复
        """
        logger.info(f"对模型 {model_name} 应用通用恢复策略，错误: {error}")
        
        # 1. 验证模型文件
        valid, issues = self.verify_model_files(model_name)
        if not valid:
            logger.warning(f"模型验证失败: {', '.join(issues)}")
            # 尝试修复配置文件
            if self.fix_model_config(model_name, issues):
                logger.info(f"成功修复模型配置")
                self.recovery_stats["successes"] += 1
                return True
        
        # 2. 尝试降低模型配置
        try:
            paths = self._get_model_paths(model_name)
            
            import yaml
            with open(paths["config_file"], 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 备份原配置
            backup_file = f"{paths['config_file']}.bak"
            shutil.copy2(paths["config_file"], backup_file)
            
            # 应用更保守的设置
            modified = False
            
            # 降低上下文大小
            if "context_size" in config and config["context_size"] > 2048:
                config["context_size"] = min(2048, config["context_size"] // 2)
                logger.info(f"降低上下文大小到 {config['context_size']}")
                modified = True
            
            # 降低批处理大小
            if "batch_size" in config and config["batch_size"] > 1:
                config["batch_size"] = 1
                logger.info("降低批处理大小到 1")
                modified = True
            
            # 减少线程数
            if "threads" in config and config["threads"] > 1:
                config["threads"] = max(1, config["threads"] // 2)
                logger.info(f"降低线程数到 {config['threads']}")
                modified = True
            
            # 保存更新后的配置
            if modified:
                with open(paths["config_file"], 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                logger.info(f"已更新模型配置，降低了资源需求")
                self.recovery_stats["successes"] += 1
                return True
            
        except Exception as config_error:
            logger.error(f"修改模型配置时发生错误: {config_error}")
        
        # 如果以上方法都失败，尝试最后的降级策略
        self.recovery_stats["failures"] += 1
        return self._recover_from_memory_error(model_name)  # 作为最后的尝试
    
    def create_model_checkpoint(self, model_name: str) -> bool:
        """
        为模型创建检查点，以便在出现问题时恢复
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否成功创建检查点
        """
        paths = self._get_model_paths(model_name)
        config_file = paths["config_file"]
        
        if not os.path.exists(config_file):
            logger.warning(f"模型配置文件不存在，无法创建检查点: {config_file}")
            return False
        
        try:
            # 检查点目录
            checkpoint_dir = os.path.join("checkpoints", "models")
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            # 检查点文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            checkpoint_file = os.path.join(checkpoint_dir, f"{model_name}_{timestamp}.yaml")
            
            # 复制配置文件作为检查点
            shutil.copy2(config_file, checkpoint_file)
            
            # 记录检查点元数据
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 检查点元数据
            metadata = {
                "checkpoint_time": timestamp,
                "model_name": model_name,
                "model_path": config.get("path", ""),
                "quantization": config.get("quantization", ""),
                "original_config": config_file
            }
            
            # 保存元数据
            metadata_file = f"{checkpoint_file}.meta"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已为模型 {model_name} 创建检查点: {checkpoint_file}")
            return True
        
        except Exception as e:
            logger.error(f"创建模型检查点时发生错误: {e}")
            return False
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        return self.recovery_stats


# 全局模型恢复实例
_model_recovery = None

def get_model_recovery() -> ModelRecovery:
    """获取模型恢复实例"""
    global _model_recovery
    if _model_recovery is None:
        _model_recovery = ModelRecovery()
    return _model_recovery


def verify_model(model_name: str) -> bool:
    """
    验证模型配置和文件的便捷函数
    
    Args:
        model_name: 模型名称
        
    Returns:
        验证是否通过
    """
    recovery = get_model_recovery()
    valid, issues = recovery.verify_model_files(model_name)
    
    if not valid:
        logger.warning(f"模型 {model_name} 验证失败: {', '.join(issues)}")
        # 尝试修复
        fixed = recovery.fix_model_config(model_name, issues)
        if fixed:
            logger.info(f"已修复模型 {model_name} 的配置")
            # 再次验证
            valid, issues = recovery.verify_model_files(model_name)
    
    return valid 