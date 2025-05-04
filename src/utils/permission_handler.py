"""文件权限处理模块

此模块负责处理文件系统权限，确保数据和模型的安全性。
主要功能包括：
1. 设置和验证文件权限
2. 管理目录访问控制
3. 实现文件隔离策略
4. 监控文件系统变化
"""

import os
import stat
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from src.utils.exceptions import PermissionError


class PermissionHandler:
    """权限处理器类"""

    def __init__(self):
        """初始化权限处理器"""
        self.is_windows = platform.system() == 'Windows'
        self.permission_map = {
            'data': 0o750,    # rwxr-x---
            'models': 0o750,  # rwxr-x---
            'cache': 0o700,   # rwx------
            'logs': 0o740,    # rwxr-----
            'config': 0o640   # rw-r-----
        }

    def set_file_permissions(self, file_path: str, permission: int) -> bool:
        """设置文件权限
        
        Args:
            file_path: 文件路径
            permission: 权限值（八进制）
            
        Returns:
            bool: 是否成功设置权限
        """
        try:
            if self.is_windows:
                # Windows系统使用icacls命令设置权限
                # 首先移除所有继承的权限
                subprocess.run(f'icacls "{file_path}" /inheritance:d', shell=True, check=True)
                subprocess.run(f'icacls "{file_path}" /remove:g "*S-1-1-0"', shell=True, check=True)  # 移除Everyone组
                
                # 构建权限字符串
                perms = []
                if permission & stat.S_IRUSR:
                    perms.append('(R)')
                if permission & stat.S_IWUSR:
                    perms.append('(W)')
                if permission & stat.S_IXUSR:
                    perms.append('(X)')
                    
                perm_str = ''.join(perms)
                if perm_str:
                    # 为当前用户和管理员组设置权限
                    subprocess.run(f'icacls "{file_path}" /grant:r "*S-1-5-32-544:{perm_str}"', shell=True, check=True)  # Administrators
                    subprocess.run(f'icacls "{file_path}" /grant:r "%USERNAME%:{perm_str}"', shell=True, check=True)  # Current user
            else:
                os.chmod(file_path, permission)
            return True
        except Exception as e:
            logger.error(f"设置文件 {file_path} 权限失败: {str(e)}")
            return False

    def set_directory_permissions(self, directory: str, recursive: bool = True) -> bool:
        """设置目录权限
        
        Args:
            directory: 目录路径
            recursive: 是否递归设置子目录
            
        Returns:
            bool: 是否成功设置权限
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                logger.warning(f"目录不存在: {directory}")
                return False
                
            # 确定目录类型和对应的权限
            dir_type = None
            for type_name in self.permission_map:
                if type_name in str(dir_path):
                    dir_type = type_name
                    break
                    
            if not dir_type:
                logger.warning(f"未知目录类型: {directory}")
                return False
                
            # 设置目录权限
            permission = self.permission_map[dir_type]
            success = self.set_file_permissions(str(dir_path), permission)
            
            if not success:
                return False
                
            # 递归设置子目录和文件的权限
            if recursive:
                for root, dirs, files in os.walk(directory):
                    # 设置子目录权限
                    for d in dirs:
                        path = os.path.join(root, d)
                        if not self.set_file_permissions(path, permission):
                            return False
                            
                    # 设置文件权限
                    for f in files:
                        path = os.path.join(root, f)
                        if not self.set_file_permissions(path, permission):
                            return False
                            
            return True
            
        except Exception as e:
            logger.error(f"设置目录 {directory} 权限失败: {str(e)}")
            return False

    def verify_permissions(self, path: str) -> bool:
        """验证文件或目录权限
        
        Args:
            path: 文件或目录路径
            
        Returns:
            bool: 权限是否符合要求
        """
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return False
                
            # 确定路径类型和对应的权限
            path_type = None
            for type_name in self.permission_map:
                if type_name in str(path_obj):
                    path_type = type_name
                    break
                    
            if not path_type:
                return False
                
            expected_permission = self.permission_map[path_type]
            
            if self.is_windows:
                try:
                    # Windows系统使用icacls检查权限
                    result = subprocess.run(
                        f'icacls "{path}"',
                        shell=True,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    output = result.stdout.lower()
                    
                    # 检查是否有正确的权限设置
                    has_admin = 'administrators' in output and ('(f)' in output or all(p in output for p in ['(r)', '(w)', '(x)']))
                    has_user = '%username%' in output.lower() and all(
                        ('(r)' in output) if expected_permission & stat.S_IRUSR else True,
                        ('(w)' in output) if expected_permission & stat.S_IWUSR else True,
                        ('(x)' in output) if expected_permission & stat.S_IXUSR else True
                    )
                    
                    return has_admin and has_user
                except subprocess.CalledProcessError:
                    return False
            else:
                # Unix系统直接检查权限值
                current_permission = stat.S_IMODE(os.stat(path).st_mode)
                return current_permission == expected_permission
                
        except Exception as e:
            logger.error(f"验证权限失败: {str(e)}")
            return False

    def secure_path(self, path: str, is_directory: bool = False) -> bool:
        """安全化路径
        
        Args:
            path: 文件或目录路径
            is_directory: 是否是目录
            
        Returns:
            bool: 是否成功安全化
        """
        try:
            if is_directory:
                return self.set_directory_permissions(path, recursive=True)
            else:
                # 确定文件类型和对应的权限
                file_type = None
                for type_name in self.permission_map:
                    if type_name in path:
                        file_type = type_name
                        break
                        
                if not file_type:
                    logger.warning(f"未知文件类型: {path}")
                    return False
                    
                return self.set_file_permissions(path, self.permission_map[file_type])
                
        except Exception as e:
            logger.error(f"安全化路径失败: {str(e)}")
            return False

    def get_permission_status(self, base_dir: str) -> Dict[str, List[str]]:
        """获取权限状态报告
        
        Args:
            base_dir: 基础目录
            
        Returns:
            Dict[str, List[str]]: 权限状态报告
        """
        status = {
            'secure': [],
            'insecure': [],
            'errors': []
        }
        
        try:
            for root, dirs, files in os.walk(base_dir):
                # 检查目录权限
                for d in dirs:
                    path = os.path.join(root, d)
                    if self.verify_permissions(path):
                        status['secure'].append(path)
                    else:
                        status['insecure'].append(path)
                        
                # 检查文件权限
                for f in files:
                    path = os.path.join(root, f)
                    if self.verify_permissions(path):
                        status['secure'].append(path)
                    else:
                        status['insecure'].append(path)
                        
        except Exception as e:
            status['errors'].append(str(e))
            
        return status

    def monitor_permission_changes(self, callback: Optional[callable] = None) -> None:
        """监控权限变化
        
        Args:
            callback: 权限变化时的回调函数
        """
        # TODO: 实现文件系统监控
        # 这需要使用特定平台的API或第三方库
        pass 