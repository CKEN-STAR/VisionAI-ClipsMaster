"""黄金样本比对系统

此模块提供视频输出与黄金样本的比对功能，用于验证视频处理结果是否符合质量标准。
主要功能：
1. 帧级相似度比较（使用结构相似度或均方误差）
2. 视频质量验证
3. 批量视频比对
"""

import os
import sys
import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("golden_compare")

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class ComparisonResult:
    """比较结果类，保存比较过程中的详细信息"""
    
    def __init__(self):
        self.frame_scores: List[float] = []
        self.min_score: float = 1.0
        self.max_score: float = 0.0
        self.avg_score: float = 0.0
        self.frame_count: int = 0
        self.passed: bool = False
        self.failed_frames: List[int] = []
        
    def add_frame_score(self, frame_idx: int, score: float, threshold: float):
        """添加帧比较分数
        
        Args:
            frame_idx: 帧索引
            score: 相似度分数
            threshold: 通过阈值
        """
        self.frame_scores.append(score)
        self.min_score = min(self.min_score, score)
        self.max_score = max(self.max_score, score)
        self.frame_count += 1
        
        if score < threshold:
            self.failed_frames.append(frame_idx)
    
    def calculate_stats(self):
        """计算比较统计信息"""
        if self.frame_count > 0:
            self.avg_score = sum(self.frame_scores) / self.frame_count
            self.passed = len(self.failed_frames) == 0
        else:
            self.passed = False
    
    def to_dict(self) -> Dict:
        """转换为字典表示
        
        Returns:
            Dict: 比较结果字典
        """
        return {
            "frame_count": self.frame_count,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "avg_score": self.avg_score,
            "passed": self.passed,
            "failed_frames": self.failed_frames
        }


def compare_frames(frame1: np.ndarray, frame2: np.ndarray, method: str = 'ssim') -> float:
    """比较两帧的相似度
    
    Args:
        frame1: 第一帧图像
        frame2: 第二帧图像
        method: 比较方法，'ssim'(结构相似度) 或 'mse'(均方误差)
    
    Returns:
        float: 相似度分数 (0-1范围，1表示完全相同)
    """
    if frame1 is None or frame2 is None:
        return 0.0
    
    # 确保两帧尺寸相同
    if frame1.shape != frame2.shape:
        frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
    
    if method == 'ssim':
        try:
            # 尝试导入scikit-image的SSIM
            from skimage.metrics import structural_similarity as ssim
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            score, _ = ssim(gray1, gray2, full=True)
            return score
        except ImportError:
            logger.warning("scikit-image未安装，回退到MSE方法")
            method = 'mse'  # 回退到MSE
    
    if method == 'mse':
        # 使用均方误差的反比作为相似度
        mse = np.mean((frame1.astype("float") - frame2.astype("float")) ** 2)
        if mse == 0:
            return 1.0
        return 1.0 / (1.0 + mse/100)  # 归一化到0-1范围
    
    # 默认回退
    return 0.0


def validate_video(
    output_path: str, 
    golden_path: str, 
    threshold: float = 0.95, 
    max_frames: int = 300,
    save_failed_frames: bool = False,
    output_dir: Optional[str] = None
) -> ComparisonResult:
    """与黄金样本逐帧比对，验证视频质量
    
    Args:
        output_path: 待测试视频路径
        golden_path: 黄金样本视频路径
        threshold: 相似度阈值 (0-1)
        max_frames: 最大比较帧数
        save_failed_frames: 是否保存失败的帧
        output_dir: 失败帧的保存目录
    
    Returns:
        ComparisonResult: 比较结果对象
    
    Raises:
        FileNotFoundError: 如果视频文件不存在
        ValueError: 如果视频打开失败
        AssertionError: 如果帧比对失败且raise_on_fail为True
    """
    # 检查文件存在
    if not os.path.exists(golden_path):
        raise FileNotFoundError(f"黄金样本文件不存在: {golden_path}")
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"测试视频文件不存在: {output_path}")
    
    # 打开视频文件
    golden = cv2.VideoCapture(golden_path)
    test = cv2.VideoCapture(output_path)
    
    if not golden.isOpened():
        raise ValueError(f"无法打开黄金样本视频: {golden_path}")
    if not test.isOpened():
        raise ValueError(f"无法打开测试视频: {output_path}")
    
    # 创建比较结果对象
    result = ComparisonResult()
    frame_idx = 0
    
    # 创建保存失败帧的目录
    if save_failed_frames and output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        while frame_idx < max_frames:
            golden_ret, golden_frame = golden.read()
            test_ret, test_frame = test.read()
            
            # 如果任一视频读取结束，则停止比较
            if not golden_ret or not test_ret:
                break
            
            # 比较当前帧
            sim_score = compare_frames(golden_frame, test_frame)
            result.add_frame_score(frame_idx, sim_score, threshold)
            
            # 如果需要，保存失败的帧
            if save_failed_frames and output_dir and sim_score < threshold:
                golden_output = os.path.join(output_dir, f"golden_frame_{frame_idx}.png")
                test_output = os.path.join(output_dir, f"test_frame_{frame_idx}.png")
                cv2.imwrite(golden_output, golden_frame)
                cv2.imwrite(test_output, test_frame)
                
                # 生成差异可视化
                diff = cv2.absdiff(golden_frame, test_frame)
                diff_output = os.path.join(output_dir, f"diff_frame_{frame_idx}.png")
                cv2.imwrite(diff_output, diff)
            
            frame_idx += 1
    finally:
        # 关闭视频文件
        golden.release()
        test.release()
    
    # 计算最终统计信息
    result.calculate_stats()
    
    # 打印比较结果
    logger.info(f"视频比对完成:")
    logger.info(f"- 比较帧数: {result.frame_count}")
    logger.info(f"- 平均相似度: {result.avg_score:.4f}")
    logger.info(f"- 最低相似度: {result.min_score:.4f}")
    logger.info(f"- 最高相似度: {result.max_score:.4f}")
    logger.info(f"- 结果: {'通过' if result.passed else '失败'}")
    
    if not result.passed:
        logger.warning(f"失败帧数量: {len(result.failed_frames)}")
        logger.warning(f"失败帧索引: {result.failed_frames[:10]}...")
    
    return result


def batch_validate_videos(
    test_dir: str, 
    golden_dir: str, 
    threshold: float = 0.95,
    file_extensions: List[str] = ['.mp4', '.avi', '.mov'],
    max_frames: int = 300,
    save_failed_frames: bool = False,
    output_dir: Optional[str] = None
) -> Dict[str, ComparisonResult]:
    """批量比对目录下所有视频与黄金样本
    
    Args:
        test_dir: 测试视频目录
        golden_dir: 黄金样本目录
        threshold: 相似度阈值
        file_extensions: 视频文件扩展名列表
        max_frames: 每个视频的最大比较帧数
        save_failed_frames: 是否保存失败的帧
        output_dir: 失败帧的保存基础目录
    
    Returns:
        Dict[str, ComparisonResult]: 文件名到比较结果的映射
    """
    results = {}
    
    # 确保目录存在
    if not os.path.exists(test_dir):
        logger.error(f"测试视频目录不存在: {test_dir}")
        return results
    if not os.path.exists(golden_dir):
        logger.error(f"黄金样本目录不存在: {golden_dir}")
        return results
    
    # 遍历测试目录下的所有视频文件
    for fname in os.listdir(test_dir):
        # 检查文件扩展名
        if not any(fname.lower().endswith(ext) for ext in file_extensions):
            continue
        
        test_path = os.path.join(test_dir, fname)
        golden_path = os.path.join(golden_dir, fname)
        
        # 检查对应的黄金样本是否存在
        if not os.path.exists(golden_path):
            logger.warning(f"黄金样本缺失: {fname}")
            continue
        
        logger.info(f"比对视频: {fname}")
        
        # 为失败帧创建特定文件的输出目录
        file_output_dir = None
        if save_failed_frames and output_dir:
            file_output_dir = os.path.join(output_dir, os.path.splitext(fname)[0])
            os.makedirs(file_output_dir, exist_ok=True)
        
        try:
            # 执行视频比对
            result = validate_video(
                test_path, 
                golden_path, 
                threshold=threshold,
                max_frames=max_frames,
                save_failed_frames=save_failed_frames,
                output_dir=file_output_dir
            )
            results[fname] = result
        except Exception as e:
            logger.error(f"比对视频 {fname} 时出错: {str(e)}")
    
    # 打印总体结果
    passed_count = sum(1 for result in results.values() if result.passed)
    total_count = len(results)
    
    if total_count > 0:
        logger.info(f"批量比对完成: {passed_count}/{total_count} 通过 ({passed_count/total_count*100:.1f}%)")
    else:
        logger.warning("未找到任何可比对的视频")
    
    return results


if __name__ == "__main__":
    # 简单的命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description="视频黄金样本比对工具")
    parser.add_argument("--test", required=True, help="测试视频文件或目录")
    parser.add_argument("--golden", required=True, help="黄金样本文件或目录")
    parser.add_argument("--threshold", type=float, default=0.95, help="相似度阈值 (0-1)")
    parser.add_argument("--max-frames", type=int, default=300, help="最大比较帧数")
    parser.add_argument("--save-failed", action="store_true", help="保存失败帧")
    parser.add_argument("--output-dir", default="./failed_frames", help="失败帧输出目录")
    args = parser.parse_args()
    
    # 检查是单个文件还是目录
    if os.path.isfile(args.test) and os.path.isfile(args.golden):
        # 单个文件比对
        result = validate_video(
            args.test, 
            args.golden, 
            threshold=args.threshold,
            max_frames=args.max_frames,
            save_failed_frames=args.save_failed,
            output_dir=args.output_dir
        )
        sys.exit(0 if result.passed else 1)
    elif os.path.isdir(args.test) and os.path.isdir(args.golden):
        # 批量目录比对
        results = batch_validate_videos(
            args.test, 
            args.golden, 
            threshold=args.threshold,
            max_frames=args.max_frames,
            save_failed_frames=args.save_failed,
            output_dir=args.output_dir
        )
        # 如果有任何视频比对失败，则返回非零退出码
        sys.exit(0 if all(r.passed for r in results.values()) else 1)
    else:
        logger.error("测试和黄金样本必须同为文件或同为目录")
        sys.exit(1) 