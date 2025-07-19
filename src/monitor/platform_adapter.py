#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多平台适配层

为不同操作系统提供统一的内存监控接口，支持Windows、macOS和Linux平台。
"""

import os
import sys
import logging
import subprocess
from typing import Dict, Tuple, Optional, Any

logger = logging.getLogger("platform_adapter")

def get_memory_usage() -> Dict[str, float]:
    """获取当前内存使用情况
    
    返回系统和进程的内存使用信息。
    
    Returns:
        包含内存信息的字典:
        {
            'total': 总内存(MB),
            'available': 可用内存(MB),
            'used': 已用内存(MB),
            'percent': 内存使用率(%),
            'process': 当前进程内存使用(MB)
        }
    """
    if sys.platform == 'win32':
        return _get_windows_memory()
    elif sys.platform == 'darwin':
        return _get_mac_memory()
    else:
        return _get_linux_memory()

def _get_windows_memory() -> Dict[str, float]:
    """获取Windows系统内存信息"""
    try:
        import psutil
        
        # 获取系统内存信息
        mem_info = psutil.virtual_memory()
        
        # 获取当前进程内存
        process = psutil.Process()
        process_mem = process.memory_info().rss / (1024 * 1024)  # MB
        
        return {
            'total': mem_info.total / (1024 * 1024),  # MB
            'available': mem_info.available / (1024 * 1024),  # MB
            'used': (mem_info.total - mem_info.available) / (1024 * 1024),  # MB
            'percent': mem_info.percent,  # %
            'process': process_mem  # MB
        }
    except ImportError:
        logger.error("未安装psutil库，无法获取详细内存信息")
        return _get_fallback_memory()
    except Exception as e:
        logger.error(f"获取Windows内存信息失败: {e}")
        return _get_fallback_memory()

def _get_mac_memory() -> Dict[str, float]:
    """获取macOS系统内存信息"""
    try:
        import psutil
        
        # 获取系统内存信息
        mem_info = psutil.virtual_memory()
        
        # 获取当前进程内存
        process = psutil.Process()
        process_mem = process.memory_info().rss / (1024 * 1024)  # MB
        
        return {
            'total': mem_info.total / (1024 * 1024),  # MB
            'available': mem_info.available / (1024 * 1024),  # MB
            'used': (mem_info.total - mem_info.available) / (1024 * 1024),  # MB
            'percent': mem_info.percent,  # %
            'process': process_mem  # MB
        }
    except ImportError:
        # 使用vm_stat命令获取内存信息
        try:
            result = subprocess.run(['vm_stat'], stdout=subprocess.PIPE, text=True, check=True)
            output = result.stdout
            
            # 解析vm_stat输出
            lines = output.strip().split('\n')
            stats = {}
            
            for line in lines[1:]:  # 跳过标题行
                if ':' in line:
                    parts = line.split(':')
                    key = parts[0].strip()
                    value = parts[1].strip().replace('.', '')
                    stats[key] = int(value)
            
            # 页大小通常为4096字节
            page_size = 4096
            
            # 计算内存值 (MB)
            mem_free = stats.get('Pages free', 0) * page_size / (1024 * 1024)
            mem_active = stats.get('Pages active', 0) * page_size / (1024 * 1024)
            mem_inactive = stats.get('Pages inactive', 0) * page_size / (1024 * 1024)
            mem_wired = stats.get('Pages wired down', 0) * page_size / (1024 * 1024)
            
            # 总内存使用ps命令获取
            total_mem_cmd = subprocess.run(['sysctl', 'hw.memsize'], stdout=subprocess.PIPE, text=True, check=True)
            total_mem_str = total_mem_cmd.stdout.split(':')[1].strip()
            total_mem = int(total_mem_str) / (1024 * 1024)  # MB
            
            # 已用内存
            used_mem = mem_active + mem_wired
            available_mem = mem_free + mem_inactive
            
            # 使用ps获取进程内存
            pid = os.getpid()
            ps_cmd = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], stdout=subprocess.PIPE, text=True, check=True)
            process_mem = int(ps_cmd.stdout.strip()) / 1024  # MB
            
            return {
                'total': total_mem,
                'available': available_mem,
                'used': used_mem,
                'percent': (used_mem / total_mem) * 100 if total_mem > 0 else 0,
                'process': process_mem
            }
        except Exception as e:
            logger.error(f"使用vm_stat获取macOS内存信息失败: {e}")
            return _get_fallback_memory()
    except Exception as e:
        logger.error(f"获取macOS内存信息失败: {e}")
        return _get_fallback_memory()

def _get_linux_memory() -> Dict[str, float]:
    """获取Linux系统内存信息"""
    try:
        import psutil
        
        # 获取系统内存信息
        mem_info = psutil.virtual_memory()
        
        # 获取当前进程内存
        process = psutil.Process()
        process_mem = process.memory_info().rss / (1024 * 1024)  # MB
        
        return {
            'total': mem_info.total / (1024 * 1024),  # MB
            'available': mem_info.available / (1024 * 1024),  # MB
            'used': (mem_info.total - mem_info.available) / (1024 * 1024),  # MB
            'percent': mem_info.percent,  # %
            'process': process_mem  # MB
        }
    except ImportError:
        # 使用/proc/meminfo获取内存信息
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # 解析内存信息
            mem_total = 0
            mem_available = 0
            
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_total = int(line.split()[1]) / 1024  # MB
                elif 'MemAvailable:' in line:
                    mem_available = int(line.split()[1]) / 1024  # MB
            
            mem_used = mem_total - mem_available
            mem_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
            
            # 获取进程内存 (/proc/[pid]/status)
            try:
                pid = os.getpid()
                with open(f'/proc/{pid}/status', 'r') as f:
                    proc_info = f.read()
                
                process_mem = 0
                for line in proc_info.split('\n'):
                    if 'VmRSS:' in line:
                        process_mem = int(line.split()[1]) / 1024  # MB
                        break
            except:
                process_mem = 0
            
            return {
                'total': mem_total,
                'available': mem_available,
                'used': mem_used,
                'percent': mem_percent,
                'process': process_mem
            }
        except Exception as e:
            logger.error(f"使用/proc/meminfo获取Linux内存信息失败: {e}")
            return _get_fallback_memory()
    except Exception as e:
        logger.error(f"获取Linux内存信息失败: {e}")
        return _get_fallback_memory()

def _get_fallback_memory() -> Dict[str, float]:
    """获取备用内存信息（当其他方法失败时）"""
    return {
        'total': 0.0,
        'available': 0.0,
        'used': 0.0,
        'percent': 0.0,
        'process': 0.0
    }

def get_platform_info() -> Dict[str, str]:
    """获取平台信息
    
    Returns:
        包含平台信息的字典:
        {
            'system': 操作系统名称,
            'release': 系统版本,
            'machine': 机器类型,
            'processor': 处理器信息
        }
    """
    try:
        import platform
        
        return {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    except Exception as e:
        logger.error(f"获取平台信息失败: {e}")
        return {
            'system': sys.platform,
            'release': 'unknown',
            'machine': 'unknown',
            'processor': 'unknown'
        }

def get_cpu_usage() -> float:
    """获取CPU使用率
    
    Returns:
        CPU使用率百分比
    """
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except ImportError:
        try:
            if sys.platform == 'win32':
                # Windows平台使用wmic
                result = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage'], 
                                      stdout=subprocess.PIPE, text=True, check=True)
                output = result.stdout.strip()
                lines = output.split('\n')
                if len(lines) >= 2:
                    return float(lines[1].strip())
                return 0.0
            elif sys.platform == 'darwin':
                # macOS平台使用top
                result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      stdout=subprocess.PIPE, text=True, check=True)
                output = result.stdout
                for line in output.split('\n'):
                    if 'CPU usage' in line:
                        # 解析格式 "CPU usage: 10.64% user, 15.81% sys, 73.54% idle"
                        parts = line.split(':')[1].split(',')
                        user = float(parts[0].strip().replace('%', '').split()[0])
                        system = float(parts[1].strip().replace('%', '').split()[0])
                        return user + system
                return 0.0
            else:
                # Linux平台使用/proc/stat
                with open('/proc/stat', 'r') as f:
                    cpu_line = f.readline()
                
                cpu_parts = cpu_line.split()
                total = sum(float(part) for part in cpu_parts[1:])
                idle = float(cpu_parts[4])
                
                # 短暂延迟后再次测量
                import time
                time.sleep(0.1)
                
                with open('/proc/stat', 'r') as f:
                    cpu_line = f.readline()
                
                cpu_parts = cpu_line.split()
                total_new = sum(float(part) for part in cpu_parts[1:])
                idle_new = float(cpu_parts[4])
                
                # 计算使用率
                total_delta = total_new - total
                idle_delta = idle_new - idle
                
                if total_delta > 0:
                    return 100.0 * (1.0 - idle_delta / total_delta)
                return 0.0
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {e}")
            return 0.0
    except Exception as e:
        logger.error(f"获取CPU使用率失败: {e}")
        return 0.0

def get_disk_usage(path: str = '.') -> Dict[str, float]:
    """获取磁盘使用情况
    
    Args:
        path: 要检查的路径
    
    Returns:
        包含磁盘信息的字典:
        {
            'total': 总空间(GB),
            'used': 已用空间(GB),
            'free': 可用空间(GB),
            'percent': 使用率(%)
        }
    """
    try:
        import psutil
        disk = psutil.disk_usage(path)
        
        return {
            'total': disk.total / (1024 * 1024 * 1024),  # GB
            'used': disk.used / (1024 * 1024 * 1024),  # GB
            'free': disk.free / (1024 * 1024 * 1024),  # GB
            'percent': disk.percent  # %
        }
    except ImportError:
        try:
            if sys.platform == 'win32':
                # Windows平台使用wmic
                drive = os.path.abspath(path)[0] + ":"
                result = subprocess.run(['wmic', 'logicaldisk', 'where', f'DeviceID="{drive}"', 'get', 'size,freespace'], 
                                      stdout=subprocess.PIPE, text=True, check=True)
                output = result.stdout.strip()
                lines = output.split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        free = float(parts[0]) / (1024 * 1024 * 1024)  # GB
                        total = float(parts[1]) / (1024 * 1024 * 1024)  # GB
                        used = total - free
                        percent = (used / total) * 100 if total > 0 else 0
                        
                        return {
                            'total': total,
                            'used': used,
                            'free': free,
                            'percent': percent
                        }
            else:
                # Unix平台使用df
                result = subprocess.run(['df', '-k', path], stdout=subprocess.PIPE, text=True, check=True)
                output = result.stdout.strip()
                lines = output.split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        total = float(parts[1]) / (1024 * 1024)  # GB
                        used = float(parts[2]) / (1024 * 1024)  # GB
                        free = float(parts[3]) / (1024 * 1024)  # GB
                        try:
                            percent = float(parts[4].replace('%', ''))
                        except:
                            percent = (used / total) * 100 if total > 0 else 0
                        
                        return {
                            'total': total,
                            'used': used,
                            'free': free,
                            'percent': percent
                        }
        except Exception as e:
            logger.error(f"获取磁盘使用情况失败: {e}")
    
    # 如果所有方法都失败，返回默认值
    return {
        'total': 0.0,
        'used': 0.0,
        'free': 0.0,
        'percent': 0.0
    }

# 导出主要函数
__all__ = ['get_memory_usage', 'get_platform_info', 'get_cpu_usage', 'get_disk_usage'] 