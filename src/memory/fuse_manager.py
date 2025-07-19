#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存熔断管理器 - VisionAI-ClipsMaster
多级熔断阈值管理和动作执行
"""

import os
import sys
import time
import gc
import threading
import logging
import tempfile
import shutil
import yaml
import psutil
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple, Set, Union
from pathlib import Path

# 设置日志
logger = logging.getLogger("memory_fuse")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class FuseLevel(Enum):
    """熔断级别枚举"""
    NORMAL = 0      # 正常状态
    WARNING = 1     # 警告状态
    CRITICAL = 2    # 临界状态
    EMERGENCY = 3   # 紧急状态


class MemoryFuseManager:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存熔断管理器，实现多级熔断阈值管理与动作执行"""
    
    def __init__(self, config_path: str = "configs/memory_fuse.yaml"):
        """
        初始化内存熔断管理器
        
        Args:
            config_path: 熔断配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化状态
        self.current_level = FuseLevel.NORMAL
        self.last_trigger_time: Dict[FuseLevel, float] = {
            level: 0.0 for level in FuseLevel
        }
        self.triggered_actions: Dict[FuseLevel, Set[str]] = {
            level: set() for level in FuseLevel
        }
        self.original_settings: Dict[str, Any] = {}
        
        # 监控线程
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        
        # 执行动作的处理函数字典
        self.action_handlers: Dict[str, Callable] = {
            "clear_temp_files": self._clear_temp_files,
            "reduce_log_verbosity": self._reduce_log_verbosity,
            "pause_background_tasks": self._pause_background_tasks,
            "reduce_cache_size": self._reduce_cache_size,
            "unload_noncritical_shards": self._unload_noncritical_shards,
            "degrade_quality": self._degrade_quality,
            "flush_memory_cache": self._flush_memory_cache,
            "switch_to_lightweight_models": self._switch_to_lightweight_models,
            "kill_largest_process": self._kill_largest_process,
            "force_gc": self._force_gc,
            "disable_features": self._disable_features,
            "activate_survival_mode": self._activate_survival_mode
        }
        
        # 自定义动作钩子
        self.custom_actions: Dict[str, Callable] = {}
        
        # 动作执行历史
        self.action_history: List[Dict[str, Any]] = []
        
        # 线程锁
        self._lock = threading.RLock()
        
        logger.info("内存熔断管理器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载熔断配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            加载的配置
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"已加载熔断配置: {config_path}")
                return config
        except Exception as e:
            logger.error(f"加载熔断配置失败: {str(e)}，使用默认配置")
            # 默认配置
            return {
                "fuse_levels": [
                    {
                        "level": "WARNING",
                        "threshold": 85,
                        "actions": ["clear_temp_files", "reduce_log_verbosity"]
                    },
                    {
                        "level": "CRITICAL",
                        "threshold": 95,
                        "actions": ["unload_noncritical_shards", "degrade_quality"]
                    },
                    {
                        "level": "EMERGENCY",
                        "threshold": 98,
                        "actions": ["kill_largest_process", "force_gc"]
                    }
                ],
                "detection": {
                    "check_interval_seconds": 5.0,
                    "stabilize_seconds": 30.0,
                    "recovery_threshold": 70
                }
            }
    
    def start_monitoring(self) -> bool:
        """
        启动内存监控线程
        
        Returns:
            是否成功启动
        """
        with self._lock:
            try:
                if self._monitor_thread is None or not self._monitor_thread.is_alive():
                    self._stop_monitor.clear()
                    check_interval = self.config["detection"].get("check_interval_seconds", 5.0)
                    self._monitor_thread = threading.Thread(
                        target=self._monitor_memory,
                        args=(check_interval,),
                        daemon=True
                    )
                    self._monitor_thread.start()
                    logger.info("内存熔断监控已启动")
                    return True
                return False
            except Exception as e:
                logger.error(f"启动内存熔断监控失败: {str(e)}")
                return False
    
    def stop_monitoring(self) -> bool:
        """
        停止内存监控线程
        
        Returns:
            是否成功停止
        """
        with self._lock:
            try:
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._stop_monitor.set()
                    self._monitor_thread.join(timeout=5.0)
                    logger.info("内存熔断监控已停止")
                    return True
                return False
            except Exception as e:
                logger.error(f"停止内存熔断监控失败: {str(e)}")
                return False
    
    def _monitor_memory(self, check_interval: float) -> None:
        """
        内存监控线程函数
        
        Args:
            check_interval: 检查间隔（秒）
        """
        logger.info(f"内存监控线程启动，检查间隔: {check_interval}秒")
        
        while not self._stop_monitor.is_set():
            try:
                # 获取当前内存使用情况
                memory_percent = psutil.virtual_memory().percent
                
                # 检查是否需要触发熔断
                self._check_and_trigger_fuse(memory_percent)
                
                # 检查是否可以恢复
                if self.current_level != FuseLevel.NORMAL:
                    self._check_recovery(memory_percent)
                
                # 等待下一次检查
                self._stop_monitor.wait(check_interval)
            except Exception as e:
                logger.error(f"内存监控异常: {str(e)}")
                # 短暂等待后继续
                time.sleep(1.0)
    
    def _check_and_trigger_fuse(self, memory_percent: float) -> None:
        """
        检查并触发熔断
        
        Args:
            memory_percent: 内存使用百分比
        """
        with self._lock:
            # 获取稳定时间
            stabilize_secs = self.config["detection"].get("stabilize_seconds", 30.0)
            current_time = time.time()
            
            # 从高到低检查各级阈值
            fuse_levels = self.config["fuse_levels"]
            triggered_level = None
            
            for level_config in reversed(fuse_levels):
                level_name = level_config["level"]
                threshold = level_config["threshold"]
                
                if memory_percent >= threshold:
                    level = getattr(FuseLevel, level_name)
                    
                    # 检查是否在稳定期内
                    last_trigger = self.last_trigger_time[level]
                    if current_time - last_trigger >= stabilize_secs:
                        triggered_level = level
                        break
            
            # 如果需要触发熔断且级别高于当前级别
            if triggered_level is not None and triggered_level.value > self.current_level.value:
                self._trigger_fuse(triggered_level, memory_percent)
    
    def _trigger_fuse(self, level: FuseLevel, memory_percent: float) -> None:
        """
        触发熔断
        
        Args:
            level: 熔断级别
            memory_percent: 内存使用百分比
        """
        logger.warning(f"触发{level.name}级别熔断，当前内存使用率: {memory_percent:.1f}%")
        
        # 更新状态
        self.current_level = level
        self.last_trigger_time[level] = time.time()
        
        # 获取对应级别的动作
        actions = []
        for level_config in self.config["fuse_levels"]:
            if level_config["level"] == level.name:
                actions = level_config["actions"]
                break
        
        # 执行动作
        for action in actions:
            if action not in self.triggered_actions[level]:
                self._execute_action(action, level)
                self.triggered_actions[level].add(action)
    
    def _check_recovery(self, memory_percent: float) -> None:
        """
        检查是否可以恢复
        
        Args:
            memory_percent: 内存使用百分比
        """
        recovery_threshold = self.config["detection"].get("recovery_threshold", 70)
        
        if memory_percent <= recovery_threshold:
            # 获取恢复延迟
            recovery_delay = self.config["recovery"].get("recovery_delay", 60)
            current_time = time.time()
            
            # 检查最后一次触发时间是否已超过恢复延迟
            last_trigger = max(self.last_trigger_time.values())
            if current_time - last_trigger >= recovery_delay:
                self._recover_from_fuse()
    
    def _recover_from_fuse(self) -> None:
        """从熔断中恢复"""
        with self._lock:
            if self.current_level == FuseLevel.NORMAL:
                return
            
            old_level = self.current_level
            logger.info(f"从{old_level.name}级别熔断恢复")
            
            # 逐步恢复
            if self.config["recovery"].get("step_recovery", True):
                # 阶梯式恢复，降低一级
                if self.current_level.value > FuseLevel.NORMAL.value:
                    self.current_level = FuseLevel(self.current_level.value - 1)
            else:
                # 直接恢复到正常状态
                self.current_level = FuseLevel.NORMAL
            
            # 恢复设置
            if self.config["recovery"].get("restore_settings", True):
                self._restore_original_settings()
            
            # 重置触发动作记录
            if self.current_level == FuseLevel.NORMAL:
                for level in FuseLevel:
                    self.triggered_actions[level] = set()
            
            # 记录恢复动作
            self._record_action("recover", old_level, self.current_level, success=True)
    
    def _execute_action(self, action: str, level: FuseLevel) -> bool:
        """
        执行熔断动作
        
        Args:
            action: 动作名称
            level: 熔断级别
            
        Returns:
            执行是否成功
        """
        logger.info(f"执行{level.name}级别熔断动作: {action}")
        
        try:
            # 检查是否有自定义处理函数
            if action in self.custom_actions:
                success = self.custom_actions[action](level)
            # 检查是否有内置处理函数
            elif action in self.action_handlers:
                success = self.action_handlers[action](level)
            else:
                logger.warning(f"未知的熔断动作: {action}")
                success = False
            
            # 记录动作执行
            self._record_action(action, level, FuseLevel.NORMAL, success)
            
            return success
        except Exception as e:
            logger.error(f"执行熔断动作[{action}]失败: {str(e)}")
            self._record_action(action, level, FuseLevel.NORMAL, False, str(e))
            return False
    
    def _record_action(
        self, 
        action: str, 
        level: FuseLevel, 
        target_level: FuseLevel, 
        success: bool, 
        error: Optional[str] = None
    ) -> None:
        """
        记录动作执行历史
        
        Args:
            action: 动作名称
            level: 熔断级别
            target_level: 目标级别(恢复用)
            success: 是否成功
            error: 错误信息
        """
        action_record = {
            "action": action,
            "level": level.name,
            "target_level": target_level.name if target_level != level else None,
            "timestamp": time.time(),
            "success": success
        }
        
        if error:
            action_record["error"] = error
        
        self.action_history.append(action_record)
        
        # 限制历史记录长度
        max_history = 100
        if len(self.action_history) > max_history:
            self.action_history = self.action_history[-max_history:]
    
    def register_custom_action(self, action: str, handler: Callable) -> 'MemoryFuseManager':
        """
        注册自定义熔断动作处理函数
        
        Args:
            action: 动作名称
            handler: 处理函数，接收一个FuseLevel参数，返回bool表示成功与否
            
        Returns:
            MemoryFuseManager实例，支持链式调用
        """
        self.custom_actions[action] = handler
        logger.info(f"已注册自定义熔断动作: {action}")
        return self
    
    def unregister_custom_action(self, action: str) -> bool:
        """
        注销自定义熔断动作处理函数
        
        Args:
            action: 动作名称
            
        Returns:
            是否成功注销
        """
        if action in self.custom_actions:
            del self.custom_actions[action]
            logger.info(f"已注销自定义熔断动作: {action}")
            return True
        return False
    
    def get_current_level(self) -> FuseLevel:
        """
        获取当前熔断级别
        
        Returns:
            当前熔断级别
        """
        return self.current_level
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """
        获取动作执行历史
        
        Returns:
            动作执行历史记录
        """
        return self.action_history
    
    def force_trigger(self, level: Union[FuseLevel, str], test_mode: bool = False) -> bool:
        """
        强制触发熔断，用于测试或紧急情况
        
        Args:
            level: 熔断级别或级别名称
            test_mode: 测试模式，不实际执行动作
            
        Returns:
            是否成功触发
        """
        with self._lock:
            # 如果传入的是字符串，转换为枚举
            if isinstance(level, str):
                try:
                    level = getattr(FuseLevel, level.upper())
                except AttributeError:
                    logger.error(f"无效的熔断级别名称: {level}")
                    return False
            
            logger.warning(f"强制触发{level.name}级别熔断{'(测试模式)' if test_mode else ''}")
            
            if not test_mode:
                self._trigger_fuse(level, 100.0)  # 使用100%作为内存使用率
                return True
            else:
                # 测试模式只记录不执行
                self._record_action("force_trigger_test", level, level, True)
                return True
    
    def _save_original_setting(self, key: str, value: Any) -> None:
        """
        保存原始设置
        
        Args:
            key: 设置键
            value: 设置值
        """
        if key not in self.original_settings:
            self.original_settings[key] = value
    
    def _restore_original_settings(self) -> None:
        """恢复原始设置"""
        for key, value in self.original_settings.items():
            logger.debug(f"恢复原始设置: {key}")
            
            # 针对不同设置类型的特殊处理
            if key == "log_level":
                logging.getLogger().setLevel(value)
            
            # 其他设置可以根据需要添加
        
        # 清空已保存的设置
        self.original_settings = {}
    
    # 以下是各种熔断动作的实现
    
    def _clear_temp_files(self, level: FuseLevel) -> bool:
        """
        清理临时文件
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            action_params = self.config.get("action_params", {}).get("clear_temp_files", {})
            
            # 获取要清理的目录
            directories = action_params.get("directories", [])
            # 替换环境变量
            directories = [os.path.expandvars(d) for d in directories]
            
            # 如果没有指定目录，使用系统临时目录
            if not directories:
                temp_dir = tempfile.gettempdir()
                directories = [os.path.join(temp_dir, "visionai_clips_temp")]
            
            # 获取文件模式和最大文件保留时间
            file_patterns = action_params.get("file_patterns", ["*.tmp", "*.temp", "*.bak"])
            max_file_age_hours = action_params.get("max_file_age_hours", 2)
            max_file_age_secs = max_file_age_hours * 3600
            
            # 当前时间
            current_time = time.time()
            
            # 清理计数
            deleted_count = 0
            deleted_size = 0
            
            # 处理每个目录
            for directory in directories:
                if not os.path.exists(directory):
                    continue
                
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # 检查文件模式是否匹配
                        if not any(Path(file_path).match(pattern) for pattern in file_patterns):
                            continue
                        
                        # 检查文件年龄
                        try:
                            file_stat = os.stat(file_path)
                            file_age = current_time - file_stat.st_mtime
                            
                            if file_age >= max_file_age_secs:
                                # 记录文件大小
                                file_size = file_stat.st_size
                                
                                # 删除文件
                                os.remove(file_path)
                                deleted_count += 1
                                deleted_size += file_size
                        except (FileNotFoundError, PermissionError):
                            # 忽略文件不存在或权限错误
                            pass
            
            logger.info(f"已清理{deleted_count}个临时文件，释放{deleted_size/1024/1024:.2f}MB空间")
            return True
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            return False
    
    def _reduce_log_verbosity(self, level: FuseLevel) -> bool:
        """
        减少日志详细程度
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            action_params = self.config.get("action_params", {}).get("reduce_log_verbosity", {})
            
            # 获取目标日志级别
            target_level_name = action_params.get("target_level", "WARNING")
            target_level = getattr(logging, target_level_name)
            
            # 保存原始日志级别
            root_logger = logging.getLogger()
            self._save_original_setting("log_level", root_logger.level)
            
            # 设置新的日志级别
            root_logger.setLevel(target_level)
            
            logger.info(f"已降低日志详细程度至: {target_level_name}")
            return True
        except Exception as e:
            logger.error(f"降低日志详细程度失败: {str(e)}")
            return False
    
    def _pause_background_tasks(self, level: FuseLevel) -> bool:
        """
        暂停后台任务
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        # 实际实现中需要与任务管理器集成
        logger.info("暂停后台任务功能已触发")
        return True
    
    def _reduce_cache_size(self, level: FuseLevel) -> bool:
        """
        减少缓存大小
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        # 实际实现中需要与缓存管理器集成
        logger.info("减少缓存大小功能已触发")
        return True
    
    def _unload_noncritical_shards(self, level: FuseLevel) -> bool:
        """
        卸载非关键分片
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            action_params = self.config.get("action_params", {}).get("unload_noncritical_shards", {})
            
            # 获取可卸载的非关键分片
            shards = action_params.get("shards", [])
            
            logger.info(f"卸载非关键分片: {', '.join(shards)}")
            
            # 实际实现中需要与分片管理器集成
            # TODO: 与分片管理器集成
            
            return True
        except Exception as e:
            logger.error(f"卸载非关键分片失败: {str(e)}")
            return False
    
    def _degrade_quality(self, level: FuseLevel) -> bool:
        """
        降低质量设置
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            action_params = self.config.get("action_params", {}).get("degrade_quality", {})
            
            # 获取质量设置
            render_quality = action_params.get("render_quality", "medium")
            preview_resolution = action_params.get("preview_resolution", "720p")
            playback_quality = action_params.get("playback_quality", "low")
            
            logger.info(f"降低质量设置: 渲染质量={render_quality}, 预览分辨率={preview_resolution}, 播放质量={playback_quality}")
            
            # 实际实现中需要与质量管理器集成
            # TODO: 与质量管理器集成
            
            return True
        except Exception as e:
            logger.error(f"降低质量设置失败: {str(e)}")
            return False
    
    def _flush_memory_cache(self, level: FuseLevel) -> bool:
        """
        清空内存缓存
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        # 实际实现中需要与缓存管理器集成
        logger.info("清空内存缓存功能已触发")
        return True
    
    def _switch_to_lightweight_models(self, level: FuseLevel) -> bool:
        """
        切换到轻量级模型
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        # 实际实现中需要与模型管理器集成
        logger.info("切换到轻量级模型功能已触发")
        return True
    
    def _kill_largest_process(self, level: FuseLevel) -> bool:
        """
        杀死最大进程
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            if level != FuseLevel.EMERGENCY:
                logger.warning("仅紧急级别能杀死最大进程")
                return False
                
            action_params = self.config.get("action_params", {}).get("kill_largest_process", {})
            
            # 获取排除进程
            exclude_processes = action_params.get("exclude_processes", ["visionai_core", "system"])
            max_memory_percent = action_params.get("max_memory_percent", 20)
            warn_before_kill = action_params.get("warn_before_kill", True)
            
            # 获取所有进程的内存使用情况
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    # 排除排除列表中的进程
                    if any(exclude in proc.info['name'].lower() for exclude in exclude_processes):
                        continue
                        
                    # 排除自身
                    if proc.info['pid'] == os.getpid():
                        continue
                        
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 按内存使用率排序
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            if not processes:
                logger.info("未找到可杀死的进程")
                return False
            
            # 检查最大内存使用进程是否超过阈值
            largest_process = processes[0]
            if largest_process.get('memory_percent', 0) < max_memory_percent:
                logger.info(f"最大进程内存使用率({largest_process.get('memory_percent', 0):.1f}%)未超过阈值({max_memory_percent}%)，不执行杀死操作")
                return False
            
            # 发出警告
            if warn_before_kill:
                logger.warning(f"准备杀死最大内存进程: PID={largest_process['pid']}, 名称={largest_process['name']}, 内存占用={largest_process.get('memory_percent', 0):.1f}%")
                time.sleep(1.0)  # 给一点时间记录日志
            
            # 杀死进程
            try:
                process = psutil.Process(largest_process['pid'])
                process.terminate()
                
                # 等待进程终止
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # 如果等待超时，强制结束
                    process.kill()
                
                logger.info(f"已杀死最大内存进程: PID={largest_process['pid']}, 名称={largest_process['name']}")
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                logger.error(f"杀死进程失败: PID={largest_process['pid']}")
                return False
            
        except Exception as e:
            logger.error(f"杀死最大进程失败: {str(e)}")
            return False
    
    def _force_gc(self, level: FuseLevel) -> bool:
        """
        强制垃圾回收
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        try:
            action_params = self.config.get("action_params", {}).get("force_gc", {})
            
            # 获取GC参数
            aggressive = action_params.get("aggressive", True)
            clear_module_caches = action_params.get("clear_module_caches", True)
            run_times = action_params.get("run_times", 3)
            
            # 清除模块缓存
            if clear_module_caches:
                # 清理一些常见的模块缓存
                for module_name in list(sys.modules.keys()):
                    module = sys.modules[module_name]
                    if hasattr(module, '_CACHE') and isinstance(getattr(module, '_CACHE'), dict):
                        getattr(module, '_CACHE').clear()
                    if hasattr(module, '_cache') and isinstance(getattr(module, '_cache'), dict):
                        getattr(module, '_cache').clear()
            
            # 获取GC前的内存使用
            before = psutil.Process().memory_info().rss
            
            # 运行垃圾回收
            for _ in range(run_times):
                # 禁用垃圾回收，手动运行
                gc.disable()
                if aggressive:
                    # 强制回收所有对象
                    gc.collect(0)  # 回收第0代（最年轻的对象）
                    gc.collect(1)  # 回收第1代
                    gc.collect(2)  # 回收第2代（最老的对象）
                else:
                    # 普通回收
                    gc.collect()
                gc.enable()
            
            # 获取GC后的内存使用
            after = psutil.Process().memory_info().rss
            
            # 计算节省的内存
            saved = before - after
            
            logger.info(f"强制垃圾回收完成，{'(激进模式)' if aggressive else ''}运行{run_times}次，释放{saved/1024/1024:.2f}MB内存")
            return True
        except Exception as e:
            logger.error(f"强制垃圾回收失败: {str(e)}")
            return False
    
    def _disable_features(self, level: FuseLevel) -> bool:
        """
        禁用非必要特性
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        # 实际实现中需要与特性管理器集成
        logger.info("禁用非必要特性功能已触发")
        return True
    
    def _activate_survival_mode(self, level: FuseLevel) -> bool:
        """
        激活生存模式
        
        Args:
            level: 熔断级别
            
        Returns:
            是否成功
        """
        if level != FuseLevel.EMERGENCY:
            logger.warning("仅紧急级别能激活生存模式")
            return False
            
        # 实际实现中需要综合多种降级措施
        logger.warning("激活生存模式!")
        
        # 执行一系列紧急措施
        self._force_gc(level)
        self._flush_memory_cache(level)
        self._disable_features(level)
        
        return True


# 全局单例
_fuse_manager = None

def get_fuse_manager() -> MemoryFuseManager:
    """
    获取熔断管理器单例
    
    Returns:
        熔断管理器实例
    """
    global _fuse_manager
    
    if _fuse_manager is None:
        _fuse_manager = MemoryFuseManager()
        
    return _fuse_manager


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试熔断管理器
    manager = get_fuse_manager()
    
    # 启动监控
    manager.start_monitoring()
    
    # 测试强制触发熔断
    manager.force_trigger("WARNING", test_mode=True)
    time.sleep(1)
    manager.force_trigger("CRITICAL", test_mode=True)
    time.sleep(1)
    manager.force_trigger("EMERGENCY", test_mode=True)
    
    # 等待一段时间
    time.sleep(10)
    
    # 查看动作历史
    history = manager.get_action_history()
    print("熔断动作历史:")
    for action in history:
        print(f"  {action['timestamp']:.1f}: {action['action']} (级别: {action['level']}, 成功: {action['success']})")
    
    # 停止监控
    manager.stop_monitoring() 