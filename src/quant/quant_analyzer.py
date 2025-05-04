"""可视化量化分析模块

此模块实现量化模型的可视化分析，包括：
1. 性能指标分析
2. 资源使用分析
3. 精度损失分析
4. 趋势分析
5. 多维度对比
"""

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from loguru import logger
from .quant_meta import QuantMetaManager

class QuantAnalyzer:
    """量化分析器"""
    
    def __init__(self, meta_manager: Optional[QuantMetaManager] = None):
        """初始化分析器
        
        Args:
            meta_manager: 元数据管理器实例
        """
        self.meta_manager = meta_manager or QuantMetaManager()
        self.output_dir = "analysis_results"
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze_performance(self,
                          model_hash: str,
                          save_plot: bool = True) -> Optional[go.Figure]:
        """分析性能指标
        
        Args:
            model_hash: 模型哈希值
            save_plot: 是否保存图表
            
        Returns:
            Optional[go.Figure]: 性能分析图表
        """
        try:
            # 获取模型记录
            records = self.meta_manager.records.get(model_hash, [])
            if not records:
                logger.warning(f"未找到模型记录: {model_hash}")
                return None
            
            # 提取性能数据
            timestamps = [r.timestamp for r in records]
            performance_data = {
                'throughput': [r.performance.get('throughput', 0) for r in records],
                'latency': [r.performance.get('latency', 0) for r in records],
                'memory': [r.memory_usage.get('used', 0) for r in records]
            }
            
            # 创建性能趋势图
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('吞吐量', '延迟', '内存使用'),
                vertical_spacing=0.1
            )
            
            # 添加吞吐量曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=performance_data['throughput'],
                    mode='lines+markers',
                    name='吞吐量'
                ),
                row=1, col=1
            )
            
            # 添加延迟曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=performance_data['latency'],
                    mode='lines+markers',
                    name='延迟'
                ),
                row=2, col=1
            )
            
            # 添加内存使用曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=performance_data['memory'],
                    mode='lines+markers',
                    name='内存使用'
                ),
                row=3, col=1
            )
            
            # 更新布局
            fig.update_layout(
                title=f'模型性能分析 - {model_hash}',
                height=900,
                showlegend=True
            )
            
            # 保存图表
            if save_plot:
                fig.write_html(os.path.join(
                    self.output_dir,
                    f'performance_analysis_{model_hash}.html'
                ))
            
            return fig
            
        except Exception as e:
            logger.error(f"性能分析失败: {str(e)}")
            return None

    def analyze_accuracy(self,
                       model_hash: str,
                       save_plot: bool = True) -> Optional[go.Figure]:
        """分析精度损失
        
        Args:
            model_hash: 模型哈希值
            save_plot: 是否保存图表
            
        Returns:
            Optional[go.Figure]: 精度分析图表
        """
        try:
            # 获取模型记录
            records = self.meta_manager.records.get(model_hash, [])
            if not records:
                logger.warning(f"未找到模型记录: {model_hash}")
                return None
            
            # 提取精度数据
            timestamps = [r.timestamp for r in records]
            accuracy_data = {
                'accuracy': [r.performance.get('accuracy', 0) for r in records],
                'loss': [r.performance.get('loss', 0) for r in records]
            }
            
            # 创建精度趋势图
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('准确率', '损失值'),
                vertical_spacing=0.1
            )
            
            # 添加准确率曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=accuracy_data['accuracy'],
                    mode='lines+markers',
                    name='准确率'
                ),
                row=1, col=1
            )
            
            # 添加损失值曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=accuracy_data['loss'],
                    mode='lines+markers',
                    name='损失值'
                ),
                row=2, col=1
            )
            
            # 更新布局
            fig.update_layout(
                title=f'模型精度分析 - {model_hash}',
                height=600,
                showlegend=True
            )
            
            # 保存图表
            if save_plot:
                fig.write_html(os.path.join(
                    self.output_dir,
                    f'accuracy_analysis_{model_hash}.html'
                ))
            
            return fig
            
        except Exception as e:
            logger.error(f"精度分析失败: {str(e)}")
            return None

    def analyze_resource_usage(self,
                             model_hash: str,
                             save_plot: bool = True) -> Optional[go.Figure]:
        """分析资源使用
        
        Args:
            model_hash: 模型哈希值
            save_plot: 是否保存图表
            
        Returns:
            Optional[go.Figure]: 资源使用分析图表
        """
        try:
            # 获取模型记录
            records = self.meta_manager.records.get(model_hash, [])
            if not records:
                logger.warning(f"未找到模型记录: {model_hash}")
                return None
            
            # 提取资源使用数据
            timestamps = [r.timestamp for r in records]
            resource_data = {
                'cpu_percent': [r.device_info.get('cpu_percent', 0) for r in records],
                'gpu_memory': [r.memory_usage.get('gpu_allocated', 0) for r in records],
                'memory_percent': [r.memory_usage.get('percent', 0) for r in records]
            }
            
            # 创建资源使用趋势图
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('CPU使用率', 'GPU内存使用', '系统内存使用率'),
                vertical_spacing=0.1
            )
            
            # 添加CPU使用率曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=resource_data['cpu_percent'],
                    mode='lines+markers',
                    name='CPU使用率'
                ),
                row=1, col=1
            )
            
            # 添加GPU内存使用曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=resource_data['gpu_memory'],
                    mode='lines+markers',
                    name='GPU内存使用'
                ),
                row=2, col=1
            )
            
            # 添加系统内存使用率曲线
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=resource_data['memory_percent'],
                    mode='lines+markers',
                    name='系统内存使用率'
                ),
                row=3, col=1
            )
            
            # 更新布局
            fig.update_layout(
                title=f'资源使用分析 - {model_hash}',
                height=900,
                showlegend=True
            )
            
            # 保存图表
            if save_plot:
                fig.write_html(os.path.join(
                    self.output_dir,
                    f'resource_analysis_{model_hash}.html'
                ))
            
            return fig
            
        except Exception as e:
            logger.error(f"资源使用分析失败: {str(e)}")
            return None

    def compare_models(self,
                      model_hashes: List[str],
                      metrics: List[str],
                      save_plot: bool = True) -> Optional[go.Figure]:
        """比较多个模型
        
        Args:
            model_hashes: 模型哈希值列表
            metrics: 指标列表
            save_plot: 是否保存图表
            
        Returns:
            Optional[go.Figure]: 模型对比图表
        """
        try:
            # 验证输入
            if not model_hashes or not metrics:
                logger.warning("模型列表或指标列表为空")
                return None
            
            # 收集数据
            comparison_data = []
            for model_hash in model_hashes:
                records = self.meta_manager.records.get(model_hash, [])
                if records:
                    latest_record = records[-1]
                    model_data = {'model': model_hash}
                    
                    # 收集指定指标
                    for metric in metrics:
                        if metric in latest_record.performance:
                            model_data[metric] = latest_record.performance[metric]
                        elif metric in latest_record.memory_usage:
                            model_data[metric] = latest_record.memory_usage[metric]
                    
                    comparison_data.append(model_data)
            
            if not comparison_data:
                logger.warning("未找到有效的比较数据")
                return None
            
            # 创建对比图表
            df = pd.DataFrame(comparison_data)
            fig = go.Figure()
            
            # 为每个指标添加柱状图
            for metric in metrics:
                if metric in df.columns:
                    fig.add_trace(
                        go.Bar(
                            name=metric,
                            x=df['model'],
                            y=df[metric],
                            text=df[metric].round(4),
                            textposition='auto'
                        )
                    )
            
            # 更新布局
            fig.update_layout(
                title='模型对比分析',
                xaxis_title='模型',
                yaxis_title='指标值',
                barmode='group',
                height=600,
                showlegend=True
            )
            
            # 保存图表
            if save_plot:
                fig.write_html(os.path.join(
                    self.output_dir,
                    'model_comparison.html'
                ))
            
            return fig
            
        except Exception as e:
            logger.error(f"模型对比分析失败: {str(e)}")
            return None

    def generate_report(self, model_hash: str) -> Optional[Dict]:
        """生成分析报告
        
        Args:
            model_hash: 模型哈希值
            
        Returns:
            Optional[Dict]: 分析报告
        """
        try:
            # 获取模型记录
            records = self.meta_manager.records.get(model_hash, [])
            if not records:
                logger.warning(f"未找到模型记录: {model_hash}")
                return None
            
            # 生成报告
            report = {
                'model_hash': model_hash,
                'record_count': len(records),
                'time_range': {
                    'start': records[0].timestamp,
                    'end': records[-1].timestamp
                },
                'performance_summary': self._calculate_performance_summary(records),
                'resource_usage_summary': self._calculate_resource_summary(records),
                'accuracy_summary': self._calculate_accuracy_summary(records),
                'recommendations': self._generate_recommendations(records)
            }
            
            # 保存报告
            try:
                import json
                with open(os.path.join(
                    self.output_dir,
                    f'analysis_report_{model_hash}.json'
                ), 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2)
            except Exception as e:
                logger.error(f"保存分析报告失败: {str(e)}")
            
            return report
            
        except Exception as e:
            logger.error(f"生成分析报告失败: {str(e)}")
            return None

    def _calculate_performance_summary(self,
                                    records: List[Dict]) -> Dict:
        """计算性能总结
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 性能总结
        """
        summary = {
            'throughput': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            },
            'latency': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            }
        }
        
        count = 0
        for record in records:
            if 'performance' in record:
                perf = record.performance
                count += 1
                
                # 更新吞吐量统计
                if 'throughput' in perf:
                    throughput = perf['throughput']
                    summary['throughput']['min'] = min(
                        summary['throughput']['min'],
                        throughput
                    )
                    summary['throughput']['max'] = max(
                        summary['throughput']['max'],
                        throughput
                    )
                    summary['throughput']['avg'] += throughput
                
                # 更新延迟统计
                if 'latency' in perf:
                    latency = perf['latency']
                    summary['latency']['min'] = min(
                        summary['latency']['min'],
                        latency
                    )
                    summary['latency']['max'] = max(
                        summary['latency']['max'],
                        latency
                    )
                    summary['latency']['avg'] += latency
        
        # 计算平均值
        if count > 0:
            summary['throughput']['avg'] /= count
            summary['latency']['avg'] /= count
        
        return summary

    def _calculate_resource_summary(self,
                                 records: List[Dict]) -> Dict:
        """计算资源使用总结
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 资源使用总结
        """
        summary = {
            'memory': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            },
            'gpu_memory': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            }
        }
        
        count = 0
        for record in records:
            if 'memory_usage' in record:
                memory = record.memory_usage
                count += 1
                
                # 更新内存使用统计
                if 'used' in memory:
                    used = memory['used']
                    summary['memory']['min'] = min(
                        summary['memory']['min'],
                        used
                    )
                    summary['memory']['max'] = max(
                        summary['memory']['max'],
                        used
                    )
                    summary['memory']['avg'] += used
                
                # 更新GPU内存使用统计
                if 'gpu_allocated' in memory:
                    gpu_mem = memory['gpu_allocated']
                    summary['gpu_memory']['min'] = min(
                        summary['gpu_memory']['min'],
                        gpu_mem
                    )
                    summary['gpu_memory']['max'] = max(
                        summary['gpu_memory']['max'],
                        gpu_mem
                    )
                    summary['gpu_memory']['avg'] += gpu_mem
        
        # 计算平均值
        if count > 0:
            summary['memory']['avg'] /= count
            summary['gpu_memory']['avg'] /= count
        
        return summary

    def _calculate_accuracy_summary(self,
                                 records: List[Dict]) -> Dict:
        """计算精度总结
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 精度总结
        """
        summary = {
            'accuracy': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            },
            'loss': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0
            }
        }
        
        count = 0
        for record in records:
            if 'performance' in record:
                perf = record.performance
                count += 1
                
                # 更新准确率统计
                if 'accuracy' in perf:
                    accuracy = perf['accuracy']
                    summary['accuracy']['min'] = min(
                        summary['accuracy']['min'],
                        accuracy
                    )
                    summary['accuracy']['max'] = max(
                        summary['accuracy']['max'],
                        accuracy
                    )
                    summary['accuracy']['avg'] += accuracy
                
                # 更新损失值统计
                if 'loss' in perf:
                    loss = perf['loss']
                    summary['loss']['min'] = min(
                        summary['loss']['min'],
                        loss
                    )
                    summary['loss']['max'] = max(
                        summary['loss']['max'],
                        loss
                    )
                    summary['loss']['avg'] += loss
        
        # 计算平均值
        if count > 0:
            summary['accuracy']['avg'] /= count
            summary['loss']['avg'] /= count
        
        return summary

    def _generate_recommendations(self,
                               records: List[Dict]) -> List[str]:
        """生成优化建议
        
        Args:
            records: 记录列表
            
        Returns:
            List[str]: 优化建议列表
        """
        recommendations = []
        
        # 分析最新记录
        if records:
            latest = records[-1]
            
            # 性能建议
            if 'performance' in latest:
                perf = latest.performance
                if perf.get('throughput', 0) < 100:
                    recommendations.append(
                        "建议优化模型结构以提高吞吐量"
                    )
                if perf.get('latency', 0) > 10:
                    recommendations.append(
                        "建议使用更高效的量化方法以降低延迟"
                    )
            
            # 资源使用建议
            if 'memory_usage' in latest:
                memory = latest.memory_usage
                if memory.get('percent', 0) > 80:
                    recommendations.append(
                        "建议优化内存使用，当前内存使用率过高"
                    )
                if memory.get('gpu_allocated', 0) > 1e9:
                    recommendations.append(
                        "建议使用更小的批次大小以减少GPU内存使用"
                    )
            
            # 精度建议
            if 'performance' in latest:
                perf = latest.performance
                if perf.get('accuracy', 1) < 0.9:
                    recommendations.append(
                        "建议调整量化参数以提高模型精度"
                    )
                if perf.get('loss', 0) > 0.1:
                    recommendations.append(
                        "建议使用更精细的量化策略以减少损失"
                    )
        
        return recommendations 