"""
配置加载器
提供监控配置的加载和管理功能
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class MonitorConfig:
    """监控配置管理器"""
    
    def __init__(self, config_file: str = "configs/monitor_config.yaml"):
        self.config_file = Path(config_file)
        self.config_data: Dict[str, Any] = {}
        self.default_config = self._get_default_config()
        
        # 加载配置
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "monitoring": {
                "enabled": True,
                "update_interval_ms": 2000,
                "auto_start": False,
                "log_level": "INFO"
            },
            "performance": {
                "auto_mode": True,
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "disk_threshold": 90.0,
                "network_threshold": 75.0
            },
            "alerts": {
                "enabled": True,
                "cpu_alert": True,
                "memory_alert": True,
                "disk_alert": True,
                "network_alert": False
            },
            "display": {
                "show_graphs": True,
                "show_processes": True,
                "show_logs": True,
                "max_log_lines": 100,
                "refresh_rate": "normal"
            },
            "resources": {
                "low_spec_mode": False,
                "max_memory_mb": 512,
                "max_cpu_percent": 50.0,
                "cache_size_mb": 64
            }
        }
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                if self.config_file.suffix.lower() == '.json':
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self.config_data = json.load(f)
                elif self.config_file.suffix.lower() in ['.yaml', '.yml']:
                    try:
                        import yaml
                        with open(self.config_file, 'r', encoding='utf-8') as f:
                            self.config_data = yaml.safe_load(f)
                    except ImportError:
                        print("[WARN] PyYAML未安装，无法加载YAML配置文件")
                        self.config_data = self.default_config.copy()
                else:
                    print(f"[WARN] 不支持的配置文件格式: {self.config_file.suffix}")
                    self.config_data = self.default_config.copy()
            else:
                print(f"[INFO] 配置文件不存在，使用默认配置: {self.config_file}")
                self.config_data = self.default_config.copy()
                self.save_config()  # 保存默认配置
            
            # 合并默认配置（确保所有必需的键都存在）
            self._merge_default_config()
            
            print("[OK] 监控配置加载完成")
            return True
            
        except Exception as e:
            print(f"[WARN] 加载配置失败: {e}")
            self.config_data = self.default_config.copy()
            return False
    
    def _merge_default_config(self):
        """合并默认配置"""
        try:
            def merge_dict(default: dict, current: dict) -> dict:
                """递归合并字典"""
                result = default.copy()
                for key, value in current.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dict(result[key], value)
                    else:
                        result[key] = value
                return result
            
            self.config_data = merge_dict(self.default_config, self.config_data)
            
        except Exception as e:
            print(f"[WARN] 合并默认配置失败: {e}")
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self.config_file.suffix.lower() == '.json':
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            elif self.config_file.suffix.lower() in ['.yaml', '.yml']:
                try:
                    import yaml
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        yaml.dump(self.config_data, f, default_flow_style=False, 
                                allow_unicode=True, indent=2)
                except ImportError:
                    print("[WARN] PyYAML未安装，无法保存YAML配置文件")
                    return False
            
            print(f"[OK] 配置已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"[WARN] 保存配置失败: {e}")
            return False
    
    def get_config(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 "monitoring.enabled"
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key_path.split('.')
            value = self.config_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            print(f"[WARN] 获取配置失败: {e}")
            return default
    
    def set_config(self, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径
            value: 配置值
            
        Returns:
            是否成功设置
        """
        try:
            keys = key_path.split('.')
            config = self.config_data
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置值
            config[keys[-1]] = value
            
            print(f"[OK] 配置已更新: {key_path} = {value}")
            return True
            
        except Exception as e:
            print(f"[WARN] 设置配置失败: {e}")
            return False
    
    def update_nested_config(self, key_path: str, value: Any) -> bool:
        """更新嵌套配置（别名）"""
        return self.set_config(key_path, value)
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.get_config("monitoring", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.get_config("performance", {})
    
    def get_alerts_config(self) -> Dict[str, Any]:
        """获取警告配置"""
        return self.get_config("alerts", {})
    
    def get_display_config(self) -> Dict[str, Any]:
        """获取显示配置"""
        return self.get_config("display", {})
    
    def get_resources_config(self) -> Dict[str, Any]:
        """获取资源配置"""
        return self.get_config("resources", {})
    
    def is_low_spec_mode(self) -> bool:
        """是否为低规格模式"""
        return self.get_config("resources.low_spec_mode", False)
    
    def enable_low_spec_mode(self, enabled: bool = True) -> bool:
        """启用/禁用低规格模式"""
        success = self.set_config("resources.low_spec_mode", enabled)
        if success and enabled:
            # 应用低规格设置
            self.set_config("performance.auto_mode", False)
            self.set_config("resources.max_memory_mb", 256)
            self.set_config("resources.max_cpu_percent", 30.0)
            self.set_config("resources.cache_size_mb", 32)
            self.set_config("display.show_graphs", False)
            self.set_config("monitoring.update_interval_ms", 5000)
        return success
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.config_data = self.default_config.copy()
            return self.save_config()
        except Exception as e:
            print(f"[WARN] 重置配置失败: {e}")
            return False
    
    def get_config_summary(self) -> str:
        """获取配置摘要"""
        try:
            monitoring = self.get_monitoring_config()
            performance = self.get_performance_config()
            resources = self.get_resources_config()
            
            summary = [
                "=== 监控配置摘要 ===",
                f"监控启用: {'是' if monitoring.get('enabled', False) else '否'}",
                f"更新间隔: {monitoring.get('update_interval_ms', 0)}ms",
                f"自动模式: {'是' if performance.get('auto_mode', False) else '否'}",
                f"低规格模式: {'是' if resources.get('low_spec_mode', False) else '否'}",
                f"内存限制: {resources.get('max_memory_mb', 0)}MB",
                f"CPU限制: {resources.get('max_cpu_percent', 0)}%",
                f"配置文件: {self.config_file}"
            ]
            
            return "\n".join(summary)
            
        except Exception as e:
            return f"获取配置摘要失败: {e}"

# 全局配置实例
monitor_config: Optional[MonitorConfig] = None

def get_monitor_config() -> MonitorConfig:
    """获取全局监控配置"""
    global monitor_config
    if monitor_config is None:
        monitor_config = MonitorConfig()
    return monitor_config

def load_monitor_config(config_file: str = "configs/monitor_config.yaml") -> MonitorConfig:
    """加载监控配置"""
    global monitor_config
    monitor_config = MonitorConfig(config_file)
    return monitor_config

__all__ = [
    'MonitorConfig',
    'monitor_config',
    'get_monitor_config',
    'load_monitor_config'
]
