"""模型切换器模块

此模块负责安全高效地进行模型切换，包括:
1. 模型状态管理
2. 内存资源释放
3. 新模型加载
4. 模型预热
5. 配置切换
"""

import os
import torch
import yaml
from typing import Optional, Dict, Any
from loguru import logger
from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice
from .unload_manager import UnloadManager

class ModelSwitcher:
    """模型切换器"""
    
    def __init__(self,
                 model_root: str,
                 memory_manager: Optional[MemoryManager] = None,
                 device_manager: Optional[HybridDevice] = None,
                 unload_manager: Optional[UnloadManager] = None):
        """初始化模型切换器
        
        Args:
            model_root: 模型根目录
            memory_manager: 内存管理器实例
            device_manager: 设备管理器实例
            unload_manager: 卸载管理器实例
        """
        self.model_root = model_root
        self.memory_manager = memory_manager or MemoryManager()
        self.device_manager = device_manager or HybridDevice()
        self.unload_manager = unload_manager or UnloadManager()
        
        # 当前模型信息
        self._current_model: Dict[str, Any] = {}
        self._model_configs: Dict[str, Dict] = {}
        
        # 加载模型配置
        self._load_model_configs()
    
    def switch_model(self, model_name: str) -> bool:
        """切换到指定模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否切换成功
        """
        try:
            logger.info(f"开始切换到模型: {model_name}")
            
            # 检查模型配置
            if model_name not in self._model_configs:
                logger.error(f"未找到模型配置: {model_name}")
                return False
            
            model_config = self._model_configs[model_name]
            
            # 检查内存需求
            required_memory = model_config.get('memory_required', 0)
            if not self.memory_manager.check_system_memory(required_memory):
                logger.error(f"系统内存不足，需要 {required_memory/1024/1024:.2f}MB")
                return False
            
            # 清理当前模型
            self._cleanup_current_model()
            
            # 选择最佳设备
            device = self.device_manager.select_device(
                model_config.get('device_requirements', {})
            )
            
            # 加载新模型
            success = self._load_new_model(model_name, model_config, device)
            if not success:
                return False
            
            # 模型预热
            self._warm_up()
            
            logger.info(f"模型切换完成: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"模型切换失败: {str(e)}")
            return False
    
    def get_current_model(self) -> Dict[str, Any]:
        """获取当前模型信息
        
        Returns:
            Dict: 当前模型信息
        """
        return self._current_model
    
    def _load_model_configs(self):
        """加载所有模型配置"""
        config_dir = os.path.join(self.model_root, 'configs')
        if not os.path.exists(config_dir):
            logger.warning(f"模型配置目录不存在: {config_dir}")
            return
            
        for file_name in os.listdir(config_dir):
            if not file_name.endswith('.yaml'):
                continue
                
            model_name = file_name[:-5]  # 移除.yaml后缀
            config_path = os.path.join(config_dir, file_name)
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self._model_configs[model_name] = config
                logger.info(f"已加载模型配置: {model_name}")
            except Exception as e:
                logger.error(f"加载模型配置失败 {model_name}: {str(e)}")
    
    def _cleanup_current_model(self):
        """清理当前模型"""
        if not self._current_model:
            return
            
        try:
            # 保存当前模型状态
            if 'checkpoint_path' in self._current_model:
                self.unload_manager.unload_component(self._current_model['name'])
            
            # 释放GPU内存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 触发内存整理
            self.memory_manager.cleanup()
            
            self._current_model = {}
            logger.info("已清理当前模型")
            
        except Exception as e:
            logger.error(f"清理当前模型失败: {str(e)}")
            raise
    
    def _load_new_model(self,
                       model_name: str,
                       model_config: Dict,
                       device: str) -> bool:
        """加载新模型
        
        Args:
            model_name: 模型名称
            model_config: 模型配置
            device: 目标设备
            
        Returns:
            bool: 是否加载成功
        """
        try:
            # 检查模型文件
            model_path = os.path.join(self.model_root, model_config['path'])
            if not os.path.exists(model_path):
                logger.error(f"模型文件不存在: {model_path}")
                return False
            
            # 分配内存
            required_memory = model_config.get('memory_required', 0)
            self.memory_manager.allocate_memory(required_memory)
            
            # 注册到卸载管理器
            self.unload_manager.register_component(
                name=model_name,
                component_type=model_config.get('type', 'OTHER'),
                size=required_memory,
                checkpoint_path=model_config.get('checkpoint_path')
            )
            
            # 更新当前模型信息
            self._current_model = {
                'name': model_name,
                'config': model_config,
                'device': device,
                'path': model_path
            }
            
            logger.info(f"已加载新模型: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载新模型失败: {str(e)}")
            return False
    
    def _warm_up(self):
        """模型预热"""
        if not self._current_model:
            return
            
        try:
            # 获取预热配置
            model_config = self._current_model['config']
            warm_up_steps = model_config.get('warm_up_steps', [])
            warm_up_batch_size = model_config.get('warm_up_batch_size', 1)
            warm_up_iterations = model_config.get('warm_up_iterations', 5)
            
            # 如果没有预热步骤，使用默认预热
            if not warm_up_steps:
                logger.info("使用默认预热策略")
                self._default_warm_up(warm_up_batch_size, warm_up_iterations)
                return
            
            # 执行预热步骤
            total_steps = len(warm_up_steps)
            for i, step in enumerate(warm_up_steps, 1):
                try:
                    step_type = step.get('type', 'inference')
                    step_config = step.get('config', {})
                    
                    if step_type == 'inference':
                        # 执行推理预热
                        self._inference_warm_up(step_config)
                    elif step_type == 'memory':
                        # 执行内存预热
                        self._memory_warm_up(step_config)
                    elif step_type == 'custom':
                        # 执行自定义预热
                        self._custom_warm_up(step_config)
                    
                    logger.info(f"完成预热步骤 {i}/{total_steps}")
                    
                except Exception as e:
                    logger.warning(f"预热步骤 {i} 失败: {str(e)}")
                    continue
            
            logger.info("模型预热完成")
            
        except Exception as e:
            logger.warning(f"模型预热失败: {str(e)}")
    
    def _default_warm_up(self, batch_size: int, iterations: int):
        """默认预热策略
        
        Args:
            batch_size: 批次大小
            iterations: 迭代次数
        """
        try:
            # 生成随机输入数据
            input_shape = self._current_model['config'].get('input_shape')
            if not input_shape:
                logger.warning("未找到输入形状配置，跳过默认预热")
                return
                
            device = self._current_model['device']
            dummy_input = torch.randn(batch_size, *input_shape).to(device)
            
            # 执行多次推理
            for i in range(iterations):
                with torch.no_grad():
                    # 这里应该调用模型的forward方法
                    # 由于模型实例在实际使用时才会创建，这里只是预留位置
                    pass
                
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            
            logger.info(f"完成默认预热: {iterations}次迭代")
            
        except Exception as e:
            logger.warning(f"默认预热失败: {str(e)}")
    
    def _inference_warm_up(self, config: Dict):
        """推理预热
        
        Args:
            config: 预热配置
        """
        batch_size = config.get('batch_size', 1)
        iterations = config.get('iterations', 5)
        input_shape = config.get('input_shape')
        
        if not input_shape:
            input_shape = self._current_model['config'].get('input_shape')
            if not input_shape:
                raise ValueError("未找到输入形状配置")
        
        device = self._current_model['device']
        dummy_input = torch.randn(batch_size, *input_shape).to(device)
        
        # 执行推理预热
        for _ in range(iterations):
            with torch.no_grad():
                # 这里应该调用模型的forward方法
                pass
            
            if torch.cuda.is_available():
                torch.cuda.synchronize()
    
    def _memory_warm_up(self, config: Dict):
        """内存预热
        
        Args:
            config: 预热配置
        """
        cache_size = config.get('cache_size', 1024 * 1024)  # 默认1MB
        
        # 预热内存缓存
        self.memory_manager.allocate_memory(cache_size)
        self.memory_manager.release_memory(cache_size)
        
        if torch.cuda.is_available():
            # 预热CUDA缓存
            torch.cuda.empty_cache()
            dummy_tensor = torch.zeros(cache_size, device='cuda')
            del dummy_tensor
            torch.cuda.empty_cache()
    
    def _custom_warm_up(self, config: Dict):
        """自定义预热
        
        Args:
            config: 预热配置
        """
        # 执行自定义预热步骤
        warm_up_fn = config.get('function')
        if warm_up_fn and callable(warm_up_fn):
            warm_up_fn(self._current_model)
    
    def __del__(self):
        """清理资源"""
        try:
            self._cleanup_current_model()
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")
