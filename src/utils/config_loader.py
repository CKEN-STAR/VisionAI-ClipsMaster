"""配置加载器模块。

此模块提供了配置文件的加载、验证和管理功能。
支持 JSON 和 YAML 格式的配置文件，实现了配置文件的自动重载和验证机制。
"""

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, Callable
import copy
import time
import glob
import logging

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .exceptions import ConfigurationError, ErrorCode, ValidationError, ConfigError
from .config_schema import ConfigSchema
from .log_handler import get_logger

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='ConfigLoader')


class ConfigValidator:
    """配置验证器，用于验证各种配置的有效性。"""

    @staticmethod
    def validate_memory_config(config: Dict[str, Any]) -> bool:
        """验证内存配置。

        Args:
            config: 内存配置字典。

        Returns:
            bool: 配置是否有效。

        Raises:
            ConfigurationError: 当配置无效时抛出。
        """
        required_fields = [
            "resource_limits.memory_limits.per_process",
            "resource_limits.memory_limits.total",
        ]
        try:
            return all(ConfigValidator._check_nested_field(config, field) for field in required_fields)
        except Exception as e:
            raise ConfigurationError(
                message=f"内存配置验证失败: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    @staticmethod
    def validate_model_config(config: Dict[str, Any]) -> bool:
        """验证模型配置。

        Args:
            config: 模型配置字典。

        Returns:
            bool: 配置是否有效。

        Raises:
            ConfigurationError: 当配置无效时抛出。
        """
        required_fields = ["base_models", "loading_strategy", "optimization"]
        try:
            return all(field in config for field in required_fields)
        except Exception as e:
            raise ConfigurationError(
                message=f"模型配置验证失败: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    @staticmethod
    def validate_security_config(config: Dict[str, Any]) -> bool:
        """验证安全配置。

        Args:
            config: 安全配置字典。

        Returns:
            bool: 配置是否有效。

        Raises:
            ConfigurationError: 当配置无效时抛出。
        """
        required_fields = {
            "max_memory_percent": (0, 100),
            "max_cpu_percent": (0, 100),
            "allowed_file_types": list,
            "max_file_size_mb": (0, float('inf'))
        }

        for field, validation in required_fields.items():
            if field not in config:
                return False
            
            value = config[field]
            if isinstance(validation, tuple):
                if not isinstance(value, (int, float)) or value < validation[0] or value > validation[1]:
                    return False
            elif not isinstance(value, validation):
                return False
        
        return True

    @staticmethod
    def validate_processing_config(config: Dict[str, Any]) -> bool:
        """验证处理配置。

        Args:
            config: 处理配置字典。

        Returns:
            bool: 配置是否有效。

        Raises:
            ConfigurationError: 当配置无效时抛出。
        """
        required_fields = {
            "max_workers": (1, 32),
            "timeout_seconds": (1, 3600),
            "retry_count": (0, 10)
        }

        for field, (min_val, max_val) in required_fields.items():
            if field not in config:
                return False
            value = config[field]
            if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                return False
        return True

    @staticmethod
    def _check_nested_field(config: Dict[str, Any], field_path: str) -> bool:
        """检查嵌套字段是否存在。

        Args:
            config: 配置字典。
            field_path: 字段路径，以点号分隔。

        Returns:
            bool: 字段是否存在。

        Raises:
            ConfigurationError: 当字段路径无效时抛出。
        """
        try:
            current = config
            for part in field_path.split("."):
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]
            return True
        except Exception as e:
            raise ConfigurationError(
                message=f"嵌套字段检查失败: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更处理器，监控配置文件的变化。"""

    def __init__(self, config_loader: "ConfigLoader") -> None:
        """初始化处理器。

        Args:
            config_loader: 配置加载器实例。
        """
        super().__init__()
        self.config_loader = config_loader

    def on_modified(self, event: Any) -> None:
        """处理文件修改事件。

        Args:
            event: 文件系统事件。
        """
        if not event.is_directory and event.src_path in self.config_loader.watched_files:
            logger.info(f"Config file changed: {event.src_path}")
            try:
                self.config_loader.reload_config(event.src_path)
            except ConfigurationError as e:
                logger.error(f"Failed to reload config: {e}")


class ConfigLoader:
    """配置加载器，负责加载和管理配置文件。"""

    _instance: Optional["ConfigLoader"] = None
    _lock = Lock()
    _VERSION = "1.0.0"  # 当前配置加载器版本

    def __new__(cls: Type[T], config_dir: Optional[str] = None) -> T:
        """实现单例模式。

        Args:
            config_dir: 配置文件目录路径。

        Returns:
            ConfigLoader: 配置加载器实例。
        """
        with cls._lock:
            if not cls._instance:
                cls._instance = super(ConfigLoader, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """初始化配置加载器。

        Args:
            config_dir: 配置文件目录路径。

        Raises:
            ConfigurationError: 初始化失败时抛出。
        """
        if getattr(self, "_initialized", False):
            return

        try:
            self._config_dir = config_dir or os.path.join(
                os.path.dirname(__file__), "..", "..", "configs"
            )
            self._backup_dir = os.path.join(self._config_dir, "backups")
            self._configs: Dict[str, Dict[str, Any]] = {}
            self._config_versions: Dict[str, str] = {}
            self._config_hashes: Dict[str, str] = {}
            self._config_cache: Dict[Path, Dict[str, Any]] = {}
            self._change_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
            self._lock = Lock()
            self._schema = ConfigSchema()
            
            # 确保备份目录存在
            os.makedirs(self._backup_dir, exist_ok=True)
            
            self.watched_files: List[str] = []
            self.validators: Dict[str, Any] = {
                "security_config.yaml": ConfigValidator.validate_security_config,
                "model_config.yaml": ConfigValidator.validate_model_config,
                "processing_config.yaml": ConfigValidator.validate_processing_config,
            }
            
            # 初始化文件监控
            self.observer = Observer()
            self.observer.schedule(ConfigChangeHandler(self), self._config_dir, recursive=True)
            self.observer.start()
            
            self._initialized = True
            self._load_all_configs()
            
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to initialize config loader: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    def _load_all_configs(self) -> None:
        """加载所有配置文件。

        Raises:
            ConfigurationError: 加载配置失败时抛出。
        """
        try:
            for file_name in os.listdir(self._config_dir):
                file_path = os.path.join(self._config_dir, file_name)
                if os.path.isfile(file_path):
                    self.load_config(file_path)
        except Exception as e:
            logger.error(f"Error loading configs: {e}")
            raise ConfigurationError(
                message=f"Failed to load configurations: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖配置值。

        环境变量格式为 CONFIG_SECTION_KEY，例如：
        CONFIG_MODEL_NAME=my_model 将覆盖 config['model_name']
        CONFIG_RESOURCE_LIMITS_MEMORY=1024 将覆盖 config['resource_limits']['memory']

        Args:
            config: 原始配置字典。

        Returns:
            Dict[str, Any]: 应用环境变量后的配置字典。
        """
        result = copy.deepcopy(config)

        for env_key, env_value in os.environ.items():
            if not env_key.startswith('CONFIG_'):
                continue

            # 移除 CONFIG_ 前缀并转换为小写
            key_path = env_key[7:].lower().split('_')
            
            # 遍历配置字典
            current = result
            for i, key in enumerate(key_path):
                if i == len(key_path) - 1:
                    # 尝试将环境变量值转换为适当的类型
                    try:
                        if isinstance(current.get(key), bool):
                            current[key] = env_value.lower() in ('true', '1', 'yes')
                        elif isinstance(current.get(key), int):
                            current[key] = int(env_value)
                        elif isinstance(current.get(key), float):
                            current[key] = float(env_value)
                        else:
                            current[key] = env_value
                    except (ValueError, TypeError):
                        current[key] = env_value
                else:
                    if key not in current:
                        current[key] = {}
                    elif not isinstance(current[key], dict):
                        current[key] = {}
                    current = current[key]

        return result

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件内容的哈希值。

        Args:
            file_path: 文件路径。

        Returns:
            str: 文件内容的哈希值。
        """
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def register_change_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """注册配置变更回调函数。

        Args:
            callback: 回调函数，接收配置文件名和新的配置内容作为参数。
        """
        self._change_callbacks.append(callback)

    def _notify_config_change(self, config_name: str, new_config: Dict[str, Any]) -> None:
        """通知所有注册的回调函数配置变更。

        Args:
            config_name: 变更的配置文件名。
            new_config: 新的配置内容。
        """
        for callback in self._change_callbacks:
            try:
                callback(config_name, new_config)
            except Exception as e:
                logger.error(f"Error in config change callback: {e}")

    def create_backup(self, config_name: str) -> str:
        """创建配置文件的备份。

        Args:
            config_name: 配置文件名。

        Returns:
            str: 备份文件路径。

        Raises:
            ConfigurationError: 备份失败时抛出。
        """
        try:
            source_path = os.path.join(self._config_dir, config_name)
            if not os.path.exists(source_path):
                raise ConfigurationError(f"Config file not found: {config_name}")

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.splitext(config_name)[0]}_{timestamp}{os.path.splitext(config_name)[1]}"
            backup_path = os.path.join(self._backup_dir, backup_name)

            import shutil
            shutil.copy2(source_path, backup_path)
            
            # 保存版本信息
            self._save_version_info(backup_path, self._config_versions.get(config_name, "1.0.0"))
            
            return backup_path

        except Exception as e:
            raise ConfigurationError(f"Failed to create backup: {e}")

    def restore_from_backup(self, backup_path: str) -> None:
        """从备份恢复配置。

        Args:
            backup_path: 备份文件路径。

        Raises:
            ConfigurationError: 恢复失败时抛出。
        """
        try:
            if not os.path.exists(backup_path):
                raise ConfigurationError(f"Backup file not found: {backup_path}")

            # 获取原始配置文件名
            original_name = os.path.basename(backup_path).split("_")[0] + os.path.splitext(backup_path)[1]
            target_path = os.path.join(self._config_dir, original_name)

            # 在恢复之前创建当前配置的备份
            self.create_backup(original_name)

            import shutil
            shutil.copy2(backup_path, target_path)
            
            # 重新加载配置
            self.reload_config(target_path)

        except Exception as e:
            raise ConfigurationError(f"Failed to restore from backup: {e}")

    def _save_version_info(self, config_path: str, version: str) -> None:
        """保存配置文件的版本信息。

        Args:
            config_path: 配置文件路径。
            version: 版本号。
        """
        version_file = config_path + ".version"
        with open(version_file, "w") as f:
            f.write(version)

    def _load_version_info(self, config_path: str) -> str:
        """加载配置文件的版本信息。

        Args:
            config_path: 配置文件路径。

        Returns:
            str: 版本号，如果未找到则返回默认版本。
        """
        version_file = config_path + ".version"
        try:
            with open(version_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "1.0.0"

    def _migrate_config(self, config: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """迁移配置到新版本。

        Args:
            config: 原配置内容。
            from_version: 原版本号。
            to_version: 目标版本号。

        Returns:
            Dict[str, Any]: 迁移后的配置。

        Raises:
            ConfigurationError: 迁移失败时抛出。
        """
        try:
            # 版本号比较
            from packaging import version
            current = version.parse(from_version)
            target = version.parse(to_version)
            
            if current == target:
                return config
                
            if current > target:
                raise ConfigurationError(f"Cannot downgrade config from {from_version} to {to_version}")

            # 执行迁移
            migrated = config.copy()
            
            # 示例迁移规则
            if current < version.parse("1.1.0"):
                # 迁移到 1.1.0 的变更
                if "security" in migrated:
                    if "max_file_size" in migrated["security"]:
                        migrated["security"]["max_file_size_mb"] = migrated["security"].pop("max_file_size")

            if current < version.parse("1.2.0"):
                # 迁移到 1.2.0 的变更
                if "logging" in migrated:
                    if "level" in migrated["logging"]:
                        migrated["logging"]["log_level"] = migrated["logging"].pop("level")

            return migrated

        except Exception as e:
            raise ConfigurationError(f"Config migration failed: {e}")

    def load_config(self, config_path: Union[str, Path], use_cache: bool = True) -> Dict[str, Any]:
        """加载配置文件。

        Args:
            config_path: 配置文件路径。
            use_cache: 是否使用缓存。

        Returns:
            Dict[str, Any]: 加载的配置字典。

        Raises:
            ConfigError: 配置加载失败时抛出。
        """
        config_path = Path(config_path)
        
        # 如果启用缓存且配置已缓存，返回缓存的配置的深拷贝
        if use_cache and config_path in self._config_cache:
            return copy.deepcopy(self._config_cache[config_path])

        try:
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    raise ConfigError(f"Unsupported config file format: {config_path.suffix}")

            # 加载版本信息
            current_version = self._load_version_info(str(config_path))
            
            # 如果需要，执行配置迁移
            if current_version != self._VERSION:
                config = self._migrate_config(config, current_version, self._VERSION)
                # 保存迁移后的配置和新版本信息
                self.save_config(config, config_path)
                self._save_version_info(str(config_path), self._VERSION)

            # 验证配置
            if not self._validate_config(config):
                raise ConfigError("Configuration validation failed")

            # 应用环境变量覆盖
            config = self._apply_env_overrides(config)

            # 缓存配置的深拷贝
            if use_cache:
                self._config_cache[config_path] = copy.deepcopy(config)
                self._config_versions[str(config_path)] = self._VERSION

            return config

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigError(f"Failed to parse config file: {str(e)}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {str(e)}")

    def get_config_version(self, config_path: str) -> str:
        """获取配置文件的版本。

        Args:
            config_path: 配置文件路径。

        Returns:
            str: 配置文件版本。
        """
        return self._config_versions.get(config_path, "1.0.0")

    def list_backups(self, config_name: str) -> List[str]:
        """列出指定配置文件的所有备份。

        Args:
            config_name: 配置文件名。

        Returns:
            List[str]: 备份文件路径列表。
        """
        base_name = os.path.splitext(config_name)[0]
        pattern = os.path.join(self._backup_dir, f"{base_name}_*.yaml")
        return sorted(glob.glob(pattern))

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置内容。

        Args:
            config: 要验证的配置字典。

        Returns:
            bool: 验证是否通过。

        Raises:
            ConfigError: 验证失败时抛出，包含详细的错误信息。
        """
        try:
            # 使用模式验证器验证配置
            self._schema.validate(config)
            return True
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False

    def get_schema(self) -> ConfigSchema:
        """获取配置模式。

        Returns:
            ConfigSchema: 配置模式实例。
        """
        return self._schema

    def create_default_config(self, config_path: Union[str, Path]) -> None:
        """创建默认配置文件。

        Args:
            config_path: 配置文件路径。

        Raises:
            ConfigurationError: 创建失败时抛出。
        """
        try:
            config_path = Path(config_path)
            default_config = self._schema.get_default_config()
            
            # 确保目录存在
            os.makedirs(config_path.parent, exist_ok=True)
            
            # 保存默认配置
            self.save_config(default_config, config_path)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create default config: {e}")

    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置文件。

        Args:
            config_path: 配置文件路径。

        Returns:
            Dict[str, Any]: 重新加载的配置内容。

        Raises:
            ConfigurationError: 重新加载失败时抛出。
        """
        try:
            return self.load_config(config_path)
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to reload config {config_path}: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置。

        Args:
            config_name: 配置文件名。

        Returns:
            Optional[Dict[str, Any]]: 配置内容，如果不存在则返回None。
        """
        return self._configs.get(config_name)

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置。

        Returns:
            Dict[str, Dict[str, Any]]: 所有配置的字典。
        """
        return self._configs.copy()

    def save_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """保存配置。

        Args:
            config_name: 配置文件名。
            config: 配置内容。

        Raises:
            ConfigurationError: 保存失败时抛出。
        """
        try:
            config_path = os.path.join(self._config_dir, config_name)
            file_ext = os.path.splitext(config_name)[1].lower()

            with self._lock:
                if file_ext == ".json":
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                elif file_ext in [".yaml", ".yml"]:
                    with open(config_path, "w", encoding="utf-8") as f:
                        yaml.safe_dump(config, f, allow_unicode=True)
                else:
                    raise ConfigurationError(
                        message=f"不支持的配置文件格式: {file_ext}",
                        code=ErrorCode.CONFIGURATION_ERROR
                    )

                self._configs[config_name] = config
                if config_path not in self.watched_files:
                    self.watched_files.append(config_path)
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to save config {config_name}: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    def __del__(self) -> None:
        """清理资源。"""
        try:
            if hasattr(self, "observer"):
                self.observer.stop()
                self.observer.join()
        except Exception as e:
            logger.error(f"Error stopping observer: {e}")

    def merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个配置。

        Args:
            configs: 要合并的配置列表。

        Returns:
            Dict[str, Any]: 合并后的配置。

        Note:
            - 字典会递归合并
            - 列表会被后面的配置完全替换
            - 简单类型会被后面的配置覆盖
        """
        def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
            merged = base.copy()
            for key, value in update.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = deep_merge(merged[key], value)
                else:
                    merged[key] = value
            return merged

        if not configs:
            return {}
        
        result = configs[0].copy()
        for config in configs[1:]:
            result = deep_merge(result, config)
        return result

    def save_config(self, config: Dict[str, Any], save_path: Union[str, Path]) -> None:
        """保存配置到文件。

        Args:
            config: 要保存的配置内容。
            save_path: 保存路径。

        Raises:
            ConfigurationError: 保存失败时抛出。
        """
        try:
            save_path = str(save_path)
            file_ext = os.path.splitext(save_path)[1].lower()

            # 处理敏感信息
            config = self._mask_sensitive_info(config.copy())

            with open(save_path, "w", encoding="utf-8") as f:
                if file_ext == ".json":
                    json.dump(config, f, indent=4, ensure_ascii=False)
                elif file_ext in [".yaml", ".yml"]:
                    yaml.safe_dump(config, f, allow_unicode=True)
                else:
                    raise ConfigurationError(
                        message=f"不支持的配置文件格式: {file_ext}",
                        code=ErrorCode.CONFIGURATION_ERROR
                    )

        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to save config to {save_path}: {e}",
                code=ErrorCode.CONFIGURATION_ERROR
            )

    def _mask_sensitive_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """掩码敏感信息。

        Args:
            config: 配置字典。

        Returns:
            Dict[str, Any]: 处理后的配置。
        """
        sensitive_fields = ["password", "api_key", "secret", "token"]
        
        def mask_dict(d: Dict[str, Any]) -> None:
            for key, value in d.items():
                if isinstance(value, dict):
                    mask_dict(value)
                elif any(field in key.lower() for field in sensitive_fields):
                    d[key] = "******"
        
        mask_dict(config)
        return config


def get_config_loader(config_dir: Optional[str] = None) -> ConfigLoader:
    """获取配置加载器实例。

    Args:
        config_dir: 配置文件目录路径。

    Returns:
        ConfigLoader: 配置加载器实例。
    """
    return ConfigLoader(config_dir)
