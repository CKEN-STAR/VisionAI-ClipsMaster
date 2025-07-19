#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试环境模拟器

用于加载和应用低内存环境模拟配置
支持Docker容器和本地环境下的内存限制测试
"""

import os
import yaml
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

# 配置日志
logger = logging.getLogger("EnvSimulator")

class EnvironmentSimulator:
    """
    环境模拟器 - 加载和应用内存环境限制
    
    功能:
    1. 加载环境配置文件
    2. 生成Docker运行命令
    3. 提供本地内存限制功能
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化环境模拟器
        
        Args:
            config_path: 配置文件路径，默认为configs/low_mem_env.yaml
        """
        if config_path is None:
            # 获取项目根目录
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = os.path.join(root_dir, "configs", "low_mem_env.yaml")
            
        self.config_path = config_path
        self.profiles = self._load_profiles()
        
    def _load_profiles(self) -> Dict:
        """
        加载环境配置文件
        
        Returns:
            Dict: 配置信息
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"成功加载环境配置，共{len(config.get('simulation_profiles', []))}个配置文件")
                return config
        except Exception as e:
            logger.error(f"加载环境配置失败: {str(e)}")
            return {"simulation_profiles": []}
    
    def list_profiles(self) -> List[Dict]:
        """
        获取所有可用的环境配置
        
        Returns:
            List[Dict]: 配置列表
        """
        return self.profiles.get("simulation_profiles", [])
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """
        根据名称获取特定配置
        
        Args:
            name: 配置名称
            
        Returns:
            Dict: 配置信息，未找到则返回None
        """
        for profile in self.list_profiles():
            if profile.get("name") == name:
                return profile
        return None
    
    def print_profiles(self):
        """打印所有可用配置"""
        print("可用的测试环境配置:")
        for i, profile in enumerate(self.list_profiles(), 1):
            print(f"{i}. {profile.get('name')} - "
                 f"{profile.get('total_mem')}MB RAM, "
                 f"Swap: {profile.get('swap_size')}MB")
    
    def generate_docker_command(self, profile_name: str, 
                               container_name: str = "memory_test_container", 
                               image: str = "visionai-clipsmaster:latest",
                               command: str = None) -> str:
        """
        生成Docker运行命令
        
        Args:
            profile_name: 配置名称
            container_name: 容器名称
            image: 容器镜像
            command: 容器内要执行的命令
            
        Returns:
            str: Docker运行命令
        """
        profile = self.get_profile(profile_name)
        if not profile:
            raise ValueError(f"未找到配置: {profile_name}")
        
        # 构建基本命令
        cmd = [
            "docker", "run",
            "--name", container_name,
            "--rm",  # 运行后自动删除容器
            "-it"    # 交互式终端
        ]
        
        # 内存限制
        mem_limit = f"{profile.get('total_mem')}m"
        cmd.extend(["--memory", mem_limit])
        
        # 交换空间限制
        swap_size = profile.get("swap_size", 0)
        if swap_size == 0:
            # 完全禁用交换
            cmd.extend(["--memory-swap", mem_limit])
        else:
            # 设置交换空间大小 (内存+交换)
            total_limit = profile.get("total_mem") + swap_size
            cmd.extend(["--memory-swap", f"{total_limit}m"])
        
        # CGroups限制 (仅部分支持)
        cgroups = profile.get("cgroups", {})
        if "memory.limit_in_bytes" in cgroups:
            limit = cgroups["memory.limit_in_bytes"]
            # Docker对cgroup的支持有限，这里通过注释说明
            logger.info(f"注意: cgroups限制 {limit} 需要在容器内通过特殊方式设置")
        
        # 添加镜像名
        cmd.append(image)
        
        # 添加要执行的命令
        if command:
            cmd.append(command)
        
        return " ".join(cmd)
    
    def run_docker_container(self, profile_name: str, 
                            container_name: str = "memory_test_container", 
                            image: str = "visionai-clipsmaster:latest",
                            command: str = None) -> int:
        """
        启动Docker容器来模拟特定内存环境
        
        Args:
            profile_name: 配置名称
            container_name: 容器名称
            image: 容器镜像
            command: 容器内要执行的命令
            
        Returns:
            int: 命令返回码
        """
        cmd = self.generate_docker_command(
            profile_name, container_name, image, command
        )
        
        logger.info(f"启动内存环境模拟容器: {profile_name}")
        logger.info(f"执行命令: {cmd}")
        
        try:
            # 执行Docker命令
            result = subprocess.run(cmd, shell=True, check=True)
            return result.returncode
        except subprocess.CalledProcessError as e:
            logger.error(f"启动Docker容器失败: {str(e)}")
            return e.returncode
        except Exception as e:
            logger.error(f"执行命令时出错: {str(e)}")
            return -1
    
    def apply_local_limits(self, profile_name: str) -> bool:
        """
        尝试在本地应用内存限制
        注意：这需要root权限，且支持有限
        
        Args:
            profile_name: 配置名称
            
        Returns:
            bool: 是否成功应用限制
        """
        profile = self.get_profile(profile_name)
        if not profile:
            logger.error(f"未找到配置: {profile_name}")
            return False
        
        logger.warning("本地应用内存限制需要root权限，且可能不被所有平台支持")
        
        try:
            # 尝试使用cgroups设置内存限制 (仅Linux)
            if os.name == "posix":
                cgroups = profile.get("cgroups", {})
                if "memory.limit_in_bytes" in cgroups:
                    limit = cgroups["memory.limit_in_bytes"]
                    # 这里需要root权限，且依赖于cgroups的支持
                    # 实际项目中可能需要更复杂的实现
                    logger.warning(f"尝试设置内存限制: {limit} (需要root权限)")
                    
                    # 本示例不实际执行限制命令，因为这需要特定的系统环境
                    # subprocess.run(["cgcreate", "-g", "memory:/memorytest"], shell=True)
                    # subprocess.run(["cgset", "-r", f"memory.limit_in_bytes={limit}", "memorytest"], shell=True)
                    # subprocess.run(["cgexec", "-g", "memory:memorytest", "cmd"], shell=True)
                    
                    logger.info("实际环境中请使用Docker或cgroup工具应用限制")
                    return True
            else:
                logger.warning("非Linux系统不支持cgroups内存限制")
                
            return False
        except Exception as e:
            logger.error(f"应用本地限制失败: {str(e)}")
            return False
        
    def create_test_script(self, profile_name: str, output_path: str = "run_memory_test.sh") -> bool:
        """
        创建测试脚本
        
        Args:
            profile_name: 配置名称
            output_path: 输出脚本路径
            
        Returns:
            bool: 是否成功创建脚本
        """
        profile = self.get_profile(profile_name)
        if not profile:
            logger.error(f"未找到配置: {profile_name}")
            return False
        
        # 生成Docker命令
        docker_cmd = self.generate_docker_command(
            profile_name, 
            command="python src/utils/memory_test_cli.py stability --hours 1 --use-model --model-id qwen2.5-7b-chat --save-report"
        )
        
        # 脚本内容
        script_content = f"""#!/bin/bash
# 内存测试环境: {profile_name}
# 总内存: {profile.get('total_mem')}MB
# 交换空间: {profile.get('swap_size')}MB

echo "启动内存受限测试环境: {profile_name}"
{docker_cmd}

echo "测试完成"
"""
        
        try:
            # 写入脚本文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 设置可执行权限 (仅POSIX系统)
            if os.name == "posix":
                os.chmod(output_path, 0o755)
                
            logger.info(f"测试脚本已创建: {output_path}")
            return True
        except Exception as e:
            logger.error(f"创建测试脚本失败: {str(e)}")
            return False


def main():
    """主入口函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建环境模拟器
    simulator = EnvironmentSimulator()
    
    # 打印可用配置
    simulator.print_profiles()
    
    # 生成Docker命令示例
    try:
        cmd = simulator.generate_docker_command("4GB连线")
        print(f"\nDocker命令示例:\n{cmd}")
        
        # 创建测试脚本
        simulator.create_test_script("4GB连线", "scripts/run_memory_test_4gb.sh")
        simulator.create_test_script("极限2GB模式", "scripts/run_memory_test_2gb.sh")
        
        print("\n测试脚本已创建在scripts目录")
    except Exception as e:
        logger.error(f"执行失败: {str(e)}")


if __name__ == "__main__":
    main() 