"""
硬件能力检测模块 - VisionAI-ClipsMaster
用于检测设备硬件能力并推荐最佳模型配置
"""

import os
import sys
import platform
import psutil
import cpuinfo
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class HardwareDetector:
    """硬件检测器，用于评估设备运行AI模型的能力"""
    
    def __init__(self):
        self.cpu_info = self._get_cpu_info()
        self.memory_info = self._get_memory_info()
        self.gpu_info = self._get_gpu_info()
        self.system_info = self._get_system_info()
        
    def _get_cpu_info(self) -> Dict:
        """获取CPU详细信息"""
        try:
            info = cpuinfo.get_cpu_info()
            
            # 检测CPU指令集支持
            instruction_sets = {
                'avx': 'avx' in info.get('flags', []),
                'avx2': 'avx2' in info.get('flags', []),
                'avx512': any('avx512' in flag for flag in info.get('flags', [])),
                'sse4_2': 'sse4_2' in info.get('flags', []),
                'neon': 'neon' in info.get('flags', []),  # ARM平台
                'f16c': 'f16c' in info.get('flags', []),  # 半精度浮点支持
            }
            
            return {
                'brand': info.get('brand_raw', 'Unknown CPU'),
                'cores_physical': psutil.cpu_count(logical=False),
                'cores_logical': psutil.cpu_count(logical=True),
                'frequency': info.get('hz_advertised_friendly', 'Unknown'),
                'architecture': info.get('arch', platform.machine()),
                'instruction_sets': instruction_sets
            }
        except Exception as e:
            logger.error(f"获取CPU信息失败: {str(e)}")
            return {'error': str(e)}
    
    def _get_memory_info(self) -> Dict:
        """获取内存详细信息"""
        try:
            mem = psutil.virtual_memory()
            return {
                'total': mem.total,
                'total_gb': round(mem.total / (1024**3), 2),
                'available': mem.available,
                'available_gb': round(mem.available / (1024**3), 2),
                'percent_used': mem.percent
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {str(e)}")
            return {'error': str(e)}
    
    def _get_gpu_info(self) -> Dict:
        """获取GPU信息（如存在）"""
        gpu_info = {'available': False, 'devices': []}
        
        # 尝试检测CUDA GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info['available'] = True
                gpu_info['type'] = 'CUDA'
                gpu_info['cuda_version'] = torch.version.cuda
                gpu_info['device_count'] = torch.cuda.device_count()
                
                for i in range(torch.cuda.device_count()):
                    gpu_info['devices'].append({
                        'name': torch.cuda.get_device_name(i),
                        'memory_total': torch.cuda.get_device_properties(i).total_memory,
                        'memory_total_gb': round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2)
                    })
                return gpu_info
        except (ImportError, Exception) as e:
            pass
            
        # 尝试检测AMD GPU (ROCm)
        try:
            if os.system("rocm-smi --showproductname") == 0:
                gpu_info['available'] = True
                gpu_info['type'] = 'ROCm'
                # 这里可以添加更多详细的ROCm GPU信息
                return gpu_info
        except Exception:
            pass
            
        # 尝试检测Intel集成显卡
        try:
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode()
                if 'Intel' in result and ('UHD' in result or 'HD Graphics' in result or 'Iris' in result):
                    gpu_info['available'] = True
                    gpu_info['type'] = 'Intel Integrated'
                    gpu_info['name'] = [line for line in result.split('\n') if 'Intel' in line][0].strip()
                    return gpu_info
            elif platform.system() == 'Linux':
                # Linux检测Intel GPU
                pass
        except Exception:
            pass
            
        return gpu_info
    
    def _get_system_info(self) -> Dict:
        """获取操作系统信息"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'python_version': platform.python_version()
        }
    
    def recommend_model_config(self) -> Dict:
        """根据硬件能力推荐最佳模型配置 - 增强版本"""
        config = {}

        # 获取硬件信息
        memory_gb = self.memory_info.get('total_gb', 0)
        available_gb = self.memory_info.get('available_gb', 0)
        gpu_available = self.gpu_info.get('available', False)
        gpu_type = self.gpu_info.get('type', 'Unknown')
        cpu_cores = self.cpu_info.get('cores_logical', 0)

        # 增强的量化等级推荐逻辑
        if memory_gb < 4:
            # 极低内存设备 (<4GB)
            config['quantization'] = 'Q2_K'
            config['model_size'] = 'nano'
            config['warning'] = '设备内存不足4GB，将使用最低配置，性能可能受限'
            config['device_category'] = 'low_memory'
        elif memory_gb < 8:
            # 低内存设备 (4-8GB)
            if gpu_available and gpu_type in ['CUDA', 'NVIDIA']:
                config['quantization'] = 'Q4_K_M'  # GPU可以补偿一些性能
            else:
                config['quantization'] = 'Q2_K'  # CPU-only设备使用更轻量级
            config['model_size'] = 'base'
            config['device_category'] = 'low_memory'
        elif memory_gb < 16:
            # 中等内存设备 (8-16GB)
            if gpu_available and gpu_type in ['CUDA', 'NVIDIA']:
                config['quantization'] = 'Q5_K_M'  # 独立GPU可以使用更高质量
            elif gpu_available:
                config['quantization'] = 'Q4_K_M'  # 集成GPU使用平衡配置
            else:
                config['quantization'] = 'Q4_K_M'  # CPU-only使用平衡配置
            config['model_size'] = 'base'
            config['device_category'] = 'medium_performance'
        elif memory_gb < 32:
            # 高内存设备 (16-32GB)
            if gpu_available and gpu_type in ['CUDA', 'NVIDIA']:
                config['quantization'] = 'Q8_0'  # 高质量量化
            else:
                config['quantization'] = 'Q5_K_M'
            config['model_size'] = 'large'
            config['device_category'] = 'high_performance'
        else:
            # 超高性能设备 (>32GB)
            if gpu_available and gpu_type in ['CUDA', 'NVIDIA']:
                config['quantization'] = 'FP16'  # 最高质量
            else:
                config['quantization'] = 'Q8_0'
            config['model_size'] = 'large'
            config['device_category'] = 'ultra_high_performance'
            
        # GPU加速设置
        if self.gpu_info.get('available', False):
            config['use_gpu'] = True
            config['gpu_type'] = self.gpu_info.get('type', 'Unknown')
            if self.gpu_info.get('type') == 'CUDA':
                config['gpu_memory'] = self.gpu_info.get('devices', [{}])[0].get('memory_total_gb', 0)
            else:
                config['gpu_memory'] = 'Unknown'
        else:
            config['use_gpu'] = False
            
            # CPU优化设置
            cpu_sets = self.cpu_info.get('instruction_sets', {})
            if cpu_sets.get('avx512', False):
                config['cpu_optimization'] = 'avx512'
            elif cpu_sets.get('avx2', False):
                config['cpu_optimization'] = 'avx2'
            elif cpu_sets.get('avx', False):
                config['cpu_optimization'] = 'avx'
            elif cpu_sets.get('sse4_2', False):
                config['cpu_optimization'] = 'sse4.2'
            elif cpu_sets.get('neon', False):
                config['cpu_optimization'] = 'neon'  # ARM架构
            else:
                config['cpu_optimization'] = 'basic'
                config['warning'] = '未检测到高级CPU指令集，性能可能受限'
                
        # 增强的批处理大小设置
        if memory_gb < 4:
            config['batch_size'] = 1
        elif memory_gb < 8:
            config['batch_size'] = 2 if not gpu_available else 4
        elif memory_gb < 16:
            config['batch_size'] = 4 if not gpu_available else 8
        else:
            config['batch_size'] = 8 if not gpu_available else 16

        # 增强的模型加载策略
        if memory_gb < 6:
            config['loading_strategy'] = 'disk_offload'  # 磁盘分片加载
        elif memory_gb < 12:
            config['loading_strategy'] = 'memory_mapped'  # 内存映射
        else:
            config['loading_strategy'] = 'full_memory'  # 全内存加载

        # 添加性能预期
        config['performance_tier'] = self._calculate_performance_tier(memory_gb, gpu_available, gpu_type, cpu_cores)

        # 添加推荐理由
        config['recommendation_reason'] = self._generate_recommendation_reason(config)
            
        return config

    def _calculate_performance_tier(self, memory_gb: float, gpu_available: bool, gpu_type: str, cpu_cores: int) -> str:
        """计算设备性能等级"""
        score = 0

        # 内存评分 (0-40分)
        if memory_gb >= 32:
            score += 40
        elif memory_gb >= 16:
            score += 30
        elif memory_gb >= 8:
            score += 20
        elif memory_gb >= 4:
            score += 10

        # GPU评分 (0-40分)
        if gpu_available:
            if gpu_type in ['CUDA', 'NVIDIA']:
                score += 40  # 独立NVIDIA GPU
            elif gpu_type in ['AMD', 'Radeon']:
                score += 30  # AMD GPU
            else:
                score += 15  # 集成GPU

        # CPU评分 (0-20分)
        if cpu_cores >= 16:
            score += 20
        elif cpu_cores >= 8:
            score += 15
        elif cpu_cores >= 4:
            score += 10
        else:
            score += 5

        # 根据总分确定等级
        if score >= 80:
            return "ultra_high"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "minimal"

    def _generate_recommendation_reason(self, config: Dict) -> str:
        """生成推荐理由"""
        memory_gb = self.memory_info.get('total_gb', 0)
        gpu_available = self.gpu_info.get('available', False)
        gpu_type = self.gpu_info.get('type', 'Unknown')
        quantization = config.get('quantization', 'Unknown')

        reasons = []

        # 内存相关理由
        if memory_gb < 8:
            reasons.append(f"内存{memory_gb:.1f}GB较少，推荐轻量级{quantization}量化")
        elif memory_gb >= 32:
            reasons.append(f"内存{memory_gb:.1f}GB充足，可使用高质量{quantization}量化")
        else:
            reasons.append(f"内存{memory_gb:.1f}GB适中，推荐平衡的{quantization}量化")

        # GPU相关理由
        if gpu_available:
            if gpu_type in ['CUDA', 'NVIDIA']:
                reasons.append("检测到NVIDIA GPU，可使用GPU加速")
            else:
                reasons.append(f"检测到{gpu_type} GPU，提供基础加速")
        else:
            reasons.append("未检测到GPU，使用CPU优化配置")

        return "; ".join(reasons)
    
    def is_compatible(self) -> Tuple[bool, str]:
        """检查设备是否满足最低要求"""
        compatible = True
        reason = ""
        
        # 检查内存
        if self.memory_info.get('total_gb', 0) < 4:
            compatible = False
            reason = f"内存不足: 需要至少4GB, 当前{self.memory_info.get('total_gb', 0)}GB"
            
        # 检查CPU
        cpu_sets = self.cpu_info.get('instruction_sets', {})
        if not (cpu_sets.get('avx', False) or cpu_sets.get('sse4_2', False) or cpu_sets.get('neon', False)):
            compatible = False
            reason += "\n不支持必要的CPU指令集(AVX/SSE4.2/NEON)"
            
        return compatible, reason
    
    def generate_report(self) -> str:
        """生成人类可读的硬件报告"""
        config = self.recommend_model_config()
        compatible, reason = self.is_compatible()
        
        report = [
            "=== VisionAI-ClipsMaster 硬件兼容性报告 ===",
            f"CPU: {self.cpu_info.get('brand', 'Unknown')}",
            f"物理核心: {self.cpu_info.get('cores_physical', 'Unknown')}",
            f"逻辑核心: {self.cpu_info.get('cores_logical', 'Unknown')}",
            f"支持指令集: {', '.join([k for k, v in self.cpu_info.get('instruction_sets', {}).items() if v])}",
            f"内存: 总计 {self.memory_info.get('total_gb', 0)}GB, 可用 {self.memory_info.get('available_gb', 0)}GB",
            f"GPU: {'可用' if self.gpu_info.get('available', False) else '不可用'}"
        ]
        
        if self.gpu_info.get('available', False):
            report.append(f"GPU类型: {self.gpu_info.get('type', 'Unknown')}")
            if self.gpu_info.get('devices'):
                report.append(f"GPU名称: {self.gpu_info.get('devices', [{}])[0].get('name', 'Unknown')}")
                report.append(f"GPU内存: {self.gpu_info.get('devices', [{}])[0].get('memory_total_gb', 0)}GB")
        
        report.extend([
            "",
            "=== 推荐配置 ===",
            f"量化等级: {config.get('quantization', 'Unknown')}",
            f"模型大小: {config.get('model_size', 'Unknown')}",
            f"批处理大小: {config.get('batch_size', 'Unknown')}",
            f"加载策略: {config.get('loading_strategy', 'Unknown')}",
            f"使用GPU: {'是' if config.get('use_gpu', False) else '否'}",
            f"CPU优化: {config.get('cpu_optimization', 'Unknown')}"
        ])
        
        if 'warning' in config:
            report.extend(["", f"警告: {config.get('warning')}", ""])
            
        report.extend([
            "",
            "=== 兼容性检查 ===",
            f"兼容: {'是' if compatible else '否'}"
        ])
        
        if not compatible:
            report.append(f"原因: {reason}")
            
        return "\n".join(report)
    
    def to_dict(self) -> Dict:
        """将所有信息转换为字典"""
        return {
            'cpu': self.cpu_info,
            'memory': self.memory_info,
            'gpu': self.gpu_info,
            'system': self.system_info,
            'recommendation': self.recommend_model_config(),
            'compatibility': self.is_compatible()[0]
        }

    def detect_hardware(self):
        """检测硬件配置并返回标准化的硬件信息对象"""
        try:
            # 获取基础信息
            memory_gb = self.memory_info.get('total_gb', 0)
            available_memory_gb = self.memory_info.get('available_gb', 0)
            cpu_cores = self.cpu_info.get('cores_logical', 0)

            # GPU信息
            gpu_info = self.gpu_info
            has_gpu = gpu_info.get('available', False)
            gpu_memory_gb = 0
            gpu_names = []
            gpu_type = "None"

            if has_gpu and gpu_info.get('devices'):
                # 获取第一个GPU的信息
                first_gpu = gpu_info['devices'][0]
                gpu_memory_gb = first_gpu.get('memory_gb', 0)
                gpu_names = [device.get('name', 'Unknown GPU') for device in gpu_info['devices']]
                gpu_type = first_gpu.get('type', 'Unknown')

            # CPU频率
            cpu_freq_mhz = 0
            try:
                freq_info = psutil.cpu_freq()
                if freq_info:
                    cpu_freq_mhz = freq_info.current
            except:
                pass

            # 性能等级评估
            performance_level = self._evaluate_performance_level(memory_gb, has_gpu, gpu_memory_gb, cpu_cores)

            # 推荐量化等级
            recommended_quantization = self._get_recommended_quantization(memory_gb, has_gpu, gpu_memory_gb)

            # 创建硬件信息对象
            class HardwareInfo:
                def __init__(self):
                    self.gpu_type = gpu_type
                    self.gpu_memory_gb = gpu_memory_gb
                    self.gpu_count = len(gpu_info.get('devices', []))
                    self.gpu_names = gpu_names
                    self.total_memory_gb = memory_gb
                    self.available_memory_gb = available_memory_gb
                    self.cpu_cores = cpu_cores
                    self.cpu_freq_mhz = cpu_freq_mhz
                    self.performance_level = performance_level
                    self.recommended_quantization = recommended_quantization
                    self.gpu_acceleration = has_gpu

            return HardwareInfo()

        except Exception as e:
            logger.error(f"硬件检测失败: {e}")
            # 返回默认的硬件信息
            class DefaultHardwareInfo:
                def __init__(self):
                    self.gpu_type = "Unknown"
                    self.gpu_memory_gb = 0
                    self.gpu_count = 0
                    self.gpu_names = []
                    self.total_memory_gb = 4.0  # 默认4GB
                    self.available_memory_gb = 2.0
                    self.cpu_cores = 4
                    self.cpu_freq_mhz = 2000
                    self.performance_level = "Low"
                    self.recommended_quantization = "Q4_K_M"
                    self.gpu_acceleration = False

            return DefaultHardwareInfo()

    def _evaluate_performance_level(self, memory_gb: float, has_gpu: bool, gpu_memory_gb: float, cpu_cores: int) -> str:
        """评估性能等级"""
        try:
            if has_gpu and gpu_memory_gb >= 8 and memory_gb >= 16:
                return "High"
            elif (has_gpu and gpu_memory_gb >= 4) or (memory_gb >= 12 and cpu_cores >= 8):
                return "Medium"
            else:
                return "Low"
        except:
            return "Low"

    def _get_recommended_quantization(self, memory_gb: float, has_gpu: bool, gpu_memory_gb: float) -> str:
        """获取推荐的量化等级"""
        try:
            if has_gpu and gpu_memory_gb >= 12:
                return "Q8_0"  # 高质量
            elif memory_gb >= 16:
                return "Q5_K_M"  # 平衡
            elif memory_gb >= 8:
                return "Q4_K_M"  # 标准
            else:
                return "Q2_K"  # 轻量
        except:
            return "Q4_K_M"

def main():
    """作为独立脚本运行时的主函数"""
    detector = HardwareDetector()
    print(detector.generate_report())
    
    # 生成推荐配置并写入文件
    recommendation = detector.recommend_model_config()
    import json
    with open('hardware_recommendation.json', 'w', encoding='utf-8') as f:
        json.dump(recommendation, f, indent=2, ensure_ascii=False)
    print(f"\n推荐配置已写入 hardware_recommendation.json")

if __name__ == "__main__":
    main() 