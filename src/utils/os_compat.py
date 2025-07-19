"""多平台兼容处理模块

此模块负责处理不同操作系统平台的特定功能，包括：
1. 系统特性检测
2. 平台特定命令生成
3. 路径处理兼容
4. 系统资源管理
5. 进程控制适配
"""

import os
import sys
import platform
import ctypes
import subprocess
from typing import Dict, List, Optional, Union
from pathlib import Path
from loguru import logger

class OSCompat:
    """操作系统兼容性处理类"""
    
    def __init__(self):
        """初始化平台兼容处理器"""
        self.system = platform.system()
        self.machine = platform.machine()
        self.is_64bit = sys.maxsize > 2**32
        self.platform_info = self._get_platform_info()
        
    def _get_platform_info(self) -> Dict[str, str]:
        """获取详细的平台信息
        
        Returns:
            Dict[str, str]: 平台信息字典
        """
        info = {
            "system": self.system,
            "release": platform.release(),
            "version": platform.version(),
            "machine": self.machine,
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }
        
        # Windows特定信息
        if self.system == "Windows":
            info["windows_edition"] = self._get_windows_edition()
        
        return info
    
    def _get_windows_edition(self) -> str:
        """获取Windows版本信息"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            edition = winreg.QueryValueEx(key, "EditionID")[0]
            winreg.CloseKey(key)
            return edition
        except Exception:
            return "Unknown"
    
    def get_process_command(self, command_type: str) -> str:
        """获取平台特定的进程控制命令
        
        Args:
            command_type: 命令类型（如 'list', 'kill', 'monitor'）
            
        Returns:
            str: 对应平台的命令
        """
        commands = {
            "Windows": {
                "list": "tasklist",
                "kill": "taskkill /F /PID",
                "monitor": "taskmgr",
                "memory": "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value"
            },
            "Darwin": {  # macOS
                "list": "ps -ef",
                "kill": "kill -9",
                "monitor": "top",
                "memory": "vm_stat"
            },
            "Linux": {
                "list": "ps -ef",
                "kill": "kill -9",
                "monitor": "top",
                "memory": "free -m"
            }
        }
        
        return commands.get(self.system, {}).get(command_type, "")
    
    def get_path_separator(self) -> str:
        """获取平台特定的路径分隔符"""
        return "\\" if self.system == "Windows" else "/"
    
    def normalize_path(self, path: Union[str, Path]) -> str:
        """标准化路径格式
        
        Args:
            path: 输入路径
            
        Returns:
            str: 标准化后的路径
        """
        return str(Path(path).absolute())
    
    def get_temp_directory(self) -> str:
        """获取平台特定的临时目录
        
        Returns:
            str: 临时目录路径
        """
        if self.system == "Windows":
            return os.environ.get("TEMP", os.path.join(os.environ["SYSTEMROOT"], "Temp"))
        else:
            return "/tmp"
    
    def get_system_encoding(self) -> str:
        """获取系统默认编码
        
        Returns:
            str: 系统编码
        """
        return sys.getfilesystemencoding()
    
    def execute_system_command(self,
                             command: str,
                             shell: bool = True,
                             timeout: Optional[int] = None) -> Dict[str, Union[int, str]]:
        """执行系统命令
        
        Args:
            command: 要执行的命令
            shell: 是否使用shell执行
            timeout: 超时时间（秒）
            
        Returns:
            Dict: 包含执行结果的字典
        """
        try:
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding=self.get_system_encoding()
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            
            return {
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(f"命令执行超时: {command}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out"
            }
        except Exception as e:
            logger.error(f"命令执行失败: {str(e)}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def is_admin(self) -> bool:
        """检查是否具有管理员权限
        
        Returns:
            bool: 是否具有管理员权限
        """
        try:
            if self.system == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    def get_memory_info(self) -> Dict[str, int]:
        """获取系统内存信息
        
        Returns:
            Dict[str, int]: 内存信息（字节）
        """
        command = self.get_process_command("memory")
        result = self.execute_system_command(command)
        
        if result["returncode"] != 0:
            return {}
            
        try:
            if self.system == "Windows":
                # 解析Windows内存信息
                lines = result["stdout"].split("\n")
                memory_info = {}
                for line in lines:
                    if "=" in line:
                        key, value = line.split("=", 1)
                        memory_info[key.strip()] = int(value.strip())
                return memory_info
                
            elif self.system == "Darwin":
                # 解析macOS内存信息
                lines = result["stdout"].split("\n")
                memory_info = {}
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        memory_info[key.strip()] = int(value.strip().replace(".", ""))
                return memory_info
                
            else:  # Linux
                # 解析Linux内存信息
                lines = result["stdout"].split("\n")
                if len(lines) >= 2:
                    headers = lines[0].split()
                    values = lines[1].split()
                    return dict(zip(headers, map(int, values)))
                    
        except Exception as e:
            logger.error(f"内存信息解析失败: {str(e)}")
            
        return {}
    
    def get_process_list(self) -> List[Dict[str, Union[int, str]]]:
        """获取进程列表
        
        Returns:
            List[Dict]: 进程信息列表
        """
        command = self.get_process_command("list")
        result = self.execute_system_command(command)
        
        if result["returncode"] != 0:
            return []
            
        processes = []
        try:
            lines = result["stdout"].split("\n")
            
            if self.system == "Windows":
                # 跳过标题行
                for line in lines[3:]:
                    if line.strip():
                        parts = line.split()
                        processes.append({
                            "name": parts[0],
                            "pid": int(parts[1]),
                            "memory": parts[4].replace(",", "")
                        })
            else:
                # Unix-like系统
                for line in lines[1:]:  # 跳过标题行
                    if line.strip():
                        parts = line.split()
                        processes.append({
                            "user": parts[0],
                            "pid": int(parts[1]),
                            "cpu": parts[2],
                            "memory": parts[3],
                            "command": " ".join(parts[7:])
                        })
                        
            return processes
            
        except Exception as e:
            logger.error(f"进程列表解析失败: {str(e)}")
            return []
    
    def kill_process(self, pid: int) -> bool:
        """结束指定进程
        
        Args:
            pid: 进程ID
            
        Returns:
            bool: 是否成功结束进程
        """
        command = f"{self.get_process_command('kill')} {pid}"
        result = self.execute_system_command(command)
        return result["returncode"] == 0
    
    def get_platform_summary(self) -> Dict:
        """获取平台综合信息摘要
        
        Returns:
            Dict: 平台信息摘要
        """
        return {
            "platform": self.platform_info,
            "memory": self.get_memory_info(),
            "admin": self.is_admin(),
            "encoding": self.get_system_encoding(),
            "temp_dir": self.get_temp_directory()
        } 