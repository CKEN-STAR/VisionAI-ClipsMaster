#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化策略切换执行器演示

展示如何在实际项目中使用量化切换器，包括：
1. 策略切换API使用
2. 性能监控
3. 内存变化追踪
4. 切换历史分析
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, List, Any
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.quant.quant_switcher import QuantSwitcher, load_model_with_level, unload_model
from src.utils.memory_guard import MemoryGuard


# 简单表格打印函数，替代tabulate库
def print_table(data, headers=None, padding=2):
    """打印简单表格"""
    if not data:
        return
    
    # 如果有表头，添加到数据的最前面
    if headers:
        data = [headers] + data
    
    # 计算每列的最大宽度
    col_widths = []
    for i in range(len(data[0])):
        col_widths.append(max(len(str(row[i])) for row in data) + padding)
    
    # 打印表头分隔符
    if headers:
        header_sep = "+" + "+".join("-" * width for width in col_widths) + "+"
        print(header_sep)
    
    # 打印数据
    for i, row in enumerate(data):
        row_str = "|"
        for j, cell in enumerate(row):
            row_str += str(cell).ljust(col_widths[j]) + "|"
        print(row_str)
        
        # 如果是表头行，打印分隔符
        if i == 0 and headers:
            print(header_sep)
    
    # 打印底部分隔符
    bottom_sep = "+" + "+".join("-" * width for width in col_widths) + "+"
    print(bottom_sep)


class QuantSwitchDemo:
    """量化策略切换演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        # 创建内存监控器
        self.memory_guard = MemoryGuard(
            low_memory_threshold=0.75,
            critical_threshold=0.90,
            enable_monitoring=True
        )
        
        # 创建量化切换器
        self.switcher = QuantSwitcher(memory_guard=self.memory_guard)
        
        # 注册测试模型
        self.models = {
            "chinese": "qwen2.5-7b-zh",
            "english": "mistral-7b-en"
        }
        
        # 量化级别切换时间数据
        self.switch_times = {}
        
        # 初始化
        self._register_models()
        logger.info("量化切换演示已初始化")
    
    def _register_models(self):
        """注册测试模型到切换器"""
        for model_type, model_name in self.models.items():
            self.switcher.register_model(
                model_name=model_name,
                load_func=lambda level, name=model_name: self._mock_load_model(name, level),
                unload_func=lambda name=model_name: self._mock_unload_model(name)
            )
            logger.info(f"已注册模型: {model_name}")
    
    def _mock_load_model(self, model_name: str, quant_level: str) -> bool:
        """模拟加载模型，按不同量化级别有不同加载时间"""
        logger.info(f"加载模型 {model_name}，量化级别 {quant_level}")
        
        # 模拟不同量化级别的加载时间
        load_times = {
            "Q2_K": 1.2,
            "Q3_K_M": 1.5,
            "Q4_K_M": 2.0,
            "Q5_K_M": 2.5,
            "Q6_K": 3.0
        }
        
        # 不同模型有不同的基础加载时间
        base_time = 1.0 if model_name.endswith("-zh") else 1.2
        
        # 模拟加载耗时
        time.sleep(base_time + load_times.get(quant_level, 1.0))
        
        # 模拟内存分配
        memory_sizes = {
            "Q2_K": 2800,
            "Q3_K_M": 3400,
            "Q4_K_M": 4100,
            "Q5_K_M": 5200,
            "Q6_K": 6300
        }
        
        # 分配一个大数组来模拟内存占用
        size_mb = memory_sizes.get(quant_level, 4000)
        self._allocate_memory(size_mb)
        
        logger.info(f"模型 {model_name} 已加载，量化级别 {quant_level}")
        return True
    
    def _mock_unload_model(self, model_name: str) -> bool:
        """模拟卸载模型"""
        logger.info(f"卸载模型 {model_name}")
        
        # 模拟卸载耗时
        time.sleep(0.5)
        
        # 手动触发垃圾回收
        import gc
        gc.collect()
        
        logger.info(f"模型 {model_name} 已卸载")
        return True
    
    def _allocate_memory(self, size_mb: int) -> None:
        """
        分配指定大小的内存以模拟模型加载
        
        Args:
            size_mb: 要分配的内存大小(MB)
        """
        # 这只是演示用，实际并不分配这么多内存
        # 但会模拟内存分配的影响
        logger.info(f"模拟分配 {size_mb}MB 内存")
        dummy_data = bytearray(1024 * 100)  # 分配100KB作为象征
    
    def demonstrate_basic_switching(self) -> None:
        """演示基本的量化级别切换"""
        print("\n基本量化级别切换演示")
        print("=" * 60)
        
        # 选择一个模型进行演示
        model_name = self.models["chinese"]
        self.switcher.active_model = model_name
        
        # 定义要切换的量化级别序列
        quant_levels = ["Q4_K_M", "Q2_K", "Q5_K_M", "Q3_K_M", "Q6_K"]
        
        # 表格数据
        table_data = []
        
        # 依次切换到不同的量化级别
        for i, level in enumerate(quant_levels):
            # 记录切换前的内存状态
            mem_before = psutil.virtual_memory()
            
            # 执行切换
            start_time = time.time()
            success = self.switcher.switch(level)
            duration = time.time() - start_time
            
            # 记录切换后的内存状态
            mem_after = psutil.virtual_memory()
            memory_change = (mem_after.used - mem_before.used) / (1024 * 1024)
            
            # 添加到表格数据
            from_level = quant_levels[i-1] if i > 0 else "None"
            table_data.append([
                f"{from_level} → {level}",
                f"{duration:.2f}秒",
                f"{memory_change:+.2f}MB",
                "✓" if success else "✗"
            ])
        
        # 打印表格
        print_table(
            table_data,
            headers=["切换路径", "耗时", "内存变化", "结果"]
        )
    
    def demonstrate_auto_switching(self) -> None:
        """演示自动量化级别切换"""
        print("\n自动量化级别切换演示")
        print("=" * 60)
        
        # 测试不同内存状态下的自动切换
        memory_scenarios = [
            ("初始状态", self.models["chinese"]),
            ("加载数据后", self.models["chinese"]),
            ("视频处理中", self.models["english"]),
            ("内存压力大", self.models["english"])
        ]
        
        # 表格数据
        table_data = []
        
        for scenario, model in memory_scenarios:
            # 检查当前内存状态
            mem_info = psutil.virtual_memory()
            available_mb = mem_info.available / (1024 * 1024)
            
            # 执行自动切换
            self.switcher.active_model = model
            start_time = time.time()
            success = self.switcher.auto_switch(model)
            duration = time.time() - start_time
            
            # 获取选择的级别
            selected_level = self.switcher.get_current_level()
            
            # 添加到表格数据
            table_data.append([
                scenario,
                model,
                f"{available_mb:.0f}MB",
                selected_level,
                f"{duration:.2f}秒",
                "✓" if success else "✗"
            ])
            
            # 短暂暂停，模拟系统状态变化
            time.sleep(1)
        
        # 打印表格
        print_table(
            table_data,
            headers=["场景", "模型", "可用内存", "选择级别", "耗时", "结果"]
        )
    
    def demonstrate_switch_performance(self) -> None:
        """演示切换性能分析"""
        print("\n量化切换性能分析")
        print("=" * 60)
        
        model_name = self.models["chinese"]
        self.switcher.active_model = model_name
        
        # 测试所有可能的切换路径
        levels = ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K"]
        
        # 表格数据
        performance_data = []
        
        # 初始化矩阵数据
        matrix_data = [["-" for _ in range(len(levels))] for _ in range(len(levels))]
        
        # 测试所有切换组合的性能
        for i, from_level in enumerate(levels):
            # 先切换到起始级别
            self.switcher.switch(from_level)
            
            for j, to_level in enumerate(levels):
                if from_level == to_level:
                    continue
                
                # 执行多次切换取平均值
                total_time = 0
                repeat_count = 2
                
                for _ in range(repeat_count):
                    # 确保当前是from_level
                    if self.switcher.get_current_level() != from_level:
                        self.switcher.switch(from_level)
                    
                    # 执行切换并计时
                    start_time = time.time()
                    self.switcher.switch(to_level)
                    duration = time.time() - start_time
                    
                    total_time += duration
                
                # 计算平均切换时间
                avg_time = total_time / repeat_count
                
                # 填充矩阵
                matrix_data[i][j] = f"{avg_time:.2f}秒"
                
                # 加入性能数据
                performance_data.append([
                    f"{from_level} → {to_level}",
                    f"{avg_time:.2f}秒"
                ])
        
        # 打印性能数据
        print("切换路径性能:")
        print_table(
            performance_data,
            headers=["切换路径", "平均耗时"]
        )
        
        # 打印切换时间矩阵
        print("\n切换时间矩阵 (秒):")
        matrix_headers = ["FROM \\ TO"] + levels
        matrix_with_headers = [
            [levels[i]] + row for i, row in enumerate(matrix_data)
        ]
        print_table(
            matrix_with_headers,
            headers=matrix_headers
        )
    
    def demonstrate_memory_impact(self) -> None:
        """演示切换的内存影响"""
        print("\n量化级别内存影响分析")
        print("=" * 60)
        
        model_name = self.models["chinese"]
        self.switcher.active_model = model_name
        
        # 测试所有级别的内存影响
        levels = ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K"]
        
        # 表格数据
        memory_data = []
        
        # 测试每个级别的内存情况
        for level in levels:
            # 记录切换前的内存
            gc_before = self._run_gc_and_measure()
            
            # 执行切换
            self.switcher.switch(level)
            
            # 记录切换后的内存
            time.sleep(0.5)  # 等待内存稳定
            mem_after = psutil.virtual_memory()
            
            # 获取量化级别信息
            level_info = self.switcher.quant_config.get_level_info(level) or {}
            
            # 添加到表格数据
            memory_data.append([
                level,
                f"{level_info.get('memory_usage', 0):.0f}MB",
                f"{level_info.get('quality_score', 0)}/100",
                f"{mem_after.percent:.1f}%",
                f"{(mem_after.total - mem_after.available) / (1024 * 1024):.0f}MB"
            ])
        
        # 打印内存数据
        print_table(
            memory_data,
            headers=["量化级别", "预计内存", "质量评分", "内存使用率", "实际内存"]
        )
    
    def _run_gc_and_measure(self) -> Dict:
        """
        运行垃圾回收并测量内存状态
        
        Returns:
            Dict: 内存状态信息
        """
        import gc
        gc.collect()
        return psutil.virtual_memory()
    
    def demonstrate_all(self) -> None:
        """运行所有演示"""
        print("\n" + "=" * 80)
        print(" " * 30 + "量化策略切换器演示")
        print("=" * 80)
        
        # 运行各项演示
        self.demonstrate_basic_switching()
        self.demonstrate_auto_switching()
        self.demonstrate_switch_performance()
        self.demonstrate_memory_impact()
        
        # 查看历史记录
        history = self.switcher.get_switch_history()
        
        print("\n切换历史记录 (最近5条):")
        print("=" * 60)
        history_data = []
        
        for record in history[-5:]:
            history_data.append([
                time.strftime("%H:%M:%S", time.localtime(record['timestamp'])),
                f"{record['from_level'] or 'None'} → {record['to_level']}",
                f"{record['duration']:.2f}秒",
                f"{record['memory_change']:.2f}MB"
            ])
        
        print_table(
            history_data,
            headers=["时间", "切换路径", "耗时", "内存变化"]
        )
        
        print("\n演示完成!")


def main():
    """主函数"""
    # 设置日志级别
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    try:
        # 创建并运行演示
        demo = QuantSwitchDemo()
        demo.demonstrate_all()
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 