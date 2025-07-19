#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster GPU加速功能代码审查工具

检查项目中GPU加速实现的正确性和完整性
"""

import os
import sys
import logging
import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gpu_code_review.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class GPUCodeReviewer:
    """GPU加速功能代码审查器"""
    
    def __init__(self):
        """初始化代码审查器"""
        self.results = {
            'gpu_modules': {},
            'video_processing': {},
            'model_inference': {},
            'memory_management': {},
            'device_switching': {},
            'fallback_mechanisms': {},
            'performance_optimizations': {},
            'issues_found': [],
            'recommendations': []
        }
        
    def run_code_review(self) -> Dict[str, Any]:
        """运行GPU代码审查"""
        logger.info("🔍 开始VisionAI-ClipsMaster GPU加速功能代码审查")
        logger.info("=" * 60)
        
        try:
            # 1. 检查GPU相关模块
            self._review_gpu_modules()
            
            # 2. 检查视频处理GPU加速
            self._review_video_processing()
            
            # 3. 检查模型推理GPU支持
            self._review_model_inference()
            
            # 4. 检查GPU内存管理
            self._review_memory_management()
            
            # 5. 检查设备切换逻辑
            self._review_device_switching()
            
            # 6. 检查降级机制
            self._review_fallback_mechanisms()
            
            # 7. 检查性能优化
            self._review_performance_optimizations()
            
            # 8. 生成建议
            self._generate_recommendations()
            
            logger.info("🎉 GPU代码审查完成！")
            return self.results
            
        except Exception as e:
            logger.error(f"GPU代码审查失败: {str(e)}")
            return self.results
    
    def _review_gpu_modules(self):
        """检查GPU相关模块"""
        logger.info("1. GPU相关模块检查")
        logger.info("-" * 40)
        
        gpu_modules = {
            'gpu_detector': {'path': 'ui/hardware/gpu_detector.py', 'exists': False, 'functions': []},
            'gpu_accelerator': {'path': 'ui/performance/gpu_accelerator.py', 'exists': False, 'functions': []},
            'compute_offloader': {'path': 'ui/hardware/compute_offloader.py', 'exists': False, 'functions': []},
            'performance_tier': {'path': 'ui/hardware/performance_tier.py', 'exists': False, 'functions': []}
        }
        
        for module_name, module_info in gpu_modules.items():
            module_path = PROJECT_ROOT / module_info['path']
            if module_path.exists():
                module_info['exists'] = True
                logger.info(f"✅ {module_name}: 文件存在")
                
                # 分析模块内容
                try:
                    with open(module_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 查找GPU相关函数
                    gpu_functions = self._find_gpu_functions(content)
                    module_info['functions'] = gpu_functions
                    
                    if gpu_functions:
                        logger.info(f"  - 发现GPU相关函数: {', '.join(gpu_functions)}")
                    else:
                        logger.warning(f"  - 未发现GPU相关函数")
                        
                except Exception as e:
                    logger.error(f"  - 读取文件失败: {str(e)}")
            else:
                logger.warning(f"⚠️ {module_name}: 文件不存在 ({module_info['path']})")
        
        self.results['gpu_modules'] = gpu_modules
    
    def _find_gpu_functions(self, content: str) -> List[str]:
        """查找GPU相关函数"""
        gpu_functions = []
        
        # 使用正则表达式查找函数定义
        function_pattern = r'def\\\1+(\\\1*(?:gpu|cuda|device|accelerat|offload)\\\1*)\\\1*\\\1'
        matches = re.findall(function_pattern, content, re.IGNORECASE)
        gpu_functions.extend(matches)
        
        # 查找包含GPU关键词的函数
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                # 检查函数体是否包含GPU相关代码
                func_body = self._get_function_body(lines, i)
                if any(keyword in func_body.lower() for keyword in ['gpu', 'cuda', 'device', 'torch.cuda']):
                    if func_name not in gpu_functions:
                        gpu_functions.append(func_name)
        
        return gpu_functions
    
    def _get_function_body(self, lines: List[str], start_line: int) -> str:
        """获取函数体内容"""
        body_lines = []
        indent_level = None
        
        for i in range(start_line + 1, min(start_line + 20, len(lines))):
            line = lines[i]
            if not line.strip():
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            if indent_level is None:
                indent_level = current_indent
            elif current_indent <= indent_level and line.strip():
                break
                
            body_lines.append(line)
        
        return '\n'.join(body_lines)
    
    def _review_video_processing(self):
        """检查视频处理GPU加速"""
        logger.info("2. 视频处理GPU加速检查")
        logger.info("-" * 40)
        
        video_processing = {
            'video_processor': {'gpu_support': False, 'gpu_functions': []},
            'clip_generator': {'gpu_support': False, 'gpu_functions': []},
            'quality_controller': {'gpu_support': False, 'gpu_functions': []}
        }
        
        # 检查视频处理器
        video_processor_path = PROJECT_ROOT / 'src/core/video_processor.py'
        if video_processor_path.exists():
            try:
                with open(video_processor_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                gpu_functions = self._find_gpu_functions(content)
                video_processing['video_processor']['gpu_functions'] = gpu_functions
                
                # 检查是否有GPU加速代码
                if any(keyword in content.lower() for keyword in ['gpu', 'cuda', 'device']):
                    video_processing['video_processor']['gpu_support'] = True
                    logger.info("✅ 视频处理器: 包含GPU加速代码")
                else:
                    logger.warning("⚠️ 视频处理器: 未发现GPU加速代码")
                    
            except Exception as e:
                logger.error(f"视频处理器检查失败: {str(e)}")
        else:
            logger.warning("⚠️ 视频处理器文件不存在")
        
        # 检查剪辑生成器
        clip_generator_path = PROJECT_ROOT / 'src/core/clip_generator.py'
        if clip_generator_path.exists():
            try:
                with open(clip_generator_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                gpu_functions = self._find_gpu_functions(content)
                video_processing['clip_generator']['gpu_functions'] = gpu_functions
                
                if any(keyword in content.lower() for keyword in ['gpu', 'cuda', 'device']):
                    video_processing['clip_generator']['gpu_support'] = True
                    logger.info("✅ 剪辑生成器: 包含GPU加速代码")
                else:
                    logger.warning("⚠️ 剪辑生成器: 未发现GPU加速代码")
                    
            except Exception as e:
                logger.error(f"剪辑生成器检查失败: {str(e)}")
        else:
            logger.warning("⚠️ 剪辑生成器文件不存在")
        
        self.results['video_processing'] = video_processing
    
    def _review_model_inference(self):
        """检查模型推理GPU支持"""
        logger.info("3. 模型推理GPU支持检查")
        logger.info("-" * 40)
        
        model_inference = {
            'base_llm': {'gpu_support': False, 'device_management': False},
            'screenplay_engineer': {'gpu_support': False, 'device_management': False},
            'model_loader': {'gpu_support': False, 'device_management': False}
        }
        
        # 检查基础LLM模型
        base_llm_path = PROJECT_ROOT / 'src/models/base_llm.py'
        if base_llm_path.exists():
            try:
                with open(base_llm_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查GPU支持
                if any(keyword in content.lower() for keyword in ['gpu', 'cuda', 'device', 'torch.cuda']):
                    model_inference['base_llm']['gpu_support'] = True
                    logger.info("✅ 基础LLM: 包含GPU支持代码")
                else:
                    logger.warning("⚠️ 基础LLM: 未发现GPU支持代码")
                
                # 检查设备管理
                if 'device' in content.lower() and ('to(' in content or '.cuda()' in content):
                    model_inference['base_llm']['device_management'] = True
                    logger.info("✅ 基础LLM: 包含设备管理代码")
                else:
                    logger.warning("⚠️ 基础LLM: 未发现设备管理代码")
                    
            except Exception as e:
                logger.error(f"基础LLM检查失败: {str(e)}")
        else:
            logger.warning("⚠️ 基础LLM文件不存在")
        
        self.results['model_inference'] = model_inference
    
    def _review_memory_management(self):
        """检查GPU内存管理"""
        logger.info("4. GPU内存管理检查")
        logger.info("-" * 40)
        
        memory_management = {
            'memory_guard': {'gpu_memory_tracking': False, 'gpu_cleanup': False},
            'memory_optimizer': {'gpu_optimization': False, 'memory_pooling': False}
        }
        
        # 检查内存守护
        memory_guard_path = PROJECT_ROOT / 'ui/performance/memory_guard.py'
        if memory_guard_path.exists():
            try:
                with open(memory_guard_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'gpu' in content.lower() or 'cuda' in content.lower():
                    memory_management['memory_guard']['gpu_memory_tracking'] = True
                    logger.info("✅ 内存守护: 包含GPU内存跟踪")
                else:
                    logger.warning("⚠️ 内存守护: 未发现GPU内存跟踪")
                    
            except Exception as e:
                logger.error(f"内存守护检查失败: {str(e)}")
        else:
            logger.warning("⚠️ 内存守护文件不存在")
        
        self.results['memory_management'] = memory_management

    def _review_device_switching(self):
        """检查设备切换逻辑"""
        logger.info("5. 设备切换逻辑检查")
        logger.info("-" * 40)

        device_switching = {
            'automatic_detection': False,
            'manual_switching': False,
            'device_validation': False,
            'error_handling': False
        }

        # 检查计算卸载器中的设备切换
        compute_offloader_path = PROJECT_ROOT / 'ui/hardware/compute_offloader.py'
        if compute_offloader_path.exists():
            try:
                with open(compute_offloader_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'device' in content.lower() and 'switch' in content.lower():
                    device_switching['automatic_detection'] = True
                    logger.info("✅ 设备切换: 包含自动检测逻辑")

                if 'set_device' in content or 'switch_device' in content:
                    device_switching['manual_switching'] = True
                    logger.info("✅ 设备切换: 包含手动切换功能")

                if 'validate' in content.lower() and 'device' in content.lower():
                    device_switching['device_validation'] = True
                    logger.info("✅ 设备切换: 包含设备验证")

                if 'try:' in content and 'except' in content:
                    device_switching['error_handling'] = True
                    logger.info("✅ 设备切换: 包含错误处理")

            except Exception as e:
                logger.error(f"设备切换检查失败: {str(e)}")
        else:
            logger.warning("⚠️ 计算卸载器文件不存在")

        self.results['device_switching'] = device_switching

    def _review_fallback_mechanisms(self):
        """检查降级机制"""
        logger.info("6. 降级机制检查")
        logger.info("-" * 40)

        fallback_mechanisms = {
            'gpu_to_cpu_fallback': False,
            'graceful_degradation': False,
            'performance_monitoring': False,
            'user_notification': False
        }

        # 搜索所有Python文件中的降级机制
        python_files = list(PROJECT_ROOT.rglob('*.py'))
        fallback_patterns = [
            r'if.*cuda.*available.*else',
            r'try.*gpu.*except.*cpu',
            r'fallback.*cpu',
            r'device.*cpu.*default'
        ]

        fallback_found = False
        for py_file in python_files[:20]:  # 限制检查文件数量
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in fallback_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        fallback_found = True
                        fallback_mechanisms['gpu_to_cpu_fallback'] = True
                        logger.info(f"✅ 降级机制: 在 {py_file.name} 中发现GPU到CPU降级")
                        break

                if fallback_found:
                    break

            except Exception:
                continue

        if not fallback_found:
            logger.warning("⚠️ 降级机制: 未发现GPU到CPU降级逻辑")

        self.results['fallback_mechanisms'] = fallback_mechanisms

    def _review_performance_optimizations(self):
        """检查性能优化"""
        logger.info("7. 性能优化检查")
        logger.info("-" * 40)

        performance_optimizations = {
            'batch_processing': False,
            'memory_pooling': False,
            'async_operations': False,
            'kernel_optimization': False
        }

        # 检查性能优化相关文件
        perf_files = [
            'ui/performance/gpu_accelerator.py',
            'ui/hardware/compute_offloader.py',
            'src/core/video_processor.py'
        ]

        for file_path in perf_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if 'batch' in content.lower():
                        performance_optimizations['batch_processing'] = True
                        logger.info(f"✅ 性能优化: {file_path} 包含批处理优化")

                    if 'pool' in content.lower() and 'memory' in content.lower():
                        performance_optimizations['memory_pooling'] = True
                        logger.info(f"✅ 性能优化: {file_path} 包含内存池优化")

                    if 'async' in content.lower() or 'await' in content:
                        performance_optimizations['async_operations'] = True
                        logger.info(f"✅ 性能优化: {file_path} 包含异步操作")

                except Exception as e:
                    logger.error(f"性能优化检查失败 {file_path}: {str(e)}")

        self.results['performance_optimizations'] = performance_optimizations

    def _generate_recommendations(self):
        """生成代码改进建议"""
        logger.info("8. 生成代码改进建议")
        logger.info("-" * 40)

        recommendations = []

        # 基于GPU模块检查结果的建议
        gpu_modules = self.results['gpu_modules']
        missing_modules = [name for name, info in gpu_modules.items() if not info['exists']]

        if missing_modules:
            recommendations.append({
                'type': 'missing_modules',
                'priority': 'high',
                'title': '缺失GPU模块',
                'description': f'以下GPU模块文件不存在: {", ".join(missing_modules)}',
                'action': '创建缺失的GPU模块文件并实现相应功能'
            })

        # 基于视频处理检查结果的建议
        video_processing = self.results['video_processing']
        if not video_processing['video_processor']['gpu_support']:
            recommendations.append({
                'type': 'video_processing',
                'priority': 'high',
                'title': '视频处理器缺少GPU加速',
                'description': '视频处理器未实现GPU加速功能',
                'action': '在视频处理器中添加GPU加速代码，使用CUDA或OpenCL'
            })

        # 基于模型推理检查结果的建议
        model_inference = self.results['model_inference']
        if not model_inference['base_llm']['gpu_support']:
            recommendations.append({
                'type': 'model_inference',
                'priority': 'high',
                'title': '模型推理缺少GPU支持',
                'description': '基础LLM模型未实现GPU推理',
                'action': '在模型推理中添加GPU设备管理和CUDA支持'
            })

        # 基于降级机制检查结果的建议
        fallback = self.results['fallback_mechanisms']
        if not fallback['gpu_to_cpu_fallback']:
            recommendations.append({
                'type': 'fallback',
                'priority': 'medium',
                'title': '缺少GPU降级机制',
                'description': '未发现GPU不可用时的CPU降级逻辑',
                'action': '实现GPU到CPU的自动降级机制，确保系统稳定性'
            })

        # 基于性能优化检查结果的建议
        perf_opt = self.results['performance_optimizations']
        if not perf_opt['batch_processing']:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'title': '缺少批处理优化',
                'description': '未发现批处理优化代码',
                'action': '实现批处理机制以提高GPU利用率'
            })

        self.results['recommendations'] = recommendations

        logger.info("生成的代码改进建议:")
        for rec in recommendations:
            logger.info(f"  [{rec['priority'].upper()}] {rec['title']}: {rec['description']}")


if __name__ == "__main__":
    reviewer = GPUCodeReviewer()
    results = reviewer.run_code_review()

    print("\n" + "=" * 60)
    print("GPU代码审查完成！详细结果请查看 gpu_code_review.log")
    print("=" * 60)
