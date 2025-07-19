#!/usr/bin/env python3
"""
硬件自适应配置脚本 - VisionAI-ClipsMaster
根据硬件检测结果自动更新模型配置文件
"""

import os
import sys
import json
import yaml
import logging
import argparse
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s | %(levelname)-8s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('hardware-config')

# 添加项目根目录到路径
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

# 导入硬件检测器
from src.utils.hardware_detector import HardwareDetector

# 尝试导入指令集优化路由器
try:
    from src.hardware.optimization_router import OptimizationRouter, select_optimization_path

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

    HAS_OPTIMIZATION_ROUTER = True
except ImportError:
    HAS_OPTIMIZATION_ROUTER = False
    logger.warning("未找到指令集优化路由器，将使用基本CPU检测")

def setup_directories():
    """确保必要的目录结构存在"""
    dirs = [
        'configs',
        'configs/models',
        'configs/models/available_models',
        'models',
        'models/qwen',
        'models/qwen/quantized',
        'models/qwen/base',
        'models/mistral',
        'models/mistral/quantized',
        'models/mistral/base',
        'src/hardware'
    ]
    
    for d in dirs:
        os.makedirs(os.path.join(root_dir, d), exist_ok=True)
    
    logger.info("目录结构已检查并创建")

def update_model_configs(hardware_config):
    """根据硬件配置更新模型配置文件"""
    configs_dir = os.path.join(root_dir, 'configs')
    models_dir = os.path.join(configs_dir, 'models')
    available_models_dir = os.path.join(models_dir, 'available_models')
    
    # 读取当前激活模型
    active_model_path = os.path.join(models_dir, 'active_model.yaml')
    
    # 读取或创建激活模型配置
    if os.path.exists(active_model_path):
        with open(active_model_path, 'r', encoding='utf-8') as f:
            active_model = yaml.safe_load(f) or {}
    else:
        # 默认配置
        active_model = {
            'active_model': 'qwen2.5-7b-zh',  # 默认使用中文模型
            'language': 'zh',
            'last_updated': '2023-07-15 12:34:56',
            'switch_history': []
        }
    
    # 获取当前激活的模型名称
    active_model_name = active_model.get('active_model', 'qwen2.5-7b-zh')
    
    # 更新中文模型配置
    zh_model_path = os.path.join(available_models_dir, 'qwen2.5-7b-zh.yaml')
    if os.path.exists(zh_model_path):
        with open(zh_model_path, 'r', encoding='utf-8') as f:
            zh_model_config = yaml.safe_load(f) or {}
    else:
        # 创建默认中文模型配置
        zh_model_config = {
            'name': 'qwen2.5-7b-zh',
            'display_name': 'Qwen 2.5-7B 中文',
            'language': 'zh',
            'description': '阿里云开发的强大中文大模型，针对对话和创意写作优化',
            'model_path': 'models/qwen/quantized/qwen2.5-7b-zh-q4km.gguf',
            'tokenizer_path': 'models/qwen/base/tokenizer.model',
            'quantization': 'Q4_K_M',
            'loading_strategy': 'normal',
            'batch_size': 2,
            'context_length': 2048,
            'temperature': 0.7,
            'top_p': 0.9,
            'repetition_penalty': 1.1,
            'cache_capacity': 25,
            'use_gpu': False,
            'gpu_layers': 0,
            'size': '7B',
            'version': '2.5',
            'license': '非商用',
            'last_updated': '2023-07-01',
            'training_status': {
                'is_finetuned': True,
                'base_model': 'qwen2.5-7b',
                'finetuning_date': '2023-07-10',
                'finetuning_samples': 1200
            }
        }
    
    # 更新英文模型配置
    en_model_path = os.path.join(available_models_dir, 'mistral-7b-en.yaml')
    if os.path.exists(en_model_path):
        with open(en_model_path, 'r', encoding='utf-8') as f:
            en_model_config = yaml.safe_load(f) or {}
    else:
        # 创建默认英文模型配置
        en_model_config = {
            'name': 'mistral-7b-en',
            'display_name': 'Mistral 7B English',
            'language': 'en',
            'description': 'Mistral AI开发的强大英文大模型，优秀的指令遵循和创意写作能力',
            'model_path': 'models/mistral/quantized/mistral-7b-instruct-v0.2-q4km.gguf',
            'tokenizer_path': 'models/mistral/base/tokenizer.model',
            'quantization': 'Q4_K_M',
            'loading_strategy': 'normal',
            'batch_size': 2,
            'context_length': 2048,
            'temperature': 0.7,
            'top_p': 0.9,
            'repetition_penalty': 1.1,
            'cache_capacity': 25,
            'use_gpu': False,
            'gpu_layers': 0,
            'size': '7B',
            'version': '0.2',
            'license': 'Apache 2.0',
            'last_updated': '2023-06-15',
            'training_status': {
                'is_finetuned': True,
                'base_model': 'mistral-7b-instruct-v0.2',
                'finetuning_date': '2023-06-25',
                'finetuning_samples': 800
            },
            'prompt_template': '<s>[INST] {prompt} [/INST]'
        }
    
    # 应用硬件配置到模型配置
    for model_config, model_name in [(zh_model_config, 'qwen2.5-7b-zh'), (en_model_config, 'mistral-7b-en')]:
        # 更新量化级别
        model_config['quantization'] = hardware_config.get('quantization', 'Q4_K_M')
        
        # 更新加载策略
        model_config['loading_strategy'] = hardware_config.get('loading_strategy', 'normal')
        
        # 更新批处理大小
        model_config['batch_size'] = hardware_config.get('batch_size', 2)
        
        # 更新GPU设置
        if hardware_config.get('use_gpu', False):
            model_config['use_gpu'] = True
            
            # GPU层数根据GPU类型调整
            gpu_type = hardware_config.get('gpu_type', '')
            if 'NVIDIA' in gpu_type or 'nvidia' in gpu_type.lower():
                model_config['gpu_layers'] = -1  # 全部层使用GPU
            elif 'Intel' in gpu_type or 'AMD' in gpu_type:
                model_config['gpu_layers'] = min(24, model_config.get('gpu_layers', 0))  # 部分层使用GPU
        else:
            model_config['use_gpu'] = False
            model_config['gpu_layers'] = 0
        
        # 根据内存情况调整上下文长度
        if 'available_gb' in hardware_config and hardware_config['available_gb'] < 4:
            model_config['context_length'] = 1024  # 内存不足时减小上下文长度
        elif 'available_gb' in hardware_config and hardware_config['available_gb'] > 12:
            model_config['context_length'] = 4096  # 内存充足时增大上下文长度
            
        # 使用优化路由器获取模型优化参数（如果可用）
        if HAS_OPTIMIZATION_ROUTER:
            try:
                router = OptimizationRouter()
                model_params = router.get_model_parameters(model_name)
                
                # 更新线程数
                if 'threads' in model_params:
                    model_config['threads'] = model_params['threads']
                
                # 调整批处理大小
                if 'batch_size' in model_params:
                    model_config['batch_size'] = model_params['batch_size']
                
                # 更新高级优化选项
                if 'use_flash_attn' in model_params:
                    model_config['use_flash_attention'] = model_params['use_flash_attn']
                    
                if 'compile_model' in model_params:
                    model_config['compile_model'] = model_params['compile_model']
                
                logger.info(f"已使用指令集优化路由器更新 {model_name} 配置")
            except Exception as e:
                logger.error(f"应用优化路由器配置失败: {str(e)}")
    
    # 保存中文模型配置
    with open(zh_model_path, 'w', encoding='utf-8') as f:
        yaml.dump(zh_model_config, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"已更新中文模型配置: {zh_model_path}")
    
    # 保存英文模型配置
    with open(en_model_path, 'w', encoding='utf-8') as f:
        yaml.dump(en_model_config, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"已更新英文模型配置: {en_model_path}")
    
    # 保存激活模型配置
    with open(active_model_path, 'w', encoding='utf-8') as f:
        yaml.dump(active_model, f, default_flow_style=False, allow_unicode=True)
    logger.info(f"已更新激活模型配置: {active_model_path}")
    
    return active_model_name

def create_model_config_yaml(hardware_config):
    """创建全局模型配置文件"""
    config_path = os.path.join(root_dir, 'configs', 'model_config.yaml')
    
    # 获取CPU优化路径
    cpu_optimization = hardware_config.get('cpu_optimization', 'basic')
    
    # 如果优化路由器可用，更新CPU优化设置
    if HAS_OPTIMIZATION_ROUTER:
        try:
            opt_path = select_optimization_path()
            # 映射优化路径到硬件检测器使用的格式
            path_mapping = {
                'avx512': 'avx512',
                'avx2': 'avx2',
                'avx': 'avx',
                'sse4.2': 'sse4_2',
                'neon': 'neon',
                'baseline': 'basic'
            }
            cpu_optimization = path_mapping.get(opt_path, cpu_optimization)
            logger.info(f"已通过优化路由器确定CPU优化路径: {opt_path}")
        except Exception as e:
            logger.warning(f"获取优化路径失败: {str(e)}")
    
    # 基本配置
    config = {
        'hardware_profile': {
            'auto_detected': True,
            'last_updated': hardware_config.get('timestamp', ''),
            'cpu': {
                'optimization': cpu_optimization,
                'threads': min(os.cpu_count() or 4, 12)  # 最多使用12线程
            },
            'memory': {
                'available_gb': hardware_config.get('available_gb', 0),
                'warning_threshold': 0.85,
                'critical_threshold': 0.95
            },
            'gpu': {
                'available': hardware_config.get('use_gpu', False),
                'type': hardware_config.get('gpu_type', 'None')
            }
        },
        
        'model_defaults': {
            'temperature': 0.7,
            'top_p': 0.9,
            'repetition_penalty': 1.1,
            'max_context_length': hardware_config.get('context_length', 2048),
            'quantization': hardware_config.get('quantization', 'Q4_K_M')
        },
        
        'inference_settings': {
            'batch_size': hardware_config.get('batch_size', 2),
            'streaming': True,
            'loading_strategy': hardware_config.get('loading_strategy', 'normal'),
            'use_mmap': True,
            'use_mlock': hardware_config.get('loading_strategy', 'normal') != 'disk_offload'
        },
        
        'system_settings': {
            'auto_gc': True,
            'memory_guard': True,
            'cache_capacity_mb': 100,
            'log_level': 'info'
        }
    }
    
    # 添加优化路由器配置（如果可用）
    if HAS_OPTIMIZATION_ROUTER:
        try:
            router = OptimizationRouter()
            level = router.get_optimization_level()
            
            # 添加指令集优化信息
            config['optimization'] = {
                'path': router.get_optimization_path(),
                'name': level.get('name', 'Unknown'),
                'description': level.get('description', ''),
                'simd_width': level.get('simd_width', 64),
                'performance_rating': level.get('performance_rating', 0),
                'parallel_threads': level.get('parallel_threads', 1)
            }
            
            logger.info(f"已添加指令集优化配置: {level.get('name')}")
        except Exception as e:
            logger.warning(f"添加优化路由器配置失败: {str(e)}")
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info(f"已创建全局模型配置: {config_path}")
    return config_path

def export_optimization_config():
    """导出优化路由器配置（如果可用）"""
    if not HAS_OPTIMIZATION_ROUTER:
        logger.warning("优化路由器不可用，无法导出配置")
        return None
        
    try:
        router = OptimizationRouter()
        config_path = router.export_config()
        logger.info(f"已导出优化路由器配置: {config_path}")
        return config_path
    except Exception as e:
        logger.error(f"导出优化路由器配置失败: {str(e)}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 硬件自适应配置工具')
    parser.add_argument('--force', action='store_true', help='强制更新所有配置')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--optimization-only', action='store_true', help='仅更新指令集优化配置')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("=== VisionAI-ClipsMaster 硬件自适应配置 ===")
    
    # 确保目录结构存在
    setup_directories()
    
    # 硬件检测
    logger.info("正在检测硬件配置...")
    detector = HardwareDetector()
    hw_info = detector.to_dict()
    
    # 获取推荐配置
    hardware_config = detector.recommend_model_config()
    
    # 显示摘要信息
    logger.info(f"CPU: {hw_info['cpu']['brand']}")
    logger.info(f"内存: {hw_info['memory']['total_gb']:.2f}GB, 可用: {hw_info['memory']['available_gb']:.2f}GB")
    logger.info(f"GPU: {'可用' if hw_info['gpu']['available'] else '不可用'} " + 
                (hw_info['gpu'].get('type', '') if hw_info['gpu']['available'] else ''))
    
    # 显示指令集优化路径
    if HAS_OPTIMIZATION_ROUTER:
        try:
            router = OptimizationRouter()
            path = router.get_optimization_path()
            level = router.get_optimization_level()
            logger.info(f"指令集优化路径: {path} ({level.get('description', '')})")
            logger.info(f"SIMD宽度: {level.get('simd_width')}位, 性能评级: {level.get('performance_rating')}/100")
            
            # 导出优化配置
            export_optimization_config()
        except Exception as e:
            logger.error(f"获取优化路径失败: {str(e)}")
    
    # 如果仅更新优化配置，则在此退出
    if args.optimization_only:
        logger.info("仅更新指令集优化配置完成，退出")
        return
    
    # 更新模型配置
    logger.info("正在更新模型配置...")
    active_model = update_model_configs(hardware_config)
    
    # 创建全局模型配置
    logger.info("正在创建全局模型配置...")
    config_path = create_model_config_yaml(hardware_config)
    
    # 兼容性检查
    compatible, reason = detector.is_compatible()
    if not compatible:
        logger.warning(f"硬件兼容性检查失败: {reason}")
    else:
        logger.info("硬件兼容性检查通过")
    
    # 生成硬件报告
    report_path = os.path.join(root_dir, 'hardware_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(hw_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"当前激活模型: {active_model}")
    logger.info(f"硬件报告已保存到: {report_path}")
    logger.info("配置已完成!")

if __name__ == "__main__":
    main() 