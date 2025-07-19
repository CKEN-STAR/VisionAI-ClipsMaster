#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 帧率转换器

此模块提供用于在时间和帧之间进行精确转换的功能，
支持各种帧率预设，并处理不同帧率之间的适配。

包含功能：
1. 秒到帧的精确转换（四舍五入或向上/向下取整）
2. 帧到秒的转换
3. 不同帧率之间的转换
4. 常见预设帧率的支持
"""

import math
import logging
from enum import Enum
from typing import Union, Dict, List, Tuple, Optional

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 如果无法导入，使用基本日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    def get_logger(name):
        return logging.getLogger(name)

# 配置日志
logger = get_logger("fps_converter")

# 预设帧率
FPS_PRESETS = {
    "film": 24.0,        # 电影标准
    "pal": 25.0,         # PAL电视标准
    "ntsc": 29.97,       # NTSC电视标准
    "ntsc_film": 23.976, # NTSC电影标准
    "web": 30.0,         # 网络视频常用
    "high": 60.0,        # 高帧率视频
    "ultra": 120.0       # 超高帧率视频
}

class RoundingMethod(Enum):
    """帧数舍入方法枚举"""
    ROUND = "round"      # 四舍五入
    FLOOR = "floor"      # 向下取整
    CEIL = "ceil"        # 向上取整
    
    def apply(self, value: float) -> int:
        """应用舍入方法到指定值
        
        Args:
            value: 要舍入的值
            
        Returns:
            舍入后的整数值
        """
        if self == RoundingMethod.ROUND:
            return round(value)
        elif self == RoundingMethod.FLOOR:
            return math.floor(value)
        elif self == RoundingMethod.CEIL:
            return math.ceil(value)
        else:
            # 默认使用四舍五入
            return round(value)


def time_to_frames(seconds: float, fps: Union[int, float], 
                  rounding: RoundingMethod = RoundingMethod.ROUND) -> int:
    """时间(秒) → 剪辑轨道帧号
    
    将秒数转换为特定帧率下的帧数。
    
    Args:
        seconds: 时间，以秒为单位
        fps: 帧率，每秒的帧数
        rounding: 舍入方法，默认为四舍五入
        
    Returns:
        int: 对应的帧数
        
    Examples:
        >>> time_to_frames(1.5, 30)  # 1.5秒在30fps下是45帧
        45
        >>> time_to_frames(1.5, 25)  # 1.5秒在25fps下是38帧(37.5四舍五入)
        38
    """
    if seconds < 0:
        raise ValueError("时间不能为负值")
    
    if fps <= 0:
        raise ValueError("帧率必须为正数")
    
    # 计算原始帧数(可能是小数)
    raw_frames = seconds * float(fps)
    
    # 使用指定的舍入方法
    return rounding.apply(raw_frames)


def frames_to_time(frames: int, fps: Union[int, float]) -> float:
    """剪辑轨道帧号 → 时间(秒)
    
    将特定帧率下的帧数转换为秒数。
    
    Args:
        frames: 帧数
        fps: 帧率，每秒的帧数
        
    Returns:
        float: 对应的时间，以秒为单位
        
    Examples:
        >>> frames_to_time(45, 30)  # 30fps下的45帧是1.5秒
        1.5
        >>> frames_to_time(38, 25)  # 25fps下的38帧是1.52秒
        1.52
    """
    if frames < 0:
        raise ValueError("帧数不能为负值")
    
    if fps <= 0:
        raise ValueError("帧率必须为正数")
    
    # 直接计算秒数
    return frames / float(fps)


def convert_frame_between_fps(
    frame: int, 
    source_fps: Union[int, float], 
    target_fps: Union[int, float],
    rounding: RoundingMethod = RoundingMethod.ROUND
) -> int:
    """在不同帧率之间转换帧号
    
    将一个帧率下的帧号转换为另一个帧率下的对应帧号。
    
    Args:
        frame: 源帧率下的帧号
        source_fps: 源帧率
        target_fps: 目标帧率
        rounding: 舍入方法，默认为四舍五入
        
    Returns:
        int: 目标帧率下的帧号
        
    Examples:
        >>> convert_frame_between_fps(30, 30, 25)  # 30fps下的第30帧在25fps下是第25帧
        25
        >>> convert_frame_between_fps(25, 25, 30)  # 25fps下的第25帧在30fps下是第30帧
        30
    """
    if frame < 0:
        raise ValueError("帧数不能为负值")
    
    if source_fps <= 0 or target_fps <= 0:
        raise ValueError("帧率必须为正数")
    
    # 先转换为时间
    time_seconds = frames_to_time(frame, source_fps)
    
    # 再从时间转换为新帧率下的帧号
    return time_to_frames(time_seconds, target_fps, rounding)


def timecode_to_frames(
    timecode: str, 
    fps: Union[int, float],
    rounding: RoundingMethod = RoundingMethod.ROUND
) -> int:
    """时间码 → 帧号
    
    将时间码字符串转换为指定帧率下的帧号。
    支持的时间码格式: "HH:MM:SS.mmm" 或 "HH:MM:SS:FF"
    
    Args:
        timecode: 时间码字符串
        fps: 帧率
        rounding: 舍入方法，默认为四舍五入
        
    Returns:
        int: 对应的帧号
        
    Examples:
        >>> timecode_to_frames("00:00:01.500", 30)  # 1.5秒在30fps下是45帧
        45
        >>> timecode_to_frames("00:00:01:15", 30)   # 1秒15帧在30fps下是45帧
        45
    """
    if fps <= 0:
        raise ValueError("帧率必须为正数")
    
    # 尝试解析两种常见时间码格式
    parts = timecode.strip().split(":")
    
    if len(parts) == 4:  # HH:MM:SS:FF 格式
        hours, minutes, seconds, frames = map(int, parts)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        if frames >= fps:
            raise ValueError(f"帧部分({frames})超出了帧率范围(0-{fps-1})")
        total_seconds += frames / fps
        return time_to_frames(total_seconds, fps, rounding)
    
    elif len(parts) == 3:  # HH:MM:SS.mmm 格式
        try:
            hours, minutes, rest = parts
            if "." in rest:
                seconds_parts = rest.split(".")
                if len(seconds_parts) == 2:
                    seconds, milliseconds = seconds_parts
                    total_seconds = (int(hours) * 3600 + int(minutes) * 60 + 
                                    int(seconds) + int(milliseconds.ljust(3, '0')[:3]) / 1000)
                    return time_to_frames(total_seconds, fps, rounding)
            else:
                # 只有整数秒
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(rest)
                return time_to_frames(total_seconds, fps, rounding)
        except ValueError:
            pass
    
    raise ValueError(f"不支持的时间码格式: {timecode}")


def frames_to_timecode(
    frames: int, 
    fps: Union[int, float], 
    use_frames: bool = False
) -> str:
    """帧号 → 时间码
    
    将帧号转换为时间码字符串。
    
    Args:
        frames: 帧号
        fps: 帧率
        use_frames: 是否使用帧数表示法(HH:MM:SS:FF)而非毫秒(HH:MM:SS.mmm)
        
    Returns:
        str: 时间码字符串
        
    Examples:
        >>> frames_to_timecode(45, 30)             # 返回 "00:00:01.500"
        "00:00:01.500"
        >>> frames_to_timecode(45, 30, True)       # 返回 "00:00:01:15" 
        "00:00:01:15"
    """
    if frames < 0:
        raise ValueError("帧数不能为负值")
    
    if fps <= 0:
        raise ValueError("帧率必须为正数")
    
    # 计算总秒数
    total_seconds = frames_to_time(frames, fps)
    
    # 计算时、分、秒
    hours = int(total_seconds // 3600)
    total_seconds %= 3600
    minutes = int(total_seconds // 60)
    total_seconds %= 60
    seconds = int(total_seconds)
    
    if use_frames:
        # 计算帧部分
        frame_part = int(round((total_seconds - seconds) * fps))
        if frame_part >= fps:  # 处理舍入导致的溢出
            frame_part = 0
            seconds += 1
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame_part:02d}"
    else:
        # 计算毫秒部分
        milliseconds = int(round((total_seconds - seconds) * 1000))
        if milliseconds >= 1000:  # 处理舍入导致的溢出
            milliseconds = 0
            seconds += 1
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def get_preset_fps(preset_name: str) -> float:
    """获取预设帧率值
    
    根据预设名称获取对应的帧率值。
    
    Args:
        preset_name: 预设名称
        
    Returns:
        float: 对应的帧率值
        
    Raises:
        ValueError: 如果找不到指定的预设
    """
    preset_name = preset_name.lower()
    
    if preset_name in FPS_PRESETS:
        return FPS_PRESETS[preset_name]
    
    # 尝试模糊匹配
    for name, fps in FPS_PRESETS.items():
        if preset_name in name or name in preset_name:
            logger.info(f"使用模糊匹配的预设: {name} ({fps}fps)")
            return fps
    
    # 找不到预设，抛出异常
    raise ValueError(f"未知的帧率预设: {preset_name}, 可用预设: {', '.join(FPS_PRESETS.keys())}")


def get_common_fps(source_fps: float, target_fps: float) -> float:
    """查找两个帧率的最小公倍数帧率
    
    查找可以无损转换的公共帧率（通常是最小公倍数）。
    这在需要在两种帧率之间无损转换时很有用。
    
    Args:
        source_fps: 源帧率
        target_fps: 目标帧率
        
    Returns:
        float: 公共帧率
    """
    # 将浮点帧率转换为分数形式
    def to_fraction(fps):
        if fps == int(fps):
            return int(fps), 1
        
        # 处理常见的非整数帧率
        if abs(fps - 29.97) < 0.01:
            return 30000, 1001
        if abs(fps - 23.976) < 0.01:
            return 24000, 1001
        if abs(fps - 59.94) < 0.01:
            return 60000, 1001
        
        # 其他情况，用简单的分数逼近
        precision = 1000  # 精度控制
        numerator = round(fps * precision)
        denominator = precision
        
        # 计算最大公约数以化简分数
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        common_divisor = gcd(numerator, denominator)
        return numerator // common_divisor, denominator // common_divisor
    
    # 计算最小公倍数
    def lcm(a, b):
        return abs(a * b) // math.gcd(a, b) if a and b else 0
    
    source_num, source_den = to_fraction(source_fps)
    target_num, target_den = to_fraction(target_fps)
    
    # 计算分母的最小公倍数
    common_den = lcm(source_den, target_den)
    
    # 调整分子
    adjusted_source_num = source_num * (common_den // source_den)
    adjusted_target_num = target_num * (common_den // target_den)
    
    # 计算分子的最小公倍数
    common_num = lcm(adjusted_source_num, adjusted_target_num)
    
    # 返回公共帧率
    return common_num / common_den


def estimate_quality_loss(source_fps: float, target_fps: float) -> float:
    """估计帧率转换的质量损失
    
    估计从源帧率转换到目标帧率可能导致的质量损失（0-1范围）。
    
    Args:
        source_fps: 源帧率
        target_fps: 目标帧率
        
    Returns:
        float: 估计的质量损失（0表示无损失，1表示最大损失）
    """
    # 简单情况：目标帧率高于或等于源帧率，无损失
    if target_fps >= source_fps:
        return 0.0
    
    # 处理整数倍关系（例如60fps到30fps）
    if source_fps / target_fps == int(source_fps / target_fps):
        return 0.1  # 轻微损失
    
    # 处理电影常见转换案例
    if abs(source_fps - 24) < 0.1 and abs(target_fps - 23.976) < 0.1:
        return 0.02  # 几乎可以忽略不计的损失
    
    if abs(source_fps - 30) < 0.1 and abs(target_fps - 29.97) < 0.1:
        return 0.01  # 几乎可以忽略不计的损失
    
    # 一般情况下的估计
    ratio = target_fps / source_fps
    
    # 非线性评估，帧率越低损失越大
    if ratio < 0.5:
        return min(0.9, (1 - ratio) * 1.2)  # 大幅损失
    else:
        return min(0.5, (1 - ratio) * 0.8)  # 中等损失


class FPSConverter:
    """帧率转换器类
    
    提供与帧率相关的转换和适配功能的综合类。
    """
    
    def __init__(self, default_fps: float = 30.0):
        """初始化帧率转换器
        
        Args:
            default_fps: 默认帧率，用于未指定帧率的情况
        """
        self.default_fps = default_fps
    
    def get_preset(self, name: str) -> float:
        """获取预设帧率
        
        Args:
            name: 预设名称
            
        Returns:
            float: 对应的帧率值
        """
        try:
            return get_preset_fps(name)
        except ValueError:
            logger.warning(f"未找到预设 '{name}'，使用默认帧率 {self.default_fps}fps")
            return self.default_fps
    
    def convert_timeline(
        self, 
        timeline_data: Dict, 
        source_fps: float,
        target_fps: float,
        rounding: RoundingMethod = RoundingMethod.ROUND
    ) -> Dict:
        """转换时间轴数据到新帧率
        
        将整个时间轴数据从一个帧率转换到另一个帧率。
        
        Args:
            timeline_data: 时间轴数据字典
            source_fps: 源帧率
            target_fps: 目标帧率
            rounding: 舍入方法
            
        Returns:
            Dict: 转换后的时间轴数据
        """
        if not timeline_data:
            return {}
        
        # 深拷贝以避免修改原始数据
        import copy
        result = copy.deepcopy(timeline_data)
        
        # 更新全局帧率
        if "fps" in result:
            result["original_fps"] = result["fps"]
            result["fps"] = target_fps
        
        # 转换片段
        if "clips" in result and isinstance(result["clips"], list):
            for clip in result["clips"]:
                self._convert_clip_timing(clip, source_fps, target_fps, rounding)
        
        # 转换轨道
        if "tracks" in result and isinstance(result["tracks"], list):
            for track in result["tracks"]:
                self._convert_track_timing(track, source_fps, target_fps, rounding)
        
        logger.info(f"时间轴已从 {source_fps}fps 转换为 {target_fps}fps")
        return result
    
    def _convert_clip_timing(
        self, 
        clip: Dict, 
        source_fps: float,
        target_fps: float,
        rounding: RoundingMethod
    ) -> None:
        """转换单个片段的时间信息
        
        Args:
            clip: 片段数据字典
            source_fps: 源帧率
            target_fps: 目标帧率
            rounding: 舍入方法
        """
        # 转换基于帧的时间属性
        for key in ["start_frame", "end_frame", "in_frame", "out_frame"]:
            if key in clip and isinstance(clip[key], int):
                clip[key] = convert_frame_between_fps(
                    clip[key], source_fps, target_fps, rounding
                )
        
        # 转换基于秒的时间属性
        for key in ["start_time", "end_time", "duration"]:
            if key in clip and isinstance(clip[key], (int, float)):
                # 对于时间属性，我们保持秒数不变，不需要转换
                pass
    
    def _convert_track_timing(
        self, 
        track: Dict, 
        source_fps: float,
        target_fps: float,
        rounding: RoundingMethod
    ) -> None:
        """转换单个轨道的时间信息
        
        Args:
            track: 轨道数据字典
            source_fps: 源帧率
            target_fps: 目标帧率
            rounding: 舍入方法
        """
        # 更新轨道帧率
        if "frame_rate" in track:
            track["original_frame_rate"] = track["frame_rate"]
            track["frame_rate"] = target_fps
        
        # 转换轨道内的项目
        if "items" in track and isinstance(track["items"], list):
            for item in track["items"]:
                self._convert_clip_timing(item, source_fps, target_fps, rounding)


# 测试代码（当直接运行此模块时）
if __name__ == "__main__":
    # 基本转换测试
    print("==== 基本转换测试 ====")
    print(f"1.5秒在30fps下是 {time_to_frames(1.5, 30)} 帧")
    print(f"1.5秒在25fps下是 {time_to_frames(1.5, 25)} 帧")
    print(f"45帧在30fps下是 {frames_to_time(45, 30):.3f} 秒")
    print(f"38帧在25fps下是 {frames_to_time(38, 25):.3f} 秒")
    
    # 帧率转换测试
    print("\n==== 帧率转换测试 ====")
    print(f"30fps下的第30帧在25fps下是第 {convert_frame_between_fps(30, 30, 25)} 帧")
    print(f"25fps下的第25帧在30fps下是第 {convert_frame_between_fps(25, 25, 30)} 帧")
    
    # 时间码转换测试
    print("\n==== 时间码转换测试 ====")
    print(f"时间码 00:00:01.500 在30fps下是 {timecode_to_frames('00:00:01.500', 30)} 帧")
    print(f"时间码 00:00:01:15 在30fps下是 {timecode_to_frames('00:00:01:15', 30)} 帧")
    print(f"45帧在30fps下的时间码是 {frames_to_timecode(45, 30)}")
    print(f"45帧在30fps下的帧时间码是 {frames_to_timecode(45, 30, True)}")
    
    # 预设测试
    print("\n==== 预设测试 ====")
    for preset in ["film", "pal", "ntsc"]:
        try:
            fps = get_preset_fps(preset)
            print(f"预设 '{preset}' 的帧率是 {fps}fps")
        except ValueError as e:
            print(f"错误: {e}")
    
    # 共同帧率测试
    print("\n==== 共同帧率测试 ====")
    test_pairs = [(24, 30), (25, 30), (29.97, 30), (24, 60)]
    for source, target in test_pairs:
        common = get_common_fps(source, target)
        print(f"{source}fps 和 {target}fps 的共同帧率是 {common}fps")
        loss = estimate_quality_loss(source, target)
        print(f"从 {source}fps 到 {target}fps 的质量损失估计: {loss:.2%}") 