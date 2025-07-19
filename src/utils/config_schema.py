"""配置模式验证模块。

此模块提供配置文件的模式定义和验证功能。
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import re

from .exceptions import ConfigurationError, ValidationError


@dataclass
class ConfigField:
    """配置字段定义。"""
    
    name: str
    field_type: type
    required: bool = True
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    description: str = ""

    def validate(self, value: Any) -> Any:
        """验证字段值。

        Args:
            value: 要验证的值。

        Returns:
            Any: 验证后的值（可能经过转换）。

        Raises:
            ValidationError: 验证失败时抛出。
        """
        if value is None:
            if self.required:
                raise ValidationError(f"Field {self.name} is required")
            return self.default

        # 类型检查和转换
        try:
            value = self.field_type(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Field {self.name} must be of type {self.field_type.__name__}"
            )

        # 数值范围检查
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(
                    f"Field {self.name} must be >= {self.min_value}"
                )
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(
                    f"Field {self.name} must be <= {self.max_value}"
                )

        # 允许值检查
        if self.allowed_values is not None and value not in self.allowed_values:
            raise ValidationError(
                f"Field {self.name} must be one of {self.allowed_values}"
            )

        # 字符串模式匹配
        if isinstance(value, str) and self.pattern:
            if not re.match(self.pattern, value):
                raise ValidationError(
                    f"Field {self.name} must match pattern {self.pattern}"
                )

        return value


class ConfigSchema:
    """配置模式定义。"""

    def __init__(self) -> None:
        """初始化配置模式。"""
        self.fields: Dict[str, ConfigField] = {}
        self._define_schema()

    def _define_schema(self) -> None:
        """定义配置模式。

        在此方法中定义所有配置字段。
        """
        # 应用配置
        self.fields.update({
            "app.name": ConfigField(
                name="name",
                field_type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                description="应用名称"
            ),
            "app.version": ConfigField(
                name="version",
                field_type=str,
                required=True,
                pattern=r"^\d+\.\d+\.\d+$",
                description="应用版本"
            ),
            "app.debug": ConfigField(
                name="debug",
                field_type=bool,
                required=False,
                default=False,
                description="调试模式"
            ),
            "app.temp_dir": ConfigField(
                name="temp_dir",
                field_type=str,
                required=True,
                description="临时目录路径"
            ),
            "app.max_memory_mb": ConfigField(
                name="max_memory_mb",
                field_type=int,
                required=True,
                min_value=128,
                max_value=32768,
                description="最大内存限制(MB)"
            ),
        })

        # 安全配置
        self.fields.update({
            "security.enable_encryption": ConfigField(
                name="enable_encryption",
                field_type=bool,
                required=True,
                description="是否启用加密"
            ),
            "security.allowed_file_types": ConfigField(
                name="allowed_file_types",
                field_type=list,
                required=True,
                description="允许的文件类型列表"
            ),
            "security.max_file_size_mb": ConfigField(
                name="max_file_size_mb",
                field_type=int,
                required=True,
                min_value=1,
                max_value=10240,
                description="最大文件大小(MB)"
            ),
        })

        # 日志配置
        self.fields.update({
            "logging.log_level": ConfigField(
                name="log_level",
                field_type=str,
                required=True,
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                description="日志级别"
            ),
            "logging.file_path": ConfigField(
                name="file_path",
                field_type=str,
                required=True,
                description="日志文件路径"
            ),
            "logging.max_size_mb": ConfigField(
                name="max_size_mb",
                field_type=int,
                required=True,
                min_value=1,
                max_value=1024,
                description="日志文件最大大小(MB)"
            ),
            "logging.backup_count": ConfigField(
                name="backup_count",
                field_type=int,
                required=True,
                min_value=0,
                max_value=100,
                description="日志文件备份数量"
            ),
        })

    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置。

        Args:
            config: 要验证的配置字典。

        Returns:
            Dict[str, Any]: 验证后的配置。

        Raises:
            ValidationError: 验证失败时抛出。
        """
        validated = {}
        
        for path, field in self.fields.items():
            # 解析字段路径
            parts = path.split(".")
            current = config
            
            # 遍历配置层级
            try:
                for part in parts[:-1]:
                    current = current[part]
                value = current.get(parts[-1])
            except (KeyError, TypeError):
                value = None
            
            # 验证字段值
            try:
                validated_value = field.validate(value)
                
                # 构建验证后的配置字典
                current = validated
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = validated_value
                
            except ValidationError as e:
                raise ValidationError(f"Validation failed for path {path}: {str(e)}")
        
        return validated

    def get_field(self, path: str) -> Optional[ConfigField]:
        """获取指定路径的字段定义。

        Args:
            path: 字段路径。

        Returns:
            Optional[ConfigField]: 字段定义，如果不存在则返回 None。
        """
        return self.fields.get(path)

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置。

        Returns:
            Dict[str, Any]: 包含所有字段默认值的配置字典。
        """
        defaults = {}
        
        for path, field in self.fields.items():
            if field.default is not None:
                parts = path.split(".")
                current = defaults
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = field.default
        
        return defaults 