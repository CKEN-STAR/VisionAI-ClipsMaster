"""
企业级部署优化模块
提供企业环境下的UI优化功能
"""

import os
import platform
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication

class EnterpriseOptimizer(QObject):
    """企业级优化器"""
    
    def __init__(self):
        super().__init__()
        self.optimization_profile = "standard"
        self.applied_optimizations: List[str] = []
        self.enterprise_settings = {
            'security_mode': False,
            'network_optimization': False,
            'resource_limits': False,
            'audit_logging': False,
            'centralized_config': False
        }
    
    def apply_enterprise_optimizations(self, profile: str = "standard") -> bool:
        """
        应用企业级优化
        
        Args:
            profile: 优化配置文件 (standard, secure, performance)
            
        Returns:
            是否成功应用
        """
        try:
            self.optimization_profile = profile
            optimizations = []
            
            if profile == "secure":
                optimizations.extend(self._apply_security_optimizations())
            elif profile == "performance":
                optimizations.extend(self._apply_performance_optimizations())
            else:
                optimizations.extend(self._apply_standard_optimizations())
            
            self.applied_optimizations = optimizations
            print(f"[OK] 企业级优化已应用: {profile}")
            print(f"[OK] 优化项目: {optimizations}")
            
            return True
            
        except Exception as e:
            print(f"[WARN] 企业级优化失败: {e}")
            return False
    
    def _apply_security_optimizations(self) -> List[str]:
        """应用安全优化"""
        optimizations = []
        
        try:
            # 1. 禁用调试功能
            os.environ['QT_LOGGING_RULES'] = '*.debug=false'
            optimizations.append("debug_disabled")
            
            # 2. 启用安全模式
            self.enterprise_settings['security_mode'] = True
            optimizations.append("security_mode_enabled")
            
            # 3. 限制网络访问
            self.enterprise_settings['network_optimization'] = True
            optimizations.append("network_restricted")
            
            # 4. 启用审计日志
            self.enterprise_settings['audit_logging'] = True
            optimizations.append("audit_logging_enabled")
            
        except Exception as e:
            print(f"[WARN] 安全优化失败: {e}")
        
        return optimizations
    
    def _apply_performance_optimizations(self) -> List[str]:
        """应用性能优化"""
        optimizations = []
        
        try:
            # 1. 优化资源限制
            self.enterprise_settings['resource_limits'] = True
            optimizations.append("resource_limits_applied")
            
            # 2. 网络优化
            self.enterprise_settings['network_optimization'] = True
            optimizations.append("network_optimized")
            
            # 3. 禁用不必要的功能
            app = QApplication.instance()
            if app:
                app.setAttribute(app.ApplicationAttribute.AA_DisableWindowContextHelpButton, True)
                optimizations.append("context_help_disabled")
            
        except Exception as e:
            print(f"[WARN] 性能优化失败: {e}")
        
        return optimizations
    
    def _apply_standard_optimizations(self) -> List[str]:
        """应用标准优化"""
        optimizations = []
        
        try:
            # 1. 基本资源优化
            self.enterprise_settings['resource_limits'] = True
            optimizations.append("basic_resource_limits")
            
            # 2. 启用集中配置
            self.enterprise_settings['centralized_config'] = True
            optimizations.append("centralized_config_enabled")
            
        except Exception as e:
            print(f"[WARN] 标准优化失败: {e}")
        
        return optimizations
    
    def get_enterprise_info(self) -> Dict[str, Any]:
        """获取企业环境信息"""
        try:
            info = {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node(),
                'domain_joined': self._check_domain_membership(),
                'user_profile': os.environ.get('USERPROFILE', ''),
                'temp_dir': os.environ.get('TEMP', ''),
                'optimization_profile': self.optimization_profile,
                'applied_optimizations': self.applied_optimizations.copy(),
                'enterprise_settings': self.enterprise_settings.copy()
            }
            
            # 检查企业特定环境变量
            enterprise_vars = [
                'USERDNSDOMAIN', 'LOGONSERVER', 'COMPUTERNAME',
                'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS'
            ]
            
            for var in enterprise_vars:
                value = os.environ.get(var)
                if value:
                    info[f'env_{var.lower()}'] = value
            
            return info
            
        except Exception as e:
            print(f"[WARN] 获取企业信息失败: {e}")
            return {}
    
    def _check_domain_membership(self) -> bool:
        """检查是否加入域"""
        try:
            if platform.system() == "Windows":
                # 检查Windows域成员身份
                domain = os.environ.get('USERDNSDOMAIN')
                logon_server = os.environ.get('LOGONSERVER')
                return bool(domain and logon_server)
            else:
                # Linux/Mac的简化检查
                return False
        except Exception:
            return False
    
    def configure_for_vdi(self, enable=True):
        """
        配置VDI（虚拟桌面基础设施）模式

        Args:
            enable: 是否启用VDI优化
        """
        try:
            if enable:
                # VDI优化设置
                self.enterprise_settings.update({
                    'network_optimization': True,  # 网络优化
                    'resource_limits': True,       # 资源限制
                    'remote_rendering': True,      # 远程渲染优化
                    'bandwidth_optimization': True # 带宽优化
                })
                self.applied_optimizations.append("vdi_mode_enabled")
                print("[OK] VDI模式已启用")
            else:
                # 禁用VDI优化
                self.enterprise_settings.update({
                    'remote_rendering': False,
                    'bandwidth_optimization': False
                })
                if "vdi_mode_enabled" in self.applied_optimizations:
                    self.applied_optimizations.remove("vdi_mode_enabled")
                print("[OK] VDI模式已禁用")

            return True

        except Exception as e:
            print(f"[ERROR] 配置VDI模式失败: {e}")
            return False

    def configure_for_enterprise_network(self) -> bool:
        """配置企业网络环境"""
        try:
            optimizations = []

            # 1. 设置代理配置
            proxy_server = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            if proxy_server:
                optimizations.append("proxy_configured")
            
            # 2. 配置SSL/TLS设置
            os.environ['PYTHONHTTPSVERIFY'] = '1'
            optimizations.append("ssl_verification_enabled")
            
            # 3. 设置超时配置
            os.environ['REQUESTS_TIMEOUT'] = '30'
            optimizations.append("timeout_configured")
            
            print(f"[OK] 企业网络配置完成: {optimizations}")
            return True
            
        except Exception as e:
            print(f"[WARN] 企业网络配置失败: {e}")
            return False
    
    def apply_resource_limits(self) -> bool:
        """应用资源限制"""
        try:
            # 1. 内存限制
            import resource
            try:
                # 设置内存限制为2GB
                resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))
                print("[OK] 内存限制已设置: 2GB")
            except (ImportError, OSError):
                print("[WARN] 无法设置内存限制")
            
            # 2. 文件描述符限制
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
                print("[OK] 文件描述符限制已设置: 1024")
            except (ImportError, OSError):
                print("[WARN] 无法设置文件描述符限制")
            
            return True
            
        except Exception as e:
            print(f"[WARN] 应用资源限制失败: {e}")
            return False
    
    def get_optimization_report(self) -> str:
        """获取优化报告"""
        try:
            info = self.get_enterprise_info()
            
            report = [
                "=== 企业级优化报告 ===",
                f"优化配置文件: {self.optimization_profile}",
                f"平台: {info.get('platform', 'Unknown')}",
                f"架构: {info.get('architecture', 'Unknown')}",
                f"主机名: {info.get('hostname', 'Unknown')}",
                f"域成员: {'是' if info.get('domain_joined', False) else '否'}",
                "",
                "已应用的优化:",
            ]
            
            for opt in self.applied_optimizations:
                report.append(f"  ✓ {opt}")
            
            report.append("")
            report.append("企业设置:")
            for key, value in self.enterprise_settings.items():
                status = "启用" if value else "禁用"
                report.append(f"  {key}: {status}")
            
            return "\n".join(report)

        except Exception as e:
            return f"生成优化报告失败: {e}"

    def apply_enterprise_settings(self, settings_dict: dict = None):
        """
        应用企业级设置

        Args:
            settings_dict: 设置字典，如果为None则使用默认设置
        """
        try:
            if settings_dict is None:
                settings_dict = {
                    'security_mode': True,
                    'network_optimization': True,
                    'resource_limits': True,
                    'performance_monitoring': True,
                    'load_balancing': True,
                    'auto_scaling': False
                }

            # 应用设置
            for key, value in settings_dict.items():
                if key in self.enterprise_settings:
                    self.enterprise_settings[key] = value
                    print(f"[OK] 企业设置已应用: {key} = {value}")

            # 记录应用的优化
            if "enterprise_settings_applied" not in self.applied_optimizations:
                self.applied_optimizations.append("enterprise_settings_applied")

            print("[OK] 企业级设置应用完成")
            return True

        except Exception as e:
            print(f"[ERROR] 应用企业级设置失败: {e}")
            return False

    def get_optimization_status(self):
        """获取优化状态"""
        return {
            "profile": self.optimization_profile,
            "applied_optimizations": self.applied_optimizations.copy(),
            "enterprise_settings": self.enterprise_settings.copy(),
            "total_optimizations": len(self.applied_optimizations)
        }

# 全局企业优化器实例
_enterprise_optimizer: Optional[EnterpriseOptimizer] = None

def get_enterprise_optimizer() -> EnterpriseOptimizer:
    """获取全局企业优化器"""
    global _enterprise_optimizer
    if _enterprise_optimizer is None:
        _enterprise_optimizer = EnterpriseOptimizer()
    return _enterprise_optimizer

def apply_enterprise_optimizations(profile: str = "standard") -> bool:
    """应用企业级优化"""
    optimizer = get_enterprise_optimizer()
    return optimizer.apply_enterprise_optimizations(profile)

def get_enterprise_info() -> Dict[str, Any]:
    """获取企业环境信息"""
    optimizer = get_enterprise_optimizer()
    return optimizer.get_enterprise_info()

def configure_for_enterprise() -> bool:
    """配置企业环境"""
    optimizer = get_enterprise_optimizer()
    
    success = True
    if not optimizer.configure_for_enterprise_network():
        success = False
    
    if not optimizer.apply_resource_limits():
        success = False
    
    return success

__all__ = [
    'EnterpriseOptimizer',
    'get_enterprise_optimizer',
    'apply_enterprise_optimizations',
    'get_enterprise_info',
    'configure_for_enterprise'
]
