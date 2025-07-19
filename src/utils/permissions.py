"""
权限管理工具
用于处理文件和目录的权限设置
"""

import os
import stat
import platform
from pathlib import Path
from typing import Union, List
from loguru import logger

class PermissionManager:
    @staticmethod
    def set_readonly(path: Union[str, Path]) -> bool:
        """设置文件或目录为只读"""
        try:
            if platform.system() == 'Windows':
                os.chmod(path, stat.S_IREAD)
            else:
                os.chmod(path, 0o444)
            return True
        except Exception as e:
            logger.error(f"设置只读权限失败 {path}: {str(e)}")
            return False

    @staticmethod
    def set_writable(path: Union[str, Path]) -> bool:
        """设置文件或目录为可写"""
        try:
            if platform.system() == 'Windows':
                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
            else:
                os.chmod(path, 0o666)
            return True
        except Exception as e:
            logger.error(f"设置可写权限失败 {path}: {str(e)}")
            return False

    @staticmethod
    def set_executable(path: Union[str, Path]) -> bool:
        """设置文件为可执行（主要用于Unix系统）"""
        try:
            if platform.system() != 'Windows':
                current = os.stat(path).st_mode
                os.chmod(path, current | stat.S_IEXEC)
            return True
        except Exception as e:
            logger.error(f"设置可执行权限失败 {path}: {str(e)}")
            return False

    @staticmethod
    def secure_directory(directory: Union[str, Path], recursive: bool = False) -> bool:
        """
        安全地设置目录权限
        - 确保目录存在
        - 设置适当的访问权限
        - 可选择是否递归处理子目录
        """
        try:
            directory = Path(directory)
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

            if platform.system() == 'Windows':
                # Windows下使用ACL
                import win32security
                import win32file
                import ntsecuritycon as con

                # 获取安全描述符
                security = win32security.GetFileSecurity(
                    str(directory),
                    win32security.DACL_SECURITY_INFORMATION
                )

                # 获取DACL
                dacl = security.GetSecurityDescriptorDacl()
                
                # 清除现有的ACL
                dacl.DeleteAce(0)
                
                # 添加新的ACE
                # 系统完全控制
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_ALL_ACCESS,
                    win32security.CreateWellKnownSid(win32security.WinLocalSystemSid)
                )
                
                # 管理员完全控制
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_ALL_ACCESS,
                    win32security.CreateWellKnownSid(win32security.WinBuiltinAdministratorsSid)
                )
                
                # 用户只读和执行
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_GENERIC_READ | con.FILE_GENERIC_EXECUTE,
                    win32security.CreateWellKnownSid(win32security.WinBuiltinUsersSid)
                )

                # 应用新的安全描述符
                security.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    str(directory),
                    win32security.DACL_SECURITY_INFORMATION,
                    security
                )
            else:
                # Unix系统使用传统权限
                os.chmod(directory, 0o755)  # rwxr-xr-x

            if recursive:
                for item in directory.rglob('*'):
                    if item.is_dir():
                        PermissionManager.secure_directory(item, False)
                    else:
                        if platform.system() == 'Windows':
                            os.chmod(item, stat.S_IREAD | stat.S_IWRITE)
                        else:
                            os.chmod(item, 0o644)  # rw-r--r--

            return True
        except Exception as e:
            logger.error(f"设置目录权限失败 {directory}: {str(e)}")
            return False

    @staticmethod
    def verify_permissions(path: Union[str, Path]) -> bool:
        """验证文件或目录的权限是否正确"""
        try:
            path = Path(path)
            if not path.exists():
                return False

            if platform.system() == 'Windows':
                # Windows下检查ACL
                import win32security
                security = win32security.GetFileSecurity(
                    str(path),
                    win32security.DACL_SECURITY_INFORMATION
                )
                dacl = security.GetSecurityDescriptorDacl()
                return dacl is not None
            else:
                # Unix系统检查基本权限
                mode = os.stat(path).st_mode
                if path.is_dir():
                    return bool(mode & stat.S_IRUSR and mode & stat.S_IXUSR)
                else:
                    return bool(mode & stat.S_IRUSR)

        except Exception as e:
            logger.error(f"验证权限失败 {path}: {str(e)}")
            return False 