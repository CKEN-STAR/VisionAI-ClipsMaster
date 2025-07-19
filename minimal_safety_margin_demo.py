#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全余量管理功能最小化演示脚本
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("safety_margin_demo")

# 导入安全余量管理器类
class MarginKeeper:
    """安全余量管理器
    
    为视频剪辑保留安全余量，确保在需要进行调整时有可用的压缩空间。
    """
    
    def __init__(self, margin_ratio: float = 0.05, config: Optional[Dict[str, Any]] = None):
        """初始化安全余量管理器
        
        Args:
            margin_ratio: 安全余量比例，默认为5%
            config: 额外配置参数
        """
        self.margin = margin_ratio  # 默认保留5%余量
        self.config = config or self._default_config()
        logger.info(f"安全余量管理器初始化完成，余量比例: {self.margin:.1%}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "auto_adjust": True,           # 自动调整时长
            "min_margin": 0.02,            # 最小安全余量（2%）
            "max_margin": 0.15,            # 最大安全余量（15%）
            "critical_threshold": 0.95,    # 触发压缩的临界阈值（当前时长/目标时长 > 95%）
            "preserve_keyframes": True,    # 在调整时尽量保留关键帧
            "duration_key": "duration",    # 场景持续时间键名
            "time_unit": "seconds"         # 时间单位：seconds（秒）或 ms（毫秒）
        }
    
    def apply_margin(self, target_duration: float) -> float:
        """应用安全余量到目标时长
        
        Args:
            target_duration: 目标时长
            
        Returns:
            应用安全余量后的实际可用时长
        """
        if target_duration <= 0:
            logger.warning("目标时长必须大于零")
            return 0
            
        # 应用安全余量
        adjusted_duration = target_duration * (1 - self.margin)
        logger.debug(f"目标时长: {target_duration:.2f}，应用{self.margin:.1%}安全余量后: {adjusted_duration:.2f}")
        
        return adjusted_duration
    
    def check_duration_safety(self, current_duration: float, target_duration: float) -> Dict[str, Any]:
        """检查当前时长是否超过安全阈值
        
        Args:
            current_duration: 当前总时长
            target_duration: 目标时长上限
            
        Returns:
            安全状态信息
        """
        if target_duration <= 0:
            return {
                "safe": False,
                "ratio": float('inf'),
                "margin_left": 0,
                "needs_compression": True,
                "compression_ratio": 0.5  # 默认压缩一半
            }
            
        # 计算当前时长与目标时长的比率
        ratio = current_duration / target_duration
        margin_left = target_duration - current_duration
        critical_threshold = self.config["critical_threshold"]
        
        # 确定安全状态
        is_safe = ratio <= critical_threshold
        needs_compression = ratio > critical_threshold
        
        # 如果需要压缩，计算建议的压缩比例
        compression_ratio = 1.0
        safe_target = None
        if needs_compression:
            # 计算需要达到的目标时长
            safe_target = target_duration * critical_threshold
            # 计算压缩比例
            compression_ratio = safe_target / current_duration
            
        return {
            "safe": is_safe,
            "ratio": ratio,
            "margin_left": margin_left,
            "needs_compression": needs_compression,
            "compression_ratio": compression_ratio,
            "safe_target": safe_target
        }

    def _is_scene_compressible(self, scene: Dict[str, Any]) -> bool:
        """检查场景是否可压缩
        
        Args:
            scene: 场景数据
            
        Returns:
            是否可压缩
        """
        # 检查是否有压缩限制标记
        compression_info = scene.get("_compression_info", {})
        if compression_info:
            # 检查是否禁止压缩
            if compression_info.get("no_compress", False):
                return False
                
            # 检查压缩限制级别
            restriction_level = compression_info.get("restriction_level", "NONE")
            if restriction_level in ("HIGH", "CRITICAL"):
                return False
            
        # 检查是否有保护信息
        protection_info = scene.get("_protection_info", {})
        if protection_info:
            # 检查保护级别
            protection_level = protection_info.get("level", "NONE")
            if protection_level in ("HIGH", "CRITICAL"):
                return False
                
            # 检查保护策略
            strategies = protection_info.get("strategies", [])
            if "NO_COMPRESS" in strategies or "LOCK" in strategies:
                return False
                
        return True
        
    def adjust_scene_durations(self, scenes: List[Dict[str, Any]], target_duration: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """根据安全余量调整场景时长
        
        当总时长超过安全阈值时，自动调整场景时长
        
        Args:
            scenes: 场景列表
            target_duration: 目标总时长
            
        Returns:
            调整后的场景列表和调整信息
        """
        if not scenes:
            return scenes, {"adjusted": False, "reason": "无场景可调整"}
            
        # 获取配置
        duration_key = self.config["duration_key"]
        auto_adjust = self.config["auto_adjust"]
        
        # 计算当前总时长
        current_total = sum(scene.get(duration_key, 0) for scene in scenes)
        
        # 检查安全状态
        safety_info = self.check_duration_safety(current_total, target_duration)
        
        # 如果在安全范围内或不需要自动调整，直接返回
        if safety_info["safe"] or not auto_adjust:
            return scenes, {
                "adjusted": False,
                "safety_info": safety_info,
                "reason": "在安全范围内" if safety_info["safe"] else "未启用自动调整"
            }
            
        # 需要调整，复制场景列表以避免修改原始数据
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 根据可压缩性对场景进行分类
        compressible_scenes = []
        protected_scenes = []
        
        for scene in adjusted_scenes:
            if self._is_scene_compressible(scene):
                compressible_scenes.append(scene)
            else:
                protected_scenes.append(scene)
                
        # 如果没有可压缩的场景，返回原场景列表
        if not compressible_scenes:
            return scenes, {
                "adjusted": False,
                "safety_info": safety_info,
                "reason": "没有可压缩的场景"
            }
            
        # 计算可压缩场景的总时长
        compressible_total = sum(scene.get(duration_key, 0) for scene in compressible_scenes)
        
        # 计算需要从可压缩场景中减少的总时长
        protected_total = sum(scene.get(duration_key, 0) for scene in protected_scenes)
        safe_target = safety_info.get("safe_target", target_duration * self.config["critical_threshold"])
        reduction_needed = current_total - safe_target
        
        # 如果需要减少的时长大于可压缩场景总时长的80%，发出警告
        if reduction_needed > compressible_total * 0.8:
            logger.warning(f"需要减少的时长({reduction_needed:.2f})接近可压缩场景总时长({compressible_total:.2f})的80%")
            
        # 计算压缩比例 - 仅应用于可压缩场景
        adjusted_compression_ratio = max(0.2, 1 - (reduction_needed / compressible_total))
        
        # 应用压缩比例到可压缩场景
        for scene in compressible_scenes:
            original_duration = scene.get(duration_key, 0)
            scene[duration_key] = original_duration * adjusted_compression_ratio
            # 记录调整信息
            scene["_adjustment_info"] = {
                "original_duration": original_duration,
                "compression_ratio": adjusted_compression_ratio,
                "reason": "安全余量调整"
            }
            
        # 重新计算调整后的总时长
        new_total = protected_total + sum(scene.get(duration_key, 0) for scene in compressible_scenes)
        
        logger.info(f"安全余量调整：原始时长 {current_total:.2f} -> 调整后 {new_total:.2f}，目标 {target_duration:.2f}")
        
        return adjusted_scenes, {
            "adjusted": True,
            "original_duration": current_total,
            "new_duration": new_total,
            "target_duration": target_duration,
            "safety_threshold": self.config["critical_threshold"],
            "compression_applied": adjusted_compression_ratio,
            "scenes_adjusted": len(compressible_scenes),
            "scenes_protected": len(protected_scenes)
        }

    def set_margin_ratio(self, margin_ratio: float) -> None:
        """设置安全余量比例
        
        Args:
            margin_ratio: 新的安全余量比例
        """
        # 确保余量在合理范围内
        min_margin = self.config["min_margin"]
        max_margin = self.config["max_margin"]
        
        if margin_ratio < min_margin:
            logger.warning(f"安全余量比例 {margin_ratio:.1%} 小于最小值 {min_margin:.1%}，已调整为最小值")
            margin_ratio = min_margin
        elif margin_ratio > max_margin:
            logger.warning(f"安全余量比例 {margin_ratio:.1%} 大于最大值 {max_margin:.1%}，已调整为最大值")
            margin_ratio = max_margin
            
        self.margin = margin_ratio
        logger.info(f"安全余量比例已设置为 {self.margin:.1%}")

def apply_safety_margin(target_duration: float, margin_ratio: float = 0.05) -> float:
    """应用安全余量到目标时长
    
    Args:
        target_duration: 目标时长
        margin_ratio: 安全余量比例，默认为5%
        
    Returns:
        应用安全余量后的实际可用时长
    """
    keeper = MarginKeeper(margin_ratio)
    return keeper.apply_margin(target_duration)

def adjust_for_safety(scenes: List[Dict[str, Any]], target_duration: float, 
                    margin_ratio: float = 0.05, 
                    config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """根据安全余量调整场景时长
    
    Args:
        scenes: 场景列表
        target_duration: 目标总时长
        margin_ratio: 安全余量比例，默认为5%
        config: 额外配置参数
        
    Returns:
        调整后的场景列表和调整信息
    """
    keeper = MarginKeeper(margin_ratio, config)
    return keeper.adjust_scene_durations(scenes, target_duration)

def create_demo_scenes() -> List[Dict[str, Any]]:
    """创建演示用的场景数据
    
    Returns:
        场景列表
    """
    return [
        {
            "id": "scene1",
            "name": "开场白",
            "start_time": 0,
            "end_time": 60,
            "duration": 60,  # 1分钟
            "_protection_info": {
                "level": "HIGH",
                "strategies": ["NO_TRIM", "LOCK"],
                "reason": "关键开场内容"
            }
        },
        {
            "id": "scene2",
            "name": "过渡场景",
            "start_time": 60,
            "end_time": 90,
            "duration": 30,  # 30秒
        },
        {
            "id": "scene3",
            "name": "主题内容A",
            "start_time": 90,
            "end_time": 270,
            "duration": 180,  # 3分钟
            "_compression_info": {
                "restriction_level": "LOW",
                "allowed_ratio": 0.8
            }
        },
        {
            "id": "scene4",
            "name": "主题内容B",
            "start_time": 270,
            "end_time": 450,
            "duration": 180,  # 3分钟
        },
        {
            "id": "scene5",
            "name": "主题内容C",
            "start_time": 450,
            "end_time": 570,
            "duration": 120,  # 2分钟
        },
        {
            "id": "scene6",
            "name": "结尾总结",
            "start_time": 570,
            "end_time": 630,
            "duration": 60,  # 1分钟
            "_protection_info": {
                "level": "MEDIUM",
                "strategies": ["NO_COMPRESS"],
                "reason": "总结关键点"
            }
        }
    ]

def demo_basic_margin_calculation():
    """演示基本的安全余量计算"""
    logger.info("===== 基本安全余量计算演示 =====")
    
    # 目标时长（秒）
    target_duration = 600.0  # 10分钟
    
    # 应用默认的5%安全余量
    safe_duration = apply_safety_margin(target_duration)
    logger.info(f"目标时长: {target_duration}秒")
    logger.info(f"应用5%安全余量后的实际可用时长: {safe_duration}秒")
    
    # 使用不同的安全余量比例
    safe_duration_3p = apply_safety_margin(target_duration, margin_ratio=0.03)
    logger.info(f"应用3%安全余量后的实际可用时长: {safe_duration_3p}秒")
    
    safe_duration_10p = apply_safety_margin(target_duration, margin_ratio=0.10)
    logger.info(f"应用10%安全余量后的实际可用时长: {safe_duration_10p}秒")
    
    # 演示超出合理范围的安全余量比例会被自动调整
    keeper = MarginKeeper()
    keeper.set_margin_ratio(0.01)  # 低于默认最小值0.02
    keeper.set_margin_ratio(0.20)  # 高于默认最大值0.15

def demo_scene_adjustment():
    """演示场景时长调整"""
    logger.info("\n===== 场景时长调整演示 =====")
    
    # 创建测试场景
    scenes = create_demo_scenes()
    
    # 计算原始总时长
    total_duration = sum(scene["duration"] for scene in scenes)
    logger.info(f"原始场景总时长: {total_duration}秒")
    
    # 设置目标时长略小于当前总时长，触发调整
    target_duration = 600  # 10分钟
    logger.info(f"目标时长上限: {target_duration}秒")
    
    # 使用默认5%安全余量
    adjusted_scenes, info = adjust_for_safety(scenes, target_duration)
    
    if info["adjusted"]:
        logger.info(f"场景已调整: {info['original_duration']}秒 -> {info['new_duration']}秒")
        logger.info(f"调整了 {info['scenes_adjusted']} 个场景，保护了 {info['scenes_protected']} 个场景")
        
        # 打印每个场景的调整信息
        logger.info("\n调整后的场景时长:")
        for i, scene in enumerate(adjusted_scenes):
            original_scene = scenes[i]
            original_duration = original_scene["duration"]
            new_duration = scene["duration"]
            name = scene["name"]
            
            if "_adjustment_info" in scene:
                adjustment = scene["_adjustment_info"]
                ratio = adjustment["compression_ratio"]
                logger.info(f"  {name}: {original_duration}秒 -> {new_duration:.1f}秒 (压缩比例: {ratio:.2f})")
            else:
                logger.info(f"  {name}: {original_duration}秒 (未调整)")
    else:
        logger.info(f"未调整场景: {info['reason']}")
        
    logger.info("\n===== 场景保护功能演示 =====")
    logger.info("启用场景保护，部分场景不会被压缩")
    
    # 创建带有保护标记的测试场景
    protected_scenes = create_demo_scenes()
    
    # 移除原有的保护信息（可能存在于示例场景中）
    for scene in protected_scenes:
        if "_protection_info" in scene:
            del scene["_protection_info"]
    
    # 为特定场景添加保护标记
    protected_scenes[0]["_protection_info"] = {
        "level": "HIGH",
        "strategies": ["NO_COMPRESS", "LOCK"],
        "reason": "开场关键内容"
    }
    
    protected_scenes[5]["_protection_info"] = {
        "level": "HIGH",
        "strategies": ["NO_COMPRESS"],
        "reason": "结尾关键内容"
    }
    
    # 设置更严格的目标时长，使压缩更明显
    target_duration = 550  # 9分10秒
    logger.info(f"更严格的目标时长: {target_duration}秒")
    
    # 创建一个安全余量管理器用于检查场景是否受保护
    protection_checker = MarginKeeper()
    
    # 调整场景
    adjusted_scenes, info = adjust_for_safety(protected_scenes, target_duration)
    
    if info["adjusted"]:
        logger.info(f"场景已调整: {info['original_duration']}秒 -> {info['new_duration']}秒")
        logger.info(f"调整了 {info['scenes_adjusted']} 个场景，保护了 {info['scenes_protected']} 个场景")
        
        # 打印每个场景的调整信息
        logger.info("\n带保护的场景调整结果:")
        for i, scene in enumerate(adjusted_scenes):
            original_scene = protected_scenes[i]
            original_duration = original_scene["duration"]
            new_duration = scene["duration"]
            name = scene["name"]
            is_protected = not protection_checker._is_scene_compressible(original_scene)
            protection_status = "受保护" if is_protected else "未保护"
            
            if "_adjustment_info" in scene:
                adjustment = scene["_adjustment_info"]
                ratio = adjustment["compression_ratio"]
                logger.info(f"  {name} [{protection_status}]: {original_duration}秒 -> {new_duration:.1f}秒 (压缩比例: {ratio:.2f})")
            else:
                logger.info(f"  {name} [{protection_status}]: {original_duration}秒 (未调整)")
    else:
        logger.info(f"未调整场景: {info['reason']}")

def main():
    """主函数"""
    logger.info("安全余量管理功能演示\n")
    
    # 演示基本安全余量计算
    demo_basic_margin_calculation()
    
    # 演示场景时长调整
    demo_scene_adjustment()
    
    logger.info("\n演示完成!")

if __name__ == "__main__":
    main() 