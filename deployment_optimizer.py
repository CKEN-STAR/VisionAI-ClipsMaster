#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 部署优化器
提供部署环境检测、配置优化、依赖验证和性能调优功能
"""

import os
import sys
import json
import yaml
import time
import psutil
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment_optimizer.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentOptimizer:
    """部署优化器主类"""
    
    def __init__(self, project_root: Optional[str] = None):
        """初始化部署优化器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_dir = self.project_root / "configs"
        self.logs_dir = self.project_root / "logs"
        self.temp_dir = self.project_root / "temp"
        
        # 确保必要目录存在
        for directory in [self.logs_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
        
        # 系统信息
        self.system_info = self._collect_system_info()
        
        # 优化结果
        self.optimization_results = {
            'timestamp': time.time(),
            'system_info': self.system_info,
            'optimizations_applied': [],
            'performance_metrics': {},
            'issues_found': [],
            'recommendations': []
        }
        
        logger.info("部署优化器初始化完成")
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': psutil.disk_usage(str(self.project_root)),
                'architecture': platform.architecture()[0]
            }
        except Exception as e:
            logger.error(f"收集系统信息失败: {e}")
            return {}
    
    def detect_deployment_environment(self) -> Dict[str, Any]:
        """检测部署环境"""
        logger.info("开始检测部署环境...")
        
        environment = {
            'type': 'unknown',
            'container': False,
            'virtual_env': False,
            'gpu_available': False,
            'performance_tier': 'medium',
            'memory_tier': 'medium',
            'storage_tier': 'medium'
        }
        
        try:
            # 检测容器环境
            if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
                environment['type'] = 'docker'
                environment['container'] = True
            
            # 检测虚拟环境
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                environment['virtual_env'] = True
            
            # 检测GPU
            try:
                import torch
                if torch.cuda.is_available():
                    environment['gpu_available'] = True
                    environment['gpu_count'] = torch.cuda.device_count()
                    environment['gpu_name'] = torch.cuda.get_device_name(0)
            except ImportError:
                pass
            
            # 性能分级
            memory_gb = self.system_info.get('memory_total', 0) / (1024**3)
            cpu_count = self.system_info.get('cpu_count', 1)
            
            if memory_gb >= 16 and cpu_count >= 8:
                environment['performance_tier'] = 'high'
                environment['memory_tier'] = 'high'
            elif memory_gb >= 8 and cpu_count >= 4:
                environment['performance_tier'] = 'medium'
                environment['memory_tier'] = 'medium'
            else:
                environment['performance_tier'] = 'low'
                environment['memory_tier'] = 'low'
            
            # 存储分级
            disk_usage = self.system_info.get('disk_usage')
            disk_free_gb = disk_usage.free / (1024**3) if disk_usage else 0
            if disk_free_gb >= 50:
                environment['storage_tier'] = 'high'
            elif disk_free_gb >= 20:
                environment['storage_tier'] = 'medium'
            else:
                environment['storage_tier'] = 'low'
            
            logger.info(f"环境检测完成: {environment}")
            return environment
            
        except Exception as e:
            logger.error(f"环境检测失败: {e}")
            return environment
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """验证依赖项"""
        logger.info("开始验证依赖项...")
        
        validation_results = {
            'python_packages': {},
            'system_dependencies': {},
            'missing_packages': [],
            'version_conflicts': [],
            'recommendations': []
        }
        
        try:
            # 检查Python包
            requirements_files = [
                'requirements.txt',
                'requirements/requirements.txt',
                'requirements_minimal.txt'
            ]
            
            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    validation_results['python_packages'][req_file] = self._validate_requirements_file(req_path)
            
            # 检查系统依赖
            system_deps = ['ffmpeg', 'git']
            for dep in system_deps:
                validation_results['system_dependencies'][dep] = self._check_system_dependency(dep)
            
            logger.info("依赖项验证完成")
            return validation_results
            
        except Exception as e:
            logger.error(f"依赖项验证失败: {e}")
            return validation_results
    
    def _validate_requirements_file(self, req_file: Path) -> Dict[str, Any]:
        """验证requirements文件"""
        result = {'status': 'unknown', 'packages': [], 'issues': []}
        
        try:
            with open(req_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    package_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                    try:
                        __import__(package_name.replace('-', '_'))
                        result['packages'].append({'name': package_name, 'status': 'installed'})
                    except ImportError:
                        result['packages'].append({'name': package_name, 'status': 'missing'})
                        result['issues'].append(f"缺少包: {package_name}")
            
            result['status'] = 'validated'
            
        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f"验证失败: {e}")
        
        return result
    
    def _check_system_dependency(self, dependency: str) -> Dict[str, Any]:
        """检查系统依赖"""
        result = {'status': 'unknown', 'version': None, 'path': None}
        
        try:
            # 尝试运行命令检查版本
            if dependency == 'ffmpeg':
                cmd = ['ffmpeg', '-version']
            elif dependency == 'git':
                cmd = ['git', '--version']
            else:
                cmd = [dependency, '--version']
            
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if process.returncode == 0:
                result['status'] = 'available'
                result['version'] = process.stdout.split('\n')[0]
                result['path'] = subprocess.run(['which', dependency], capture_output=True, text=True).stdout.strip()
            else:
                result['status'] = 'missing'
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            result['status'] = 'missing'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def optimize_configuration(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """根据环境优化配置"""
        logger.info("开始优化配置...")
        
        optimization_results = {
            'config_files_updated': [],
            'optimizations_applied': [],
            'performance_improvements': []
        }
        
        try:
            # 根据性能分级优化配置
            tier = environment.get('performance_tier', 'medium')
            
            # 更新系统设置
            system_config = self._generate_optimized_system_config(environment)
            self._save_config('system_settings.yaml', system_config)
            optimization_results['config_files_updated'].append('system_settings.yaml')
            
            # 更新模型配置
            model_config = self._generate_optimized_model_config(environment)
            self._save_config('model_config.yaml', model_config)
            optimization_results['config_files_updated'].append('model_config.yaml')
            
            # 更新优化配置
            opt_config = self._generate_optimization_config(environment)
            self._save_config('optimization.json', opt_config)
            optimization_results['config_files_updated'].append('optimization.json')
            
            logger.info("配置优化完成")
            return optimization_results
            
        except Exception as e:
            logger.error(f"配置优化失败: {e}")
            return optimization_results
    
    def _generate_optimized_system_config(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """生成优化的系统配置"""
        tier = environment.get('performance_tier', 'medium')
        memory_gb = self.system_info.get('memory_total', 0) / (1024**3)
        
        config = {
            'hardware': {
                'auto_detect': True,
                'performance_tier': tier,
                'min_memory_mb': 1024,
                'min_storage_mb': 5120,
                'gpu_acceleration': environment.get('gpu_available', False)
            },
            'optimization': {}
        }
        
        if tier == 'low':
            config['optimization']['low_tier'] = {
                'model_quantization': 'Q2_K',
                'batch_size': 1,
                'dynamic_unload': True,
                'worker_threads': 1,
                'chunk_size': 256,
                'offload_to_disk': True,
                'compute_device': 'cpu',
                'realtime_preview': False,
                'execution_mode': 'efficiency'
            }
        elif tier == 'medium':
            config['optimization']['medium_tier'] = {
                'model_quantization': 'Q4_K_M',
                'batch_size': 2,
                'dynamic_unload': False,
                'worker_threads': min(4, self.system_info.get('cpu_count', 2)),
                'chunk_size': 512,
                'offload_to_disk': False,
                'compute_device': 'auto',
                'realtime_preview': True,
                'execution_mode': 'balanced'
            }
        else:  # high
            config['optimization']['high_tier'] = {
                'model_quantization': 'Q5_K',
                'batch_size': 4,
                'dynamic_unload': False,
                'worker_threads': min(8, self.system_info.get('cpu_count', 4)),
                'chunk_size': 1024,
                'offload_to_disk': False,
                'compute_device': 'gpu' if environment.get('gpu_available') else 'cpu',
                'realtime_preview': True,
                'execution_mode': 'performance'
            }
        
        return config
    
    def _generate_optimized_model_config(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """生成优化的模型配置"""
        tier = environment.get('performance_tier', 'medium')
        
        config = {
            'active_models': {
                'chinese': 'qwen2.5-7b-zh',
                'english': 'mistral-7b-en'
            },
            'quantization': {
                'default': 'Q4_K_M' if tier != 'low' else 'Q2_K',
                'low_memory': 'Q2_K',
                'high_performance': 'Q5_K' if tier == 'high' else 'Q4_K_M'
            },
            'performance': {
                'max_threads': min(self.system_info.get('cpu_count', 2), 8 if tier == 'high' else 4),
                'batch_size': 4 if tier == 'high' else (2 if tier == 'medium' else 1),
                'use_gpu': environment.get('gpu_available', False) and tier != 'low'
            }
        }
        
        return config
    
    def _generate_optimization_config(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """生成优化配置"""
        tier = environment.get('performance_tier', 'medium')
        cpu_count = self.system_info.get('cpu_count', 2)
        
        config = {
            'optimization_path': 'avx2' if tier != 'low' else 'sse4',
            'cpu_features': {
                'sse': True,
                'sse2': True,
                'ssse3': True,
                'sse4_1': True,
                'sse4_2': True,
                'avx': tier != 'low',
                'avx2': tier == 'high',
                'fma': tier != 'low',
                'f16c': tier != 'low',
                'aes': True
            },
            'details': {
                'name': 'AVX2' if tier == 'high' else ('SSE4' if tier == 'low' else 'AVX'),
                'description': f'{tier.title()} 优化 ({min(cpu_count, 8 if tier == "high" else 4)}线程)',
                'parallel_threads': min(cpu_count, 8 if tier == 'high' else (4 if tier == 'medium' else 2)),
                'simd_width': 256 if tier != 'low' else 128,
                'performance_rating': 90 if tier == 'high' else (70 if tier == 'medium' else 50),
                'simd_type': 'avx2' if tier == 'high' else ('avx' if tier == 'medium' else 'sse4'),
                'active': True
            }
        }
        
        return config
    
    def _save_config(self, filename: str, config: Dict[str, Any]):
        """保存配置文件"""
        config_path = self.config_dir / filename
        
        try:
            if filename.endswith('.json'):
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            elif filename.endswith('.yaml') or filename.endswith('.yml'):
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            logger.info(f"配置文件已保存: {config_path}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败 {filename}: {e}")
    
    def perform_integrity_check(self) -> Dict[str, Any]:
        """执行完整性检查"""
        logger.info("开始执行完整性检查...")
        
        check_results = {
            'file_integrity': {},
            'configuration_validity': {},
            'dependency_status': {},
            'performance_baseline': {},
            'issues_found': [],
            'overall_status': 'unknown'
        }
        
        try:
            # 检查关键文件
            critical_files = [
                'simple_ui_fixed.py',
                'src/core/language_detector.py',
                'src/utils/memory_guard.py',
                'configs/system_settings.yaml'
            ]
            
            for file_path in critical_files:
                full_path = self.project_root / file_path
                check_results['file_integrity'][file_path] = {
                    'exists': full_path.exists(),
                    'readable': full_path.exists() and os.access(full_path, os.R_OK),
                    'size': full_path.stat().st_size if full_path.exists() else 0
                }
            
            # 检查配置有效性
            config_files = ['system_settings.yaml', 'model_config.yaml', 'optimization.json']
            for config_file in config_files:
                config_path = self.config_dir / config_file
                if config_path.exists():
                    try:
                        if config_file.endswith('.json'):
                            with open(config_path, 'r', encoding='utf-8') as f:
                                json.load(f)
                        else:
                            with open(config_path, 'r', encoding='utf-8') as f:
                                yaml.safe_load(f)
                        check_results['configuration_validity'][config_file] = 'valid'
                    except Exception as e:
                        check_results['configuration_validity'][config_file] = f'invalid: {e}'
                        check_results['issues_found'].append(f"配置文件无效: {config_file}")
                else:
                    check_results['configuration_validity'][config_file] = 'missing'
                    check_results['issues_found'].append(f"配置文件缺失: {config_file}")
            
            # 确定整体状态
            if len(check_results['issues_found']) == 0:
                check_results['overall_status'] = 'healthy'
            elif len(check_results['issues_found']) <= 2:
                check_results['overall_status'] = 'warning'
            else:
                check_results['overall_status'] = 'critical'
            
            logger.info(f"完整性检查完成，状态: {check_results['overall_status']}")
            return check_results
            
        except Exception as e:
            logger.error(f"完整性检查失败: {e}")
            check_results['overall_status'] = 'error'
            return check_results
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """运行完整的部署优化流程"""
        logger.info("开始运行完整部署优化...")
        
        start_time = time.time()
        
        try:
            # 1. 环境检测
            environment = self.detect_deployment_environment()
            self.optimization_results['environment'] = environment
            
            # 2. 依赖验证
            dependencies = self.validate_dependencies()
            self.optimization_results['dependencies'] = dependencies
            
            # 3. 配置优化
            config_optimization = self.optimize_configuration(environment)
            self.optimization_results['configuration'] = config_optimization
            
            # 4. 完整性检查
            integrity_check = self.perform_integrity_check()
            self.optimization_results['integrity'] = integrity_check
            
            # 5. 生成报告
            elapsed_time = time.time() - start_time
            self.optimization_results['execution_time'] = elapsed_time
            self.optimization_results['status'] = 'completed'
            
            # 保存结果
            self._save_optimization_report()
            
            logger.info(f"部署优化完成，耗时: {elapsed_time:.2f}秒")
            return self.optimization_results
            
        except Exception as e:
            logger.error(f"部署优化失败: {e}")
            self.optimization_results['status'] = 'failed'
            self.optimization_results['error'] = str(e)
            return self.optimization_results
    
    def _save_optimization_report(self):
        """保存优化报告"""
        report_path = self.logs_dir / f"deployment_optimization_{int(time.time())}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.optimization_results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"优化报告已保存: {report_path}")
            
        except Exception as e:
            logger.error(f"保存优化报告失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 VisionAI-ClipsMaster 部署优化器")
    print("=" * 60)
    
    optimizer = DeploymentOptimizer()
    results = optimizer.run_full_optimization()
    
    print(f"\n✅ 优化完成，状态: {results.get('status', 'unknown')}")
    if results.get('execution_time'):
        print(f"⏱️  执行时间: {results['execution_time']:.2f}秒")
    
    return results

if __name__ == "__main__":
    main()
