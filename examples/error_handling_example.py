#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理示例程序

演示如何在VisionAI-ClipsMaster中正确处理错误，包括错误捕获、分类、记录和恢复
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, Union

# 确保能够导入src模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入错误相关模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
    from src.exporters.error_dashboard import get_error_monitor
    from src.utils.exception_classifier import get_exception_classifier
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保您在正确的目录中运行此示例")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("error_handling_example")


def demonstrate_error_handling() -> None:
    """演示各种错误处理方法"""
    # 获取错误监控看板实例
    monitor = get_error_monitor()
    
    # 启动错误监控
    monitor.start_monitoring()
    logger.info("已启动错误监控")
    
    # 注册错误回调函数
    monitor.register_callback(error_callback)
    
    # 演示不同类型的错误处理
    logger.info("\n=== 1. 基本错误捕获与记录 ===")
    basic_error_handling()
    
    logger.info("\n=== 2. 使用不同的错误类型 ===")
    handle_different_error_types()
    
    logger.info("\n=== 3. 错误恢复示例 ===")
    error_recovery_example()
    
    logger.info("\n=== 4. 错误分类和分析 ===")
    error_classification_example()
    
    # 获取错误统计
    stats = monitor.stop_monitoring()
    
    # 打印最终统计
    logger.info("\n=== 错误监控统计 ===")
    logger.info(f"总错误数: {stats.get('total_errors', 0)}")
    logger.info(f"错误类型分布: {stats.get('error_types', {})}")
    logger.info(f"错误组件分布: {stats.get('component_errors', {})}")


def error_callback(metrics: Dict[str, Any]) -> None:
    """错误监控回调函数
    
    当发生新错误时被调用
    
    Args:
        metrics: 错误监控指标
    """
    if metrics.get('recent_errors'):
        latest = metrics['recent_errors'][-1]
        logger.info(f"[回调] 检测到新错误: {latest.get('error_code')} - {latest.get('message')}")
        logger.info(f"[回调] 建议: {latest.get('suggestion', '无建议')}")


def basic_error_handling() -> None:
    """基本的错误捕获与记录演示"""
    monitor = get_error_monitor()
    
    # 示例1: 简单try-except
    try:
        logger.info("尝试打开不存在的文件...")
        with open("不存在的文件.txt", "r") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        # 将错误记录到监控看板
        monitor.update_dashboard(e)
    
    # 示例2: 使用自定义错误
    try:
        logger.info("模拟文件未找到错误...")
        raise ClipMasterError(
            "文件未找到", 
            code=ErrorCode.FILE_NOT_FOUND,
            details={"path": "test/missing.mp4", "operation": "read"}
        )
    except ClipMasterError as e:
        logger.error(f"发生自定义错误: {e.message} (代码: {e.code})")
        logger.error(f"错误详情: {e.details}")
        # 将错误记录到监控看板
        monitor.update_dashboard(e)


def handle_different_error_types() -> None:
    """处理不同类型错误的示例"""
    monitor = get_error_monitor()
    
    # 文件操作错误
    try:
        logger.info("模拟文件权限错误...")
        raise ClipMasterError(
            "无权限访问文件", 
            code=ErrorCode.PERMISSION_DENIED,
            details={"path": "/system/protected.file"}
        )
    except ClipMasterError as e:
        if e.code == ErrorCode.PERMISSION_DENIED:
            logger.error("权限错误: 需要管理员权限")
            # 在实际应用中，可以提示用户或尝试提升权限
        monitor.update_dashboard(e)
    
    # 模型错误
    try:
        logger.info("模拟模型加载错误...")
        raise ClipMasterError(
            "模型加载失败", 
            code=ErrorCode.MODEL_ERROR,
            details={"model": "qwen2.5-7b-zh", "reason": "文件不完整"}
        )
    except ClipMasterError as e:
        if e.code == ErrorCode.MODEL_ERROR:
            logger.error("模型错误: 建议重新下载模型")
            # 在实际应用中，可以提供重新下载模型的选项
        monitor.update_dashboard(e)
    
    # 网络错误
    try:
        logger.info("模拟网络错误...")
        raise ClipMasterError(
            "API请求失败", 
            code=ErrorCode.NETWORK_ERROR,
            details={"url": "https://api.example.com/v1/generate", "status": 503}
        )
    except ClipMasterError as e:
        if e.code == ErrorCode.NETWORK_ERROR:
            logger.error("网络错误: 服务不可用，稍后重试")
            # 在实际应用中，可以实现自动重试逻辑
        monitor.update_dashboard(e)


def error_recovery_example() -> None:
    """错误恢复示例"""
    monitor = get_error_monitor()
    
    # 示例: 多级回退策略
    def process_with_fallback(input_path: str, options: Dict[str, Any]) -> Optional[str]:
        """带有回退策略的处理函数
        
        Args:
            input_path: 输入文件路径
            options: 处理选项
            
        Returns:
            Optional[str]: 输出路径或None表示处理失败
        """
        # 尝试使用首选方法
        try:
            logger.info(f"尝试使用首选方法处理: {input_path}")
            # 模拟首选方法错误
            raise ClipMasterError(
                "GPU加速处理失败", 
                code=ErrorCode.PROCESSING_ERROR,
                details={"device": "cuda:0", "reason": "显存不足"}
            )
        except Exception as primary_error:
            logger.warning(f"首选方法失败: {str(primary_error)}")
            monitor.update_dashboard(primary_error)
            
            # 尝试回退方法1: CPU处理
            try:
                logger.info("尝试使用CPU回退方法...")
                # 模拟回退成功
                return "output_cpu_processed.mp4"
            except Exception as fallback1_error:
                logger.warning(f"CPU回退方法失败: {str(fallback1_error)}")
                monitor.update_dashboard(fallback1_error)
                
                # 尝试回退方法2: 降低品质
                try:
                    logger.info("尝试使用低品质回退方法...")
                    # 模拟成功
                    return "output_low_quality.mp4"
                except Exception as fallback2_error:
                    logger.error(f"所有回退方法失败: {str(fallback2_error)}")
                    monitor.update_dashboard(fallback2_error)
                    return None
    
    # 使用回退处理函数
    result = process_with_fallback("input.mp4", {"quality": "high"})
    if result:
        logger.info(f"处理成功，输出文件: {result}")
    else:
        logger.error("处理失败")


def error_classification_example() -> None:
    """错误分类与分析示例"""
    monitor = get_error_monitor()
    
    try:
        # 导入异常分类器
        try:
            classifier = get_exception_classifier()
        except ImportError:
            logger.warning("无法导入异常分类器，使用简化版本")
            classifier = None
        
        # 生成测试错误
        logger.info("生成测试错误并进行分类...")
        test_error = ClipMasterError(
            "视频帧提取失败", 
            code=ErrorCode.PROCESSING_ERROR,
            details={"video": "broken.mp4", "frame": 120}
        )
        
        # 记录错误
        monitor.update_dashboard(test_error)
        
        # 分类错误
        if classifier:
            classification = classifier.classify(test_error, {})
            logger.info(f"错误分类: {classification.to_dict()}")
            logger.info(f"严重程度: {classification.severity}")
            logger.info(f"建议操作: {classification.recommended_action}")
        
        # 获取错误统计
        dashboard_data = monitor.get_dashboard_data()
        
        # 分析错误模式
        logger.info("\n-- 错误模式分析 --")
        logger.info(f"错误类别分布: {dashboard_data['error_categories']}")
        logger.info(f"组件错误分布: {dashboard_data['component_errors']}")
        
        # 获取错误摘要
        summary = monitor.get_error_summary()
        logger.info(f"\n错误状态: {summary['status']}")
        logger.info(f"错误总数: {summary['total_errors']}")
        logger.info(f"最常见错误: {summary['most_common_error']}")
        logger.info(f"恢复建议: {summary['suggestion']}")
        
    except Exception as e:
        logger.error(f"分类示例出错: {str(e)}")
        monitor.update_dashboard(e)


if __name__ == "__main__":
    try:
        demonstrate_error_handling()
    except Exception as e:
        logger.critical(f"示例程序崩溃: {str(e)}")
        sys.exit(1) 