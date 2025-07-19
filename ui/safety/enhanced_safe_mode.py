"""
增强安全模式系统
提供智能诊断、自动修复和问题解决向导
"""

import os
import sys
import time
import subprocess
import traceback
from typing import Dict, List, Optional, Any, Tuple
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, QTabWidget,
                            QProgressBar, QListWidget, QListWidgetItem,
                            QGroupBox, QCheckBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

class SystemDiagnostic:
    """系统诊断工具"""
    
    def __init__(self):
        self.diagnostic_results = {}
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """运行完整系统诊断"""
        print("[诊断] 开始系统诊断...")
        
        results = {
            'python_environment': self._check_python_environment(),
            'dependencies': self._check_dependencies(),
            'system_resources': self._check_system_resources(),
            'file_permissions': self._check_file_permissions(),
            'network_connectivity': self._check_network_connectivity(),
            'gpu_cuda': self._check_gpu_cuda(),
            'ffmpeg': self._check_ffmpeg(),
            'disk_space': self._check_disk_space()
        }
        
        # 计算总体健康度
        total_checks = len(results)
        passed_checks = sum(1 for result in results.values() if result.get('status') == 'ok')
        health_score = (passed_checks / total_checks) * 100
        
        results['overall'] = {
            'health_score': health_score,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks
        }
        
        self.diagnostic_results = results
        print(f"[诊断] 系统健康度: {health_score:.1f}% ({passed_checks}/{total_checks})")
        
        return results
    
    def _check_python_environment(self) -> Dict[str, Any]:
        """检查Python环境"""
        try:
            python_version = sys.version
            python_path = sys.executable
            
            # 检查Python版本
            version_info = sys.version_info
            is_supported = version_info.major == 3 and version_info.minor >= 8
            
            return {
                'status': 'ok' if is_supported else 'warning',
                'version': python_version,
                'path': python_path,
                'supported': is_supported,
                'message': 'Python环境正常' if is_supported else 'Python版本可能不兼容'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Python环境检查失败'
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖包"""
        required_packages = [
            'PyQt6', 'numpy', 'requests', 'psutil'
        ]
        
        optional_packages = [
            'torch', 'librosa', 'opencv-python'
        ]
        
        results = {
            'required': {},
            'optional': {},
            'missing_required': [],
            'missing_optional': []
        }
        
        # 检查必需包
        for package in required_packages:
            try:
                __import__(package)
                results['required'][package] = 'installed'
            except ImportError:
                results['required'][package] = 'missing'
                results['missing_required'].append(package)
            except Exception as e:
                # 处理其他导入错误（如torch的CUDA问题）
                results['required'][package] = 'error'
                print(f"[WARN] 包 {package} 导入错误: {e}")

        # 检查可选包
        for package in optional_packages:
            try:
                # 对于torch包，使用特殊处理
                if package == 'torch':
                    # 尝试安全导入torch
                    import importlib.util
                    spec = importlib.util.find_spec('torch')
                    if spec is not None:
                        results['optional'][package] = 'installed'
                    else:
                        results['optional'][package] = 'missing'
                        results['missing_optional'].append(package)
                else:
                    __import__(package)
                    results['optional'][package] = 'installed'
            except ImportError:
                results['optional'][package] = 'missing'
                results['missing_optional'].append(package)
            except Exception as e:
                # 处理其他导入错误
                results['optional'][package] = 'error'
                print(f"[WARN] 包 {package} 导入错误: {e}")
        
        # 确定状态
        if results['missing_required']:
            status = 'error'
            message = f"缺少必需依赖: {', '.join(results['missing_required'])}"
        elif results['missing_optional']:
            status = 'warning'
            message = f"缺少可选依赖: {', '.join(results['missing_optional'])}"
        else:
            status = 'ok'
            message = '所有依赖包正常'
        
        results.update({
            'status': status,
            'message': message
        })
        
        return results
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        try:
            import psutil
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_usage = memory.percent
            
            # CPU信息
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 磁盘信息
            disk = psutil.disk_usage('.')
            disk_free_gb = disk.free / (1024**3)
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # 评估资源状况
            issues = []
            if memory_gb < 4:
                issues.append(f"内存不足: {memory_gb:.1f}GB (建议4GB+)")
            if memory_usage > 90:
                issues.append(f"内存使用率过高: {memory_usage:.1f}%")
            if disk_free_gb < 2:
                issues.append(f"磁盘空间不足: {disk_free_gb:.1f}GB")
            if cpu_usage > 80:
                issues.append(f"CPU使用率过高: {cpu_usage:.1f}%")
            
            status = 'error' if len(issues) > 2 else 'warning' if issues else 'ok'
            message = '; '.join(issues) if issues else '系统资源充足'
            
            return {
                'status': status,
                'message': message,
                'memory_gb': memory_gb,
                'memory_usage': memory_usage,
                'cpu_count': cpu_count,
                'cpu_usage': cpu_usage,
                'disk_free_gb': disk_free_gb,
                'disk_usage_percent': disk_usage_percent,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '系统资源检查失败'
            }
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """检查文件权限"""
        try:
            # 检查当前目录权限
            current_dir = os.getcwd()
            can_read = os.access(current_dir, os.R_OK)
            can_write = os.access(current_dir, os.W_OK)
            
            # 检查关键目录
            key_dirs = ['models', 'config', 'logs', 'cache']
            dir_permissions = {}
            
            for dir_name in key_dirs:
                if os.path.exists(dir_name):
                    dir_permissions[dir_name] = {
                        'exists': True,
                        'readable': os.access(dir_name, os.R_OK),
                        'writable': os.access(dir_name, os.W_OK)
                    }
                else:
                    dir_permissions[dir_name] = {'exists': False}
            
            # 评估权限状况
            issues = []
            if not can_write:
                issues.append("当前目录无写入权限")
            
            for dir_name, perms in dir_permissions.items():
                if perms['exists'] and not perms['writable']:
                    issues.append(f"{dir_name}目录无写入权限")
            
            status = 'error' if not can_write else 'warning' if issues else 'ok'
            message = '; '.join(issues) if issues else '文件权限正常'
            
            return {
                'status': status,
                'message': message,
                'current_dir_readable': can_read,
                'current_dir_writable': can_write,
                'directory_permissions': dir_permissions,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '文件权限检查失败'
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """检查网络连接"""
        try:
            import requests
            
            # 测试网络连接
            test_urls = [
                'https://www.baidu.com',
                'https://www.google.com',
                'https://github.com'
            ]
            
            connectivity_results = {}
            successful_connections = 0
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    connectivity_results[url] = {
                        'status': 'ok',
                        'response_time': response.elapsed.total_seconds()
                    }
                    successful_connections += 1
                except Exception as e:
                    connectivity_results[url] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # 评估网络状况
            if successful_connections == 0:
                status = 'error'
                message = '网络连接失败'
            elif successful_connections < len(test_urls):
                status = 'warning'
                message = f'部分网络连接失败 ({successful_connections}/{len(test_urls)})'
            else:
                status = 'ok'
                message = '网络连接正常'
            
            return {
                'status': status,
                'message': message,
                'successful_connections': successful_connections,
                'total_tests': len(test_urls),
                'results': connectivity_results
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': '网络检查失败（可能是requests包未安装）'
            }
    
    def _check_gpu_cuda(self) -> Dict[str, Any]:
        """检查GPU和CUDA"""
        try:
            # 尝试导入torch检查CUDA
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    gpu_count = torch.cuda.device_count()
                    gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "未知"
                    return {
                        'status': 'ok',
                        'message': f'CUDA可用，GPU: {gpu_name}',
                        'cuda_available': True,
                        'gpu_count': gpu_count,
                        'gpu_name': gpu_name
                    }
                else:
                    return {
                        'status': 'warning',
                        'message': 'CUDA不可用，将使用CPU模式',
                        'cuda_available': False
                    }
            except ImportError:
                return {
                    'status': 'warning',
                    'message': 'PyTorch未安装，无法检查CUDA',
                    'torch_installed': False
                }
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': 'GPU/CUDA检查失败'
            }
    
    def _check_ffmpeg(self) -> Dict[str, Any]:
        """检查FFmpeg"""
        try:
            # 尝试运行ffmpeg命令
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return {
                    'status': 'ok',
                    'message': 'FFmpeg已安装',
                    'version': version_line,
                    'installed': True
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'FFmpeg命令执行失败',
                    'installed': False
                }
        except FileNotFoundError:
            return {
                'status': 'warning',
                'message': 'FFmpeg未安装，视频处理功能将不可用',
                'installed': False
            }
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'message': 'FFmpeg检查失败',
                'installed': False
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            import psutil
            
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            total_gb = disk.total / (1024**3)
            used_percent = (disk.used / disk.total) * 100
            
            # 评估磁盘空间
            if free_gb < 1:
                status = 'error'
                message = f'磁盘空间严重不足: {free_gb:.1f}GB'
            elif free_gb < 5:
                status = 'warning'
                message = f'磁盘空间不足: {free_gb:.1f}GB'
            else:
                status = 'ok'
                message = f'磁盘空间充足: {free_gb:.1f}GB'
            
            return {
                'status': status,
                'message': message,
                'free_gb': free_gb,
                'total_gb': total_gb,
                'used_percent': used_percent
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '磁盘空间检查失败'
            }

class AutoRepairSystem:
    """自动修复系统"""

    def __init__(self):
        self.repair_history = []

    def suggest_repairs(self, diagnostic_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据诊断结果建议修复方案"""
        suggestions = []

        # 检查Python环境问题
        python_result = diagnostic_results.get('python_environment', {})
        if python_result.get('status') == 'warning':
            suggestions.append({
                'category': 'python',
                'priority': 'high',
                'title': 'Python版本兼容性问题',
                'description': 'Python版本可能不兼容，建议升级到Python 3.8+',
                'auto_fixable': False,
                'manual_steps': [
                    '1. 下载Python 3.8或更高版本',
                    '2. 安装新版本Python',
                    '3. 重新安装项目依赖'
                ]
            })

        # 检查依赖问题
        deps_result = diagnostic_results.get('dependencies', {})
        if deps_result.get('missing_required'):
            suggestions.append({
                'category': 'dependencies',
                'priority': 'critical',
                'title': '缺少必需依赖包',
                'description': f"缺少: {', '.join(deps_result['missing_required'])}",
                'auto_fixable': True,
                'packages': deps_result['missing_required'],
                'repair_function': self._repair_missing_packages
            })

        if deps_result.get('missing_optional'):
            suggestions.append({
                'category': 'dependencies',
                'priority': 'medium',
                'title': '缺少可选依赖包',
                'description': f"缺少: {', '.join(deps_result['missing_optional'])}",
                'auto_fixable': True,
                'packages': deps_result['missing_optional'],
                'repair_function': self._repair_missing_packages
            })

        # 检查系统资源问题
        resources_result = diagnostic_results.get('system_resources', {})
        if resources_result.get('issues'):
            for issue in resources_result['issues']:
                if '内存' in issue:
                    suggestions.append({
                        'category': 'memory',
                        'priority': 'high',
                        'title': '内存资源不足',
                        'description': issue,
                        'auto_fixable': True,
                        'repair_function': self._repair_memory_issues
                    })
                elif '磁盘' in issue:
                    suggestions.append({
                        'category': 'disk',
                        'priority': 'high',
                        'title': '磁盘空间不足',
                        'description': issue,
                        'auto_fixable': True,
                        'repair_function': self._repair_disk_issues
                    })

        # 检查文件权限问题
        perms_result = diagnostic_results.get('file_permissions', {})
        if perms_result.get('status') in ['error', 'warning']:
            suggestions.append({
                'category': 'permissions',
                'priority': 'high',
                'title': '文件权限问题',
                'description': perms_result.get('message', ''),
                'auto_fixable': True,
                'repair_function': self._repair_permission_issues
            })

        # 检查FFmpeg问题
        ffmpeg_result = diagnostic_results.get('ffmpeg', {})
        if not ffmpeg_result.get('installed', True):
            suggestions.append({
                'category': 'ffmpeg',
                'priority': 'medium',
                'title': 'FFmpeg未安装',
                'description': 'FFmpeg未安装，视频处理功能将不可用',
                'auto_fixable': False,
                'manual_steps': [
                    '1. 访问 https://ffmpeg.org/download.html',
                    '2. 下载适合您系统的FFmpeg',
                    '3. 将FFmpeg添加到系统PATH',
                    '4. 重启应用程序'
                ]
            })

        return suggestions

    def _repair_missing_packages(self, packages: List[str]) -> Dict[str, Any]:
        """修复缺失的包"""
        try:
            import subprocess

            results = {}
            for package in packages:
                try:
                    print(f"[修复] 正在安装 {package}...")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package
                    ], capture_output=True, text=True, timeout=300)

                    if result.returncode == 0:
                        results[package] = {'status': 'success', 'message': '安装成功'}
                        print(f"[修复] {package} 安装成功")
                    else:
                        results[package] = {
                            'status': 'error',
                            'message': result.stderr or '安装失败'
                        }
                        print(f"[修复] {package} 安装失败: {result.stderr}")

                except subprocess.TimeoutExpired:
                    results[package] = {'status': 'error', 'message': '安装超时'}
                except Exception as e:
                    results[package] = {'status': 'error', 'message': str(e)}

            success_count = sum(1 for r in results.values() if r['status'] == 'success')

            return {
                'overall_status': 'success' if success_count == len(packages) else 'partial',
                'success_count': success_count,
                'total_count': len(packages),
                'details': results
            }

        except Exception as e:
            return {
                'overall_status': 'error',
                'error': str(e),
                'message': '包安装修复失败'
            }

    def _repair_memory_issues(self) -> Dict[str, Any]:
        """修复内存问题"""
        try:
            import gc

            # 强制垃圾回收
            collected = gc.collect()

            # 尝试释放一些缓存
            try:
                import psutil
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB

                # 清理Python缓存
                sys.modules.clear()

                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_freed = memory_before - memory_after

                return {
                    'status': 'success',
                    'message': f'内存清理完成，释放了 {memory_freed:.1f}MB',
                    'objects_collected': collected,
                    'memory_freed_mb': memory_freed
                }
            except:
                return {
                    'status': 'success',
                    'message': f'垃圾回收完成，清理了 {collected} 个对象',
                    'objects_collected': collected
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '内存清理失败'
            }

    def _repair_disk_issues(self) -> Dict[str, Any]:
        """修复磁盘空间问题"""
        try:
            import shutil

            # 清理临时文件和缓存
            cleaned_dirs = []
            total_freed = 0

            # 清理缓存目录
            cache_dirs = ['cache', '__pycache__', '.pytest_cache', 'logs']
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        dir_size = self._get_dir_size(cache_dir)
                        shutil.rmtree(cache_dir)
                        os.makedirs(cache_dir, exist_ok=True)
                        cleaned_dirs.append(cache_dir)
                        total_freed += dir_size
                    except Exception as e:
                        print(f"[修复] 清理 {cache_dir} 失败: {e}")

            # 清理临时文件
            temp_patterns = ['*.tmp', '*.log', '*.bak']
            for pattern in temp_patterns:
                import glob
                for file_path in glob.glob(pattern):
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_freed += file_size
                    except Exception:
                        pass

            freed_mb = total_freed / 1024 / 1024

            return {
                'status': 'success',
                'message': f'磁盘清理完成，释放了 {freed_mb:.1f}MB',
                'cleaned_directories': cleaned_dirs,
                'freed_bytes': total_freed,
                'freed_mb': freed_mb
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '磁盘清理失败'
            }

    def _repair_permission_issues(self) -> Dict[str, Any]:
        """修复权限问题"""
        try:
            # 尝试创建必要的目录
            required_dirs = ['models', 'config', 'logs', 'cache']
            created_dirs = []

            for dir_name in required_dirs:
                if not os.path.exists(dir_name):
                    try:
                        os.makedirs(dir_name, exist_ok=True)
                        created_dirs.append(dir_name)
                    except Exception as e:
                        print(f"[修复] 创建目录 {dir_name} 失败: {e}")

            # 尝试创建测试文件检查写入权限
            test_file = 'test_write_permission.tmp'
            can_write = False
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                can_write = True
            except Exception:
                pass

            return {
                'status': 'success' if can_write else 'partial',
                'message': f'权限修复完成，创建了 {len(created_dirs)} 个目录',
                'created_directories': created_dirs,
                'write_permission': can_write
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '权限修复失败'
            }

    def _get_dir_size(self, path: str) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass
        except Exception:
            pass
        return total_size

__all__ = ['SystemDiagnostic', 'AutoRepairSystem']
