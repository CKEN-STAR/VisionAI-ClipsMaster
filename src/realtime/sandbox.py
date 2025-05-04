#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交互沙盒隔离器

提供安全的代码执行环境，通过容器化技术隔离用户代码，
防止恶意代码访问系统资源或影响主程序运行。
"""

import os
import re
import json
import uuid
import time
import asyncio
import logging
import threading
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from pathlib import Path
from abc import ABC, abstractmethod

# 配置日志记录器
logger = logging.getLogger(__name__)

class SandboxExecutionError(Exception):
    """沙盒执行错误"""
    pass

class DockerManager:
    """Docker容器管理器
    
    负责创建、执行和销毁Docker容器。
    """
    
    def __init__(self, image_name: str = "python-sandbox", timeout: int = 30):
        """初始化Docker管理器
        
        Args:
            image_name: Docker镜像名称
            timeout: 执行超时时间(秒)
        """
        self.image_name = image_name
        self.timeout = timeout
        self.container_ids: Set[str] = set()
        self.lock = threading.RLock()
        
        # 确保沙盒镜像存在
        self._ensure_sandbox_image()
        
        logger.info(f"Docker管理器已初始化，使用镜像: {image_name}")
    
    def _ensure_sandbox_image(self) -> None:
        """确保沙盒Docker镜像存在
        
        如果镜像不存在，则创建它。
        """
        try:
            # 检查镜像是否存在
            result = subprocess.run(
                ["docker", "image", "ls", "-q", self.image_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                logger.info(f"沙盒镜像不存在，正在创建: {self.image_name}")
                self._create_sandbox_image()
            else:
                logger.debug(f"沙盒镜像已存在: {self.image_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"检查Docker镜像时出错: {str(e)}")
            logger.error(f"错误输出: {e.stderr}")
            raise SandboxExecutionError(f"Docker命令失败: {str(e)}")
        except Exception as e:
            logger.error(f"确保沙盒镜像存在时出错: {str(e)}")
            raise SandboxExecutionError(f"创建沙盒镜像失败: {str(e)}")
    
    def _create_sandbox_image(self) -> None:
        """创建沙盒Docker镜像"""
        # 创建临时Dockerfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dockerfile', delete=False) as f:
            dockerfile_path = f.name
            f.write("""
FROM python:3.9-slim

# 安装基本依赖
RUN pip install --no-cache-dir numpy pandas matplotlib scipy scikit-learn

# 创建非root用户
RUN useradd -m -u 1000 sandbox
WORKDIR /home/sandbox
USER sandbox

# 设置Python路径
ENV PYTHONPATH=/home/sandbox

# 设置容器入口点
ENTRYPOINT ["python", "-c"]
            """)
        
        try:
            # 构建Docker镜像
            subprocess.run(
                ["docker", "build", "-t", self.image_name, "-f", dockerfile_path, "."],
                check=True
            )
            logger.info(f"成功创建沙盒镜像: {self.image_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"创建Docker镜像失败: {str(e)}")
            raise SandboxExecutionError(f"创建沙盒镜像失败: {str(e)}")
        finally:
            # 删除临时Dockerfile
            os.unlink(dockerfile_path)
    
    async def spawn(self, container_name: Optional[str] = None) -> str:
        """创建并启动Docker容器
        
        Args:
            container_name: 容器名称，如不提供则自动生成
            
        Returns:
            str: 容器ID
        """
        container_id = container_name or f"sandbox-{uuid.uuid4().hex[:8]}"
        
        try:
            # 创建容器但不启动
            proc = await asyncio.create_subprocess_exec(
                "docker", "create",
                "--name", container_id,
                "--network", "none",  # 禁用网络
                "--cpus", "0.5",      # 限制CPU使用
                "--memory", "512m",   # 限制内存使用
                "--pids-limit", "50", # 限制进程数
                "--cap-drop", "ALL",  # 删除所有特权
                self.image_name,
                "echo", "Container created",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                raise SandboxExecutionError(f"容器创建失败: {stderr.decode('utf-8')}")
            
            with self.lock:
                self.container_ids.add(container_id)
            
            logger.debug(f"已创建沙盒容器: {container_id}")
            return container_id
            
        except Exception as e:
            logger.error(f"创建Docker容器时出错: {str(e)}")
            raise SandboxExecutionError(f"创建Docker容器失败: {str(e)}")
    
    async def exec(self, container_id: str, code: str) -> Tuple[str, str, int]:
        """在容器中执行代码
        
        Args:
            container_id: 容器ID
            code: 要执行的Python代码
            
        Returns:
            Tuple[str, str, int]: 标准输出、标准错误和返回码
        """
        # 检查容器是否存在
        if container_id not in self.container_ids:
            raise SandboxExecutionError(f"容器不存在: {container_id}")
        
        try:
            # 启动容器
            start_proc = await asyncio.create_subprocess_exec(
                "docker", "start", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await start_proc.communicate()
            if start_proc.returncode != 0:
                raise SandboxExecutionError(f"启动容器失败: {container_id}")
            
            # 在容器中执行代码
            exec_proc = await asyncio.create_subprocess_exec(
                "docker", "exec", 
                container_id,
                "python", "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    exec_proc.communicate(), 
                    timeout=self.timeout
                )
                return stdout.decode('utf-8'), stderr.decode('utf-8'), exec_proc.returncode
            except asyncio.TimeoutError:
                logger.warning(f"容器执行超时: {container_id}")
                return "", "执行超时", -1
            
        except Exception as e:
            logger.error(f"执行代码时出错: {str(e)}")
            return "", str(e), -1
        finally:
            # 停止容器但不删除，以便重用
            await self._stop_container(container_id)
    
    async def _stop_container(self, container_id: str) -> None:
        """停止容器
        
        Args:
            container_id: 容器ID
        """
        try:
            stop_proc = await asyncio.create_subprocess_exec(
                "docker", "stop", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await stop_proc.communicate()
        except Exception as e:
            logger.error(f"停止容器时出错: {str(e)}")
    
    async def destroy(self, container_id: str) -> None:
        """销毁容器
        
        Args:
            container_id: 容器ID
        """
        if container_id not in self.container_ids:
            return
        
        try:
            # 确保容器已停止
            await self._stop_container(container_id)
            
            # 删除容器
            rm_proc = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await rm_proc.communicate()
            
            with self.lock:
                self.container_ids.discard(container_id)
            
            logger.debug(f"已销毁沙盒容器: {container_id}")
        except Exception as e:
            logger.error(f"销毁容器时出错: {str(e)}")
    
    async def cleanup(self) -> None:
        """清理所有容器"""
        with self.lock:
            container_ids = list(self.container_ids)
        
        for container_id in container_ids:
            await self.destroy(container_id)
        
        logger.info("已清理所有沙盒容器")


class SandboxBase(ABC):
    """沙盒基类
    
    定义沙盒的通用接口。
    """
    
    @abstractmethod
    async def execute(self, code: str) -> Dict[str, Any]:
        """执行代码
        
        Args:
            code: 要执行的代码
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        pass


class DockerSandbox(SandboxBase):
    """基于Docker的沙盒
    
    通过Docker容器提供隔离的代码执行环境。
    """
    
    def __init__(self, timeout: int = 30):
        """初始化Docker沙盒
        
        Args:
            timeout: 执行超时时间(秒)
        """
        self.docker_manager = DockerManager(timeout=timeout)
        self.container_id = None
        logger.info("Docker沙盒已初始化")
    
    async def execute(self, code: str) -> Dict[str, Any]:
        """在Docker容器中执行代码
        
        Args:
            code: 要执行的Python代码
            
        Returns:
            Dict[str, Any]: 执行结果，包含stdout、stderr和exitcode
        """
        try:
            # 检查代码安全性
            sanitized_code = self._sanitize_code(code)
            
            # 创建容器（如果尚未创建）
            if self.container_id is None:
                self.container_id = await self.docker_manager.spawn()
            
            # 执行代码
            stdout, stderr, exit_code = await self.docker_manager.exec(
                self.container_id, sanitized_code
            )
            
            return {
                "success": exit_code == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
        except Exception as e:
            logger.error(f"沙盒执行失败: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
    
    def _sanitize_code(self, code: str) -> str:
        """净化代码，移除潜在危险操作
        
        Args:
            code: 原始代码
            
        Returns:
            str: 净化后的代码
        """
        # 移除导入危险模块
        dangerous_imports = [
            r'import\s+os(?:\s|\.|$)',
            r'from\s+os\s+import',
            r'import\s+subprocess(?:\s|\.|$)',
            r'from\s+subprocess\s+import',
            r'import\s+sys(?:\s|\.|$)',
            r'from\s+sys\s+import',
            r'__import__\([\'"]os[\'"]\)',
            r'__import__\([\'"]subprocess[\'"]\)',
            r'__import__\([\'"]sys[\'"]\)',
            r'eval\(',
            r'exec\(',
            r'open\(',
            r'file\('
        ]
        
        sanitized_code = code
        for pattern in dangerous_imports:
            sanitized_code = re.sub(pattern, '# REMOVED: ', sanitized_code)
        
        # 包装代码在try-except块中以捕获所有异常
        safe_code = f"""
try:
    import traceback
    import json

    # === 用户代码开始 ===
{sanitized_code}
    # === 用户代码结束 ===
except Exception as e:
    print(f"错误: {{str(e)}}")
    traceback.print_exc()
"""
        return safe_code
    
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        if self.container_id:
            await self.docker_manager.destroy(self.container_id)
            self.container_id = None
        
        logger.debug("沙盒资源已清理")


class SubprocessSandbox(SandboxBase):
    """基于子进程的沙盒
    
    通过Python子进程提供代码执行环境。
    适用于Docker不可用的场景，但隔离性较弱。
    """
    
    def __init__(self, timeout: int = 30):
        """初始化子进程沙盒
        
        Args:
            timeout: 执行超时时间(秒)
        """
        self.timeout = timeout
        self.temp_files: List[str] = []
        logger.info("子进程沙盒已初始化")
    
    async def execute(self, code: str) -> Dict[str, Any]:
        """在Python子进程中执行代码
        
        Args:
            code: 要执行的Python代码
            
        Returns:
            Dict[str, Any]: 执行结果，包含stdout、stderr和exitcode
        """
        # 创建临时Python文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            script_path = f.name
            self.temp_files.append(script_path)
            
            # 编写安全的代码到文件
            sanitized_code = self._sanitize_code(code)
            f.write(sanitized_code)
        
        try:
            # 执行Python脚本
            proc = await asyncio.create_subprocess_exec(
                "python", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), 
                    timeout=self.timeout
                )
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8'),
                    "exit_code": proc.returncode
                }
            except asyncio.TimeoutError:
                # 超时，强制终止进程
                proc.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "执行超时",
                    "exit_code": -1
                }
        except Exception as e:
            logger.error(f"子进程执行失败: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
    
    def _sanitize_code(self, code: str) -> str:
        """净化代码，移除潜在危险操作
        
        Args:
            code: 原始代码
            
        Returns:
            str: 净化后的代码
        """
        # 移除危险模块导入
        dangerous_imports = [
            r'import\s+os(?:\s|\.|$)',
            r'from\s+os\s+import',
            r'import\s+subprocess(?:\s|\.|$)',
            r'from\s+subprocess\s+import',
            r'import\s+sys(?:\s|\.|$)',
            r'from\s+sys\s+import',
            r'__import__\([\'"]os[\'"]\)',
            r'__import__\([\'"]subprocess[\'"]\)',
            r'__import__\([\'"]sys[\'"]\)',
            r'eval\(',
            r'exec\(',
            r'open\(',
            r'file\('
        ]
        
        sanitized_code = code
        for pattern in dangerous_imports:
            sanitized_code = re.sub(pattern, '# REMOVED: ', sanitized_code)
        
        # 包装代码在try-except块中
        safe_code = f"""
import traceback
import sys
import builtins

# 安全的打开文件函数
def safe_open(*args, **kwargs):
    raise PermissionError("安全限制: 不允许打开文件")

# 替换危险函数
builtins.open = safe_open
builtins.__import__ = lambda *args, **kwargs: None

# 重定向标准输出和标准错误
from io import StringIO
sys.stdout = StringIO()
sys.stderr = StringIO()

try:
    # === 用户代码开始 ===
{sanitized_code}
    # === 用户代码结束 ===
except Exception as e:
    print(f"错误: {{str(e)}}")
    traceback.print_exc()

# 打印缓冲的输出
print(sys.stdout.getvalue())
print("STDERR:", sys.stderr.getvalue(), file=sys.stderr)
"""
        return safe_code
    
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        # 删除临时文件
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"删除临时文件时出错: {str(e)}")
        
        self.temp_files = []
        logger.debug("子进程沙盒资源已清理")


class InteractionSandbox:
    """交互沙盒隔离器
    
    提供安全的代码执行环境，用于执行用户提供的代码片段。
    根据系统环境自动选择适当的沙盒实现。
    """
    
    def __init__(self, timeout: int = 30, force_subprocess: bool = False):
        """初始化交互沙盒隔离器
        
        Args:
            timeout: 执行超时时间(秒)
            force_subprocess: 是否强制使用子进程沙盒
        """
        self.timeout = timeout
        self.sandbox = self._create_sandbox(force_subprocess)
        logger.info(f"交互沙盒隔离器已初始化，使用: {self.sandbox.__class__.__name__}")
    
    def _create_sandbox(self, force_subprocess: bool) -> SandboxBase:
        """创建适当的沙盒实现
        
        根据系统环境和配置选择Docker或子进程沙盒。
        
        Args:
            force_subprocess: 是否强制使用子进程沙盒
            
        Returns:
            SandboxBase: 沙盒实现
        """
        if force_subprocess:
            return SubprocessSandbox(timeout=self.timeout)
        
        # 检查Docker可用性
        try:
            if self._check_docker_available():
                return DockerSandbox(timeout=self.timeout)
            else:
                logger.warning("Docker不可用，降级使用子进程沙盒")
                return SubprocessSandbox(timeout=self.timeout)
        except Exception as e:
            logger.warning(f"检查Docker可用性时出错: {str(e)}")
            logger.warning("降级使用子进程沙盒")
            return SubprocessSandbox(timeout=self.timeout)
    
    def _check_docker_available(self) -> bool:
        """检查Docker是否可用
        
        Returns:
            bool: Docker是否可用
        """
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def safe_execute(self, code_snippet: str) -> Dict[str, Any]:
        """安全执行代码片段
        
        在沙盒环境中执行代码，隔离潜在危险操作。
        
        Args:
            code_snippet: 要执行的Python代码片段
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        logger.debug(f"准备执行代码片段:\n{code_snippet[:100]}...")
        
        try:
            # 在沙盒中执行代码
            result = await self.sandbox.execute(code_snippet)
            
            # 记录执行结果
            if result["success"]:
                logger.debug("代码执行成功")
            else:
                logger.warning(f"代码执行失败: {result['stderr']}")
            
            return result
        except Exception as e:
            logger.error(f"沙盒执行出错: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": f"沙盒执行错误: {str(e)}",
                "exit_code": -1
            }
    
    async def cleanup(self) -> None:
        """清理沙盒资源"""
        if self.sandbox:
            await self.sandbox.cleanup()
        
        logger.info("交互沙盒资源已清理")


# 全局单例
_sandbox_instance = None
_sandbox_lock = threading.Lock()

def get_interaction_sandbox() -> InteractionSandbox:
    """获取交互沙盒隔离器单例
    
    Returns:
        InteractionSandbox: 交互沙盒隔离器实例
    """
    global _sandbox_instance
    
    if _sandbox_instance is None:
        with _sandbox_lock:
            if _sandbox_instance is None:
                _sandbox_instance = InteractionSandbox()
    
    return _sandbox_instance

async def initialize_interaction_sandbox(timeout: int = 30, force_subprocess: bool = False) -> InteractionSandbox:
    """初始化交互沙盒隔离器
    
    Args:
        timeout: 执行超时时间(秒)
        force_subprocess: 是否强制使用子进程沙盒
        
    Returns:
        InteractionSandbox: 交互沙盒隔离器实例
    """
    global _sandbox_instance
    
    with _sandbox_lock:
        if _sandbox_instance is not None:
            await _sandbox_instance.cleanup()
        
        _sandbox_instance = InteractionSandbox(
            timeout=timeout,
            force_subprocess=force_subprocess
        )
    
    return _sandbox_instance 